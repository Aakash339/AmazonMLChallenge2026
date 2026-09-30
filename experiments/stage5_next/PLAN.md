# Stage 5 follow-up: retrieval and learned scoring plan

## Goal and boundaries

Investigate meaningful held-out macro F0.5 gains above the current combined candidate (exact pair / unique-name fallback, exact name plus address overlap >=0.40, and exact address plus name similarity >=0.75). Use only supplied training sources and ground truth. Do not edit `student_resource/`, modify frozen Stage 4, overwrite earlier packages, submit to the portal, or claim a test/leaderboard score from training metrics.

## Checkpoint A — baseline and data audit

- Reconfirm source schemas, class/country populations, current combined-rule metrics, and package/validator status.
- Confirm the evaluation metric is per-Source-1 macro F0.5, including empty truth entities.
- Record environment/dependencies. Prefer a small reproducible scorer and avoid a broad all-pairs stage.

## Checkpoint B — candidate retrieval discovery

- Use a new fixed split seed `20261030`; holdout buckets 0 and 1 are disjoint discovery/confirmation cohorts. Use population-proportional samples by match-count class × country; development/training queries come only from buckets 2, 3, and 4.
- Compare the current combined rule against separately measured additions: (1) fuzzy normalized-name similarity paired with address-token overlap; (2) rare name-token blocks; and (3) capped rare address-token blocks. Record candidate recall before filtering, candidates per S1, false links, and macro F0.5 after filtering.
- Put hard posting and per-query candidate caps in exploratory retrieval to bound memory/time. A cap may be accepted only if the disjoint confirmation sample preserves its measured gain.
- Never build the 12.67B-pair frozen Stage 4 test set.

## Checkpoint C — compact pair scorer

- Train a deterministic, lightweight pair scorer only on candidates generated from development S1 IDs. Keep all links for each S1 in one split; sample negative pairs with a recorded seed and weight/calibrate them on discovery data.
- Candidate features use supplied normalized names/addresses, token overlap, exact/abbreviation agreement, country equality, source prefix, and retrieval-rule flags. No external data, pretrained model, or text augmentation.
- Tune only on discovery; freeze features, coefficients, and thresholds before evaluating confirmation. Optimize the official per-S1 macro F0.5, not pair accuracy.

## Checkpoint D — decision gate

- Require a reproducible improvement over the current combined rule on both disjoint holdouts, without material deterioration in zero-match S1s or candidate recall. Report uncertainty, candidate volume, precision/recall, and failure slices. If the gate fails, retain the current candidate and document why.
- Only after passing the gate, build a separate package/output, run the official validator with `--check-ids`, and preserve every existing package.

## Current status

- Checkpoint A: passed. Schemas and official metric were confirmed. Existing Stage 4 evidence shows A+HF recalls 97.42% on its 1,500-S1 sample at 7,311 candidates/S1. Local Python has no sklearn/LightGBM/XGBoost; bundled Python has NumPy 2.3.5. No package dependency was added.
- Checkpoint B: one two-split experiment completed. The frozen A+HF candidate set preserved 97.27%/97.58% candidate recall on 750-S1 samples. Adding fuzzy name similarity ≥0.85 with at least two shared address tokens and containment ≥0.40 improved macro F0.5 from 0.45484/0.47759 to 0.63775/0.65753. It also reduced zero-match accuracy from 0.952/0.881 to 0.524/0.452 and relies on the infeasible broad candidate set. It is diagnostic evidence, not a production rule. Details: `RETRIEVAL_REPORT.md` and `retrieval_results.json`.
- Checkpoint C: passed with the optimized one-pass exact-key retrieval runner. The deterministic logistic model trains on bucket 0, tunes threshold 0.30 on bucket 1, and evaluates once on fresh bucket 3. Bucket 2 is reported as a secondary diagnostic only. Confirmation candidate recall was 29.97% at 8.92 candidates/S1. The paired stratified bootstrap gain over the `.40/.75` rule was +0.03495 macro F0.5 (95% interval +0.02341 to +0.04753). Full result and reproducible package training code are under `experiments/stage5_submission3_learned/package/` and `experiments/stage5_next/compact_model/COMPACT_MODEL_REPORT.md`.
- Checkpoint D: passed for preparing a separate candidate: discovery and fresh confirmation both improved, and confirmation zero-match accuracy was unchanged. Submission #3 outputs were generated separately and passed the supplied validator with `--check-ids`. Earlier packages and frozen Stage 4 remain unchanged. No score ≥0.80 or leaderboard result is claimed; test labels are unavailable.
