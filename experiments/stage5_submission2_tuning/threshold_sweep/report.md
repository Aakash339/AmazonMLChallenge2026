# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `325608b098e3f8a0f9271445d426b738fa71eb99d75df1453c766c3523b89884`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20261020`, sample seed `20261025`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22176 | 0.8840 | 0.0750 | 2592 | 340 | 31988 | 2932 | 0.9364 |
| addr_exact_name_sim_095 | 0.23098 | 0.8916 | 0.0809 | 2797 | 340 | 31783 | 3137 | 0.9364 |
| addr_exact_name_sim_090 | 0.25279 | 0.9053 | 0.0951 | 3288 | 344 | 31292 | 3632 | 0.9364 |
| name_exact_addr_overlap_080 | 0.34302 | 0.9370 | 0.1468 | 5075 | 341 | 29505 | 5416 | 0.9364 |
| name_exact_addr_overlap_060 | 0.39670 | 0.9483 | 0.1892 | 6544 | 357 | 28036 | 6901 | 0.9346 |
| name_exact_addr_overlap_040 | 0.40871 | 0.9128 | 0.2042 | 7062 | 675 | 27518 | 7737 | 0.9081 |
| name_exact_addr_overlap_030 | 0.40688 | 0.8687 | 0.2052 | 7095 | 1072 | 27485 | 8167 | 0.8922 |
| name_exact_addr_overlap_020 | 0.40051 | 0.7768 | 0.2053 | 7100 | 2040 | 27480 | 9140 | 0.8463 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,895): 0.18006; zero (n=566): 0.93640; one (n=539): 0.15955
**addr_exact_name_sim_095:** multi (n=8,895): 0.18991; zero (n=566): 0.93640; one (n=539): 0.16801
**addr_exact_name_sim_090:** multi (n=8,895): 0.21329; zero (n=566): 0.93640; one (n=539): 0.18677
**name_exact_addr_overlap_080:** multi (n=8,895): 0.31458; zero (n=566): 0.93640; one (n=539): 0.18924
**name_exact_addr_overlap_060:** multi (n=8,895): 0.37386; zero (n=566): 0.93463; one (n=539): 0.20882
**name_exact_addr_overlap_040:** multi (n=8,895): 0.38901; zero (n=566): 0.90813; one (n=539): 0.20933
**name_exact_addr_overlap_030:** multi (n=8,895): 0.38802; zero (n=566): 0.89223; one (n=539): 0.20851
**name_exact_addr_overlap_020:** multi (n=8,895): 0.38390; zero (n=566): 0.84629; one (n=539): 0.20654

## Marginal additions versus Submission #1

- `addr_exact_name_sim_095`: 205 true, 0 false, 205 added predictions.
- `addr_exact_name_sim_090`: 696 true, 4 false, 700 added predictions.
- `name_exact_addr_overlap_080`: 2483 true, 1 false, 2484 added predictions.
- `name_exact_addr_overlap_060`: 3952 true, 17 false, 3969 added predictions.
- `name_exact_addr_overlap_040`: 4470 true, 335 false, 4805 added predictions.
- `name_exact_addr_overlap_030`: 4503 true, 732 false, 5235 added predictions.
- `name_exact_addr_overlap_020`: 4508 true, 1700 false, 6208 added predictions.

## Baseline error groups

False positives:
- other: 340

False negatives:
- typo_like_name: 13808
- other_or_candidate_miss: 7465
- missing_target_address: 1438
- name_variation_same_address: 2985
- address_variation_same_name: 4554
- name_order_or_punctuation: 1738

See `results.json` for example errors, exact stratum counts, and runtimes.
