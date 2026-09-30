# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `7b281fc71daa78628dcd194ad1d8c29019a61badbc97818c12bc5eaf64c59064`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20261020`, sample seed `20261023`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22361 | 0.8803 | 0.0770 | 2662 | 362 | 31902 | 3024 | 0.9188 |
| addr_exact_name_sim_095 | 0.23281 | 0.8872 | 0.0826 | 2855 | 363 | 31709 | 3218 | 0.9188 |
| addr_exact_name_sim_090 | 0.25488 | 0.9021 | 0.0974 | 3365 | 365 | 31199 | 3730 | 0.9188 |
| name_exact_addr_overlap_080 | 0.34532 | 0.9344 | 0.1504 | 5197 | 365 | 29367 | 5562 | 0.9188 |
| name_exact_addr_overlap_060 | 0.40072 | 0.9463 | 0.1926 | 6657 | 378 | 27907 | 7035 | 0.9170 |
| name_exact_addr_overlap_040 | 0.41398 | 0.9224 | 0.2067 | 7145 | 601 | 27419 | 7746 | 0.9025 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,910): 0.18464; zero (n=554): 0.91877; one (n=536): 0.15299
**addr_exact_name_sim_095:** multi (n=8,910): 0.19485; zero (n=554): 0.91877; one (n=536): 0.15485
**addr_exact_name_sim_090:** multi (n=8,910): 0.21860; zero (n=554): 0.91877; one (n=536): 0.17164
**name_exact_addr_overlap_080:** multi (n=8,910): 0.31921; zero (n=554): 0.91877; one (n=536): 0.18657
**name_exact_addr_overlap_060:** multi (n=8,910): 0.38005; zero (n=554): 0.91697; one (n=536): 0.21082
**name_exact_addr_overlap_040:** multi (n=8,910): 0.39559; zero (n=554): 0.90253; one (n=536): 0.21476

## Marginal additions versus Submission #1

- `addr_exact_name_sim_095`: 193 true, 1 false, 194 added predictions.
- `addr_exact_name_sim_090`: 703 true, 3 false, 706 added predictions.
- `name_exact_addr_overlap_080`: 2535 true, 3 false, 2538 added predictions.
- `name_exact_addr_overlap_060`: 3995 true, 16 false, 4011 added predictions.
- `name_exact_addr_overlap_040`: 4483 true, 239 false, 4722 added predictions.

## Baseline error groups

False positives:
- other: 362

False negatives:
- other_or_candidate_miss: 7197
- name_order_or_punctuation: 1745
- typo_like_name: 13902
- address_variation_same_name: 4566
- name_variation_same_address: 3074
- missing_target_address: 1418

See `results.json` for example errors, exact stratum counts, and runtimes.
