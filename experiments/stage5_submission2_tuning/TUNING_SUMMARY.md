# Submission #2 address-overlap threshold tuning

## Design

Used three disjoint 10,000-entity, population-proportional SHA-256 holdout buckets (2, 3, 4; split seed `20261020`). The exact Submission #1 baseline was compared with exact normalized-name matches requiring at least two shared normalized-address tokens at containment thresholds 0.80, 0.60, 0.40, 0.30, and 0.20. Bucket 2 selected 0.40 among 0.80/0.60/0.40; buckets 3 and 4 confirmed it. All candidate settings were fixed from training data only. The data split and full metrics are in the per-bucket `results.json` and `report.md` files.

## Macro F0.5

| Bucket | Exact baseline | 0.80 | 0.60 | 0.40 | 0.30 | 0.20 |
|---|---:|---:|---:|---:|---:|---:|
| 2 (discovery) | 0.22361 | 0.34532 | 0.40072 | **0.41398** | not run | not run |
| 3 (confirmation) | 0.22165 | 0.34010 | 0.39653 | **0.40995** | not run | not run |
| 4 (confirmation) | 0.22176 | 0.34302 | 0.39670 | **0.40871** | 0.40688 | 0.40051 |

The 0.40 rule retained high link precision on these samples (0.9128–0.9224) at 0.2042–0.2067 recall. By comparison, 0.20 had precision 0.7768 and recall 0.2053 on bucket 4; the small recall gain did not offset the false matches. The highest measured value here is about 0.414, far below 0.75.

## Test candidate

The 0.40 rule was run over test sources into `experiments/stage5_submission2_overlap040/package/output/`. It predicts 2,310,532 target IDs over 1,732,544 Source 1 rows; both TSVs passed the supplied validator with `--check-ids`. Test truth is unavailable, so test and leaderboard scores are unknown. This variant is separate from and preserves the earlier 0.80 package.
