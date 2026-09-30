#!/usr/bin/env python3
"""Population-proportional held-out evaluation of Submission #1 and two narrow relaxations."""
from __future__ import annotations
import csv, hashlib, heapq, json, math, statistics, time, difflib, sys, sqlite3, tempfile, argparse
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'student_resource/dataset/train'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations

SPLIT_SEED=20261020
SAMPLE_SEED=20261021
SAMPLE_N=10000
CLASSES=('zero','one','multi')

def rows(path):
    with open(path,encoding='utf-8',newline='') as f:
        yield from csv.DictReader(f,delimiter='\t')
def links(s): return [x.strip() for x in s.split(',') if x.strip()]
def h(seed,s): return int.from_bytes(hashlib.sha256(f'{seed}\0{s}'.encode()).digest(),'big')
def sample(split_bucket=0):
    # First define a disjoint 20% entity-level holdout pool, then sample it
    # proportionally by match-count class x observed country.
    # Keep the multi-million-row labels and the holdout pool on disk. Only the
    # final 10k selected records are retained in memory.
    with tempfile.TemporaryDirectory(prefix='stage5_diag_sample_') as td:
        db=sqlite3.connect(str(Path(td)/'sample.sqlite'))
        db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
        db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-65536')
        db.execute('CREATE TABLE g (id TEXT PRIMARY KEY, truth TEXT NOT NULL, n INTEGER NOT NULL)')
        for i,g in enumerate(rows(DATA/'train_ground_truth.tsv'),1):
            ids=links(g['matched_entity_ids'])
            db.execute('INSERT INTO g VALUES(?,?,?)',(g['source1_entity_id'],json.dumps(ids),len(ids)))
            if i%50000==0: db.commit()
        db.commit()
        db.execute('CREATE TABLE holdout (id TEXT PRIMARY KEY, country TEXT, cls TEXT, rank TEXT, row_json TEXT, truth TEXT)')
        for i,r in enumerate(rows(DATA/'train_source1.tsv'),1):
            sid=r['entity_id']
            if h(SPLIT_SEED,sid)%5 != split_bucket: continue
            got=db.execute('SELECT truth,n FROM g WHERE id=?',(sid,)).fetchone()
            if got is None: raise RuntimeError(f'No ground truth row for sampled Source 1 ID {sid}')
            truth,n=got;cl='zero' if n==0 else ('one' if n==1 else 'multi')
            rank=f'{h(SAMPLE_SEED,sid):064x}'
            db.execute('INSERT INTO holdout VALUES(?,?,?,?,?,?)',(sid,r['country'],cl,rank,json.dumps(r,ensure_ascii=False),truth))
            if i%50000==0: db.commit()
        db.commit()
        counts={(cl,c):n for cl,c,n in db.execute('SELECT cls,country,COUNT(*) FROM holdout GROUP BY cls,country')}
        total=sum(counts.values())
        quotas={k:SAMPLE_N*n//total for k,n in counts.items()}
        rem=SAMPLE_N-sum(quotas.values())
        for k in sorted(counts,key=lambda k:(-(SAMPLE_N*counts[k]%total),k[0],k[1]))[:rem]: quotas[k]+=1
        selected=[]
        for (cl,c),q in quotas.items():
            for sid,row_json,truth_json in db.execute('SELECT id,row_json,truth FROM holdout WHERE cls=? AND country=? ORDER BY rank,id LIMIT ?', (cl,c,q)):
                selected.append((sid,json.loads(row_json),json.loads(truth_json)))
        db.close()
    if len(selected)!=SAMPLE_N: raise RuntimeError(f'sample size {len(selected)}')
    selected.sort(key=lambda x:(x[1]['country'],x[0]))
    ids=[x[0] for x in selected]
    (OUT/'sample_ids.txt').write_text('\n'.join(ids)+'\n',encoding='utf-8')
    spec={'split_seed':SPLIT_SEED,'sample_seed':SAMPLE_SEED,'holdout_definition':f'SHA256(split_seed + NUL + S1 ID) integer mod 5 == {split_bucket}; this bucket is disjoint from other hash buckets','sample_method':'population-proportional stratified bottom-k by match class x country within holdout pool','sample_size':len(selected),'holdout_population':total,'stratum_population':{f'{k[0]}/{k[1]}':counts[k] for k in sorted(counts)},'stratum_sample':{f'{k[0]}/{k[1]}':quotas[k] for k in sorted(quotas)},'countries':sorted({k[1] for k in counts}),'ordered_ids_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),'true_links':sum(len(x[2]) for x in selected),'sample_selection_storage':'SQLite temporary file; full ground truth and holdout pool are not retained in Python memory'}
    return selected,spec

def tokens(s): return set((s or '').split())
def overlap(a,b):
    if not a or not b:return 0.0
    return len(a&b)/min(len(a),len(b))
def main():
    global OUT, SPLIT_SEED, SAMPLE_SEED
    ap=argparse.ArgumentParser()
    ap.add_argument('--holdout-bucket',type=int,default=0,choices=range(5))
    ap.add_argument('--split-seed',type=int,default=SPLIT_SEED)
    ap.add_argument('--sample-seed',type=int,default=SAMPLE_SEED)
    ap.add_argument('--output-dir',type=Path,default=OUT)
    args=ap.parse_args();OUT=args.output_dir;SPLIT_SEED=args.split_seed;SAMPLE_SEED=args.sample_seed;OUT.mkdir(parents=True,exist_ok=True)
    required=[DATA/'train_source1.tsv',DATA/'train_source2.tsv',DATA/'train_source3.tsv',DATA/'train_ground_truth.tsv']
    missing=[str(p) for p in required if not p.is_file()]
    if missing:
        raise SystemExit('Held-out evaluation cannot run; required supplied input file(s) missing: '+', '.join(missing))
    started=time.time(); sample_rows,spec=sample(args.holdout_bucket)
    by_name=defaultdict(list); by_addr=defaultdict(list); by_pair=defaultdict(list); by_abbr=defaultdict(list)
    addr_count=Counter(); target_info={}; truth_ids={t for _,_,ls in sample_rows for t in ls}
    qnames=set(); qaddrs=set(); qpairs=set(); qabbr=set()
    for sid,r,ls in sample_rows:
        c=r['country']; n=normalize_name(r['business_name']) or ''; a=normalize_address(r['business_address']) or ''; ab=normalize_address_abbreviations(r['business_address']) or ''
        r['_n']=n;r['_a']=a;r['_ab']=ab;r['_truth']=set(ls)
        if n:qnames.add((c,n))
        if a:qaddrs.add((c,a))
        if ab:qaddrs.add((c,ab))
        if n and a:qpairs.add((c,n,a))
        if n and ab:qabbr.add((c,n,ab))
    scan_start=time.time(); target_rows=0
    for fn in ('train_source2.tsv','train_source3.tsv'):
        for t in rows(DATA/fn):
            target_rows+=1;c=t['country'];n=normalize_name(t['business_name']) or '';a=normalize_address(t['business_address']) or '';ab=normalize_address_abbreviations(t['business_address']) or '';tid=t['entity_id']
            if (c,n) in qnames: by_name[(c,n)].append(tid)
            if a and (c,a) in qaddrs: by_addr[(c,a)].append(tid)
            if ab and (c,ab) in qaddrs: by_addr[(c,ab)].append(tid)
            if n and a and (c,n,a) in qpairs: by_pair[(c,n,a)].append(tid)
            if n and ab and (c,n,ab) in qabbr: by_abbr[(c,n,ab)].append(tid)
            if tid in truth_ids or ((c,n) in qnames) or (a and (c,a) in qaddrs) or (ab and (c,ab) in qaddrs):
                target_info[tid]={'entity_id':tid,'country':c,'business_name':t['business_name'],'business_address':t['business_address'],'n':n,'a':a,'ab':ab,'at':tokens(a)}
    scan_seconds=time.time()-scan_start
    results=[];error_counts=Counter();error_examples=defaultdict(list); fp_categories=Counter(); fn_categories=Counter()
    total_cands=Counter(); outputs={name:[] for name in ('baseline','addr_exact_name_sim_095','name_exact_addr_overlap_080')}
    for sid,r,ls in sample_rows:
        c=r['country'];n=r['_n'];a=r['_a'];ab=r['_ab']; truth=r['_truth']
        exact=set(by_pair.get((c,n,a),()))|set(by_abbr.get((c,n,ab),())) if n and a else set()
        name_ids=set(by_name.get((c,n),())) if n else set()
        addr_ids=(set(by_addr.get((c,a),()))|set(by_addr.get((c,ab),()))) if a else set()
        base=set(exact)
        if not base and len(name_ids)==1: base=name_ids
        # Experiment 1: exact approved address representation plus very high name similarity.
        fuzzy_addr=set()
        for tid in addr_ids:
            t=target_info.get(tid)
            if t and n and t['n'] and difflib.SequenceMatcher(None,n,t['n'],autojunk=False).ratio()>=0.95:
                fuzzy_addr.add(tid)
        # Experiment 2: exact name plus address token containment >= .80 and at least 2 shared tokens.
        fuzzy_name=set()
        if n and a:
            qt=tokens(a)
            for tid in name_ids:
                t=target_info.get(tid)
                if t and len(qt&t['at'])>=2 and overlap(qt,t['at'])>=0.80:
                    fuzzy_name.add(tid)
        variants={'baseline':base,'addr_exact_name_sim_095':base|fuzzy_addr,'name_exact_addr_overlap_080':base|fuzzy_name}
        for k,ids in variants.items():
            outputs[k].append(ids);total_cands[k]+=len(ids)
        # Failure classification for exact baseline, mutually exclusive per missed link.
        for tid in truth-base:
            t=target_info.get(tid,{})
            tn=t.get('n','');ta=t.get('a','');tab=t.get('ab','')
            if not (t.get('business_address') or '').strip(): cat='missing_target_address'
            elif n==tn and a!=ta and ab!=tab: cat='address_variation_same_name'
            elif a==ta or ab==tab: cat='name_variation_same_address'
            elif n==tn: cat='address_variation_same_name'
            elif tokens(n)==tokens(tn) and n!=tn: cat='name_order_or_punctuation'
            elif n and tn and difflib.SequenceMatcher(None,n,tn,autojunk=False).ratio()>=.75: cat='typo_like_name'
            else: cat='other_or_candidate_miss'
            fn_categories[cat]+=1
            if len(error_examples[cat])<8:error_examples[cat].append({'s1':sid,'target':tid,'s1_name':r['business_name'],'target_name':t.get('business_name',''),'s1_address':r['business_address'],'target_address':t.get('business_address','')})
        for tid in base-truth:
            t=target_info.get(tid,{})
            if len(name_ids)>1: cat='ambiguous_exact_name_fallback'
            elif n==t.get('n','') and a==t.get('a',''): cat='exact_pair_false_match_or_label_gap'
            else: cat='other'
            fp_categories[cat]+=1
            if len(error_examples['FP_'+cat])<8:error_examples['FP_'+cat].append({'s1':sid,'target':tid,'s1_name':r['business_name'],'target_name':t.get('business_name',''),'s1_address':r['business_address'],'target_address':t.get('business_address','')})
    def f05(p,rr):return 1.25*p*rr/(.25*p+rr) if .25*p+rr else 0.0
    def evalpred(preds):
        fs=[];tp=fp=fn=predn=0;z=zc=0;by_class=defaultdict(lambda:{'f':[],'tp':0,'fp':0,'fn':0,'entities':0})
        for (_,r,ls),p in zip(sample_rows,preds):
            truth=set(ls); hit=len(truth&p); nfp=len(p-truth); nfn=len(truth-p);tp+=hit;fp+=nfp;fn+=nfn;predn+=len(p)
            cl='zero' if not truth else ('one' if len(truth)==1 else 'multi'); d=by_class[cl];d['tp']+=hit;d['fp']+=nfp;d['fn']+=nfn;d['entities']+=1
            if not truth:
                z+=1
                if not p: fs.append(1.0);d['f'].append(1.0);zc+=1
                else:fs.append(0.0);d['f'].append(0.0)
            else:
                f=f05(hit/len(p) if p else 0.0,hit/len(truth));fs.append(f);d['f'].append(f)
        class_metrics={cl:{'entities':d['entities'],'macro_f0_5':statistics.fmean(d['f']),'tp':d['tp'],'fp':d['fp'],'fn':d['fn']} for cl,d in by_class.items()}
        return {'macro_f0_5':statistics.fmean(fs),'micro_precision':tp/(tp+fp) if tp+fp else 0,'micro_recall':tp/(tp+fn) if tp+fn else 0,'tp':tp,'fp':fp,'fn':fn,'predicted_links':predn,'zero_match_entities':z,'zero_match_correct_empty':zc,'zero_match_accuracy':zc/z if z else None,'per_truth_class':class_metrics}
    for k,preds in outputs.items():
        m=evalpred(preds);m['final_prediction_ids']=total_cands[k];m['per_s1']={
            'zero':sum(not x for x in preds),'one':sum(len(x)==1 for x in preds),'multi':sum(len(x)>1 for x in preds)}
        results.append((k,m))
    # Variations: how many added predictions help/hurt compared with baseline.
    baseline=outputs['baseline'];delta={}
    for k in ('addr_exact_name_sim_095','name_exact_addr_overlap_080'):
        added_tp=added_fp=0
        for (_,_,ls),b,p in zip(sample_rows,baseline,outputs[k]):
            added=p-b; added_tp+=len(added&set(ls));added_fp+=len(added-set(ls))
        delta[k]={'added_true_links':added_tp,'added_false_links':added_fp,'added_links':added_tp+added_fp}
    out={'title':'Submission #1 held-out reproduction and controlled rule experiments','sample':spec,'submission1_rules':'same-country exact normalized name+address OR exact normalized name+approved abbreviation-address; only if neither produces a match, emit normalized-name posting iff unique across S2+S3','experiments':{k:v for k,v in results},'marginal_vs_baseline':delta,'baseline_error_groups':{'false_positive_links':dict(fp_categories),'false_negative_links':dict(fn_categories),'examples':dict(error_examples)},'runtime':{'total_seconds':round(time.time()-started,3),'target_scan_seconds':round(scan_seconds,3),'target_rows_streamed':target_rows,'final_prediction_ids_by_mode':dict(total_cands)},'limitations':['Single deterministic holdout sample; rule thresholds were prespecified, but sampling uncertainty remains.','Training labels can contain noise; string-based categories are diagnostic proxies, not adjudication.','Country validation covers only countries present in supplied training data.']}
    (OUT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'report.md').write_text(report_text(out),encoding='utf-8')
    print(json.dumps({'sample':spec,'experiments':out['experiments'],'marginal_vs_baseline':delta,'error_groups':out['baseline_error_groups'],'runtime':out['runtime']},ensure_ascii=True,indent=2))

def report_text(o):
    lines=['# Submission #2 held-out diagnosis','',f"- Sample size: {o['sample']['sample_size']:,}; ordered ID SHA-256: `{o['sample']['ordered_ids_sha256']}`.",f"- Population-proportional sample by match class × country; deterministic entity-level split seed `{o['sample']['split_seed']}`, sample seed `{o['sample']['sample_seed']}`.",'','## Results','','| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for k,m in o['experiments'].items(): lines.append(f"| {k} | {m['macro_f0_5']:.5f} | {m['micro_precision']:.4f} | {m['micro_recall']:.4f} | {m['tp']} | {m['fp']} | {m['fn']} | {m['predicted_links']} | {m['zero_match_accuracy']:.4f} |")
    lines += ['', '## Macro F0.5 by true match-count class','']
    for k,m in o['experiments'].items():
        lines.append(f"**{k}:** " + '; '.join(f"{cl} (n={v['entities']:,}): {v['macro_f0_5']:.5f}" for cl,v in m['per_truth_class'].items()))
    lines += ['', '## Marginal additions versus Submission #1','']
    for k,v in o['marginal_vs_baseline'].items():lines.append(f"- `{k}`: {v['added_true_links']} true, {v['added_false_links']} false, {v['added_links']} added predictions.")
    lines += ['', '## Baseline error groups','', 'False positives:']
    lines += [f"- {k}: {v}" for k,v in o['baseline_error_groups']['false_positive_links'].items()]
    lines += ['', 'False negatives:']
    lines += [f"- {k}: {v}" for k,v in o['baseline_error_groups']['false_negative_links'].items()]
    lines += ['', 'See `results.json` for example errors, exact stratum counts, and runtimes.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':main()
