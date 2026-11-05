# Golden baseline

`example_data/` is the pipeline's output on the synthetic workbook
`examples/example_data.xlsx` (Stages QC to 4, default configs): every CSV that
`run_pipeline.sh` writes under a `data/`, `tables/` or `qc/` directory.
`tests/test_golden_baseline.py` reruns the pipeline and compares each file with
`pandas.testing.assert_frame_equal` (`rtol=1e-9`, `atol=1e-12`). It also fails
when a stage writes a new CSV or stops writing one.

Excluded, because they change from run to run or are not deliverables:

- reports, manifests, logs and figures
- columns holding the absolute input path (`source_file`, `source_file_stage2`,
  …) or a stage timestamp (`stage2_processed_utc`, …), and their example values
  in `column_inventory.csv`

## Known discrepancies captured in the baseline

The baseline records today's output, including behaviour that is known to differ
from the prototype and is scheduled to change. When the change lands, its PR
regenerates the baseline and lists the differences.

- **CRM/STD rows in Stage 3/4 group-key counts (#47, #44).** roap carries CRM
  and TRIS rows through every stage (#29), and Stage 3 `build_qc_summary` counts
  every row it receives. So sample rows report
  `n_rows_with_incomplete_group_key = 7` (the 4 CRM and 3 TRIS rows, which have
  no station or sample ID) where the prototype reports 0, and Stage 4
  `missing_key_rows.csv` lists those 7 rows plus sample `S007`. #44 makes this
  grouping count only Samples.

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
