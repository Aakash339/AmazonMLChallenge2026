# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `46f4e97b12541ea03b6c2bde323ca33591762a6482b8c4b587bf492c8f88f0f4`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20260927`, sample seed `20260928`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22344 | 0.8908 | 0.0764 | 2644 | 324 | 31960 | 2968 | 0.9282 |
| addr_exact_name_sim_085 | 0.27123 | 0.9177 | 0.1066 | 3689 | 331 | 30915 | 4020 | 0.9264 |
| addr_exact_name_sim_080 | 0.28414 | 0.9231 | 0.1159 | 4011 | 334 | 30593 | 4345 | 0.9264 |
| addr_exact_name_sim_075 | 0.29673 | 0.9274 | 0.1248 | 4317 | 338 | 30287 | 4655 | 0.9264 |
| name_exact_addr_overlap_040 | 0.41088 | 0.9167 | 0.2051 | 7097 | 645 | 27507 | 7742 | 0.9066 |
| combined_085 | 0.44982 | 0.9259 | 0.2353 | 8142 | 652 | 26462 | 8794 | 0.9048 |
| combined_080 | 0.46039 | 0.9282 | 0.2446 | 8464 | 655 | 26140 | 9119 | 0.9048 |
| combined_075 | 0.47047 | 0.9301 | 0.2534 | 8770 | 659 | 25834 | 9429 | 0.9048 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,898): 0.18391; zero (n=557): 0.92819; one (n=545): 0.14862
**addr_exact_name_sim_085:** multi (n=8,898): 0.23570; zero (n=557): 0.92639; one (n=545): 0.18165
**addr_exact_name_sim_080:** multi (n=8,898): 0.24987; zero (n=557): 0.92639; one (n=545): 0.18716
**addr_exact_name_sim_075:** multi (n=8,898): 0.26380; zero (n=557): 0.92639; one (n=545): 0.19083
**name_exact_addr_overlap_040:** multi (n=8,898): 0.39179; zero (n=557): 0.90664; one (n=545): 0.21583
**combined_085:** multi (n=8,898): 0.43364; zero (n=557): 0.90485; one (n=545): 0.24886
**combined_080:** multi (n=8,898): 0.44519; zero (n=557): 0.90485; one (n=545): 0.25436
**combined_075:** multi (n=8,898): 0.45629; zero (n=557): 0.90485; one (n=545): 0.25803

## Marginal additions versus Submission #1

- `addr_exact_name_sim_085`: 1045 true, 7 false, 1052 added predictions.
- `addr_exact_name_sim_080`: 1367 true, 10 false, 1377 added predictions.
- `addr_exact_name_sim_075`: 1673 true, 14 false, 1687 added predictions.
- `name_exact_addr_overlap_040`: 4453 true, 321 false, 4774 added predictions.
- `combined_085`: 5498 true, 328 false, 5826 added predictions.
- `combined_080`: 5820 true, 331 false, 6151 added predictions.
- `combined_075`: 6126 true, 335 false, 6461 added predictions.

## Baseline error groups

False positives:
- other: 324

False negatives:
- typo_like_name: 14004
- address_variation_same_name: 4546
- name_variation_same_address: 2964
- other_or_candidate_miss: 7245
- missing_target_address: 1386
- name_order_or_punctuation: 1815

See `results.json` for example errors, exact stratum counts, and runtimes.
