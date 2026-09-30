# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `6403a055de20edf85254c6ab64138c6bca20c6c5e8e2e1f292bc48e1f4a40601`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20261020`, sample seed `20261021`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22020 | 0.8904 | 0.0750 | 2607 | 321 | 32169 | 2928 | 0.9250 |
| addr_exact_name_sim_095 | 0.22916 | 0.8962 | 0.0805 | 2798 | 324 | 31978 | 3122 | 0.9250 |
| name_exact_addr_overlap_080 | 0.34272 | 0.9409 | 0.1488 | 5173 | 325 | 29603 | 5498 | 0.9250 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,900): 0.18000; one (n=540): 0.15185; zero (n=560): 0.92500
**addr_exact_name_sim_095:** multi (n=8,900): 0.18974; one (n=540): 0.15741; zero (n=560): 0.92500
**name_exact_addr_overlap_080:** multi (n=8,900): 0.31542; one (n=540): 0.18889; zero (n=560): 0.92500

## Marginal additions versus Submission #1

- `addr_exact_name_sim_095`: 191 true, 3 false, 194 added predictions.
- `name_exact_addr_overlap_080`: 2566 true, 4 false, 2570 added predictions.

## Baseline error groups

False positives:
- other: 321

False negatives:
- typo_like_name: 13932
- missing_target_address: 1436
- other_or_candidate_miss: 7358
- name_order_or_punctuation: 1776
- name_variation_same_address: 2996
- address_variation_same_name: 4671

See `results.json` for example errors, exact stratum counts, and runtimes.
