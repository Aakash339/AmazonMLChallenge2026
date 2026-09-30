# ML Challenge 2026: Business Entity Resolution Solution

**Team Name:** Not recorded in the workspace  
**Team Members:** Not recorded in the workspace  
**Submission Date:** 2026-09-27

---

## 1. Executive Summary

Submission #2 uses deterministic, country-aware matching rules based on the supplied names and addresses. On three disjoint, population-proportional 10,000-entity training holdouts, adding exact normalized-name plus address-token containment ≥0.40 raised macro F0.5 from 0.22361 to 0.41398, 0.22165 to 0.40995, and 0.22176 to 0.40871. These are validation results; test labels are unavailable and no Submission #2 leaderboard score is claimed.

---

## 2. Methodology

### 2.1 Problem Analysis

Source 1 records can match zero or multiple Source 2/3 records. Training includes US and India; the test set also includes France. The implementation compares the country strings directly, so it does not restrict the country set. Existing project measurements show a large multi-match class, and name/address variation, missing target addresses, name-order differences, and typo-like names all occur. No external business lookup, API, data augmentation, transliteration, or newly trained model was used.

### 2.2 Solution Strategy

**Approach Type:** Deterministic blocking and rule-based matching  
**Core Innovation:** Add address-token overlap for exact normalized-name matches, requiring at least two shared tokens and containment ≥0.40 to balance recall and false matches.

Normalization uses the supplied project utility: NFKC, case folding, punctuation-to-space, and whitespace cleanup. An approved small address-abbreviation representation is used for the existing exact-address rule. Raw input files were preserved.

---

## 3. Candidate Generation (Blocking)

- **Blocking keys used:** Exact country and normalized business name across test S2 and S3. The index is restricted to target name keys present in test S1. Exact normalized and approved abbreviation-normalized addresses are then checked; the added rule compares normalized address token sets.
- **Candidate pairs generated:** 2,310,532 final accepted target IDs across the 1,732,544 test Source 1 rows. This rule-only pipeline writes those final accepted IDs in `candidate_pairs.tsv`; it does not emit the broad frozen Stage 4 blocker set.
- **How true matches were protected:** Preserve every exact pair match; use exact-name fallback only when no exact pair is found and the country/name posting is unique across S2+S3; accept the added overlap rule only with at least two shared tokens and containment ≥0.40. The final candidate list contains every emitted match.

The full frozen Stage 4 candidate generator was not used or changed. Its large candidate volume was not materialized.

---

## 4. Matching Model

**Features used:**
- Name: exact normalized name equality; existing baseline rules do not use fuzzy name similarity in the selected Submission #2 configuration.
- Address: exact normalized address, exact approved abbreviation-normalized address, and address token containment for exact-name pairs.
- Other: exact country equality; unique normalized-name posting across both target sources as a fallback.

**Model type:** Deterministic rules; no trained classifier or external model.  
**Threshold selection method:** A prespecified sweep compared containment thresholds 0.80, 0.60, 0.40, 0.30, and 0.20 on one population-proportional training bucket. The best sweep result was 0.40. It then beat the exact baseline on two additional disjoint buckets (macro F0.5 0.40995 and 0.40871). The fixed threshold was not chosen from test labels.

---

## 5. Results & Error Analysis

- **F0.5 Score (macro):** The selected 0.40 rule scored 0.41398, 0.40995, and 0.40871 on three disjoint 10,000-entity holdouts; the exact baseline on those same samples scored 0.22361, 0.22165, and 0.22176. These are held-out training results, not a test or leaderboard score. Submission #1 previously scored 0.228 on the leaderboard; Submission #2 has not been scored there.
- **Common false positives (wrong merges):** At threshold 0.40, the rule added 239, 292, and 335 false links versus baseline across the three holdouts. At 0.20, false links rose to 1,700 on the threshold-sweep sample and macro F0.5 fell from 0.40871 to 0.40051. String-overlap rules can still join distinct businesses sharing a name and similar address tokens; training labels may also be incomplete or noisy.
- **Common false negatives (missed matches):** Remaining misses include typo-like name changes, address variation, name variation with a similar address, missing target addresses, and candidate misses. The rule cannot recover records without an exact normalized name, and address-token overlap cannot help when addresses are missing or substantially different.

Validation used entity-level SHA-256 buckets 2, 3, and 4 with split seed `20261020`; sample seeds were `20261023`, `20261024`, and `20261025`. The ordered sample ID hashes and full metrics are in the experiment results. The official submission validator passed with `--check-ids`: all 1,732,544 required S1 rows and all 9,969,589 test target IDs were checked. Test precision, recall, and F0.5 are unknown because test labels are unavailable.

---

## 6. Conclusion

The exact-name/address-overlap rule at containment 0.40 improved macro F0.5 on three disjoint, population-proportional training holdouts. It adds recall with a measurable rise in false predictions; the test outputs are format- and ID-validated, but leaderboard quality remains unmeasured. The results support a Submission #2 candidate; they do not establish a leaderboard score gain or the requested 0.75 target.

---

## Appendix

### A. Code Artefacts

The runnable generator is `code/business_entity_resolution/src/generate_submission2.py`; the conservative normalizer is included under `src/normalization/normalize.py`. Run instructions and environment details are in `code/business_entity_resolution/README.md`, `requirements.txt`, and `runtime.txt`. The generator reads the supplied test files from the project root and writes the two TSVs under `output/`.

### B. Additional Results

Detailed threshold sweep and confirmation results, error examples, population strata, and timings are in `experiments/stage5_submission2_tuning/` in the working project. The selected samples use disjoint hash buckets. France is processed as an open-set country value but cannot be validated from training labels.
