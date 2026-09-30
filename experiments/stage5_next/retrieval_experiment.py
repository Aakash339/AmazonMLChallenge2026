#!/usr/bin/env python3
"""Bounded discovery/confirmation of fuzzy-name + partial-address retrieval."""
from __future__ import annotations
import csv, hashlib, heapq, json, sqlite3, statistics, sys, tempfile, time
from collections import Counter, defaultdict
from pathlib import Path
from difflib import SequenceMatcher

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'student_resource/dataset/train'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'experiments/stage5'))
from candidate_generator import read_rows, build_index, candidates
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations

SPLIT_SEED=20261030; SAMPLE_SEED=20261031; PER_BUCKET=750
THRESHOLDS=(0.95,0.90,0.85,0.80,0.75)

def links(raw): return [x.strip() for x in raw.split(',') if x.strip()]
def rank(seed,sid): return int.from_bytes(hashlib.sha256(f'{seed}\0{sid}'.encode()).digest(),'big')
def address_tokens(raw): return set((normalize_address(raw) or '').split())
def overlap(a,b): return len(a&b)/min(len(a),len(b)) if a and b else 0.0
def f05(p,r): return 1.25*p*r/(0.25*p+r) if 0.25*p+r else 0.0

def prior_ids():
    found=set()
    for p in (ROOT/'experiments').rglob('sample_ids.txt'):
        if p.parent==OUT: continue
        try: found.update(p.read_text(encoding='utf-8').splitlines())
        except OSError: pass
    for p in (ROOT/'experiments').rglob('validation_ids.txt'):
        if p.parent==OUT: continue
        try: found.update(p.read_text(encoding='utf-8').splitlines())
        except OSError: pass
    for p in OUT.glob('sample_ids_bucket*.txt'):
        # This experiment's own saved IDs must reproduce the same deterministic cohort.
        try: found.difference_update(p.read_text(encoding='utf-8').splitlines())
        except OSError: pass
    return found

def select_samples():
    excluded=prior_ids()
    with tempfile.TemporaryDirectory(prefix='s5_next_sample_') as td:
        db=sqlite3.connect(str(Path(td)/'sample.sqlite')); db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('PRAGMA temp_store=FILE')
        db.execute('CREATE TABLE gt(id TEXT PRIMARY KEY,links TEXT NOT NULL,n INTEGER NOT NULL)')
        for i,g in enumerate(read_rows(DATA/'train_ground_truth.tsv'),1):
            ls=links(g['matched_entity_ids']);db.execute('INSERT INTO gt VALUES(?,?,?)',(g['source1_entity_id'],json.dumps(ls),len(ls)))
            if i%100000==0:db.commit()
        db.commit()
        db.execute('CREATE TABLE pool(bucket INTEGER,id TEXT,country TEXT,cls TEXT,rank TEXT,row_json TEXT,truth TEXT)')
        for i,r in enumerate(read_rows(DATA/'train_source1.tsv'),1):
            sid=r['entity_id']; bucket=rank(SPLIT_SEED,sid)%5
            if bucket not in (0,1) or sid in excluded: continue
            got=db.execute('SELECT links,n FROM gt WHERE id=?',(sid,)).fetchone()
            if got is None: raise RuntimeError(f'Missing training truth for {sid}')
            raw,n=got; cls='zero' if n==0 else 'one' if n==1 else 'multi'
            db.execute('INSERT INTO pool VALUES(?,?,?,?,?,?,?)',(bucket,sid,r['country'],cls,f'{rank(SAMPLE_SEED,sid):064x}',json.dumps(r,ensure_ascii=False),raw))
            if i%100000==0: db.commit()
        db.commit()
        chosen=[]; specs={}
        for bucket in (0,1):
            counts={(c,cl):n for c,cl,n in db.execute('SELECT country,cls,COUNT(*) FROM pool WHERE bucket=? GROUP BY country,cls',(bucket,))}
            total=sum(counts.values()); quotas={k:PER_BUCKET*n//total for k,n in counts.items()}
            rem=PER_BUCKET-sum(quotas.values())
            for k in sorted(counts,key=lambda k:(-(PER_BUCKET*counts[k]%total),k[0],k[1]))[:rem]:quotas[k]+=1
            sample=[]
            for (country,cls),q in quotas.items():
                for row in db.execute('SELECT id,row_json,truth FROM pool WHERE bucket=? AND country=? AND cls=? ORDER BY rank,id LIMIT ?',(bucket,country,cls,q)):
                    sid,raw,truth=row; r=json.loads(raw); r['truth']=json.loads(truth);r['class']=cls;r['bucket']=bucket;sample.append(r)
            sample.sort(key=lambda r:(r['country'],r['entity_id']))
            ids=[r['entity_id'] for r in sample]
            if len(ids)!=PER_BUCKET or any(not (t.startswith('S2-') or t.startswith('S3-')) for r in sample for t in r['truth']):
                raise RuntimeError('Sample/ground-truth ID integrity check failed')
            (OUT/f'sample_ids_bucket{bucket}.txt').write_text('\n'.join(ids)+'\n',encoding='utf-8')
            specs[str(bucket)]={'size':len(ids),'holdout_bucket':bucket,'stratum_population':{f'{k[0]}/{k[1]}':counts[k] for k in sorted(counts)},'stratum_sample':{f'{k[0]}/{k[1]}':quotas[k] for k in sorted(quotas)},'id_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),'true_links':sum(len(r['truth']) for r in sample)}
            chosen.extend(sample)
        db.close()
    return chosen,specs,len(excluded)

def main():
    start=time.time(); samples,specs,n_excluded=select_samples()
    missing=[DATA/n for n in ('train_source1.tsv','train_source2.tsv','train_source3.tsv','train_ground_truth.tsv') if not (DATA/n).is_file()]
    if missing: raise SystemExit('Missing supplied training input(s): '+', '.join(map(str,missing)))
    preserve={t for r in samples for t in r['truth']}
    idx=build_index(samples,[DATA/'train_source2.tsv',DATA/'train_source3.tsv'],preserve_ids=preserve)
    predictions={k:{r['entity_id']:set() for r in samples} for k in ('current_combined',)+tuple(f'fuzzy_addr_overlap_{int(t*100)}' for t in THRESHOLDS)}
    candidate_counts=Counter(); recovered=Counter(); thresholds=tuple((t,f'fuzzy_addr_overlap_{int(t*100)}') for t in THRESHOLDS)
    for row in samples:
        sid=row['entity_id']; c=row['country']; truth=set(row['truth']); base_ids=candidates(row,idx); candidate_counts[row['bucket']]+=len(base_ids)
        recovered[row['bucket']]+=sum(t in base_ids for t in truth)
        qname=normalize_name(row['business_name']) or ''; qaddr=normalize_address(row['business_address']) or ''; qa=set(qaddr.split()); qabbr=normalize_address_abbreviations(row['business_address']) or ''
        exact=[]; overlaps=[]; fuzzy_exact=set(); fuzzy_partial={t:set() for t in THRESHOLDS}
        name_postings=[]
        # The frozen A+HF blocks include the exact-name and overlapping-address targets for these queries.
        for tid in base_ids:
            target=idx['target_info'].get(tid)
            if not target or target['country']!=c: continue
            tn=normalize_name(target['business_name']) or '';ta=normalize_address(target.get('business_address')) or '';tab=normalize_address_abbreviations(target.get('business_address')) or ''
            same_addr=bool((qaddr and ta==qaddr) or (qabbr and tab==qabbr))
            if qname and tn==qname:
                name_postings.append(tid)
                if same_addr: exact.append(tid)
                tt=set(ta.split()) if ta else set(); shared=len(qa&tt)
                if shared>=2 and overlap(qa,tt)>=0.40: overlaps.append(tid)
            tt=set(ta.split()) if ta else set(); shared=len(qa&tt)
            if same_addr and qname and tn:
                sim=SequenceMatcher(None,qname,tn,autojunk=False).ratio()
                if sim>=0.75:fuzzy_exact.add(tid)
            if shared>=2 and overlap(qa,tt)>=0.40 and qname and tn:
                sim=SequenceMatcher(None,qname,tn,autojunk=False).ratio()
                for threshold,key in thresholds:
                    if sim>=threshold: fuzzy_partial[threshold].add(tid)
        # Unique-name fallback uses all indexed same-name targets, but only when exact pair is absent.
        base=set(exact)
        if not base and len(name_postings)==1: base=set(name_postings)
        current=base|set(overlaps)|fuzzy_exact
        predictions['current_combined'][sid]=current
        for t,key in thresholds:
            predictions[key][sid]=current|fuzzy_partial[t]
    output={'title':'Fuzzy-name plus partial-address retrieval experiment','split_seed':SPLIT_SEED,'sample_seed':SAMPLE_SEED,'per_bucket':PER_BUCKET,'excluded_prior_validation_ids':n_excluded,'samples':specs,'candidate_rule':'frozen Stage 4 A+HF address/name candidate set; rank/filter by fuzzy name similarity only after at least two shared normalized address tokens and address containment >=0.40','candidate_recall':{str(b):{'candidates':candidate_counts[b],'true_links_found':recovered[b],'true_links':specs[str(b)]['true_links'],'recall':recovered[b]/specs[str(b)]['true_links']} for b in (0,1)},'metrics':{}}
    for b in (0,1):
        rows=[r for r in samples if r['bucket']==b]
        for name,preds in predictions.items():
            per=[];tp=fp=fn=0;z=zc=0
            for r in rows:
                truth=set(r['truth']);p=preds[r['entity_id']];hit=len(truth&p);falsep=len(p-truth);falsen=len(truth-p);tp+=hit;fp+=falsep;fn+=falsen
                if not truth:
                    z+=1;zc+=int(not p);per.append(1.0 if not p else 0.0)
                else: per.append(f05(hit/len(p) if p else 0.0,hit/len(truth)))
            output['metrics'].setdefault(name,{})[str(b)]={'macro_f0_5':statistics.fmean(per),'precision':tp/(tp+fp) if tp+fp else 0.0,'recall':tp/(tp+fn) if tp+fn else 0.0,'tp':tp,'fp':fp,'fn':fn,'zero_match_accuracy':zc/z if z else None,'predicted_ids':sum(len(preds[r['entity_id']]) for r in rows)}
    output['runtime_seconds']=round(time.time()-start,3)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'retrieval_results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'samples':specs,'candidate_recall':output['candidate_recall'],'metrics':output['metrics'],'runtime_seconds':output['runtime_seconds']},indent=2))

if __name__=='__main__':main()
