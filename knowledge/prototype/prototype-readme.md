---
type: Architecture
title: Prototype README
description: "oa_pipeline v0.2.0: 8 notebooks, 9 package modules, 3 run modes (CLI/GUI/Notebook), Windows Git Bash requirement, example data, 221 tests"
tags: [prototype, readme, notebooks, modules, run-modes, testing]
generated: { by: agent/cli, at: "2026-10-02T05:40:42Z" }
status: stable
---

# oa_pipeline v0.2.0 — Prototype README

## Pipeline Flow

Eight notebook preprocessing pipeline for ocean acidification carbonate chemistry data. Reads Excel workbook with TA, pH, temperature, salinity, DIC measurements. Applies CRM corrected TA QC, pH standard correction, canonical column harmonisation, best source analysis field selection, duplicate and replicate checks, carbonate system internal consistency diagnostics, and a final per row audit verdict.

Final output: PASS / REVIEW / FAIL per row → analysis_ready.csv

```
oa_prelim_data.xlsx
    │ Notebook 01 optional: Excel sheet preview
    ▼
02_ta_ph_qc
    │ CRM TA correction and pH standard correction
    ▼
04_stage1a
    │ Canonical schema and alias resolution
    ▼
05_stage1b
    │ Best source fields such as ta_best_umolkg and ph_best
    ▼
06_stage2
    │ Duplicate checks and replicate harmonisation
    ▼
07_stage3
    │ DIC species sum and pH diagnostic checks
    ▼
08_stage4
    │ Final PASS / REVIEW / FAIL verdicts
    ▼
final analysis ready dataset
```

Notebook 03 is optional read-only review of Notebook 02 outputs.

## Package Modules (src/oa_pipeline/)

| Module | Provides | Imported By |
|--------|----------|-------------|
| common | Generic helpers for paths, JSON/CSV writing, timestamps, coercion, Excel reading, missingness tables, coalescing helpers, robust outlier flags | All notebooks |
| schema | Canonical schema, alias resolution, config loading, unit and pH scale normalisation, duplicate key helpers, canonical export ordering | Stages 1A to 4 |
| policy | RangePolicy, range configuration, stage range flag helpers | Stages 1A, 1B, and 4 |
| qc_ta_ph | TA CRM correction, pH standard correction, QC plots, QC markdown reports | Notebook 02 |
| inspect | Read only output tree inspection helpers | Notebook 03 |
| stage1b | Best source coalescing and sample ready filtering | Notebook 05 |
| stage2 | Duplicate detection, replicate harmonisation, replicate SD checks, conflict annotations | Notebook 06, reused by 07 and 08 |
| stage3 | Carbonate integrity checks: DIC species sum, pH diagnostic, scale flags, unit flags, provenance flags | Notebook 07 |
| stage4 | Final audit, range checks, strict DIC audit, PASS/REVIEW/FAIL verdicts, reason code tables | Notebook 08 |

## Configuration

`run_pipeline.sh --config-dir configs` looks for optional per-stage YAML configs:
- 02_ta_ph_qc.yaml, 04_stage1a.yaml, 05_stage1b.yaml, 06_stage2.yaml, 07_stage3.yaml, 08_stage4.yaml

Reference files: cruise_grade_thresholds.yaml, regional.yaml, crm_certified_values.yaml

## Three Ways to Run

1. **Full CLI**: `./run_pipeline.sh INPUT_XLSX OUTPUT_ROOT [options]`
2. **Desktop GUI**: `python oa_pipeline_app.py` (Tkinter, no terminal)
3. **Interactive Notebooks**: Edit parameters cell → Restart Kernel and Run All

## Windows Specific

Must use Git Bash (not WSL) — path handling differences. Forward-slash paths work on all platforms. Desktop launcher auto-detects Git Bash.

## Example Dataset

`python examples/make_example_data.py` → examples/example_data.xlsx (27 rows: 20 samples, 4 CRM, 3 TRIS)
4 injected issues with known expected verdicts for integration testing.

## Testing

221 tests passing: `python -m pytest -q`
Includes unit tests for schema, coalesce, readiness, QC, and Papermill end-to-end test on example workbook.
