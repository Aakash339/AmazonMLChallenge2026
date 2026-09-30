#!/usr/bin/env python3
"""Sparse exact/rare-address candidate retrieval plus a small logistic pair scorer.

Training-only experiment. The target sources are streamed twice into temporary
SQLite postings; no broad all-pairs candidate set is materialized.
"""
from __future__ import annotations
import csv, hashlib, json, math, sqlite3, statistics, sys, tempfile, time
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'student_resource/dataset/train'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations

SPLIT_SEED=20261101; SAMPLE_SEED=20261102; PER_BUCKET=500
BUCKETS=(0,1,2); TOKEN_DF_CAP=25000; NAME_SIM_MIN=0.75; PARTIAL_SIM_MIN=0.85; ADDR_CONTAINMENT_MIN=0.40; MIN_SHARED=2
FEATURES=('name_char','name_jaccard','name_containment','address_jaccard','address_containment','address_exact','address_abbr_exact','name_exact','shared_count','rare_address','name_length_ratio','source_s2','source_s3','rule_unique','rule_exact_pair','rule_name_overlap','rule_fuzzy_exact','rule_fuzzy_partial')

def rows(path):
    with open(path,encoding='utf-8',newline='') as f: yield from csv.DictReader(f,delimiter='\t')
def links(raw): return [v.strip() for v in raw.split(',') if v.strip()]
def hash_rank(seed,s): return int.from_bytes(hashlib.sha256(f'{seed}\0{s}'.encode()).digest(),'big')
def f05(p,r): return 1.25*p*r/(0.25*p+r) if 0.25*p+r else 0.0
def name_tokens(s): return set((s or '').split())
def addr_tokens(s): return set((s or '').split())
def overlap(a,b): return len(a&b)/min(len(a),len(b)) if a and b else 0.0
def jaccard(a,b): return len(a&b)/len(a|b) if a or b else 0.0

def previous_ids():
    found=set()
    for pattern in ('sample_ids.txt','validation_ids.txt','sample_ids_bucket*.txt'):
        for p in (ROOT/'experiments').rglob(pattern):
            try: found.update(p.read_text(encoding='utf-8').splitlines())
            except OSError: pass
    # Exclude this experiment's own saved cohorts on repeat runs so its split is reproducible.
    for p in OUT.glob('sample_ids_bucket*.txt'):
        try: found.difference_update(p.read_text(encoding='utf-8').splitlines())
        except OSError: pass
    return found

def select_samples():
    excluded=previous_ids()
    with tempfile.TemporaryDirectory(prefix='s5_compact_sample_') as td:
        db=sqlite3.connect(str(Path(td)/'s.sqlite'));db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
        db.execute('CREATE TABLE gt(id TEXT PRIMARY KEY,truth TEXT,n INTEGER)')
        for i,g in enumerate(rows(DATA/'train_ground_truth.tsv'),1):
            ls=links(g['matched_entity_ids']);db.execute('INSERT INTO gt VALUES(?,?,?)',(g['source1_entity_id'],json.dumps(ls),len(ls)))
            if i%100000==0:db.commit()
            if i%500000==0:print(f'sample-prep: loaded {i:,} ground-truth rows',flush=True)
        db.commit();db.execute('CREATE TABLE pool(bucket INTEGER,id TEXT,country TEXT,cls TEXT,rk TEXT,row_json TEXT,truth TEXT)')
        for i,r in enumerate(rows(DATA/'train_source1.tsv'),1):
            sid=r['entity_id'];b=hash_rank(SPLIT_SEED,sid)%5
            if b not in BUCKETS or sid in excluded: continue
            truth,n=db.execute('SELECT truth,n FROM gt WHERE id=?',(sid,)).fetchone();cl='zero' if n==0 else 'one' if n==1 else 'multi'
            db.execute('INSERT INTO pool VALUES(?,?,?,?,?,?,?)',(b,sid,r['country'],cl,f'{hash_rank(SAMPLE_SEED,sid):064x}',json.dumps(r,ensure_ascii=False),truth))
            if i%100000==0:db.commit()
            if i%500000==0:print(f'sample-prep: scanned {i:,} Source 1 rows',flush=True)
        db.commit(); selected=[]; spec={}
        for b in BUCKETS:
            counts={(c,cl):n for c,cl,n in db.execute('SELECT country,cls,COUNT(*) FROM pool WHERE bucket=? GROUP BY country,cls',(b,))}
            total=sum(counts.values()); quotas={k:PER_BUCKET*n//total for k,n in counts.items()}; rem=PER_BUCKET-sum(quotas.values())
            for k in sorted(counts,key=lambda k:(-(PER_BUCKET*counts[k]%total),k[0],k[1]))[:rem]:quotas[k]+=1
            sample=[]
            for (country,cl),q in quotas.items():
                for sid,raw,truth in db.execute('SELECT id,row_json,truth FROM pool WHERE bucket=? AND country=? AND cls=? ORDER BY rk,id LIMIT ?',(b,country,cl,q)):
                    r=json.loads(raw);r['truth']=json.loads(truth);r['class']=cl;r['bucket']=b;sample.append(r)
            sample.sort(key=lambda x:(x['country'],x['entity_id'])); ids=[x['entity_id'] for x in sample]
            if len(ids)!=PER_BUCKET or any(not (z.startswith('S2-') or z.startswith('S3-')) for x in sample for z in x['truth']):raise RuntimeError('Sample or S2/S3 truth-ID validation failed')
            (OUT/f'sample_ids_bucket{b}.txt').write_text('\n'.join(ids)+'\n',encoding='utf-8')
            spec[str(b)]={'size':len(ids),'id_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),'true_links':sum(len(x['truth']) for x in sample),'stratum_counts':{f'{k[0]}/{k[1]}':counts[k] for k in sorted(counts)},'stratum_sample':{f'{k[0]}/{k[1]}':quotas[k] for k in sorted(quotas)}}
            selected.extend(sample)
        db.close()
    return selected,spec,len(excluded)

def prep_queries(samples):
    qs={}
    all_names=set();all_addr_keys=set();all_tokens=set()
    for r in samples:
        c=r['country'];n=normalize_name(r['business_name']) or '';a=normalize_address(r['business_address']) or '';ab=normalize_address_abbreviations(r['business_address']) or ''
        at=addr_tokens(a); nt=name_tokens(n)
        q={'id':r['entity_id'],'bucket':r['bucket'],'truth':set(r['truth']),'class':r['class'],'country':c,'raw_name':r['business_name'],'raw_address':r['business_address'],'name':n,'address':a,'abbr':ab,'nt':nt,'at':at}
        qs[r['entity_id']]=q
        if n:all_names.add((c,n))
        if a:all_addr_keys.add((c,a))
        if ab:all_addr_keys.add((c,ab))
        all_tokens.update((c,t) for t in at if t)
    return qs,all_names,all_addr_keys,all_tokens

def create_target_index(samples,dbpath):
    qs,qnames,qaddrkeys,qtokens=prep_queries(samples)
    db=sqlite3.connect(str(dbpath));db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-262144')
    db.execute('CREATE TABLE token_df(country TEXT,token TEXT,n INTEGER,PRIMARY KEY(country,token)) WITHOUT ROWID')
    db.execute('CREATE TABLE targets(tid TEXT PRIMARY KEY,country TEXT,name TEXT,normname TEXT,address TEXT,abbr TEXT,tokens TEXT,source TEXT) WITHOUT ROWID')
    db.execute('CREATE TABLE postings(country TEXT,token TEXT,tid TEXT,PRIMARY KEY(country,token,tid)) WITHOUT ROWID')
    db.execute('CREATE TABLE exact_addr(country TEXT,address TEXT,tid TEXT,PRIMARY KEY(country,address,tid)) WITHOUT ROWID')
    df=Counter(); name_df=Counter(); target_rows=0
    paths=[DATA/'train_source2.tsv',DATA/'train_source3.tsv']
    for p in paths:
        print(f'index-frequency: scanning {p.name}',flush=True)
        for i,r in enumerate(rows(p),1):
            target_rows+=1;c=r['country'];n=normalize_name(r['business_name']) or '';a=normalize_address(r['business_address']) or '';at=addr_tokens(a)
            if n and (c,n) in qnames:name_df[(c,n)]+=1
            for t in at:
                if (c,t) in qtokens:df[(c,t)]+=1
            if i%500000==0:print(f'index-frequency: {p.name} {i:,} rows',flush=True)
    batch=[(c,t,n) for (c,t),n in df.items()]
    db.executemany('INSERT INTO token_df VALUES(?,?,?)',batch);db.commit()
    q_token_df={k:v for k,v in df.items() if 0<v<=TOKEN_DF_CAP}
    ins_t='INSERT OR IGNORE INTO targets VALUES(?,?,?,?,?,?,?,?)';ins_p='INSERT OR IGNORE INTO postings VALUES(?,?,?)';ins_a='INSERT OR IGNORE INTO exact_addr VALUES(?,?,?)'
    tb=[];pb=[];ab=[]; indexed_targets=0; posting_rows=0
    unique_names={k for k,v in name_df.items() if v==1}
    build_rows=0
    for p in paths:
        print(f'index-build: scanning {p.name}',flush=True)
        for r in rows(p):
            build_rows+=1
            c=r['country'];tid=r['entity_id'];n=normalize_name(r['business_name']) or '';a=normalize_address(r['business_address']) or '';abbr=normalize_address_abbreviations(r['business_address']) or '';at=addr_tokens(a)
            tok=[t for t in at if (c,t) in q_token_df]
            exact_keys={k for k in (a,abbr) if k and (c,k) in qaddrkeys}
            uniq=(c,n) in unique_names
            if not tok and not exact_keys and not uniq:continue
            tb.append((tid,c,r['business_name'],n,a,abbr,json.dumps(sorted(at),ensure_ascii=False),tid[:3]))
            indexed_targets+=1
            for t in tok:pb.append((c,t,tid));posting_rows+=1
            for key in exact_keys:ab.append((c,key,tid))
            if len(tb)>=5000:
                db.executemany(ins_t,tb);tb.clear()
            if len(pb)>=20000:
                db.executemany(ins_p,pb);pb.clear()
            if len(ab)>=5000:
                db.executemany(ins_a,ab);ab.clear()
            if build_rows%500000==0:print(f'index-build: {build_rows:,} target rows',flush=True)
        db.executemany(ins_t,tb);tb.clear();db.executemany(ins_p,pb);pb.clear();db.executemany(ins_a,ab);ab.clear();db.commit()
    db.execute('CREATE INDEX targets_name ON targets(country,normname)');db.execute('CREATE INDEX targets_addr ON targets(country,address)');db.commit()
    return db,qs,name_df,{'target_rows_streamed':target_rows,'indexed_target_rows':indexed_targets,'address_posting_rows':posting_rows,'queried_address_tokens':len(qtokens),'eligible_tokens':len(q_token_df),'name_keys':len(qnames),'sample_exact_address_keys':len(qaddrkeys),'token_df_cap':TOKEN_DF_CAP}

def pair_features(q,t,shared,dfs):
    qn=q['name'];tn=t['normname'];qa=q['at'];ta=set(json.loads(t['tokens']));qnt=q['nt'];tnt=name_tokens(tn)
    sim=SequenceMatcher(None,qn,tn,autojunk=False).ratio() if qn and tn else 0.0
    addr_cont=overlap(qa,ta); name_cont=overlap(qnt,tnt); union=qa|ta
    rare=sum(math.log1p(1_000_000/(dfs.get((q['country'],x),1))) for x in qa&ta)/max(1,shared)
    same_addr=bool((q['address'] and t['address']==q['address']) or (q['abbr'] and t['abbr']==q['abbr']))
    f={'name_char':sim,'name_jaccard':jaccard(qnt,tnt),'name_containment':name_cont,'address_jaccard':jaccard(qa,ta),'address_containment':addr_cont,'address_exact':float(bool(q['address'] and t['address']==q['address'])),'address_abbr_exact':float(bool(q['abbr'] and t['abbr']==q['abbr'])),'name_exact':float(bool(qn and qn==tn)),'shared_count':min(shared,8)/8.0,'rare_address':min(rare,30)/30.0,'name_length_ratio':min(len(qn),len(tn))/max(1,max(len(qn),len(tn))),'source_s2':float(t['source']=='S2-'),'source_s3':float(t['source']=='S3-'),'rule_unique':0.0,'rule_exact_pair':0.0,'rule_name_overlap':0.0,'rule_fuzzy_exact':0.0,'rule_fuzzy_partial':0.0}
    return np.array([f[k] for k in FEATURES],dtype=np.float64),same_addr,sim,addr_cont,shared

def candidate_pairs(q,db,dfs,name_df):
    ids=Counter()
    eligible=[t for t in q['at'] if dfs.get((q['country'],t),0)<=TOKEN_DF_CAP and dfs.get((q['country'],t),0)>0]
    for tok in eligible:
        ids.update(x[0] for x in db.execute('SELECT tid FROM postings WHERE country=? AND token=?',(q['country'],tok)))
    exact_ids=set()
    for key in {q['address'],q['abbr']}:
        if key:exact_ids.update(x[0] for x in db.execute('SELECT tid FROM exact_addr WHERE country=? AND address=?',(q['country'],key)))
    # Name uniqueness must use counts over *all* targets. The sparse address
    # index intentionally omits many targets, so counting indexed rows here
    # could incorrectly turn a common name into a unique-name fallback.
    unique=[]
    if q['name'] and name_df.get((q['country'],q['name']),0)==1:
        unique=list(db.execute('SELECT tid FROM targets WHERE country=? AND normname=? LIMIT 1',(q['country'],q['name'])))
    cand=set(ids)|exact_ids
    if len(unique)==1:cand.add(unique[0][0])
    feats={}; exact_name=[]; exact_pair=[]; name_overlap=[]; fuzzy_exact=[]; fuzzy_partial=[]
    for tid in cand:
        row=db.execute('SELECT tid,country,name,normname,address,abbr,tokens,source FROM targets WHERE tid=?',(tid,)).fetchone()
        if not row:continue
        t=dict(zip(('tid','country','business_name','normname','address','abbr','tokens','source'),row))
        ta=set(json.loads(t['tokens']));shared=len(q['at']&ta)
        x,same_addr,sim,addr_cont,shared=pair_features(q,t,shared,dfs)
        exact_nm=bool(q['name'] and q['name']==t['normname'])
        if exact_nm:exact_name.append(tid)
        if exact_nm and same_addr:exact_pair.append(tid)
        if exact_nm and shared>=MIN_SHARED and addr_cont>=ADDR_CONTAINMENT_MIN:name_overlap.append(tid)
        if same_addr and sim>=NAME_SIM_MIN:fuzzy_exact.append(tid)
        if shared>=MIN_SHARED and addr_cont>=ADDR_CONTAINMENT_MIN and sim>=PARTIAL_SIM_MIN:fuzzy_partial.append(tid)
        feats[tid]=(x,t,shared,sim,addr_cont,same_addr)
    exact=set(exact_pair); base=set(exact)
    name_freq=name_df.get((q['country'],q['name']),0)
    if not base and name_freq==1:base=set(exact_name)
    pool=base|set(name_overlap)|set(fuzzy_exact)|set(fuzzy_partial)
    # Store explicit retrieval-rule indicators as model features.
    out=[]
    for tid in pool:
        x,t,shared,sim,cont,same=feats[tid]
        x=x.copy();x[FEATURES.index('rule_unique')]=float(not exact and name_freq==1 and tid in base)
        x[FEATURES.index('rule_exact_pair')]=float(tid in exact)
        x[FEATURES.index('rule_name_overlap')]=float(tid in name_overlap)
        x[FEATURES.index('rule_fuzzy_exact')]=float(tid in fuzzy_exact)
        x[FEATURES.index('rule_fuzzy_partial')]=float(tid in fuzzy_partial)
        out.append((tid,x))
    return out

def logistic_fit(x,y,w):
    mu=x.mean(axis=0); sd=x.std(axis=0);sd[sd<1e-8]=1.0
    z=(x-mu)/sd; coef=np.zeros(z.shape[1],dtype=np.float64); bias=math.log((float(y.sum())+1)/(len(y)-float(y.sum())+1))
    # Deterministic batch logistic regression with L2 regularization.
    for _ in range(350):
        raw=np.clip(z@coef+bias,-30,30); p=1/(1+np.exp(-raw)); err=(p-y)*w
        gc=(z.T@err)/w.sum()+0.02*coef; gb=float(err.sum()/w.sum())
        coef-=0.15*gc; bias-=0.15*gb
    return {'mean':mu,'scale':sd,'coef':coef,'bias':bias}
def logistic_predict(model,x):
    z=(x-model['mean'])/model['scale']; raw=np.clip(z@model['coef']+model['bias'],-30,30);return 1/(1+np.exp(-raw))

def metrics(rows0,prob_by_sid,threshold):
    fs=[];tp=fp=fn=pred=0;z=zc=0
    for q in rows0:
        truth=q['truth']; vals=prob_by_sid.get(q['id'],[]); chosen={tid for tid,p in vals if p>=threshold}; hit=len(chosen&truth);falsep=len(chosen-truth);miss=len(truth-chosen);tp+=hit;fp+=falsep;fn+=miss;pred+=len(chosen)
        if not truth:z+=1;zc+=int(not chosen);fs.append(1.0 if not chosen else 0.0)
        else:fs.append(f05(hit/len(chosen) if chosen else 0.0,hit/len(truth)))
    return {'macro_f0_5':statistics.fmean(fs),'precision':tp/(tp+fp) if tp+fp else 0.0,'recall':tp/(tp+fn) if tp+fn else 0.0,'tp':tp,'fp':fp,'fn':fn,'predicted_ids':pred,'zero_match_accuracy':zc/z if z else None}

def main():
    started=time.time();samples,specs,excluded=select_samples();dbpath=OUT/'compact_training_index.sqlite'
    # Use a transient temp database; never leave a multi-million-row index in the project.
    with tempfile.TemporaryDirectory(prefix='s5_compact_index_') as td:
        db,queries,name_df,index_stats=create_target_index(samples,Path(td)/'targets.sqlite')
        dfs={(c,t):n for c,t,n in db.execute('SELECT country,token,n FROM token_df')}
        rows_by_bucket={b:[queries[r['entity_id']] for r in samples if r['bucket']==b] for b in BUCKETS}
        features_by_bucket={b:{} for b in BUCKETS}; pool_stats={b:{'candidate_rows':0,'candidate_true':0,'true_links':0,'predictions_rule':0,'tp_rule':0,'fp_rule':0} for b in BUCKETS}
        for b in BUCKETS:
            for q in rows_by_bucket[b]:
                pairs=candidate_pairs(q,db,dfs,name_df);truth=q['truth'];pool_stats[b]['candidate_rows']+=len(pairs);pool_stats[b]['true_links']+=len(truth);pool_stats[b]['candidate_true']+=sum(t in {x[0] for x in pairs} for t in truth)
                features_by_bucket[b][q['id']]=[(tid,x) for tid,x in pairs]
                pred={tid for tid,x in pairs if x[FEATURES.index('rule_exact_pair')]>0 or x[FEATURES.index('rule_unique')]>0 or x[FEATURES.index('rule_name_overlap')]>0 or x[FEATURES.index('rule_fuzzy_exact')]>0 or x[FEATURES.index('rule_fuzzy_partial')]>0}
                pool_stats[b]['predictions_rule']+=len(pred);pool_stats[b]['tp_rule']+=len(pred&truth);pool_stats[b]['fp_rule']+=len(pred-truth)
        train_x=[];train_y=[];train_w=[]
        for q in rows_by_bucket[0]:
            rows1=features_by_bucket[0][q['id']];n=max(1,len(rows1))
            for tid,x in rows1:
                train_x.append(x);train_y.append(float(tid in q['truth']));train_w.append((1.0/n)*(4.0 if tid in q['truth'] else 1.0))
        if not train_x or sum(train_y)<10:raise RuntimeError('Insufficient training candidates or positives')
        model=logistic_fit(np.vstack(train_x),np.array(train_y,dtype=np.float64),np.array(train_w,dtype=np.float64))
        probabilities={}
        for b in (1,2):
            xx=[];meta=[]
            for q in rows_by_bucket[b]:
                for tid,x in features_by_bucket[b][q['id']]:xx.append(x);meta.append((q['id'],tid))
            ps=logistic_predict(model,np.vstack(xx)) if xx else np.array([]);by_sid={q['id']:[] for q in rows_by_bucket[b]}
            for (sid,tid),p in zip(meta,ps):by_sid[sid].append((tid,float(p)))
            probabilities[b]=by_sid
        grid=[round(0.02+i*0.02,2) for i in range(48)]; sweep=[(metrics(rows_by_bucket[1],probabilities[1],t),t) for t in grid]
        chosen=max(sweep,key=lambda z:(z[0]['macro_f0_5'],z[1]))[1]
        result={'title':'Compact address/name retrieval with supervised logistic pair scorer','seeds':{'split':SPLIT_SEED,'sample':SAMPLE_SEED},'sample_specs':specs,'excluded_prior_validation_id_count':excluded,'retrieval':{'token_df_cap':TOKEN_DF_CAP,'minimum_shared_address_tokens':MIN_SHARED,'address_containment_min':ADDR_CONTAINMENT_MIN,'exact_name_similarity_min':NAME_SIM_MIN,'partial_name_similarity_min':PARTIAL_SIM_MIN,'index':index_stats,'candidate_stats':pool_stats},'features':list(FEATURES),'train_pairs':len(train_x),'train_positives':int(sum(train_y)),'train_negative_weighted_sampling':'All compact-pool pairs; S1 rows weighted equally by inverse candidate count, positive pairs receive 4x weight.','model':'standardized batch logistic regression, L2=0.02, 350 deterministic gradient steps, step size 0.15','discovery_threshold_sweep':{str(t):m for m,t in sweep},'selected_threshold':chosen,'confirmation_metrics':metrics(rows_by_bucket[2],probabilities[2],chosen),'confirmation_rule_metrics':metrics(rows_by_bucket[2],{q['id']:[(tid,1.0) for tid,x in features_by_bucket[2][q['id']] if any(x[i]>0 for i in range(13,18))] for q in rows_by_bucket[2]},0.5),'model_parameters':{'mean':model['mean'].tolist(),'scale':model['scale'].tolist(),'coef':model['coef'].tolist(),'bias':float(model['bias'])},'runtime_seconds':round(time.time()-started,3)}
        (OUT/'compact_model_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        db.close()
    print(json.dumps({'samples':specs,'retrieval':result['retrieval'],'train_pairs':result['train_pairs'],'train_positives':result['train_positives'],'selected_threshold':result['selected_threshold'],'confirmation_metrics':result['confirmation_metrics'],'confirmation_rule_metrics':result['confirmation_rule_metrics'],'runtime_seconds':result['runtime_seconds']},indent=2))

if __name__=='__main__':main()
