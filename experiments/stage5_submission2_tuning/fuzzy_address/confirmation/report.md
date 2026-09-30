# Submission #2 held-out diagnosis

- Sample size: 10,000; ordered ID SHA-256: `a3ccb4534789527622ebe33a4c5ea99bfeb7b59fe18df9687298c4668c245fb3`.
- Population-proportional sample by match class × country; deterministic entity-level split seed `20260927`, sample seed `20260928`.

## Results

| Method | Macro F0.5 | Precision | Recall | TP | FP | FN | Predicted links | Zero accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.22049 | 0.8869 | 0.0743 | 2571 | 328 | 32040 | 2899 | 0.9483 |
| addr_exact_name_sim_085 | 0.26905 | 0.9172 | 0.1063 | 3679 | 332 | 30932 | 4011 | 0.9483 |
| addr_exact_name_sim_080 | 0.28278 | 0.9237 | 0.1161 | 4019 | 332 | 30592 | 4351 | 0.9483 |
| addr_exact_name_sim_075 | 0.29477 | 0.9281 | 0.1246 | 4312 | 334 | 30299 | 4646 | 0.9465 |
| name_exact_addr_overlap_040 | 0.41113 | 0.9159 | 0.2055 | 7111 | 653 | 27500 | 7764 | 0.9251 |
| combined_085 | 0.45236 | 0.9260 | 0.2375 | 8219 | 657 | 26392 | 8876 | 0.9251 |
| combined_080 | 0.46377 | 0.9287 | 0.2473 | 8559 | 657 | 26052 | 9216 | 0.9251 |
| combined_075 | 0.47395 | 0.9307 | 0.2558 | 8852 | 659 | 25759 | 9511 | 0.9234 |

## Macro F0.5 by true match-count class

**baseline:** multi (n=8,901): 0.17818; one (n=538): 0.16171; zero (n=561): 0.94831
**addr_exact_name_sim_085:** multi (n=8,901): 0.23098; one (n=538): 0.19062; zero (n=561): 0.94831
**addr_exact_name_sim_080:** multi (n=8,901): 0.24595; one (n=538): 0.19806; zero (n=561): 0.94831
**addr_exact_name_sim_075:** multi (n=8,901): 0.25942; one (n=538): 0.19992; zero (n=561): 0.94652
**name_exact_addr_overlap_040:** multi (n=8,901): 0.38861; one (n=538): 0.24785; zero (n=561): 0.92513
**combined_085:** multi (n=8,901): 0.43318; one (n=538): 0.27677; zero (n=561): 0.92513
**combined_080:** multi (n=8,901): 0.44554; one (n=538): 0.28420; zero (n=561): 0.92513
**combined_075:** multi (n=8,901): 0.45698; one (n=538): 0.28606; zero (n=561): 0.92335

## Marginal additions versus Submission #1

- `addr_exact_name_sim_085`: 1108 true, 4 false, 1112 added predictions.
- `addr_exact_name_sim_080`: 1448 true, 4 false, 1452 added predictions.
- `addr_exact_name_sim_075`: 1741 true, 6 false, 1747 added predictions.
- `name_exact_addr_overlap_040`: 4540 true, 325 false, 4865 added predictions.
- `combined_085`: 5648 true, 329 false, 5977 added predictions.
- `combined_080`: 5988 true, 329 false, 6317 added predictions.
- `combined_075`: 6281 true, 331 false, 6612 added predictions.

## Baseline error groups

False positives:
- other: 328

False negatives:
- other_or_candidate_miss: 7236
- name_variation_same_address: 2918
- address_variation_same_name: 4618
- name_order_or_punctuation: 1779
- missing_target_address: 1416
- typo_like_name: 14073

See `results.json` for example errors, exact stratum counts, and runtimes.
