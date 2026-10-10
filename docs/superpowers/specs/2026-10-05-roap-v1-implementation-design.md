# ROAP v1.0.0 — Implementation Design

**Status**: Approved **Date**: 2026-10-05 **Based on**: AI-Friendly PRD
(`docs/ai-prd.md`), decisions (`decisions.md`), council review, prototype v0.2.0

---

## Overview

Transform the `oa_pipeline` v0.2.0 research prototype (8 Papermill notebooks,
221 tests, Windows-only) into a production-grade, cross-platform, citable Python
package with CLI, GUI, and notebook interfaces — delivering reproducible ocean
acidification carbonate chemistry QC processing per Frontiers 2021 data
standards.

**North Star**: Fresh clone → `pixi install` →
`pixi run pipeline examples/example_data.xlsx outputs/test` →
`analysis_ready.csv` with expected 4 FAIL verdicts in <10 min on Linux, macOS,
Windows.

---

## Architecture

### Single Engine, Three Doors (ADR-0010)

```
src/oa_pipeline/          # Core engine (12 pure Python modules)
    ├── __init__.py       # Public API re-exports
    ├── common.py         # Paths, I/O, coalescing, flags, manifests
    ├── schema.py         # Canonical schema, aliases, normalizers, export order
    ├── qc_ta_ph.py       # TA CRM correction, pH standard correction, plots
    ├── policy.py         # RangePolicy, range flag helpers
    ├── stage1b.py        # Best source coalescing
    ├── stage2.py         # Duplicate detection, replicate harmonisation
    ├── stage3.py         # Carbonate integrity: DIC sum, pH diagnostic, provenance
    ├── stage4.py         # Final audit, PASS/REVIEW/FAIL verdicts
    ├── inspect.py        # Read-only output tree inspection
    ├── carbonate_calc.py # PyCO2SYS wrapper (legacy — not used in current pipeline)
    └── duplicate_precision.py # Legacy — not used in current pipeline

tools/
    ├── oa_pipeline_app.py        # Tkinter GUI launcher
    ├── oa_pipeline_app_core.py   # GUI-independent launcher logic
    └── stamp_carbonate_provenance.py # Provenance stamping helper

notebooks/                # 8 orchestration notebooks (Papermill)
    ├── 01_preview.ipynb
    ├── 02_ta_ph_qc.ipynb
    ├── 04_stage1a.ipynb
    ├── 05_stage1b.ipynb
    ├── 06_stage2.ipynb
    ├── 07_stage3.ipynb
    ├── 08_stage4.ipynb
    └── ...

CLI: run_pipeline.sh → src/oa_pipeline modules
GUI: tools/oa_pipeline_app.py → src/oa_pipeline modules
Notebook: notebooks/*.ipynb → src/oa_pipeline modules
```

---

## Phase Breakdown

### P-1: Prototype Migration (Weeks 1-2) — BLOCKING

**Goal**: Copy prototype → target repo structure, all 221 tests pass, pipeline
runs on synthetic data.

### P0: Cross-Platform CI + Invariant Test + Entry Point (Weeks 3-4)

**Goal**: CI green on Ubuntu/macOS/Windows + invariant test fails on column
mutation + single README.

### P1: Tagged Release v0.2.0 + Run Bundles + Config Gate (Weeks 5-6)

**Goal**: `pip install oa-pipeline==0.2.0` works; config gate enforced; run
bundles produced.

### P2: Schema/Provenance/CRM/Excel Fixes + Property Tests (Weeks 7-9)

**Goal**: Frontiers 2021 audit complete; Excel round-trip fixed; CRM/std
validation fails fast; hypothesis tests in CI.

### P4: ADR 0001 — Queryable Layer Scope (Week 9, 2-3 days)

**Goal**: ADR written, reviewed, decided before P3.

### P3: GOA-ON Export + Pre-Flight Validation + Manual Regression (Weeks 10-11)

**Goal**: Pre-flight CLI/GUI works; GOA-ON export valid; April 2026 dataset →
22/16/0.

### v1.0.0: Tagged Release v1.0.0 (Week 12)

**Goal**: All Definition of Done criteria met.

---

## Key Decisions (from `decisions.md`)

1. **ADR 0001**: Option B — File Manifest (not DuckDB)
2. **PyCO2SYS**: v1 Stable (`opt_k_carbonic=10`, `opt_pH_scale=1`)
3. **Dataset**: Local path available for manual regression
4. **GPG Signing**: Deferred to post-v1.0.0 (unsigned tags)
5. **PyPI Publishing**: Manual for v1.0.0 (org not ready)
6. **CI**: GitHub Actions matrix (Ubuntu/macOS/Windows Git Bash), Python 3.11,
   Pixi only
7. **Architecture**: Single engine, three doors (ADR-0010)
8. **Data Standard**: Frontiers 2021 (ADR-0009)
9. **Invariant Test**: In CI on every PR (ADR-0003)
10. **Config Gate**: `compatible_pipeline_version` enforced at runtime

---

## Risk Mitigation

| Risk                                                        | Mitigation                                                         |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| Prototype migration reveals hidden dependencies             | P-1 verification runs full test suite + pipeline before P0         |
| Invariant test catches latent bugs requiring schema changes | P0 invariant test fails fast; schema changes in P2                 |
| Cross-platform CI flakiness on Windows                      | Git Bash documented; cache pixi env; `OA_KEEP_PYTEST_RUNS=1` debug |
| Unpublished dataset regression fails                        | Document exact manual process; release gate, not CI gate           |
| Config-driven aliases break existing configs                | Config compatibility gate (P1) enforces version pinning            |

---

## Success Metrics (v1.0.0)

| Metric                      | Target                                                   |
| --------------------------- | -------------------------------------------------------- |
| Onboarding time (Ruu)       | < 1 hour                                                 |
| Cross-platform CI pass rate | 100% on every PR                                         |
| Invariant test coverage     | Catches all column mutation classes                      |
| Schema compliance           | 0 undocumented Frontiers 2021 deviations                 |
| Config-driven adoption      | Fatou maps archive via `schema_aliases.yaml` only        |
| Release citability          | `pip install oa-pipeline==1.0.0` + tagged release + PyPI |
| Reproducibility             | `oa-pipeline verify-bundle` validates any archived run   |
| Kofi workflow               | Excel validation via GUI in <5s, no terminal             |
| GOA-ON export               | Portal sandbox ingestion passes                          |
| Manual regression           | April 2026 dataset → 22/16/0 before every release        |

---

## Out of Scope (Non-Goals)

- Reimplement PyCO2SYS chemistry (wrap, don't rewrite)
- Queryable time-series database in v1.0 (ADR 0001 Option B chosen)
- Web-based UI (Tkinter GUI meets Kofi's need)
- Real-time/streaming processing (batch <100 bottles)
- Multi-tenant SaaS (regional network deployment model)
- Automated CRM certification lookup (human verification required)
- pH scale conversion engine (records scale, audits consistency)

---

## Approval

- [x] P-1 design approved
- [x] P0 design approved
- [x] P1 design approved
- [x] P2 design approved
- [x] P4 design approved
- [x] P3 design approved
- [x] v1.0.0 design approved
