# Submission #2 validation blocker

## Resolution (2026-09-27)

The original training Source 2 file has since been restored to the required path and verified at 489,301,488 bytes with the expected four-column TSV header and 5,034,616 data rows. The historical input audit below describes the earlier blocked preflight. Evaluation is complete in this folder's `results.json` and `report.md`; a second disjoint confirmation is in `experiments/stage5_submission2_confirmation/`.

The held-out experiment is prepared in `run_experiments.py`, but it cannot run against the supplied workspace data because `student_resource/dataset/train/train_source2.tsv` is absent. The supplied archive `student_resource/dataset-20260927T071941Z-1-001.zip` was inspected and also has no training Source 2 entry. A local read-only search found no other copy.

This input is required to reproduce Submission #1: its exact-name uniqueness fallback counts records across both target sources, and its exact name/address rules match against both sources. Evaluating with S3 only would change the baseline and produce invalid precision, recall, and macro F0.5 comparisons. The runner performs a preflight check and stops with the missing path identified.

No baseline score, error diagnosis, experimental score, or Submission #2 output is claimed. The experiment folder contains the planned reproducible runner and input audit only. Restore the original supplied `train_source2.tsv` under `student_resource/dataset/train/`, then run:

```powershell
python experiments/stage5_submission2_diagnosis/run_experiments.py
```

The runner uses a deterministic 20% entity-level holdout pool and a 10,000-entity sample proportioned by match class and country. It compares exact Submission #1 rules with two narrow relaxations. It does not change Stage 4 or write submission outputs.
