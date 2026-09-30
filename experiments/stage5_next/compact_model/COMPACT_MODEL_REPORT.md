# Compact pair scorer experiment — completed

## Outcome

A one-pass exact-name/exact-address candidate index and deterministic logistic pair scorer improved macro F0.5 over the current combined `.40/.75` rule on the discovery and fresh confirmation samples. A separate Submission #3 package was generated and passed the official validator. No test or leaderboard score is available or claimed. Earlier packages remain unchanged.

## Experiment design

The fixed cohorts contain 500 population-proportional S1 entities each, stratified by country × match-count class. Hash split seed `20261101`, sample seed `20261102`; bucket 0 trained the model, bucket 1 selected the threshold, bucket 3 was the untouched confirmation, and bucket 2 was a secondary diagnostic. All samples were verified unique and disjoint from each other and from 14 earlier validation-ID files. Bucket-3 ordered ID SHA-256: `2440175c2cf5ab269c874d5761f61ecc376256588018a06616d8612037aa67cb`.

The final retrieval scans S2+S3 once and indexes only targets reached by exact normalized-name or exact normalized/approved-abbreviation-address keys. The model uses 15 text/overlap/source/rule features. Training uses standardized NumPy logistic regression (L2 0.02, 350 batch steps, 0.12 step size); S1 groups are equally weighted, positive pairs receive 4× weight. Threshold 0.30 was selected on bucket 1 and frozen before bucket 3.

## Results

| Cohort | Method | Macro F0.5 | Precision | Recall | TP | FP | Zero-match accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| Discovery, bucket 1 | Logistic scorer | 0.49534 | 0.89869 | 0.28769 | 479 | 54 | 27/28 |
| Discovery, bucket 1 | Current `.40/.75` rule | 0.45893 | 0.91503 | 0.25225 | 420 | 39 | 27/28 |
| Fresh confirmation, bucket 3 | Logistic scorer | 0.50095 | 0.86972 | 0.29145 | 494 | 74 | 25/28 |
| Fresh confirmation, bucket 3 | Current `.40/.75` rule | 0.46599 | 0.91295 | 0.25369 | 430 | 41 | 25/28 |

Confirmation candidate recall was 508/1,695 (29.97%) before scoring; the pool averaged 8.92 candidates per S1. A paired bootstrap stratified by country × match-count class estimated +0.03495 macro F0.5 over the rule (95% interval +0.02341 to +0.04753; 10,000 replicates; seed `20261103`). The secondary bucket-2 score was 0.50237 versus 0.45690. These are offline sample metrics, not a leaderboard score.

## Test package and verification

The separate package is `experiments/stage5_submission3_learned/package/`. It generated one row for every 1,732,544 test S1 IDs, 11,478,881 candidate pairs (mean 6.63/S1), and 2,981,735 final predicted IDs. The candidate output contains the entire model-scored retrieval pool. The supplied `validate_submission.py --check-ids` passed and checked all 9,969,589 S2/S3 target IDs. Runtime was approximately 20.5 minutes, mostly test inference. France is processed by open-set country equality. Test labels are unavailable; portal submission/score remains unknown.

## Earlier failed route

The initial two-pass frequency-capped index was too slow for this environment; its first attempt also had a corrected schema-name bug. No metrics or outputs came from that route, and its temporary indexes were removed. The successful one-pass runner and reproducible package training code supersede it. Stage 4 remains frozen.
