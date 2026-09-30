#!/usr/bin/env python3
"""Single-pass exact-key candidate scorer experiment (train data only)."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics, time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np

PACKAGE=Path(__file__).resolve().parents[3]
DATA=Path('.')
COHORT_DIR=PACKAGE/'code/business_entity_resolution/cohorts'
RESULT_PATH=PACKAGE/'training_metrics.json'
from sys import path
path.insert(0,str(Path(__file__).resolve().parent))
from normalization.normalize import normalize_name, normalize_address, normalize_address_abbreviations

BUCKETS=(0,1,2,3); SAMPLES_PER_BUCKET=500; NAME_SIM=0.75; ADDRESS_OVERLAP=0.40
FEATURES=('name_char','name_token_jaccard','name_token_containment','address_token_jaccard','address_token_containment','address_exact','address_abbr_exact','name_exact','name_length_ratio','source_s2','source_s3','rule_exact_pair','rule_unique','rule_name_overlap','rule_fuzzy_address')

def rows(path):
    with open(path,encoding='utf-8',newline='') as f: yield from csv.DictReader(f,delimiter='\t')
def tokens(s): return set((s or '').split())
def jac(a,b): return len(a&b)/len(a|b) if a|b else 0.0
def containment(a,b): return len(a&b)/min(len(a),len(b)) if a and b else 0.0
def f05(p,r): return 1.25*p*r/(0.25*p+r) if 0.25*p+r else 0.0

def load_samples():
    samples=[]
    ids_by_bucket={b:(COHORT_DIR/f'sample_ids_bucket{b}.txt').read_text(encoding='utf-8').splitlines() for b in BUCKETS}
    all_ids=set().union(*(set(v) for v in ids_by_bucket.values()))
    if any(len(ids_by_bucket[b])!=SAMPLES_PER_BUCKET or len(set(ids_by_bucket[b]))!=SAMPLES_PER_BUCKET for b in BUCKETS):
        raise RuntimeError('Saved fixed cohorts must each contain exactly 500 unique IDs')
    if sum(map(len,ids_by_bucket.values()))!=len(all_ids): raise RuntimeError('Saved cohorts overlap')
    truth={}
    for g in rows(DATA/'train_ground_truth.tsv'):
        sid=g['source1_entity_id']
        if sid in all_ids:
            try: vals=json.loads(g['matched_entity_ids']) if g['matched_entity_ids'] else []
            except json.JSONDecodeError: vals=[x.strip() for x in g['matched_entity_ids'].split(',') if x.strip()]
            truth[sid]=set(vals)
    raw={}
    for r in rows(DATA/'train_source1.tsv'):
        if r['entity_id'] in all_ids: raw[r['entity_id']]=r
    if set(raw)!=all_ids or set(truth)!=all_ids: raise RuntimeError('Sample IDs do not join one-to-one to supplied S1 and ground truth')
    for b,ids in ids_by_bucket.items():
        for sid in ids:
            r=raw[sid]; n=normalize_name(r['business_name']) or ''; a=normalize_address(r['business_address']) or ''; ab=normalize_address_abbreviations(r['business_address']) or ''
            samples.append({'id':sid,'bucket':b,'country':r['country'],'raw_name':r['business_name'],'raw_address':r['business_address'],'name':n,'address':a,'abbr':ab,'nt':tokens(n),'at':tokens(a),'truth':truth[sid]})
    hashes={str(b):hashlib.sha256(('\n'.join(ids_by_bucket[b])).encode()).hexdigest() for b in BUCKETS}
    return samples,hashes

def feature(q,t,rule_flags):
    qn=q['name'];tn=t['name'];qa=q['at'];ta=t['at'];qnt=q['nt'];tnt=t['nt']
    sim=SequenceMatcher(None,qn,tn,autojunk=False).ratio() if qn and tn else 0.0
    return np.array([sim,jac(qnt,tnt),containment(qnt,tnt),jac(qa,ta),containment(qa,ta),float(bool(q['address'] and q['address']==t['address'])),float(bool(q['abbr'] and q['abbr']==t['abbr'])),float(bool(qn and qn==tn)),min(len(qn),len(tn))/max(1,max(len(qn),len(tn))),float(t['source']=='S2-'),float(t['source']=='S3-'),*rule_flags],dtype=np.float64)

def make_candidates(samples):
    names={(q['country'],q['name']) for q in samples if q['name']}
    addresses={(q['country'],k) for q in samples for k in (q['address'],q['abbr']) if k}
    by_name=defaultdict(list);by_addr=defaultdict(list);target={};rows_seen=0;started=time.time()
    for fn in ('train_source2.tsv','train_source3.tsv'):
        print(f'target scan: {fn}',flush=True)
        for i,r in enumerate(rows(DATA/fn),1):
            rows_seen+=1;c=r['country'];tid=r['entity_id'];name=normalize_name(r['business_name']) or '';addr=normalize_address(r['business_address']) or '';abbr=normalize_address_abbreviations(r['business_address']) or ''
            nk=(c,name); akeys={(c,k) for k in (addr,abbr) if k}
            if nk in names or akeys&addresses:
                target[tid]={'id':tid,'country':c,'name':name,'address':addr,'abbr':abbr,'nt':tokens(name),'at':tokens(addr),'source':tid[:3]}
                if nk in names:by_name[nk].append(tid)
                for ak in akeys&addresses:by_addr[ak].append(tid)
            if i%500000==0:print(f'target scan: {fn} {i:,} rows; indexed {len(target):,}',flush=True)
    print(f'target scan complete: {rows_seen:,} records, {len(target):,} relevant targets, {time.time()-started:.1f}s',flush=True)
    features={}; rule_predictions={}; stats={}
    for b in BUCKETS:
        qs=[q for q in samples if q['bucket']==b]; bucket_features={}; bucket_rules={}; n_pairs=0; true_found=0; true_total=0
        for q in qs:
            names0=list(dict.fromkeys(by_name.get((q['country'],q['name']),[]))) if q['name'] else []
            addr0=set()
            for k in {q['address'],q['abbr']}:
                if k:addr0.update(by_addr.get((q['country'],k),[]))
            pool=set(names0)|addr0; exact_pairs=set(); fuzzy_addr=set(); name_overlap=set(); scored={}
            for tid in pool:
                t=target[tid];at=t['at'];shared=len(q['at']&at); cont=containment(q['at'],at)
                same_addr=bool(q['address'] and t['address']==q['address'] or q['abbr'] and t['abbr']==q['abbr'])
                name_exact=bool(q['name'] and q['name']==t['name'])
                sim=SequenceMatcher(None,q['name'],t['name'],autojunk=False).ratio() if q['name'] and t['name'] else 0.0
                if name_exact and same_addr:exact_pairs.add(tid)
                if name_exact and shared>=2 and cont>=ADDRESS_OVERLAP:name_overlap.add(tid)
                if same_addr and sim>=NAME_SIM:fuzzy_addr.add(tid)
                flags=(float(tid in exact_pairs),float(False),float(tid in name_overlap),float(tid in fuzzy_addr))
                scored[tid]=feature(q,t,flags)
            exact=set(exact_pairs); unique=set(names0) if len(names0)==1 else set()
            base=exact or unique
            rules=base|name_overlap|fuzzy_addr
            for tid,x in scored.items():
                x=x.copy();x[FEATURES.index('rule_exact_pair')]=float(tid in exact)
                x[FEATURES.index('rule_unique')]=float(not exact and tid in unique)
                x[FEATURES.index('rule_name_overlap')]=float(tid in name_overlap)
                x[FEATURES.index('rule_fuzzy_address')]=float(tid in fuzzy_addr)
                scored[tid]=x
            # Model sees the union of exact-name and exact-address retrievals.
            bucket_features[q['id']]=[(tid,scored[tid]) for tid in pool]
            bucket_rules[q['id']]=rules
            n_pairs+=len(pool);true_total+=len(q['truth']);true_found+=len(q['truth']&pool)
        features[b]=bucket_features;rule_predictions[b]=bucket_rules
        stats[b]={'rows':len(qs),'candidate_pairs':n_pairs,'mean_candidates_per_s1':n_pairs/len(qs),'true_links':true_total,'candidate_true_links':true_found,'candidate_recall':true_found/true_total if true_total else 0.0}
    return features,rule_predictions,stats,{'target_rows_scanned':rows_seen,'relevant_target_rows':len(target),'scan_seconds':round(time.time()-started,3)}

def metrics(qs,preds):
    f=[];tp=fp=fn=0;z=zc=0
    for q in qs:
        pred=set(preds.get(q['id'],set()));truth=q['truth'];hit=len(pred&truth);fp0=len(pred-truth);miss=len(truth-pred);tp+=hit;fp+=fp0;fn+=miss
        if not truth:z+=1;zc+=int(not pred);f.append(float(not pred))
        else:f.append(f05(hit/len(pred) if pred else 0.0,hit/len(truth)))
    return {'macro_f0_5':statistics.fmean(f),'precision':tp/(tp+fp) if tp+fp else 0.0,'recall':tp/(tp+fn) if tp+fn else 0.0,'tp':tp,'fp':fp,'fn':fn,'predicted_ids':tp+fp,'zero_match_accuracy':zc/z if z else None}

def fit(x,y,w):
    mu=x.mean(0);sd=x.std(0);sd[sd<1e-8]=1;z=(x-mu)/sd;coef=np.zeros(z.shape[1]);bias=math.log((y.sum()+1)/(len(y)-y.sum()+1))
    for _ in range(350):
        p=1/(1+np.exp(-np.clip(z@coef+bias,-30,30)));err=(p-y)*w;coef-=0.12*((z.T@err)/w.sum()+0.02*coef);bias-=0.12*(err.sum()/w.sum())
    return {'mean':mu,'scale':sd,'coef':coef,'bias':float(bias)}
def predict(m,x):return 1/(1+np.exp(-np.clip(((x-m['mean'])/m['scale'])@m['coef']+m['bias'],-30,30)))

def main():
    global DATA
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,required=True,help='Challenge project root containing student_resource/dataset/train');args=ap.parse_args()
    DATA=args.project_root/'student_resource/dataset/train'
    missing=[str(DATA/f) for f in ('train_source1.tsv','train_source2.tsv','train_source3.tsv','train_ground_truth.tsv') if not (DATA/f).is_file()]
    if missing:raise SystemExit('Missing supplied training inputs: '+', '.join(missing))
    t0=time.time();samples,hashes=load_samples();features,rules,stats,scan=make_candidates(samples);byid={q['id']:q for q in samples}
    train=[];labels=[];weights=[]
    for q in (x for x in samples if x['bucket']==0):
        pairs=features[0][q['id']];n=max(1,len(pairs))
        for tid,x in pairs:train.append(x);labels.append(float(tid in q['truth']));weights.append((1/n)*(4 if tid in q['truth'] else 1))
    x=np.vstack(train);y=np.asarray(labels);w=np.asarray(weights)
    if y.sum()<10:raise RuntimeError(f'Only {int(y.sum())} positive training pairs; refuse to score')
    model=fit(x,y,w);probs={}
    for b in (1,2,3):
        flat=[];meta=[]
        for qid,pairs in features[b].items():
            for tid,fx in pairs:flat.append(fx);meta.append((qid,tid))
        ps=predict(model,np.vstack(flat)) if flat else []
        probs[b]=defaultdict(set);prob_lists={q['id']:[] for q in samples if q['bucket']==b}
        for (qid,tid),p in zip(meta,ps):prob_lists[qid].append((tid,float(p)))
        probs[b]=prob_lists
    grid=[round(i*0.02,2) for i in range(1,50)];sweep=[]
    for threshold in grid:
        pred={qid:{tid for tid,p in vals if p>=threshold} for qid,vals in probs[1].items()};sweep.append((metrics([q for q in samples if q['bucket']==1],pred),threshold))
    chosen=max(sweep,key=lambda z:(z[0]['macro_f0_5'],z[1]))[1]
    model_metrics={};rule_metrics={}
    for b in (1,2,3):
        pred={qid:{tid for tid,p in vals if p>=chosen} for qid,vals in probs[b].items()}
        qs=[q for q in samples if q['bucket']==b]
        model_metrics[b]=metrics(qs,pred);rule_metrics[b]=metrics(qs,rules[b])
    confirmation=[q for q in samples if q['bucket']==3]
    fm=[];fr=[];strata=defaultdict(list)
    for i,q in enumerate(confirmation):
        mp={tid for tid,p in probs[3][q['id']] if p>=chosen};rp=rules[3][q['id']];truth=q['truth']
        fm.append(1.0 if not truth and not mp else 0.0 if not truth else f05(len(mp&truth)/len(mp) if mp else 0.0,len(mp&truth)/len(truth)))
        fr.append(1.0 if not truth and not rp else 0.0 if not truth else f05(len(rp&truth)/len(rp) if rp else 0.0,len(rp&truth)/len(truth)))
        cls='zero' if not truth else 'one' if len(truth)==1 else 'multi';strata[(q['country'],cls)].append(i)
    rng=np.random.default_rng(20261103);deltas=np.empty(10000,dtype=np.float64)
    for k in range(len(deltas)):
        ix=np.concatenate([rng.choice(v,size=len(v),replace=True) for v in strata.values()])
        deltas[k]=float(np.mean(np.asarray(fm)[ix])-np.mean(np.asarray(fr)[ix]))
    bootstrap={'method':'10,000 paired bootstrap resamples, stratified by country x match-count class','seed':20261103,'delta_macro_f0_5':model_metrics[3]['macro_f0_5']-rule_metrics[3]['macro_f0_5'],'delta_95pct_interval':[float(np.quantile(deltas,0.025)),float(np.quantile(deltas,0.975))],'probability_delta_positive':float(np.mean(deltas>0)),'confirmation_zero_match_entities':sum(not q['truth'] for q in confirmation)}
    params={'mean':model['mean'].tolist(),'scale':model['scale'].tolist(),'coef':model['coef'].tolist(),'bias':model['bias']}
    result={'status':'training_only_no_submission_created','seeds':{'split':20261101,'sample':20261102},'sample_id_sha256':hashes,'sample_sizes':{str(b):sum(q['bucket']==b for q in samples) for b in BUCKETS},'retrieval':'one streaming pass; exact normalized name and normalized/approved-abbreviation address keys; scorer sees the union','retrieval_stats':stats,'scan':scan,'feature_names':list(FEATURES),'training':{'pairs':len(y),'positives':int(y.sum()),'negative_weighting':'per-S1 inverse candidate count; positive weight x4'},'model':'standardized deterministic NumPy logistic regression; L2=0.02; 350 batch-gradient steps; step 0.12','discovery_threshold':chosen,'discovery_sweep':{str(th):m for m,th in sweep},'discovery_model':model_metrics[1],'exploratory_bucket2_model':model_metrics[2],'confirmation_bucket':3,'confirmation_model':model_metrics[3],'discovery_rule':rule_metrics[1],'exploratory_bucket2_rule':rule_metrics[2],'confirmation_rule':rule_metrics[3],'paired_bootstrap':bootstrap,'model_parameters':params,'runtime_seconds':round(time.time()-t0,3)}
    (PACKAGE/'training_metrics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    config={**params,'threshold':chosen,'features':list(FEATURES),'training_seed':20261102,'split_seed':20261101}
    (PACKAGE/'model_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('discovery_threshold','discovery_model','confirmation_model','confirmation_rule','paired_bootstrap')},indent=2),flush=True)

if __name__=='__main__':main()
