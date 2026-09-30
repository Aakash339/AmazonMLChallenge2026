# Current State (2026-09-27)

**Project:** Amazon ML Challenge 2026 — Business Entity Resolution  
**Root:** Use the current workspace root; older machine-specific path notes are historical.  
**Goal:** Improve on Submission #1 while preserving the frozen Stage 4 methodology and all project rules.

Stages 1–4 are complete; Stage 4 is frozen. Submission #1 scored leaderboard F0.5=0.228. The missing original training Source 2 file has been restored and verified. Two disjoint, population-proportional 10,000-S1 holdouts support the same exact-name/address-token-containment rule: macro F0.5 0.34272 vs 0.22020, then 0.34566 vs 0.22453.

The newest separate Submission #2 candidate combines exact-name/address containment 0.40 with exact-address/name-similarity 0.75. It scored offline macro F0.5 0.47047 and 0.47395 on two disjoint 10,000-S1 training holdouts; the overlap-only comparator scored 0.41088 and 0.41113. Its test outputs and package are in `experiments/stage5_submission2_combined075/`, and passed the supplied validator with `--check-ids`. No portal score exists. The .40 and .80 packages remain preserved. Test truth is unavailable; 0.80 has not been reached.

Next: review the combined candidate against the preserved .40 and .80 versions; if submitting, record its portal score. Preserve Submission #1, use only supplied data, and keep Stage 4 frozen.
