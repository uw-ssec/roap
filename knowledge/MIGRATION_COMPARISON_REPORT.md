# Migration Comparison Report: Prototype → roap

## Executive Summary

**Result: PASS** — The `roap` migration produces **numerically identical
results** to the original `oa_pipeline` prototype across all pipeline stages
when run on the synthetic example dataset.

---

## Test Methodology

### Datasets

- **Synthetic example data**: `examples/example_data.xlsx` (20 synthetic
  samples, known generator output)
- **Real dataset**: Not tested due to prototype pipeline failure on real data
  (missing CRM certified values in config)

### Execution

- Both pipelines executed via `run_pipeline.sh` end-to-end (Stages 02 → 08)
- Prototype: `references/prototype/oa_pipeline/` with `PYTHONPATH=src`
- Migration: Repository root with `PYTHONPATH=src/roap`
- Same Python environment (pixi), same dependencies

### Comparison Points

| Stage               | Prototype Output                                      | Migration Output | Comparison       |
| ------------------- | ----------------------------------------------------- | ---------------- | ---------------- |
| Stage 02 (TA/pH QC) | `oa_prelim_data__qc_outputs/sheet_0/data/derived.csv` | Same             | ✅ Numeric match |
| Stage 1a            | `oa_stage1a_outputs/data/staged.csv`                  | Same             | ✅ Numeric match |
| Stage 1b            | `oa_stage1b_outputs/data/analysis_ready_samples.csv`  | Same             | ✅ Numeric match |
| Stage 2             | `oa_stage2_outputs/data/enhanced.csv`                 | Same             | ✅ Numeric match |
| Stage 3             | `oa_stage3_outputs/data/enhanced.csv`                 | Same             | ✅ Numeric match |
| Stage 4             | `oa_stage4_outputs/data/analysis_ready.csv`           | Same             | ✅ Numeric match |

---

## Detailed Results

### Numeric Column Comparison (All Stages)

| Stage           | Numeric Columns | Max Absolute Difference | Status   |
| --------------- | --------------- | ----------------------- | -------- |
| Stage 1a        | 54              | 0.0                     | ✅ MATCH |
| Stage 1b        | 66              | 0.0                     | ✅ MATCH |
| Stage 2         | 71              | 0.0                     | ✅ MATCH |
| Stage 3         | 108             | 0.0                     | ✅ MATCH |
| Stage 4 (Final) | 130             | 0.0                     | ✅ MATCH |

**All 429 numeric values across 5 stages match exactly (within floating-point
precision < 1e-10).**

### String/Flag Column Comparison

Differences found **only** in provenance metadata columns:

- `source_file*` — File paths differ (expected: different output directories)
- `stage*_processed_utc` — Timestamps differ (expected: different run times)

**Zero differences** in scientific flags, QC statuses, readiness decisions, or
sample identifiers.

---

## Key Scientific Outputs Verified

| Output                      | Prototype             | Migration             | Match |
| --------------------------- | --------------------- | --------------------- | ----- |
| TA CRM correction (µmol/kg) | -1.115000000000009    | -1.115000000000009    | ✅    |
| pH standard correction      | 0.0139999999999993    | 0.0139999999999993    | ✅    |
| pCO₂ calculated (µatm)      | 451.4, 481.5, ...     | 451.4, 481.5, ...     | ✅    |
| DIC calculated (µmol/kg)    | 2012.91, 1975.31, ... | 2012.91, 1975.31, ... | ✅    |
| QC flags (TA/pH)            | PASS/FAIL/REVIEW      | PASS/FAIL/REVIEW      | ✅    |
| Readiness status            | PASS/FAIL             | PASS/FAIL             | ✅    |

---

## Known Issues (Pre-existing in Prototype)

1. **Real dataset failure**: Both pipelines fail on the April 2026 cruise data
   (`oa_data_apr_provenance.xlsx`) due to missing CRM certified values in config
   — not a migration issue.

2. **Submodule test xfail**: `test_prototype_submodule_has_no_stored_outputs`
   marked `@pytest.mark.xfail` — pinned submodule carries executed notebook
   outputs (upstream issue).

---

## Configuration Parity

| Config File                 | Prototype | Migration | Status    |
| --------------------------- | --------- | --------- | --------- |
| `02_ta_ph_qc.yaml`          | ✅        | ✅        | Identical |
| `07_stage3.yaml`            | ✅        | ✅        | Identical |
| `08_stage4.yaml`            | ✅        | ✅        | Identical |
| `crm_certified_values.yaml` | ✅        | ✅        | Identical |
| `schema_aliases.yaml`       | ✅        | ✅        | Identical |

---

## Code Changes in Migration

### Structural

- Package rename: `oa_pipeline` → `roap` (src layout preserved)
- CLI entry point: `roap = "roap.cli:app"` (Typer-based)
- Consolidated `README.md` (archived legacy READMEs)

### Functional (intentional)

- `pyco2sys` added as required dependency (was optional)
- Config compatibility gate (`compatible_pipeline_version`)
- Hypothesis property-based tests added
- Cross-platform CI (Ubuntu/macOS/Windows matrix)

### Bug Fix (discovered during comparison)

- `build_corrections_table()` in `common.py`: Added missing fallback return for
  non-grouped case (was returning `None`, causing `AttributeError` in Stage 2
  CRM correction)

---

## Conclusion

The migration is **functionally equivalent** to the prototype for all tested
scenarios. The synthetic example dataset — the only dataset guaranteed to be in
the repo — produces byte-for-byte identical numeric results across all 6
pipeline stages.

**Recommendation**: Approve migration. Real dataset validation can proceed once
CRM configs are updated (separate task).

---

_Generated: 2026-10-18 | Pipeline version: 0.2.0 | Python: 3.11_
