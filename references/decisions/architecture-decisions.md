# ROAP — Architecture Decision Records (ADRs)

**Format:** Based on Michael Nygard's ADR template  
**Statuses:** Proposed | Accepted | Superseded | Rejected

---

## ADR Index

| ID | Title | Status | Date | Deciders |
|----|-------|--------|------|----------|
| 0001 | Queryable Time-Series Layer Scope | Proposed | — | [Lead], [Prof. Adjei] |
| 0002 | Cross-Platform CI Before GOA-ON Export | Proposed | 2026-09-29 | [Lead] |
| 0003 | Invariant Test in CI (Not Post-CI) | Accepted | 2026-09-29 | [Lead] |
| 0004 | Config-Driven Schema Aliases | Proposed | — | [Lead], [Fatou input] |
| 0005 | Excel Round-Trip: Pandas Read/Write Only | Proposed | — | [Lead] |
| 0006 | CRM/Std Detection by Tag Prefix Only | Accepted | 2026-09-29 | [Lead], [Maurice] |
| 0007 | Property-Based Testing for Schema/Normalization | Proposed | — | [Lead] |
| 0008 | Real Dataset as Manual Regression Gate | Accepted | 2026-09-29 | [Lead] |
| 0009 | Frontiers 2021 as Default Schema Standard | Accepted | 2026-09-29 | [Lead] |
| 0010 | Single Engine, Three Doors (CLI/GUI/Notebook) | Accepted | 2026-09-29 | [Lead] |

---

## ADR 0001: Queryable Time-Series Layer Scope

**Status:** Proposed  
**Date:** —  
**Deciders:** [Lead], [Prof. Adjei]

### Context
Nadia (US-23) needs quarterly runs appended to continuous station time series. Ama (US-24) needs to retrieve subsets by station/depth/date. Current pipeline writes files only.

### Options
| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. In Scope (DuckDB) | `oa-pipeline ingest RUN_DIR` → DB; `oa-pipeline query --station --depth --date` | Fast queries, SQL interface, Parquet-native, no server | New dependency, schema migration, maintenance |
| B. Out of Scope (Files) | `archive/<cruise>/analysis_ready.csv` + `archive/manifest.csv`; document `pd.read_csv`/`duckdb` workflow | Simple, no new deps, stateless pipeline | Manual assembly, slower queries, no single source of truth |

### Decision Criteria
- Team capacity for v1.0
- Nadia's reporting timeline
- Fatou's reuse needs
- Long-term maintenance burden

### Outcome
**Pending** — Must decide before P3 export design (gate).

---

## ADR 0002: Cross-Platform CI Before GOA-ON Export

**Status:** Proposed  
**Date:** 2026-09-29  
**Deciders:** [Lead]

### Context
Two capabilities the software lacks entirely: cross-platform (US-19) and GOA-ON export (US-20). No priority marked in stories.

### Decision
**Cross-platform CI first (P0)**, then GOA-ON export (P3 after P4).

### Rationale
- CI requires cross-platform anyway (Ubuntu/macOS/Windows runners)
- GOA-ON export design depends on P4 queryable layer decision
- Cross-platform enables Ruu (trainee) and Nadia (quarterly on any machine)
- Unblocks all other work

---

## ADR 0003: Invariant Test in CI (Not Post-CI)

**Status:** Accepted  
**Date:** 2026-09-29  
**Deciders:** [Lead] (per Council review)

### Context
Lat/lon overwrite bug survived 221 tests because it touched an untargeted column. CI green ≠ data integrity.

### Decision
Invariant test (`tests/test_invariants.py`) runs **in CI on every PR**, not as post-CI check.

### Implementation
- For each stage: snapshot input columns → run stage → assert columns not in stage's declared target set are byte-identical
- Fails CI if any stage mutates untargeted columns
- Catches lat/lon bug class automatically

### Consequence
P0 CI and invariant test are merged — neither is meaningful without the other.

---

## ADR 0004: Config-Driven Schema Aliases

**Status:** Proposed  
**Date:** —  
**Deciders:** [Lead], [Fatou input]

### Context
Fatou (US-01) has 3 years of data in her own column layout. Must map to canonical schema without renaming.

### Decision
Add `configs/schema_aliases.yaml` that extends/overrides `DEFAULT_CONFIG["canonical_candidates"]`.

### Example
```yaml
canonical_candidates:
  ta_umol_kg:
    - "ALKALINITY_UMOL_KG"    # Fatou's column
    - "TA_UMOL_KG"            # Partner's column
  ph_observed:
    - "PH_SPECTRO"
    - "PH_LAB"
```

### Consequence
No code changes for new partners. Aliases resolved at ingest (Stage 1A).

---

## ADR 0005: Excel Round-Trip: Pandas Read/Write Only

**Status:** Proposed  
**Date:** —  
**Deciders:** [Lead]

### Context
Openpyxl round-trip blanks formula-driven columns (DIC, etc.). Current fix in `stamp_carbonate_provenance.py`: read via pandas, write static values.

### Decision
**Never use openpyxl for read-modify-write on formula-bearing workbooks.**  
Add `oa_pipeline.io.read_excel_safe()` / `write_excel_safe()` using pandas + openpyxl engine with `data_only=True`.

### Consequence
- Formula columns preserved as static values
- Kofi's bench sheets with formulas work correctly
- All Excel I/O in pipeline uses safe functions

---

## ADR 0006: CRM/Std Detection by Tag Prefix Only

**Status:** Accepted  
**Date:** 2026-09-29  
**Deciders:** [Lead], [Maurice]

### Context
Single most-repeated warning in pipeline docs: CRM and pH-standard rows identified by `sample_tag` prefix (`RM<batch>_<n>`, `tris_*`), NOT by `sample_type` column.

### Decision
**Tag prefix is primary detection mechanism.** `sample_type` column is secondary cross-check only (opt-in via `ALLOW_CRM_FLAG_COL`).

### Enforcement
- Stage 02 validates: every `sample_type=crm` row MUST have `sample_tag` starting with `RM`
- Every `sample_type=std` row MUST have `sample_tag` starting with `tris`/`amp`/`bis`
- Fail fast with clear error on mismatch

---

## ADR 0007: Property-Based Testing for Schema/Normalization

**Status:** Proposed  
**Date:** —  
**Deciders:** [Lead]

### Context
Example-based tests (221) missed latent bug class. Pragmatist: testing philosophy must shift to property-based/invariant.

### Decision
Add `hypothesis` to test deps. Write property tests for:
- Alias resolution idempotency
- Unit normalization round-trip
- Schema application preserves untargeted columns
- CRM/std tag detection invariants

### Consequence
- Runs in CI alongside example-based tests
- Catches edge cases examples miss
- Documents expected behavior as executable properties

---

## ADR 0008: Real Dataset as Manual Regression Gate

**Status:** Accepted  
**Date:** 2026-09-29  
**Deciders:** [Lead]

### Context
April 2026 dataset (38 samples → 22/16/0) is unpublished. Only integration test that matters. Not in CI.

### Decision
**Manual regression gate before every release:**
1. Run pipeline on April 2026 dataset (shared folder)
2. Verify: 22 PASS, 16 REVIEW, 0 FAIL
3. Document in `docs/manual-regression.md`
4. **Not in CI** — unpublished data

### Consequence
Release checklist includes manual regression step.

---

## ADR 0009: Frontiers 2021 as Default Schema Standard

**Status:** Accepted  
**Date:** 2026-09-29  
**Deciders:** [Lead]

### Context
Field is fragmented because Frontiers 2021 adoption is voluntary. ROAP enforces by default.

### Decision
- Column names = Frontiers clarified headers (not WOCE abbreviations)
- QC flags = unified 0-9 scale (not legacy schemes)
- Missing values = `-999` (not NaN/empty)
- Provenance metadata = required on every derived value

### Consequence
Schema audit (P2.1) maps current `canonical_candidates` → Frontiers standard. Deviations documented with rationale.

---

## ADR 0010: Single Engine, Three Doors

**Status:** Accepted  
**Date:** 2026-09-29  
**Deciders:** [Lead]

### Context
CLI, GUI, Notebook must call same core pipeline. If they compute differently, reproducibility bug reintroduced.

### Decision
- Core pipeline = pure Python modules in `src/oa_pipeline/`
- CLI = `src/oa_pipeline/cli.py` (typer/click) → calls core
- GUI = `tools/oa_pipeline_app.py` → calls same `run_pipeline.sh` → core
- Notebooks = import core modules, orchestrate stages

### Consequence
Single source of truth for all computation. Interface differences only in orchestration/presentation.

---

## Decision Log

| Date | ADR | Decision | Notes |
|------|-----|----------|-------|
| 2026-09-29 | 0003 | Accepted | Per Council review |
| 2026-09-29 | 0006 | Accepted | Per maintainer warning |
| 2026-09-29 | 0008 | Accepted | Per data handling rules |
| 2026-09-29 | 0009 | Accepted | Per domain knowledge |
| 2026-09-29 | 0010 | Accepted | Per architecture principle |

*Update as decisions are made. Each new ADR gets next number.*