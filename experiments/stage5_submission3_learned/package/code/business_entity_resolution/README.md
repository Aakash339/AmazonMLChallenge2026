# Business Entity Resolution — Learned Submission #3

This package contains a small supervised logistic pair scorer trained only on the challenge’s supplied training sources and labels. No pretrained model, external business data, lookup service, or test labels are used. The model has 15 coefficients and uses the MIT-licensed implementation included here.

## Reproduce the model and test outputs

Requirements: Python 3.12.14 and the pinned dependency in `requirements.txt`. Keep the supplied `student_resource/` folder available under the project root.

From PowerShell:

```powershell
$projectRoot = 'C:\path\to\challenge\project'
$packageDir = 'C:\path\to\Submission3\package'
python (Join-Path $packageDir 'code/business_entity_resolution/src/train_model.py') `
  --project-root $projectRoot
python (Join-Path $packageDir 'code/business_entity_resolution/src/generate_submission3.py') `
  --project-root $projectRoot `
  --output-dir (Join-Path $packageDir 'output')
python (Join-Path $projectRoot 'student_resource/utils/validate_submission.py') `
  --matching (Join-Path $packageDir 'output/matching_results.tsv') `
  --candidate (Join-Path $packageDir 'output/candidate_pairs.tsv') `
  --test-dir (Join-Path $projectRoot 'student_resource/dataset/test') `
  --check-ids
```

`train_model.py` uses the fixed S1 cohorts in `cohorts/`: bucket 0 trains the scorer; bucket 1 selects the threshold; bucket 3 is the untouched confirmation cohort. Bucket 2 is retained as a secondary diagnostic cohort. Cohorts are stratified by country and match-count class, with seeds and hashes in `training_metrics.json`. Training writes `model_config.json` and `training_metrics.json` in the package root.

The test generator reads all S1 rows to define query keys, streams both target sources into a temporary SQLite index restricted to those keys, scores the union of exact normalized-name and exact normalized/approved-abbreviation-address candidates, and writes both contract TSVs. `candidate_pairs.tsv` lists the full set scored for each S1, so all final matches are included. The temporary index is removed when generation completes.

## Validation and results

The supplied validator passed with `--check-ids`: 1,732,544 matching rows, 1,732,544 candidate rows, and all 9,969,589 target IDs checked. Test labels are unavailable; there is no test score or leaderboard score claim.

On the prespecified discovery cohort, macro F0.5 was 0.49534 for the model and 0.45893 for the current `.40/.75` rule. On the fresh confirmation cohort, it was 0.50095 versus 0.46599. Confirmation precision/recall were 0.86972/0.29145 for the model and 0.91295/0.25369 for the rule. Zero-match accuracy was unchanged at 25/28. A paired bootstrap, stratified by country × match-count class, estimated a +0.03495 macro F0.5 gain with a 95% interval of [+0.02341, +0.04753] (10,000 replicates, seed 20261103).

This is offline evidence from 500-entity samples, not a guarantee of leaderboard performance. The measured retrieval candidate recall was about 30%; this is the main known limitation.
