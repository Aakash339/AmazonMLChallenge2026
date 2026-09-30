#!/usr/bin/env python3
"""Generate a separate test submission using the twice-validated rule set."""
import argparse, csv, json, sqlite3, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'student_resource/dataset/test'
OUT=ROOT/'experiments/stage5_submission2/output'
sys.path.insert(0,str(ROOT))
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations

def rows(path):
    with open(path,encoding='utf-8',newline='') as f:
        yield from csv.DictReader(f,delimiter='\t')

def main():
    global DATA, OUT
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root',type=Path,default=ROOT,help='Project root containing student_resource/dataset/test')
    ap.add_argument('--output-dir',type=Path,default=OUT,help='Directory for matching_results.tsv and candidate_pairs.tsv')
    args=ap.parse_args();DATA=args.project_root/'student_resource/dataset/test';OUT=args.output_dir
    s1_path=DATA/'test_source1.tsv'; targets=[DATA/'test_source2.tsv',DATA/'test_source3.tsv']
    missing=[str(p) for p in [s1_path,*targets] if not p.is_file()]
    if missing: raise SystemExit('Missing required supplied test input(s): '+', '.join(missing))
    start=time.time(); qkeys=set(); s1_count=0
    for r in rows(s1_path):
        n=normalize_name(r['business_name']) or ''
        if n:qkeys.add((r['country'],n))
        s1_count+=1
    print(f's1_rows={s1_count}; distinct_country_name_keys={len(qkeys)}')
    OUT.mkdir(parents=True,exist_ok=True)
    match_path=OUT/'matching_results.tsv'; candidate_path=OUT/'candidate_pairs.tsv'
    with tempfile.TemporaryDirectory(prefix='stage5_submission2_targets_') as td:
        db=sqlite3.connect(str(Path(td)/'targets.sqlite'))
        db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
        db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-262144')
        db.execute('CREATE TABLE targets(country TEXT NOT NULL,name TEXT NOT NULL,tid TEXT NOT NULL,address TEXT NOT NULL,abbr TEXT NOT NULL,PRIMARY KEY(country,name,tid)) WITHOUT ROWID')
        ins='INSERT INTO targets VALUES(?,?,?,?,?)'; batch=[]; target_rows=0; indexed=0
        for path in targets:
            for r in rows(path):
                target_rows+=1;country=r['country'];name=normalize_name(r['business_name']) or ''
                if name and (country,name) in qkeys:
                    address=normalize_address(r['business_address']) or ''
                    abbr=normalize_address_abbreviations(r['business_address']) or ''
                    batch.append((country,name,r['entity_id'],address,abbr));indexed+=1
                    if len(batch)>=10000:db.executemany(ins,batch);batch.clear()
            if batch:db.executemany(ins,batch);batch.clear()
            db.commit()
        print(f'target_rows_streamed={target_rows}; exact_name_index_rows={indexed}')
        total_predictions=0; no_match=0; index_build_done=time.time()
        with open(match_path,'w',encoding='utf-8',newline='') as mf, open(candidate_path,'w',encoding='utf-8',newline='') as cf:
            mw=csv.writer(mf,delimiter='\t',lineterminator='\n');cw=csv.writer(cf,delimiter='\t',lineterminator='\n')
            mw.writerow(['source1_entity_id','matched_entity_ids']);cw.writerow(['source1_entity_id','candidate_entity_ids'])
            for r in rows(s1_path):
                sid=r['entity_id'];country=r['country'];name=normalize_name(r['business_name']) or ''
                address=normalize_address(r['business_address']) or '';abbr=normalize_address_abbreviations(r['business_address']) or ''
                query_tokens=set(address.split()) if address else set()
                result=[]
                if name:
                    postings=db.execute('SELECT tid,address,abbr FROM targets WHERE country=? AND name=?',(country,name)).fetchall()
                    exact=[];overlap=[]
                    for tid,ta,tab in postings:
                        if address and ((ta and ta==address) or (abbr and tab and tab==abbr)):
                            exact.append(tid)
                        target_tokens=set(ta.split()) if ta else set()
                        shared=len(query_tokens & target_tokens)
                        if shared>=2 and shared/min(len(query_tokens),len(target_tokens))>=0.80:
                            overlap.append(tid)
                    if exact:
                        result=exact
                    elif len(postings)==1:
                        result=[postings[0][0]]
                    result=sorted(set(result)|set(overlap))
                if result:total_predictions+=len(result)
                else:no_match+=1
                joined=','.join(result)
                mw.writerow([sid,joined]);cw.writerow([sid,joined])
        db.close()
    print(json.dumps({'s1_rows':s1_count,'target_rows_streamed':target_rows,'exact_name_index_rows':indexed,'predicted_ids':total_predictions,'empty_s1_rows':no_match,'index_build_seconds':round(index_build_done-start,3),'total_seconds':round(time.time()-start,3),'matching_bytes':match_path.stat().st_size,'candidate_bytes':candidate_path.stat().st_size,'matching_path':str(match_path),'candidate_path':str(candidate_path)},indent=2))

if __name__=='__main__':main()
