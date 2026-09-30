# Amazon ML Challenge 2026 — Team Handoff

## Project

Business Entity Resolution: for every Source 1 business, identify zero or more corresponding Source 2 and Source 3 records.

## Current status

- Stage 1: COMPLETE
- Stage 2: COMPLETE
- Stage 3: COMPLETE
- Stage 4: COMPLETE / FROZEN
- Stage 5: Submission #2 candidate generated and validated; portal result pending.
- Submission #1: completed; leaderboard F0.5 = **0.228**

The 0.228 score came from the fast Submission #1 direct-match baseline, not the full frozen Stage 4 + Stage 5 scorer. The separate combined candidate adds an exact-address/name-similarity ≥0.75 rule to the confirmed exact-name/address-token containment ≥0.40 rule. It scored macro F0.5 0.47047 and 0.47395 on two disjoint 10,000-entity training holdouts; the .40-only rule scored 0.41088 and 0.41113 on the same samples. Test outputs and package are under `experiments/stage5_submission2_combined075/`; the supplied validator passed with target-ID checks. These are offline scores; no Submission #2 leaderboard score is available, and 0.80 has not been reached.

## Dataset setup

The official dataset is intentionally not stored in Git. Obtain the official challenge files and place them locally under:

```text
student_resource/
├── dataset/
│   ├── train/
│   └── test/
├── utils/
└── ...
```

The challenge files are required locally. Teammates should obtain them separately through the official challenge distribution/account, then place them in the structure above. Do not redistribute or copy the large dataset into Git. Do not modify `student_resource/dataset/`.

To verify the expected files in a local checkout, run from the project root:

```sh
for f in \
  student_resource/dataset/train/train_source1.tsv \
  student_resource/dataset/train/train_source2.tsv \
  student_resource/dataset/train/train_source3.tsv \
  student_resource/dataset/train/train_ground_truth.tsv \
  student_resource/dataset/test/test_source1.tsv \
  student_resource/dataset/test/test_source2.tsv \
  student_resource/dataset/test/test_source3.tsv \
  student_resource/utils/validate_submission.py; do
  test -f "$f" || echo "Missing: $f"
done
```

The supplied `.gitignore` excludes `student_resource/dataset/`, `output/`, TSV/CSV exports, and local database files. Before staging, verify with `git check-ignore -v student_resource/dataset/train/train_source1.tsv output/matching_results.tsv experiments/stage5/submission1_fast_baseline/target_index.sqlite`, then inspect `git status --short` and the staged file list. Do not use `git add -f` on ignored data or generated files.

## Frozen Stage 4 design

**A = Prefix5 UNION Address2500.** The frozen operational strategy is **A + HF-address/name**: same-country address token df 2,501–25,000 **AND** same-country name token df 1–25,000.

Stage 4.7 used 1,500 S1s and 5,156 true links:

| Strategy | Recall | Candidates |
|---|---:|---:|
| A | 96.18% (4,959/5,156) | 10,906,369 |
| A + HF-address/name (frozen) | 97.42% (5,023/5,156) | 10,967,173 |
| B | 98.84% (5,096/5,156) | 36,380,324 |
| A + name-token≤2,500 | 97.63% (5,034/5,156) | 11,770,701 |

Do not silently change these definitions. Record any proposed change as a separate experiment. See `experiments/stage4_7/` for the validation evidence.

## Stage 5 scorer and compute limit

The held-out training validation scorer baseline measured F0.5=0.5483, precision=0.9030, recall=0.2510, threshold=12.0. Of 482 true links, 17 were not generated as candidates, 465 were scored, 121 scored ≥12, and 344 scored below 12. It was not the source of Submission #1's leaderboard score.

The frozen generator is estimated to produce about 12.67 billion test candidates. At the measured ~19,600 pair scores/second, scoring the full set would take about 178 hours. Do not launch that job or materialize hundreds of GB of candidates. Stage 4 remains frozen; pursue a separately documented computationally feasible retrieval approach.

## Submission #1

The fast direct indexed exact/strong matching baseline processed 1,732,544 S1 rows and predicted 510,033 target IDs:

- 1,232,937 S1 rows with zero matches
- 489,960 S1 rows with one match
- 9,647 S1 rows with multiple matches

The supplied validator passed. The leaderboard score was F0.5=0.228. This is the first real leaderboard baseline, not the final approach. Its compact `candidate_pairs.tsv` is an accepted-ID representation for this submission and is not the complete frozen Stage 4 blocker set. See `experiments/stage5/submission1_fast_baseline/` for code, rules, benchmark, and results.

## Immediate next task: review the separate Submission #2 candidates

1. Review `experiments/stage5_submission2_combined075/Amazon_ML_Challenge_2026_submission2_combined075.zip` and its held-out evidence alongside the preserved .40 and .80 packages.
2. If submitting, record the resulting portal score separately; offline scores are not leaderboard scores.
3. Preserve Submission #1 and all historical experiments. Stage 4 remains frozen.

Never score the 12.6B candidate set or materialize hundreds of GB. Do not modify `student_resource/`, use external data/APIs, install unnecessary packages, delete historical experiments, or declare a best model before validation.

## History and control files

Preserve `experiments/stage4_3/`, `stage4_4/`, `stage4_5/`, `stage4_6/`, `stage4_7/`, and `stage5/`. `AGENTS.md`, `PROJECT_STATE.md`, and `EXPERIMENT_LOG.md` are project-control records. Continuation notes for fresh sessions are under `continuation/`.
