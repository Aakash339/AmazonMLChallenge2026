# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `adc06db822ca9eeaee08139cb407dec82ba6b9e27e69e78a3033fe359b3d0e21`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20261020`, sample seed `20261022`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22453 | 0.8908 | 0.0765 | 2650 | 325 | 31989 | 2975 | 0.9442 |
| addr_exact_name_sim_095 | 0.23255 | 0.8956 | 0.0815 | 2822 | 329 | 31817 | 3151 | 0.9442 |
| name_exact_addr_overlap_080 | 0.34566 | 0.9406 | 0.1500 | 5196 | 328 | 29443 | 5524 | 0.9424 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,903): 0.18312; zero (n=556): 0.94424; one (n=541): 0.16636
**addr_exact_name_sim_095:** multi (n=8,903): 0.19201; zero (n=556): 0.94424; one (n=541): 0.16821
**name_exact_addr_overlap_080:** multi (n=8,903): 0.31704; zero (n=556): 0.94245; one (n=541): 0.20333

## Marginal additions versus Submission #1

- `addr_exact_name_sim_095`: 172 true, 4 false, 176 added predictions.
- `name_exact_addr_overlap_080`: 2546 true, 3 false, 2549 added predictions.

## Baseline error groups

False positives:
- other: 325

False negatives:
- name_variation_same_address: 3012
- typo_like_name: 13882
- address_variation_same_name: 4587
- other_or_candidate_miss: 7274
- missing_target_address: 1390
- name_order_or_punctuation: 1844

See `results.json` for example errors, exact stratum counts, and runtimes.
