---
type: Decision
title: Portable notebook defaults and live package references
description:
  P1 notebooks use repository-local inputs while Papermill overrides and
  historical prototype references remain intact.
tags: [notebooks, portability, p1, rename]
generated: { by: agent/dinesh-codex, at: "2026-10-26T21:39:30Z" }
status: draft
---

## Scope and status

This note records the implementation choices for P1 issues
[#54](https://github.com/uw-ssec/roap/issues/54) and
[#55](https://github.com/uw-ssec/roap/issues/55), pending code PR review. Don
authorized direct PR creation after Richard/Dinesh cross-review on 2026-10-26
and required knowledge changes to be separate PRs (maintainer direction).

## Portable defaults

- Notebook kernels started at the repository root or in `notebooks/` resolve the
  same repository-local inputs with `pathlib.Path`.
- `01_excel_viewer.ipynb` and `02_ta_ph_qc.ipynb` use
  `examples/example_data.xlsx` by default. Their existing `OUT_DIR = None`
  behavior keeps outputs next to that workbook.
- `03_qc_output_review.ipynb` uses `examples/example_data__qc_outputs`, matching
  Notebook 02's interactive default. The runner supplies its explicit QC output
  directory during batch runs.
- `oa_figures.ipynb` uses the synthetic workbook. `oa_figures_extended.ipynb`
  uses `outputs/test/oa_stage4_outputs/data/analysis_ready.csv` for both `INPUT`
  and `INPUT_PHD`, matching the README quickstart. Run the quickstart pipeline
  first or set the inputs to an existing run.
- Preserve the existing parameter names and `parameters` tags. `run_pipeline.sh`
  continues to inject `XLSX_PATH`, `OUT_DIR` and `OUTPUT_ROOT`; default path
  cleanup must not override supplied parameters.
- No automatic search for private cruise workbooks, and no embedded personal
  home-directory paths.

Source: `notebooks/01_excel_viewer.ipynb`, `notebooks/02_ta_ph_qc.ipynb`,
`notebooks/03_qc_output_review.ipynb`, `notebooks/oa_figures.ipynb`,
`notebooks/oa_figures_extended.ipynb`, `run_pipeline.sh`, `README.md`.

## Live names versus history

Live README import examples, config comments, tool docstrings, runner help and
test docstrings use `roap`. Historical plans, `knowledge/` records, upstream
prototype paths and regression tests deliberately naming the old package retain
`oa_pipeline`. Notebook personal-path cleanup belongs to #55 rather than a
textual package rename. Issue source-path references in #12, #15, #19 and #20
are corrected separately from git changes.

Source: [#54 scope and exclusions](https://github.com/uw-ssec/roap/issues/54).

## Verification requirements

`tests/test_notebook_imports.py` guards all executable notebook cells against
the old package name without a Windows-path exemption, and against Windows,
macOS and Linux user home paths. The original six defaults were reproduced as
guard failures before replacement. Check actual parameter expressions from both
supported working directories, the complete package test suite, the pipeline's
injected parameters, and `pixi run pre-commit-all` before submission.

Linked reference: [engineering decisions](engineering-decisions.md).
