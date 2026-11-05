# Golden baseline

`example_data/` is the pipeline's output on the synthetic workbook
`examples/example_data.xlsx` (Stages QC to 4, default configs): every CSV that
`run_pipeline.sh` writes under a `data/`, `tables/` or `qc/` directory.
`tests/test_golden_baseline.py` reruns the pipeline and compares each file cell
by cell as CSV text, with no type inference and no NA parsing, so `0213` differs
from `213` and a literal `NA` differs from an empty cell. Tolerance
(`rtol=1e-9`, `atol=1e-12`) applies only in the measured and computed columns
listed in `FLOAT_COLUMNS` in `tools/golden_baseline.py`, and only when both
values are written as floats. Identifiers, flags, counts and text always match
exactly, so station `01.0` differs from `1.0`. A new float column must be added
to `FLOAT_COLUMNS` on purpose before it gets tolerance. It also fails when a
stage writes a new CSV or stops writing one.

`tests/test_no_unpublished_data.py` allows tracked data under `example_data/`
only at the CSV paths the generator writes
(`oa_*_outputs/[sheet/]{data,tables,qc}/*.csv`).

Excluded, because they change from run to run or are not deliverables:

- reports, manifests, logs and figures
- columns holding the absolute input path (`source_file`, `source_file_stage2`,
  …) or a stage timestamp (`stage2_processed_utc`, …), and their example values
  in `column_inventory.csv`

## Known discrepancies captured in the baseline

The baseline records today's output, including behaviour that is known to differ
from the prototype and is scheduled to change. When the change lands, its PR
regenerates the baseline and lists the differences.

- **CRM/STD rows in Stage 4 `missing_key_rows.csv` (#44).** roap carries CRM and
  TRIS rows through every stage (#29). Since #44 only Samples count in
  duplicate, replicate and per-group QC grouping, so Stage 3 reports
  `n_rows_with_incomplete_group_key = 0` as the prototype does. Stage 4's
  key-completeness report is not grouping and still checks every row, so
  `missing_key_rows.csv` lists the 4 CRM and 3 TRIS rows (no station or sample
  ID) plus sample `S007`.

## Changing the baseline

A PR that changes pipeline output must change the baseline on purpose:

1. Regenerate: `pixi run python tools/golden_baseline.py`
2. Review `git diff tests/golden/`
3. List **every** intended difference in the PR description: which file, which
   rows or columns, and why. A reviewer should be able to match each changed
   line in the diff to one item in that list.

`pixi run python tools/golden_baseline.py --check` compares without writing.

This is the fast per-PR check. The ADR-0008 manual regression on the April 2026
dataset (22 PASS / 16 REVIEW / 0 FAIL) remains the release check.
