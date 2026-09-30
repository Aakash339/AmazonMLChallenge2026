# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `972d33675fbb90dab3bec7963c51902b10b0cd11aa3c3b9765d4a7121ba7fa50`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20261020`, sample seed `20261024`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22165 | 0.8900 | 0.0752 | 2630 | 325 | 32335 | 2955 | 0.9443 |
| addr_exact_name_sim_095 | 0.23231 | 0.8980 | 0.0818 | 2860 | 325 | 32105 | 3185 | 0.9443 |
| addr_exact_name_sim_090 | 0.25407 | 0.9108 | 0.0960 | 3358 | 329 | 31607 | 3687 | 0.9443 |
| name_exact_addr_overlap_080 | 0.34010 | 0.9400 | 0.1465 | 5123 | 327 | 29842 | 5450 | 0.9443 |
| name_exact_addr_overlap_060 | 0.39653 | 0.9510 | 0.1904 | 6656 | 343 | 28309 | 6999 | 0.9408 |
| name_exact_addr_overlap_040 | 0.40995 | 0.9207 | 0.2050 | 7168 | 617 | 27797 | 7785 | 0.9192 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,900): 0.18118; zero (n=557): 0.94434; one (n=543): 0.14365
**addr_exact_name_sim_095:** multi (n=8,900): 0.19282; zero (n=557): 0.94434; one (n=543): 0.14917
**addr_exact_name_sim_090:** multi (n=8,900): 0.21575; zero (n=557): 0.94434; one (n=543): 0.17414
**name_exact_addr_overlap_080:** multi (n=8,900): 0.31270; zero (n=557): 0.94434; one (n=543): 0.16943
**name_exact_addr_overlap_060:** multi (n=8,900): 0.37497; zero (n=557): 0.94075; one (n=543): 0.19153
**name_exact_addr_overlap_040:** multi (n=8,900): 0.39099; zero (n=557): 0.91921; one (n=543): 0.19828

## Marginal additions versus Submission #1

- `addr_exact_name_sim_095`: 230 true, 0 false, 230 added predictions.
- `addr_exact_name_sim_090`: 728 true, 4 false, 732 added predictions.
- `name_exact_addr_overlap_080`: 2493 true, 2 false, 2495 added predictions.
- `name_exact_addr_overlap_060`: 4026 true, 18 false, 4044 added predictions.
- `name_exact_addr_overlap_040`: 4538 true, 292 false, 4830 added predictions.

## Baseline error groups

False positives:
- other: 325

False negatives:
- typo_like_name: 13927
- name_variation_same_address: 3092
- other_or_candidate_miss: 7575
- name_order_or_punctuation: 1744
- address_variation_same_name: 4615
- missing_target_address: 1382

See `results.json` for example errors, exact stratum counts, and runtimes.
