#!/usr/bin/env python3
"""Generate Submission #3 using the frozen training-only logistic scorer."""
import argparse, csv, json, math, sqlite3, sys, tempfile, time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations
FEATURES=('name_char','name_token_jaccard','name_token_containment','address_token_jaccard','address_token_containment','address_exact','address_abbr_exact','name_exact','name_length_ratio','source_s2','source_s3','rule_exact_pair','rule_unique','rule_name_overlap','rule_fuzzy_address')

def rows(path):
    with open(path,encoding='utf-8',newline='') as f: yield from csv.DictReader(f,delimiter='\t')
def tokens(s): return set((s or '').split())
def jac(a,b): return len(a&b)/len(a|b) if a|b else 0.0
def cont(a,b): return len(a&b)/min(len(a),len(b)) if a and b else 0.0
def feat(q,t,flags):
    qn=q['name'];tn=t['name'];qa=q['at'];ta=t['at'];qnt=q['nt'];tnt=t['nt']
    sim=SequenceMatcher(None,qn,tn,autojunk=False).ratio() if qn and tn else 0.0
    return [sim,jac(qnt,tnt),cont(qnt,tnt),jac(qa,ta),cont(qa,ta),float(bool(q['address'] and q['address']==t['address'])),float(bool(q['abbr'] and q['abbr']==t['abbr'])),float(bool(qn and qn==tn)),min(len(qn),len(tn))/max(1,max(len(qn),len(tn))),float(t['source']=='S2-'),float(t['source']=='S3-'),*flags]
def score(config,x):
    mu=config['mean'];scale=config['scale'];coef=config['coef'];raw=config['bias']
    for v,m,s,c in zip(x,mu,scale,coef):raw+=((v-m)/s)*c
    raw=max(-30.0,min(30.0,raw));return 1.0/(1.0+math.exp(-raw))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,required=True);ap.add_argument('--output-dir',type=Path,default=HERE.parents[2]/'output');args=ap.parse_args()
    data=args.project_root/'student_resource/dataset/test';s1=data/'test_source1.tsv';targets=(data/'test_source2.tsv',data/'test_source3.tsv')
    missing=[str(p) for p in (s1,*targets) if not p.is_file()]
    if missing:raise SystemExit('Missing supplied test input(s): '+', '.join(missing))
    cfg=json.loads((HERE.parents[2]/'model_config.json').read_text(encoding='utf-8'));start=time.time();qnames=set();qaddrs=set();s1_rows=0
    for r in rows(s1):
        c=r['country'];n=normalize_name(r['business_name']) or '';a=normalize_address(r['business_address']) or '';ab=normalize_address_abbreviations(r['business_address']) or ''
        if n:qnames.add((c,n))
        for key in (a,ab):
            if key:qaddrs.add((c,key))
        s1_rows+=1
        if s1_rows%500000==0:print(f'query-key scan: {s1_rows:,} Source 1 rows',flush=True)
    args.output_dir.mkdir(parents=True,exist_ok=True);match_path=args.output_dir/'matching_results.tsv';candidate_path=args.output_dir/'candidate_pairs.tsv'
    with tempfile.TemporaryDirectory(prefix='stage5_s3_targets_') as td:
        db=sqlite3.connect(str(Path(td)/'targets.sqlite'));db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-262144')
        db.execute('CREATE TABLE targets(tid TEXT PRIMARY KEY,country TEXT,name TEXT,address TEXT,abbr TEXT,source TEXT) WITHOUT ROWID')
        db.execute('CREATE TABLE addr_idx(country TEXT,address TEXT,tid TEXT,PRIMARY KEY(country,address,tid)) WITHOUT ROWID')
        it='INSERT OR IGNORE INTO targets VALUES(?,?,?,?,?,?)';ia='INSERT OR IGNORE INTO addr_idx VALUES(?,?,?)';tb=[];ab=[];target_rows=0;relevant=0
        for p in targets:
            print(f'target-key scan: {p.name}',flush=True)
            for i,r in enumerate(rows(p),1):
                target_rows+=1;c=r['country'];tid=r['entity_id'];n=normalize_name(r['business_name']) or '';a=normalize_address(r['business_address']) or '';abbr=normalize_address_abbreviations(r['business_address']) or ''
                name_hit=bool(n and (c,n) in qnames);addr_hits=[k for k in {a,abbr} if k and (c,k) in qaddrs]
                if name_hit or addr_hits:
                    tb.append((tid,c,n,a,abbr,tid[:3]));relevant+=1
                    for key in addr_hits:ab.append((c,key,tid))
                if len(tb)>=10000:db.executemany(it,tb);tb.clear()
                if len(ab)>=20000:db.executemany(ia,ab);ab.clear()
                if i%500000==0:print(f'target-key scan: {p.name} {i:,} rows; indexed {relevant:,}',flush=True)
            if tb:db.executemany(it,tb);tb.clear()
            if ab:db.executemany(ia,ab);ab.clear()
            db.commit()
        db.execute('CREATE INDEX targets_name ON targets(country,name)');db.execute('CREATE INDEX address_lookup ON addr_idx(country,address)');db.commit()
        print(f'indexed {relevant:,} relevant target rows from {target_rows:,}; writing outputs',flush=True)
        match_count=candidate_count=zero_rows=0;pool_total=0
        with open(match_path,'w',encoding='utf-8',newline='') as mf,open(candidate_path,'w',encoding='utf-8',newline='') as cf:
            mw=csv.writer(mf,delimiter='\t',lineterminator='\n');cw=csv.writer(cf,delimiter='\t',lineterminator='\n');mw.writerow(['source1_entity_id','matched_entity_ids']);cw.writerow(['source1_entity_id','candidate_entity_ids'])
            for i,qrow in enumerate(rows(s1),1):
                c=qrow['country'];n=normalize_name(qrow['business_name']) or '';a=normalize_address(qrow['business_address']) or '';abbr=normalize_address_abbreviations(qrow['business_address']) or '';sid=qrow['entity_id']
                q={'country':c,'name':n,'address':a,'abbr':abbr,'nt':tokens(n),'at':tokens(a)}
                pool={}
                if n:
                    for row in db.execute('SELECT tid,country,name,address,abbr,source FROM targets WHERE country=? AND name=?',(c,n)):
                        pool[row[0]]={'id':row[0],'country':row[1],'name':row[2],'address':row[3],'abbr':row[4],'source':row[5],'nt':tokens(row[2]),'at':tokens(row[3])}
                for key in {a,abbr}:
                    if key:
                        for row in db.execute('SELECT t.tid,t.country,t.name,t.address,t.abbr,t.source FROM addr_idx ai JOIN targets t ON t.tid=ai.tid WHERE ai.country=? AND ai.address=?',(c,key)):
                            pool[row[0]]={'id':row[0],'country':row[1],'name':row[2],'address':row[3],'abbr':row[4],'source':row[5],'nt':tokens(row[2]),'at':tokens(row[3])}
                names=[tid for tid,t in pool.items() if n and t['name']==n];exact=set();over=set();fuzzy=set();vectors={}
                for tid,t in pool.items():
                    shared=len(q['at']&t['at']);containment=cont(q['at'],t['at']);same=bool(a and t['address']==a or abbr and t['abbr']==abbr);sim=SequenceMatcher(None,n,t['name'],autojunk=False).ratio() if n and t['name'] else 0.0
                    if tid in names and same:exact.add(tid)
                    if tid in names and shared>=2 and containment>=0.40:over.add(tid)
                    if same and sim>=0.75:fuzzy.add(tid)
                base=exact or (set(names) if len(names)==1 else set())
                for tid,t in pool.items():
                    flags=(float(tid in exact),float(not exact and len(names)==1 and tid in names),float(tid in over),float(tid in fuzzy))
                    vectors[tid]=feat(q,t,flags)
                cand_ids=sorted(pool);pred_ids=sorted(tid for tid in pool if score(cfg,vectors[tid])>=cfg['threshold'])
                cw.writerow([sid,','.join(cand_ids)]);mw.writerow([sid,','.join(pred_ids)]);candidate_count+=len(cand_ids);match_count+=len(pred_ids);pool_total+=len(pool);zero_rows+=int(not pred_ids)
                if i%100000==0:print(f'inference: {i:,}/{s1_rows:,} S1 rows; candidate IDs {candidate_count:,}; matches {match_count:,}',flush=True)
        db.close()
    print(json.dumps({'s1_rows':s1_rows,'target_rows_scanned':target_rows,'relevant_target_rows':relevant,'candidate_pairs':candidate_count,'mean_candidates_per_s1':candidate_count/s1_rows,'predicted_ids':match_count,'empty_match_rows':zero_rows,'threshold':cfg['threshold'],'elapsed_seconds':round(time.time()-start,2),'matching_path':str(match_path),'candidate_path':str(candidate_path)},indent=2),flush=True)

if __name__=='__main__':main()
