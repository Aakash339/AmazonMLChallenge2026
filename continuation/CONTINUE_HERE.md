# Continue Here — Amazon ML Challenge 2026

**Current date:** 2026-09-27  
**Current objective:** Review the separate combined Submission #2 candidate; portal score remains pending unless the user submits it.

## Current state

- Stages 1–3 complete; Stage 4 complete and frozen.
- Submission #1 scored leaderboard macro F0.5=0.228.
- The original training `train_source2.tsv` was restored and verified: 489,301,488 bytes, expected four-column TSV header, and 5,034,616 data rows.
- The separate combined candidate adds exact-address/name-similarity ≥0.75 to the confirmed .40 overlap rule. Two disjoint 10,000-S1 holdouts scored macro F0.5 0.47047 and 0.47395 vs .40-only 0.41088 and 0.41113.
- Candidate package and test outputs are under `experiments/stage5_submission2_combined075/`; validator passed with target-ID checks. Offline results are not leaderboard scores and remain below 0.80. Prior .40 and .80 packages are preserved.

## Method and limits

The combined candidate retains exact pair and unique-name fallback rules, the exact-name/address overlap ≥0.40 rule, and accepts exact normalized/approved abbreviation-address matches with name similarity ≥0.75. Stage 4 was not changed. Only supplied data was used; France is open-set but has no labeled training validation.

Do not report held-out metrics as leaderboard results. Preserve Submission #1 and all candidate packages. If a candidate is submitted, record the portal result and submission count. See `PROJECT_STATE.md`, `EXPERIMENT_LOG.md`, and `experiments/stage5_submission2_combined075/`.
