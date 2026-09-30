# Submission #2 combined 0.75 candidate

This is a separately generated and validated package that preserves all earlier candidates. Its matching rule combines:

1. The exact Submission #1 rules.
2. Exact normalized name plus at least two shared normalized address tokens with containment ≥0.40.
3. Exact normalized or approved abbreviation-normalized address plus normalized-name character similarity ≥0.75.

## Held-out evidence

The two population-proportional 10,000-S1 holdouts use disjoint SHA-256 buckets 0 and 1, split seed `20260927`, and sample seed `20260928`. On bucket 0, macro F0.5 was 0.47047 for the combined rule, 0.41088 for the .40-only rule, and 0.22344 for the exact baseline. On bucket 1, corresponding scores were 0.47395, 0.41113, and 0.22049. These are training holdout metrics, not a test or leaderboard score. The target of 0.80 was not reached.

Full result JSON, reports, and sample IDs are under `../stage5_submission2_tuning/fuzzy_address/` and its `confirmation/` child.

## Test outputs and validation

The package under `package/` generated outputs for 1,732,544 Source 1 rows and predicted 2,580,681 target IDs. The supplied validator passed with `--check-ids`, checking all 9,969,589 target IDs. Test truth is unavailable. The candidate-pairs file contains the rule's final accepted IDs, not every pair from the frozen Stage 4 blocker set.

The ZIP artifact is `Amazon_ML_Challenge_2026_submission2_combined075.zip`.
