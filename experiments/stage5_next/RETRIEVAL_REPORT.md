# Retrieval experiment: fuzzy name plus partial address

## Question

Can a fuzzy normalized-name match recover additional true links when both records share multiple address tokens, while retaining a useful precision-heavy macro F0.5?

## Data and split

- Supplied train S1/S2/S3 and ground truth only. No original data files were changed.
- Split seed `20261030`; hash buckets 0 and 1 are disjoint. A population-proportional sample of 750 S1s was selected in each bucket by match class × country, excluding every previously saved validation ID.
- Sample ID SHA-256: bucket 0 `bb6a8d4e5ecbb6b43418c15b2617f24fce060aba34778090f85b31d4053a796e`; bucket 1 `1de7a32d8ca8021b01980a2a82b0611a301d78aa76abcc5ca0e2950a11888416`.
- True links: 2,602 and 2,523. Each sample has 42 zero-match entities, approximately 40 singleton entities, and the rest multi-match entities.

## Fixed candidate set and rule

The frozen Stage 4 A+HF-address/name blocker was used unchanged to retrieve training candidates. It retrieved 2,531/2,602 (97.27%) true links in bucket 0 and 2,462/2,523 (97.58%) in bucket 1, but yielded 5,496,650 and 5,217,837 total candidates across only 750 S1s. This confirms that its raw candidate stream is too large to transfer directly to full test inference.

The reference rule was the current combined .40/.75 candidate: exact Submission #1 rules, exact normalized name plus at least two shared address tokens with containment ≥0.40, and exact normalized/approved-abbreviation address plus normalized-name similarity ≥0.75. The tested addition allows non-exact names when the candidate shares at least two normalized address tokens with containment ≥0.40. Similarity thresholds .95/.90/.85/.80/.75 were fixed before these two samples were scored. The discovery sample selected .85; bucket 1 independently repeated the gain.

## Results

| Rule | Similarity | Bucket | Macro F0.5 | Precision | Recall | TP | FP | Predicted IDs | Zero-match accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Current combined | — | 0 | 0.45484 | 0.93544 | 0.25058 | 652 | 45 | 697 | 0.95238 |
| Current combined | — | 1 | 0.47759 | 0.94366 | 0.26556 | 670 | 40 | 710 | 0.88095 |
| Added fuzzy name + address overlap | ≥0.95 | 0 | 0.52111 | 0.92632 | 0.30438 | 792 | 63 | 855 | 0.95238 |
| Added fuzzy name + address overlap | ≥0.95 | 1 | 0.53696 | 0.93714 | 0.31907 | 805 | 54 | 859 | 0.88095 |
| Added fuzzy name + address overlap | ≥0.90 | 0 | 0.62109 | 0.86530 | 0.43736 | 1,137 | 177 | 1,314 | 0.85714 |
| Added fuzzy name + address overlap | ≥0.90 | 1 | 0.64351 | 0.87900 | 0.45184 | 1,140 | 157 | 1,297 | 0.71429 |
| **Added fuzzy name + address overlap** | **≥0.85** | **0** | **0.63775** | **0.73952** | **0.53574** | **1,394** | **491** | **1,885** | **0.52381** |
| **Added fuzzy name + address overlap** | **≥0.85** | **1** | **0.65753** | **0.73397** | **0.54895** | **1,385** | **502** | **1,887** | **0.45238** |
| Added fuzzy name + address overlap | ≥0.80 | 0 | 0.62675 | 0.57941 | 0.60992 | 1,587 | 1,152 | 2,739 | 0.38095 |
| Added fuzzy name + address overlap | ≥0.80 | 1 | 0.63629 | 0.54177 | 0.62981 | 1,589 | 1,344 | 2,933 | 0.21429 |
| Added fuzzy name + address overlap | ≥0.75 | 0 | 0.59947 | 0.44235 | 0.66641 | 1,734 | 2,186 | 3,920 | 0.23810 |
| Added fuzzy name + address overlap | ≥0.75 | 1 | 0.60177 | 0.39457 | 0.69124 | 1,744 | 2,676 | 4,420 | 0.09524 |

All metrics are per these held-out training samples; they are not test or leaderboard scores. The .85 setting substantially increases recall and macro F0.5, but false matches increase sharply and zero-match accuracy falls by 43–48 percentage points. Lowering the threshold further hurts F0.5 despite higher link recall.

## Decision and next checkpoint

This is a promising retrieval/scoring rule for the next experiment, not a production candidate. Its measurement uses the large frozen A+HF candidate pool (about 7,000 candidates per S1); a full test run is still infeasible. Do not add it to a submission until a compact retrieval stage can preserve its recall and a pair scorer can control false positives, especially on zero-match entities. Next, test frequency-capped address-token/name blocks and a small learned or calibrated pair scorer on disjoint development/discovery/confirmation splits. Freeze the scorer before confirmation. Keep the current .40/.75 package unchanged.

Implementation: `retrieval_experiment.py`. Machine-readable results and exact configuration: `retrieval_results.json`. Runtime: 1,092.614 seconds. The first attempted run had a ground-truth JSON parsing error; it was discarded. The reported run added S2/S3-prefix integrity checks and passed them.
