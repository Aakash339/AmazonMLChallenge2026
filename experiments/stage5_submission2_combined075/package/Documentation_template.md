# ML Challenge 2026: Business Entity Resolution Solution

**Team Name:** Not recorded in the workspace  
**Team Members:** Not recorded in the workspace  
**Submission Date:** 2026-09-27

---

## 1. Executive Summary

This candidate combines two deterministic rules based only on supplied names and addresses. On two disjoint, population-proportional 10,000-entity training holdouts, the combination scored macro F0.5 0.47047 and 0.47395, versus 0.41088 and 0.41113 for the 0.40 address-overlap rule alone. These are held-out training results; test labels are unavailable and no leaderboard score is claimed. This remains below the requested 0.80 target.

---

## 2. Methodology

### 2.1 Problem Analysis

Source 1 records can match zero or multiple Source 2/3 records. Training includes US and India; the test set also includes France. The implementation compares the country strings directly, so it does not restrict the country set. Existing project measurements show a large multi-match class, and name/address variation, missing target addresses, name-order differences, and typo-like names all occur. No external business lookup, API, data augmentation, transliteration, or newly trained model was used.

### 2.2 Solution Strategy

**Approach Type:** Deterministic blocking and rule-based matching  
**Core Innovation:** Combine (a) address-token overlap for exact normalized-name matches, requiring at least two shared tokens and containment ≥0.40, and (b) exact normalized or approved abbreviation-normalized address matches whose normalized names have character similarity ≥0.75.

Normalization uses the supplied project utility: NFKC, case folding, punctuation-to-space, and whitespace cleanup. An approved small address-abbreviation representation is used for the existing exact-address rule. Raw input files were preserved.

---

## 3. Candidate Generation (Blocking)

- **Blocking keys used:** Exact country and normalized business name, plus exact country and normalized/approved-abbreviation address. SQLite indexes retain only keys present in Source 1.
- **Candidate pairs generated:** 2,580,681 final accepted target IDs across the 1,732,544 test Source 1 rows. This rule-only pipeline writes those final accepted IDs in `candidate_pairs.tsv`; it does not emit the broad frozen Stage 4 blocker set.
- **How true matches were protected:** Preserve exact pair matches; use exact-name fallback only when no exact pair is found and the country/name posting is unique across S2+S3; include exact-name/address-overlap matches meeting the .40 rule; and include exact normalized or approved abbreviation-address matches with normalized-name similarity ≥0.75. Final IDs are deduplicated.

The full frozen Stage 4 candidate generator was not used or changed. Its large candidate volume was not materialized.

---

## 4. Matching Model

**Features used:**
- Name: exact normalized name, or character similarity ≥0.75 when normalized/approved-abbreviation addresses match exactly.
- Address: exact normalized address, exact approved abbreviation-normalized address, and address token containment for exact-name pairs.
- Other: exact country equality; unique normalized-name posting across both target sources as a fallback.

**Model type:** Deterministic rules; no trained classifier or external model.  
**Threshold selection method:** Prior disjoint holdouts selected and confirmed containment 0.40. A fresh discovery split compared name similarity thresholds 0.85, 0.80, and 0.75 for exact-address candidates, each combined with the .40 overlap rule; .75 scored highest. A disjoint companion split confirmed this setting. No test labels were used.

---

## 5. Results & Error Analysis

- **F0.5 Score (macro):** Combined rule: 0.47047 and 0.47395 on two disjoint 10,000-entity holdouts; overlap-only rule: 0.41088 and 0.41113 on those same samples; exact baseline: 0.22344 and 0.22049. These are held-out training results, not a leaderboard score. Submission #1 previously scored 0.228; this candidate has not been scored on the leaderboard.
- **Common false positives (wrong merges):** Relative to exact baseline, the combination added 328/331 false links while adding 5,498/6,281 true links across the discovery/confirmation splits. Exact-address fuzzy-name additions alone caused 14/6 false links for 1,673/1,741 true links. Exact addresses may be shared and training labels may be incomplete or noisy.
- **Common false negatives (missed matches):** Remaining misses include address variation, missing target addresses, name changes below the similarity cutoff, name variation when addresses differ, and candidate misses.

Validation used disjoint entity-level SHA-256 buckets 0 and 1 with split seed `20260927`, sample seed `20260928`, and ordered-ID SHA-256 values `46f4e97b12541ea03b6c2bde323ca33591762a6482b8c4b587bf492c8f88f0f4` and `a3ccb4534789527622ebe33a4c5ea99bfeb7b59fe18df9687298c4668c245fb3`. Full metrics are in `experiments/stage5_submission2_tuning/fuzzy_address/`. The official validator passed with `--check-ids`: all 1,732,544 required S1 rows and all 9,969,589 test target IDs were checked. Test metrics and leaderboard score remain unknown.

---

## 6. Conclusion

The combined rule improved held-out macro F0.5 over the already-confirmed .40 rule on two disjoint, population-proportional training holdouts. Generated outputs passed the official validator with target-ID checks. The offline result remains below 0.80; leaderboard quality remains unknown.

---

## Appendix

### A. Code Artefacts

The runnable generator is `code/business_entity_resolution/src/generate_submission2.py`; the conservative normalizer is included under `src/normalization/normalize.py`. Run instructions and environment details are in `code/business_entity_resolution/README.md`, `requirements.txt`, and `runtime.txt`. The generator reads the supplied test files from the project root and writes the two TSVs under `output/`.

### B. Additional Results

Detailed threshold sweep and confirmation results, error examples, population strata, and timings are in `experiments/stage5_submission2_tuning/` in the working project. The selected samples use disjoint hash buckets. France is processed as an open-set country value but cannot be validated from training labels.
