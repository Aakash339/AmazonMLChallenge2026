# ML Challenge 2026: Business Entity Resolution Solution

**Team Name:** Not recorded in workspace  
**Team Members:** Not recorded in workspace  
**Submission Date:** 2026-09-27

## 1. Executive Summary

Submission #3 uses deterministic, supplied-data normalization, exact-key candidate generation, and a compact supervised logistic pair scorer. It was prepared as a separate package after a prespecified held-out experiment improved macro F0.5 over the existing `.40/.75` rule on discovery and fresh confirmation samples. The held-out result is not a test or leaderboard score.

## 2. Data and Constraints

Only supplied `student_resource/dataset/train/` and `student_resource/dataset/test/` files are used. Original challenge inputs are unchanged. Country is treated as an open-set string value, including France at inference. No external entity lookup, augmentation, API, or pretrained model is used. The learned model has 15 coefficients and the implementation is MIT licensed.

## 3. Normalization and Candidate Generation

The supplied project normalization utility creates conservative NFKC/case-folded, punctuation-to-space, whitespace-normalized names and addresses. The approved address-abbreviation form remains separate. At inference, candidates are the union of all same-country exact normalized-name targets and targets whose normalized or approved abbreviation-normalized address exactly matches. This compact pool averaged 6.63 candidates per test S1 and contained 11,478,881 total pairs. The candidate file lists this complete model-scored pool, not only final predictions.

## 4. Matching Model

The model is deterministic standardized batch logistic regression with L2 regularization 0.02, 350 gradient steps, step size 0.12, and threshold 0.30. Training uses all candidates from 500 S1s in hash bucket 0, with equal total pair weight per S1 and a fourfold positive weight. Features are normalized-name character similarity, name/address token Jaccard and containment, exact address and abbreviation agreement, exact name, name-length ratio, target source indicator, and four current-rule flags. The threshold was selected by a macro-F0.5 sweep on bucket 1 and frozen before bucket 3 confirmation. Bucket 2 is an additional exploratory diagnostic only.

## 5. Held-out Evaluation

Each cohort contains 500 population-proportional S1 entities stratified by country × match-count class. Hash split seed: `20261101`; sample seed: `20261102`. Confirmation bucket 3 sample ID hash: `2440175c2cf5ab269c874d5761f61ecc376256588018a06616d8612037aa67cb`.

| Cohort | Method | Macro F0.5 | Precision | Recall | TP | FP | Zero-match accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| Discovery, bucket 1 | Logistic scorer | 0.49534 | 0.89869 | 0.28769 | 479 | 54 | 27/28 |
| Discovery, bucket 1 | Current `.40/.75` rule | 0.45893 | 0.91503 | 0.25225 | 420 | 39 | 27/28 |
| Confirmation, bucket 3 | Logistic scorer | 0.50095 | 0.86972 | 0.29145 | 494 | 74 | 25/28 |
| Confirmation, bucket 3 | Current `.40/.75` rule | 0.46599 | 0.91295 | 0.25369 | 430 | 41 | 25/28 |

The paired, stratified bootstrap on confirmation estimated a macro F0.5 difference of +0.03495, 95% interval [+0.02341, +0.04753], with 10,000 replicates and seed `20261103`. Candidate recall before scoring was 29.97% (508/1,695 true links) on confirmation. Candidate recall is a substantial limitation; the model cannot recover links outside its exact-key pool.

## 6. Test Output and Limitations

The supplied validator passed with `--check-ids`. The output contains one row per 1,732,544 test S1 IDs and references only existing S2/S3 IDs. It contains 11,478,881 candidate pairs and 2,981,735 predicted links. These are output counts, not a test score. No test labels or leaderboard result are available, and no score above 0.8 is claimed. Existing packages are preserved separately.

## 7. Reproduction Artifacts

Training code: `code/business_entity_resolution/src/train_model.py`; test generator: `code/business_entity_resolution/src/generate_submission3.py`; fixed cohort IDs: `code/business_entity_resolution/cohorts/`; model parameters and metrics: `model_config.json` and `training_metrics.json`. Follow `code/business_entity_resolution/README.md` and validate with the supplied challenge validator.
