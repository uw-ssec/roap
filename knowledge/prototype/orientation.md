---
type: Fact
title: OA Pipeline Orientation
description: "Three run modes, 8 notebook stages, 12 package modules, configuration system, example data, Windows Git Bash requirement"
tags: [orientation, run-modes, notebooks, modules, config, windows]
generated: { by: agent/cli, at: "2026-10-02T00:43:23Z" }
status: stable
---

# OA Pipeline Orientation

## Quick Start
The pipeline reads an Excel workbook with TA, pH, temperature, salinity, DIC measurements and produces analysis_ready.csv with PASS/REVIEW/FAIL verdicts per row.

## Three Ways to Run
1. **Full CLI**: `./run_pipeline.sh INPUT_XLSX OUTPUT_ROOT [options]`
2. **Desktop GUI**: `python oa_pipeline_app.py` (Tkinter, no terminal)
3. **Interactive Notebooks**: Open in Jupyter/VS Code, edit parameters cell, Restart Kernel and Run All

## Eight Notebook Stages
| # | Notebook | Role | Reads | Writes |
|---|----------|------|-------|--------|
| 01 | 01_excel_viewer.ipynb | Optional preview | Input workbook | oa_viewer_outputs/ |
| 02 | 02_ta_ph_qc.ipynb | TA CRM + pH std correction | Input workbook | derived.csv |
| 03 | 03_qc_output_review.ipynb | Optional review of 02 | 02 output | Review tables |
| 04 | 04_stage1a.ipynb | Canonical schema, aliases | derived.csv | staged.csv |
| 05 | 05_stage1b.ipynb | Best source coalescing | staged.csv | analysis_ready_samples.csv |
| 06 | 06_stage2.ipynb | Duplicates, replicates | analysis_ready_samples.csv | enhanced.csv |
| 07 | 07_stage3.ipynb | DIC sum, pH diagnostics | enhanced.csv | enhanced.csv |
| 08 | 08_stage4.ipynb | Final audit verdicts | enhanced.csv | analysis_ready.csv |

## Package Modules (src/oa_pipeline/)
12 modules: common, schema, policy, qc_ta_ph, inspect, stage1b, stage2, stage3, stage4, carbonate_calc, duplicate_precision, __init__

## Configuration
Per-stage YAML configs in configs/ directory. Key files:
- crm_certified_values.yaml - Dickson CRM batch certified TA values
- cruise_grade_thresholds.yaml - Quality thresholds
- regional.yaml - Regional settings
- 02_ta_ph_qc.yaml, 07_stage3.yaml - Stage-specific overrides

## Example Data
`python examples/make_example_data.py` → examples/example_data.xlsx (27 rows: 20 samples, 4 CRM, 3 TRIS)
4 injected issues with known expected verdicts for integration testing.

## Windows Specific
- Must use Git Bash (not WSL) - path handling differences
- Forward-slash paths work on all platforms: `C:/Users/.../file.xlsx`
- Desktop launcher auto-detects Git Bash
