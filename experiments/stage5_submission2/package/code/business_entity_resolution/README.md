# Business Entity Resolution — Submission #2

This package reproduces the rule-based test outputs using only the supplied challenge data. It contains no learned model and uses Python's standard library plus the copied project normalization module.

## Inputs

The project data must be available under `student_resource/dataset/test/` with `test_source1.tsv`, `test_source2.tsv`, and `test_source3.tsv`. The challenge validator must be available at `student_resource/utils/validate_submission.py`.

## Reproduce outputs

After extracting this package, set `$packageDir` to its folder and `$projectRoot` to the challenge project folder that contains `student_resource/`, then run:

```powershell
$packageDir = 'C:\path\to\extracted\package'
$projectRoot = 'C:\path\to\challenge\project'
python (Join-Path $packageDir 'code/business_entity_resolution/src/generate_submission2.py') `
  --project-root $projectRoot `
  --output-dir (Join-Path $packageDir 'output')
```

The script streams the target TSVs into a temporary SQLite index restricted to target country/name keys present in Source 1, then writes both output TSVs. The matching rules are documented in `Documentation_template.md` at the package root. Temporary index data is removed when the script exits.

## Validate

```powershell
python (Join-Path $projectRoot 'student_resource/utils/validate_submission.py') `
  --matching (Join-Path $packageDir 'output/matching_results.tsv') `
  --candidate (Join-Path $packageDir 'output/candidate_pairs.tsv') `
  --test-dir (Join-Path $projectRoot 'student_resource/dataset/test') `
  --check-ids
```

The recorded run passed this validator, including target ID checks. Test labels are unavailable, so the package does not claim a test or leaderboard score.

## Environment

Runtime used: Python 3.14.3. `requirements.txt` is intentionally empty of third-party packages because the pipeline uses only the Python standard library. `runtime.txt` records the Python version used for this run.
