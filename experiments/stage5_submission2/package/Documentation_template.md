# ML Challenge 2026: Business Entity Resolution Solution

**Team Name:** Not recorded in the workspace  
**Team Members:** Not recorded in the workspace  
**Submission Date:** 2026-09-27

---

## 1. Executive Summary

Submission #2 uses deterministic, country-aware matching rules based on the supplied names and addresses. On two disjoint, population-proportional 10,000-entity training holdouts, adding exact normalized-name plus high address-token containment raised macro F0.5 from 0.22020 to 0.34272, and from 0.22453 to 0.34566. These are validation results; test labels are unavailable and no Submission #2 leaderboard score is claimed.

---

## 2. Methodology

### 2.1 Problem Analysis

Source 1 records can match zero or multiple Source 2/3 records. Training includes US and India; the test set also includes France. The implementation compares the country strings directly, so it does not restrict the country set. Existing project measurements show a large multi-match class, and name/address variation, missing target addresses, name-order differences, and typo-like names all occur. No external business lookup, API, data augmentation, transliteration, or newly trained model was used.

### 2.2 Solution Strategy

**Approach Type:** Deterministic blocking and rule-based matching  
**Core Innovation:** Add a narrow address-overlap rule to exact normalized-name matches while requiring at least two shared address tokens and high containment to limit false matches.

Normalization uses the supplied project utility: NFKC, case folding, punctuation-to-space, and whitespace cleanup. An approved small address-abbreviation representation is used for the existing exact-address rule. Raw input files were preserved.

---

## 3. Candidate Generation (Blocking)

- **Blocking keys used:** Exact country and normalized business name across test S2 and S3. The index is restricted to target name keys present in test S1. Exact normalized and approved abbreviation-normalized addresses are then checked; the added rule compares normalized address token sets.
- **Candidate pairs generated:** 1,028,030 final accepted target IDs across the 1,732,544 test Source 1 rows. This rule-only pipeline writes those final accepted IDs in `candidate_pairs.tsv`; it does not emit the broad frozen Stage 4 blocker set.
- **How true matches were protected:** Preserve every exact pair match; use exact-name fallback only when no exact pair is found and the country/name posting is unique across S2+S3; accept the added overlap rule only with at least two shared tokens and containment ≥0.80. The final candidate list contains every emitted match.

The full frozen Stage 4 candidate generator was not used or changed. Its large candidate volume was not materialized.

---

## 4. Matching Model

**Features used:**
- Name: exact normalized name equality; existing baseline rules do not use fuzzy name similarity in the selected Submission #2 configuration.
- Address: exact normalized address, exact approved abbreviation-normalized address, and address token containment for exact-name pairs.
- Other: exact country equality; unique normalized-name posting across both target sources as a fallback.

**Model type:** Deterministic rules; no trained classifier or external model.  
**Threshold selection method:** The fixed address rule (at least two shared tokens and `shared / min(query token count, target token count) ≥ 0.80`) was compared with the exact Submission #1 baseline on two disjoint, preselected holdout buckets. The same rule improved macro F0.5 in both; no test labels were used to tune it.

---

## 5. Results & Error Analysis

- **F0.5 Score (macro):** Best measured validation value 0.34566 on the second 10,000-entity holdout; the exact baseline on that same holdout scored 0.22453. On the first holdout the rule scored 0.34272 versus 0.22020. These are held-out training results, not a test or leaderboard score. Submission #1 previously scored 0.228 on the leaderboard; Submission #2 has not been scored there.
- **Common false positives (wrong merges):** The added rule produced 4 false links on the first holdout and 3 on the second. String-overlap rules can still join distinct businesses sharing a name and similar address tokens; training labels may also be incomplete or noisy.
- **Common false negatives (missed matches):** Remaining misses include typo-like name changes, address variation, name variation with a similar address, missing target addresses, and candidate misses. The rule cannot recover records without an exact normalized name, and address-token overlap cannot help when addresses are missing or substantially different.

Validation used entity-level SHA-256 buckets 0 and 1 with split seed `20261020`; sample seeds were `20261021` and `20261022`. The ordered sample ID hashes and full metrics are in the accompanying experiment results. The official submission validator passed with `--check-ids`: all 1,732,544 required S1 rows and all 9,969,589 test target IDs were checked. Test precision, recall, and F0.5 are unknown because test labels are unavailable.

---

## 6. Conclusion

The additional exact-name/address-overlap rule improved macro F0.5 on two disjoint, population-proportional training holdouts while adding few false predictions in those samples. The generated test outputs are format- and ID-validated, but their leaderboard quality remains unmeasured. The results support a Submission #2 candidate; they do not establish a leaderboard score gain.

---

## Appendix

### A. Code Artefacts

The runnable generator is `code/business_entity_resolution/src/generate_submission2.py`; the conservative normalizer is included under `src/normalization/normalize.py`. Run instructions and environment details are in `code/business_entity_resolution/README.md`, `requirements.txt`, and `runtime.txt`. The generator reads the supplied test files from the project root and writes the two TSVs under `output/`.

### B. Additional Results

Detailed reproducible results, error examples, population strata, and run timings are in `experiments/stage5_submission2_diagnosis/` and `experiments/stage5_submission2_confirmation/` in the working project. The first and second holdout IDs are disjoint by hash bucket. France is processed as an open-set country value but cannot be validated from training labels.
