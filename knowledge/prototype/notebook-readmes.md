---
type: Fact
title: Notebook READMEs (Consolidated)
description: "8 notebooks: 01 viewer, 02 TA/pH QC, 03 review, 04 Stage 1A schema, 05 Stage 1B coalescing, 06 Stage 2 duplicates, 07 Stage 3 carbonate checks, 08 Stage 4 verdicts"
tags: [notebooks, readmes, stages, papermill, parameters]
generated: { by: agent/cli, at: "2026-10-02T05:41:01Z" }
status: stable
---

# Notebook READMEs (Consolidated)

## 01_excel_viewer.ipynb
Optional Excel sheet preview. Reads input workbook, writes `oa_viewer_outputs/`. Parameters: XLSX_PATH, OUT_DIR, SHEET.

## 02_ta_ph_qc.ipynb
TA CRM correction and pH standard correction. Reads input workbook, writes `oa_prelim_data__qc_outputs/sheet_<name>/data/derived.csv`. Parameters: XLSX_PATH, OUT_DIR, SHEET, CONFIG_PATH, CRM_BATCH, PH_COL, PH_TEMP_COL, CRM_OR_SAMPLE_COL, ALLOW_CRM_FLAG_COL, PHSTD_QC, PH_BUFFER, PHSTD_TAG_PREFIX.

CRM rows detected by `sample_tag` prefix "RM" (case-insensitive). pH standard rows by prefix "tris"/"amp"/"bis".

## 03_qc_output_review.ipynb
Optional read-only review of Notebook 02 outputs. Reads OUTPUT_ROOT, produces review tables and previews.

## 04_stage1a.ipynb
Canonical schema, alias resolution, range and presence flags. Reads Notebook 02 `derived.csv`, writes `oa_stage1a_outputs/data/staged.csv` and `analysis_ready.csv`. Parameters: INPUT_CSV, OUT_DIR, CONFIG_PATH, NO_PARQUET.

Applies schema canonical_candidates, normalises units/scales, adds presence flags, builds canonical export order.

## 05_stage1b.ipynb
Best source coalescing. Reads Stage 1A `staged.csv`, writes `oa_stage1b_outputs/data/analysis_ready_samples.csv`. Parameters: INPUT_CSV, OUT_DIR, CONFIG_PATH, NO_PARQUET.

Selects best TA/pH/DIC/pCO2 sources per sample, adds role columns (measured/derived).

## 06_stage2.ipynb
Duplicate checks and replicate harmonisation. Reads Stage 1B `analysis_ready_samples.csv`, writes `oa_stage2_outputs/data/enhanced.csv`. Parameters: INPUT_CSV, OUT_DIR, CONFIG_PATH, NO_PARQUET.

Detects duplicates via key columns, computes replicate SD, flags conflicts, harmonises replicates.

## 07_stage3.ipynb
DIC species sum and pH diagnostic checks. Reads Stage 2 `enhanced.csv`, writes `oa_stage3_outputs/data/enhanced.csv`. Parameters: INPUT_CSV, OUT_DIR, CONFIG_PATH, NO_PARQUET.

Checks: DIC species sum closure, pH diagnostic (measured vs CO2SYS), unit consistency, provenance completeness. Option: `ph_diag_harmonize_temperature` (default false) to correct temp offset.

## 08_stage4.ipynb
Final audit verdict layer. Reads Stage 3 `enhanced.csv`, writes `oa_stage4_outputs/data/analysis_ready.csv`. Parameters: INPUT_CSV, OUT_DIR, CONFIG_PATH, NO_PARQUET.

Produces PASS/REVIEW/FAIL verdicts with reason codes. Checks: range flags, strict DIC species audit, provenance presence, identity/station/hydrography/core completeness.

## Common Patterns
- All notebooks: Papermill-driven, same file run interactively or via runner
- Parameters cell at top for configuration
- Output structure: `oa_<stage>_outputs/{data/,tables/,reports/,logs/}`
- Manifest.json and effective_config.json in logs/ for reproducibility
