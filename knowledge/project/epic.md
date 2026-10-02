---
type: Requirement
title: ROAP v1.0.0 Epic Delivery Plan
description: "Revised priority matrix with P-1 migration blocking all work, P0 CI+invariant test, P1 packaging, P2 schema/provenance, P4 ADR gate, P3 export/validation"
tags: [epic, priority, council-review, migration, ci, packaging, schema, adr, export]
generated: { by: agent/cli, at: "2026-10-02T05:45:31Z" }
status: stable
okf_version: "0.2"
---

# ROAP — Reproducible Ocean Acidification Pipeline
## Epic: From Research Prototype to Production Platform

**Status:** Planning (revised after council review)
**Lead:** TBD
**Target:** v1.0.0 (tagged release, cross-platform, CI/CD, citable in methods)

---

## Critical Finding from Council Review

> **This repository (`roap`) is a project template. The actual `oa_pipeline` v0.2.0 codebase lives in `references/prototype/oa_pipeline/` (git submodule) with its own `.git/`, `.venv_run/`, 221 tests, 8 notebooks, and `src/oa_pipeline/` modules. Zero P0-P4 work can begin until the prototype is migrated into this repo.**

---

## Revised Priority Matrix

| Priority | Theme | Personas Served | Rationale |
|----------|-------|-----------------|-----------|
| **P-1** | **Prototype Migration** (BLOCKING) | All | Prerequisite: code must exist in this repo before CI, packaging, or schema work |
| **P0** | Cross-Platform CI + Invariant Test + Entry Point | Ruu, Kofi, Nadia, Ama | CI is meaningless without invariant test (lat/lon bug survived 221 tests) |
| **P1** | Packaging, Releases, Version Pinning, Run Bundles | Fatou, Prof. Adjei, Nadia | Citable releases + config compatibility gate + reproducible run records |
| **P2** | Schema/Provenance/CRM/Excel Fixes + Property-Based Testing | Ama, Fatou, Prof. Adjei, Kofi | Core reproducibility + fix structural bugs missing from original plan |
| **P4** | **ADR: Queryable Time-Series Layer Scope** (GATE for P3) | Nadia, Ama | Must decide before designing P3 export (DB vs file changes everything) |
| **P3** | International Export + Pre-Flight Validation | Nadia, Kofi | GOA-ON export + no-code validation for Kofi (after P4 decision) |

---

## P-1: Prototype Migration (BLOCKING — 2-3 days)

### Problem
The `roap` repo is a template. The pipeline code, tests, notebooks, configs, and example data live in `references/prototype/oa_pipeline/` (git submodule). Nothing in P0-P4 works until this code is here.

### Action Items
- [ ] **P-1.1** Copy `references/prototype/oa_pipeline/src/oa_pipeline/` → `src/oa_pipeline/`
- [ ] **P-1.2** Copy `references/prototype/oa_pipeline/tests/` → `tests/` (all 221 tests)
- [ ] **P-1.3** Copy `references/prototype/oa_pipeline/examples/` → `examples/` (synthetic data + `make_example_data.py`)
- [ ] **P-1.4** Copy `references/prototype/oa_pipeline/configs/` → `configs/`
- [ ] **P-1.5** Merge `oa_pipeline/pyproject.toml` dependencies into this repo:
  - Create `pyproject.toml` for the `oa_pipeline` package (src-layout, `src/oa_pipeline`)
  - Keep `pixi.toml` for dev environment (pre-commit, gh-cli, onboard)
  - Align Python version (3.11), deps (pandas, numpy, openpyxl, matplotlib, pyyaml, pyarrow, tabulate, papermill, pytest, ipykernel, ipython)
- [ ] **P-1.6** Extract notebook orchestration → CLI entry points:
  - `run_pipeline.sh` already exists — verify it works with new structure
  - Add `src/oa_pipeline/cli.py` with `typer`/`click` for `oa-pipeline validate`, `oa-pipeline export`, `oa-pipeline verify-bundle`
  - Notebooks 02-08 become callable module functions (already mostly are in `src/oa_pipeline/stage*.py`)
- [ ] **P-1.7** Add `.gitignore` entry for Unpublished data
- [ ] **P-1.8** Verify migration: `pixi install` → `pytest -q` → 221 pass → `./run_pipeline.sh examples/example_data.xlsx outputs/test` → expected 4 FAIL verdicts on injected rows

### Success Criteria
- [ ] `src/oa_pipeline/` exists with all 12 modules (`__init__.py`, `common.py`, `schema.py`, `qc_ta_ph.py`, `stage1b.py`, `stage2.py`, `stage3.py`, `stage4.py`, `policy.py`, `inspect.py`, `carbonate_calc.py`, `duplicate_precision.py`)
- [ ] `tests/` has 221+ passing tests (`pytest -q` → `221 passed`)
- [ ] `examples/example_data.xlsx` exists (or regenerates via `make_example_data.py`)
- [ ] `configs/` has all YAML configs including `07_stage3.yaml` with `ph_diag_harmonize_temperature: true`
- [ ] `./run_pipeline.sh` works end-to-end on synthetic data
- [ ] **Unpublished data is NOT in git** (verified by `git status`)

### Good Practices
- Do **not** commit `local/` to this repo's history — it's reference material only
- Preserve `oa_pipeline`'s git history in the submodule for reference; this repo starts fresh
- Run migration verification **before** any P0 work

---

## P0: Cross-Platform CI + Invariant Test + Single Entry Point

### Problem
- Pipeline only ever run on Windows + Git Bash (never macOS/Linux)
- 4 READMEs + loose scripts at root — no clear entry point
- No CI — tests run manually, nothing verifies PRs
- **Invariant test missing** — lat/lon overwrite bug survived 221 tests because it touched an untargeted column. CI green ≠ data integrity.
- Ruu needs clean laptop → successful run in <1 hour
- Kofi needs no-terminal interface

### Action Items
- [ ] **P0.1 GitHub Actions workflow** (`.github/workflows/ci.yml`)
  - Matrix: Ubuntu-latest, macOS-latest, Windows-latest
  - Python 3.11 (match pixi.toml)
  - Steps: `pixi install` → `pixi run pre-commit-all` → `pytest -q` → `./run_pipeline.sh examples/example_data.xlsx outputs/ci_test`
  - Artifact upload: `analysis_ready.csv`, manifests, reports
  - **Invariant test runs in CI** (see P0.3) — CI fails if any stage mutates untargeted columns
- [ ] **P0.2 Consolidate entry points**
  - Single `README.md` at repo root with: quickstart (3 paths: CLI, GUI, notebook), prerequisites, troubleshooting
  - Archive `APP_README.md`, `ALKA_README.md`, `SETUP_GUIDE.md` → `docs/legacy/`
  - Move loose scripts (`oa_pipeline_app.py`, `oa_pipeline_app_core.py`, `stamp_carbonate_provenance.py`, `run_pipeline.sh`) → `tools/` with clear purpose in README
- [ ] **P0.3 Invariant test: untouched columns unchanged** (HIGHEST LEVERAGE TEST)
  - New file: `tests/test_invariants.py`
  - For each stage (1A, 1B, 2, 3, 4): snapshot input columns → run stage → assert columns not in stage's declared target set are byte-identical
  - Catches the lat/lon overwrite bug automatically
  - Run in CI on every PR
- [ ] **P0.4 Validate GUI launcher works cross-platform**
  - Test `python tools/oa_pipeline_app.py` on macOS/Linux (Tkinter bundled with python.org installer)
  - Document any platform-specific quirks
- [ ] **P0.5 Add `pixi run test` and `pixi run pipeline` tasks** to pixi.toml for one-command runs
- [ ] **P0.6 Document Git Bash requirement on Windows** clearly (already in README, keep prominent)

### Success Criteria
- [ ] CI passes on **all three platforms** (Ubuntu, macOS, Windows) on every push/PR
- [ ] **Invariant test fails** if any stage mutates a column it doesn't target (lat/lon, or any other)
- [ ] Fresh clone → `pixi install` → `pixi run pipeline examples/example_data.xlsx outputs/test` → produces `analysis_ready.csv` with expected verdict counts (4 FAIL injected rows) in <10 min
- [ ] Single `README.md` is the **only** file a newcomer needs to read to run the pipeline
- [ ] `pixi run test` executes full test suite (221+ tests + invariant test) and passes
- [ ] GUI launcher (`python tools/oa_pipeline_app.py`) opens and runs on all three platforms

### Good Practices
- Cache pixi environment in CI (`pixi cache` or `actions/cache`)
- Use `pytest --tb=short` for cleaner CI logs
- Add `OA_KEEP_PYTEST_RUNS=1` debug mode to CI for failed runs
- Pin GitHub Actions versions (e.g., `actions/checkout@v4`)

---

## P1: Packaging, Releases, Version Pinning, Run Bundles

### Problem
- `pyproject.toml` for `oa_pipeline` package doesn't exist in this repo yet
- **No tags, no releases, no distribution** — Fatou needs citable tagged release for methods
- Ama needs pipeline to **refuse to run** on incompatible config/schema version
- Nadia needs quarterly regeneration by colleague who never ran it before

### Action Items
- [ ] **P1.1 Semantic versioning + GitHub Releases**
  - Tag `v0.2.0` for migrated state (match original `pyproject.toml` version)
  - Establish release process: `CHANGELOG.md` + `git tag -s` + `gh release create` + PyPI publish
  - Document release checklist in `RELEASE.md`
- [ ] **P1.2 Config compatibility gate** (verify existing implementation)
  - Verify `compatible_pipeline_version` in config YAMLs is enforced at runtime
  - Add test: config with older version pin → pipeline exits with clear error
- [ ] **P1.3 Archived run bundles** (for Prof. Adjei's sign-off)
  - Standardize `outputs/<run>/` + `runs/<timestamp>/` as immutable run record
  - Add `run_bundle_manifest.json` linking: input file SHA256, config SHA256s, code version (git sha), `oa_pipeline` version, timestamp, output file hashes
  - CLI command: `oa-pipeline verify-bundle <run_dir>` → validates integrity
- [ ] **P1.4 Add `__version__` to `oa_pipeline/__init__.py`** sourced from `pyproject.toml` (use `importlib.metadata`)
- [ ] **P1.5 Pin dependencies in `pixi.lock`** (already done) + document upgrade process

### Success Criteria
- [ ] `git tag v0.2.0` exists; `gh release create v0.2.0` published with assets
- [ ] `pip install oa-pipeline==0.2.0` works (PyPI) or `pip install git+https://github.com/reez-png/oa_pipeline@v0.2.0`
- [ ] Running pipeline with stale config (`compatible_pipeline_version: ">=0.1.0"`) against v0.2.0 code **fails fast with actionable error**
- [ ] Every run produces `run_bundle_manifest.json` with: input SHA256, config SHA256s, git commit, `oa_pipeline` version, timestamp, output file hashes
- [ ] `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format

### Good Practices
- Automate release with `release` skill (already in `.agents/skills/release/`)
- Sign tags with GPG if possible
- Include `SBOM` (Software Bill of Materials) in release artifacts
- Document dependency upgrade policy (e.g., `pixi update` + test matrix)

---

## P2: Schema/Provenance/CRM/Excel Fixes + Property-Based Testing

### Problem
- Schema uses project-specific column names; should adopt **Frontiers 2021** standard (GOA-ON compatibility)
- **Provenance columns required but invariant test (P0.3) catches mutation — now need completeness check**
- **Excel round-trip bug** — openpyxl blanks formula-driven columns (structural risk, affects Kofi's input)
- **CRM/std detection by `sample_tag` prefix** — single most-repeated warning, not validated in tests
- Fatou needs config-driven column mapping (not manual renaming)
- Testing philosophy is example-based; must add property-based/invariant testing

### Action Items
- [ ] **P2.1 Audit schema against Frontiers 2021** (`.agents/skills/data-standard/references/qc-flags-and-columns.md`)
  - Map `oa_pipeline.schema.DEFAULT_CONFIG["canonical_candidates"]` → standard column names
  - Add missing standard fields (QC flags 0-9 per variable, `-999` missing sentinel)
  - Document deviations with rationale
- [ ] **P2.2 Config-driven alias override**
  - Allow `configs/schema_aliases.yaml` to extend/override `canonical_candidates`
  - Fatou maps her columns via config, not code changes
- [ ] **P2.3 Provenance completeness check**
  - Stage 4 requires `carbonate_solver`, `carbon_input_pair_used`, `carbonate_constants`, `carbonate_ph_scale`, `carbonate_output_temperature`
  - Add test: every row with derived carbonate values has non-empty provenance columns
  - Fail fast if provenance missing (current behavior: FAIL all rows — correct)
- [ ] **P2.4 QC flag fields (0-9) on every numeric measurement**
  - Add `*_qc_flag` columns per Frontiers standard
  - Default = 2 (acceptable) or 9 (missing) per standard
- [ ] **P2.5 Excel round-trip fix** (structural, affects Kofi's workflow)
  - Current fix: read via pandas, write static values (in `stamp_carbonate_provenance.py`)
  - **Root cause**: any openpyxl round-trip blanks formula columns
  - Solution: never use openpyxl for read-modify-write on formula-bearing workbooks
  - Add `oa_pipeline.io.read_excel_safe()` / `write_excel_safe()` that use pandas + openpyxl engine with `data_only=True` for reading
  - Test: workbook with formula column → read → write → formula column preserved as static value
- [ ] **P2.6 CRM/std tag validation** (prevents silent corruption)
  - Add validation in Stage 02: every row with `sample_type`=`crm` MUST have `sample_tag` starting with `RM` (configurable prefix)
  - Every row with `sample_type`=`std` MUST have `sample_tag` starting with `tris`/`amp`/`bis` (configurable)
  - Fail fast with clear error if mismatch — this is the #1 silent corruption vector
- [ ] **P2.7 Property-based testing foundation**
  - Add `hypothesis` to test dependencies
  - Write property tests for: alias resolution (idempotent), unit normalization (round-trip), schema application (preserves untargeted columns)
  - Run in CI alongside example-based tests

### Success Criteria
- [ ] `schema.py` canonical names match Frontiers 2021 clarified headers (or documented deviation)
- [ ] Fatou can run her 3-year archive by adding only a `schema_aliases.yaml` config — no column renaming
- [ ] **Invariant test (P0.3) catches column mutation** in any stage
- [ ] Every numeric column in output has corresponding `*_qc_flag` (0-9 scale)
- [ ] Missing values export as `-999` (not `NaN`, not empty string)
- [ ] Provenance columns present and non-empty on all sample rows with derived carbonate values
- [ ] **Excel formula columns survive read-write round-trip** (tested)
- [ ] **CRM/std tag mismatch fails fast** with actionable error (tested)
- [ ] Property-based tests run in CI and pass

### Good Practices
- Generate schema documentation from code (single source of truth)
- Add schema version field to all outputs
- Use `pydantic` models for schema validation (consider for v1.1)

---

## P4: ADR — Queryable Time-Series Layer Scope (GATE for P3)

### Problem
- Nadia: quarterly runs appended to continuous station time series under consistent QC
- Ama: retrieve consistent subset by station, depth, date range
- Current software: file-writing pipeline, no queryable store
- **P3 export design depends entirely on this decision** — GOA-ON export structure differs between DB-backed and file-based approaches

### Action Items
- [ ] **P4.1 Write ADR** (`docs/adr/0001-queryable-layer-scope.md`)
  - Options: (A) In scope: DuckDB/SQLite layer with SQLAlchemy; (B) Out of scope: file-based manifest index
  - Criteria: team capacity, Nadia's reporting timeline, Fatou's reuse needs, maintenance burden
  - Decision maker: [Lead] + [PI/Prof. Adjei input]
- [ ] **P4.2 If IN SCOPE (Option A):**
  - [ ] Schema for `stations`, `cruises`, `samples`, `measurements` tables
  - [ ] `oa-pipeline ingest RUN_DIR` → appends to DB with run metadata
  - [ ] `oa-pipeline query --station J2 --depth-range 0-50 --date-range 2024-01-01:2024-12-31`
  - [ ] Index on (station_id, sample_date, depth_m) for fast retrieval
- [ ] **P4.3 If OUT OF SCOPE (Option B):**
  - [ ] Standardized file layout: `archive/<cruise_id>/analysis_ready.csv` + `archive/manifest.csv`
  - [ ] `oa-pipeline assemble-manifest` → builds `manifest.csv` from `outputs/` tree
  - [ ] Document how to query with `pandas`/`duckdb` on file collection

### Success Criteria
- [ ] ADR written, reviewed, and **decided** before P3 work starts
- [ ] If in scope: quarterly ingest + query works end-to-end on synthetic multi-cruise data
- [ ] If out of scope: `manifest.csv` enables `pd.read_csv` + filter workflow for Ama/Nadia

### Good Practices
- Use DuckDB for analytical queries (fast, no server, reads Parquet directly)
- Keep pipeline stateless — DB is derived artifact, not source of truth
- Version the DB schema alongside pipeline version

---

## P3: International Export + Pre-Flight Validation (AFTER P4 Decision)

### Problem
- Nadia needs export in **international OA reporting stream structure** (GOA-ON data portal compatible)
- Kofi needs **immediate validation** of his bench sheet before full pipeline run
- No standalone validation step exists
- **Export format depends on P4 decision** (DB-friendly vs file-friendly)

### Action Items
- [ ] **P3.1 Pre-flight validation CLI command**
  - `oa-pipeline validate INPUT_XLSX --config-dir configs`
  - Checks: required columns present (via aliases), dtypes plausible, CRM/std tags correct, `CRM_BATCH` in certified values
  - Output: human-readable report + machine-readable JSON (exit code 0 = clean, 1 = issues)
  - Runs in <5 seconds on 50-row file
- [ ] **P3.2 Kofi's Excel validation UX (no terminal)**
  - GUI launcher: "Validate Only" button → runs pre-flight → shows pass/fail with row numbers
  - CLI: `oa-pipeline validate --gui` opens simple Tkinter window with results
- [ ] **P3.3 GOA-ON / Frontiers 2021 export format**
  - If P4 = DB: `oa-pipeline export-analysis-ready --db-path <db> --format goa-on`
  - If P4 = files: `oa-pipeline export-analysis-ready INPUT_CSV --format goa-on`
  - Output: standardized column names, QC flags, provenance metadata sheet, `-999` missing values
  - Validate against GOA-ON portal template (if available)
- [ ] **P3.4 Real dataset as manual regression gate**
  - Document process: run pipeline on Unpublished dataset (shared folder, not in repo)
  - Verify: 22 PASS, 16 REVIEW, 0 FAIL
  - Document as `docs/manual-regression.md` with steps and expected outputs
  - **Not in CI** (unpublished data) — but required before every release

### Success Criteria
- [ ] `oa-pipeline validate` catches: missing required columns, wrong dtypes, unknown CRM batch, mis-tagged CRM/std rows
- [ ] Validation runs on raw Excel **without** executing full pipeline
- [ ] Exported dataset passes GOA-ON portal ingestion (test with portal sandbox if available)
- [ ] Kofi can validate his bench sheet via GUI without terminal
- [ ] Export includes all provenance metadata needed for reproducibility
- [ ] Manual regression on Unpublished dataset produces 22/16/0 before every release

### Good Practices
- Reuse schema validation logic for both pre-flight and Stage 1A
- Export as both CSV + Parquet (Parquet preserves dtypes better)
- Include `export_manifest.json` with schema version, export timestamp, code version

---

## Cross-Cutting Good Practices (Apply to All Issues)

| Practice | Where to Apply |
|----------|----------------|
| **Conventional commits** (`feat:`, `fix:`, `test:`, `docs:`, `chore:`) | All commits |
| **Pre-commit hooks** (ruff, black, mypy, pytest) | Already in `pixi.toml` — enforce in CI |
| **Type hints on all public functions** | `src/oa_pipeline/` modules |
| **Docstrings** (NumPy style) on all public functions/classes | `src/oa_pipeline/` modules |
| **Test-first for new features** | All new code (TDD workflow) |
| **ADR (Architecture Decision Records)** for significant choices | `docs/adr/` |
| **Update `CARBONATE_CHEMISTRY_KNOWLEDGE.md` first**, then propagate to skills | Any domain change |
| **Never commit Unpublished data** | Enforced by `.gitignore` + pre-commit check |
| **Property-based testing** (hypothesis) for schema/normalization | `tests/test_properties.py` |

---

## Suggested Issue Breakdown (for GitHub)

| Epic | Issue Title | Priority | Labels |
|------|-------------|----------|--------|
| P-1 | Migrate `oa_pipeline` prototype into this repo (src/, tests/, examples/, configs/) | P-1 | `migration`, `blocking` |
| P-1 | Create `pyproject.toml` for `oa_pipeline` package (src-layout) | P-1 | `packaging`, `blocking` |
| P-1 | Extract notebook orchestration → CLI entry points (`oa-pipeline` command) | P-1 | `cli`, `refactor` |
| P-1 | Verify migration: 221 tests pass + pipeline runs on synthetic data | P-1 | `test`, `verification` |
| P0 | GitHub Actions CI matrix (Ubuntu/macOS/Windows) + invariant test | P0 | `ci`, `cross-platform`, `invariant-test` |
| P0 | Consolidate READMEs → single entry point | P0 | `docs`, `onboarding` |
| P0 | Move loose scripts to `tools/` + update imports | P0 | `refactor`, `structure` |
| P0 | Validate GUI launcher on macOS/Linux | P0 | `gui`, `cross-platform` |
| P0 | Invariant test: untouched columns unchanged per stage | P0 | `test`, `regression`, `critical` |
| P1 | Tag v0.2.0 + GitHub Release + PyPI publish | P1 | `release`, `packaging` |
| P1 | Config compatibility gate test | P1 | `test`, `config` |
| P1 | Run bundle manifest + verify CLI | P1 | `provenance`, `cli` |
| P2 | Schema audit vs Frontiers 2021 | P2 | `schema`, `data-standard` |
| P2 | Config-driven alias override (`schema_aliases.yaml`) | P2 | `schema`, `config` |
| P2 | QC flag fields (0-9) on all numeric outputs | P2 | `schema`, `data-standard` |
| P2 | Excel round-trip fix: safe read/write for formula columns | P2 | `bugfix`, `io`, `kofi` |
| P2 | CRM/std tag validation (fail fast on prefix mismatch) | P2 | `validation`, `critical`, `ama` |
| P2 | Property-based testing foundation (hypothesis) | P2 | `test`, `property-based` |
| P4 | ADR: Queryable time-series layer scope (gate for P3) | P4 | `architecture`, `decision`, `gate` |
| P3 | Pre-flight validation CLI + GUI (for Kofi) | P3 | `cli`, `gui`, `validation`, `kofi` |
| P3 | GOA-ON export format (design per P4 decision) | P3 | `export`, `interoperability`, `nadia` |
| P3 | Manual regression process for Unpublished dataset | P3 | `test`, `regression`, `manual` |

---

## Definition of Done for v1.0.0

- [ ] **P-1 complete**: Prototype migrated, 221 tests pass, pipeline runs on synthetic data
- [ ] **P0 complete**: CI passes on Linux, macOS, Windows **with invariant test**; single `README.md` enables clean-laptop → successful run in <1 hour
- [ ] **P1 complete**: Tagged release `v1.0.0` on GitHub (and PyPI); config compatibility gate works; run bundles produced
- [ ] **P2 complete**: Schema aligned with Frontiers 2021; Excel round-trip fixed; CRM/std tag validation fails fast; property-based tests in CI
- [ ] **P4 complete**: ADR decided and documented
- [ ] **P3 complete**: Pre-flight validation works for Kofi (CLI + GUI); GOA-ON export produces valid output; manual regression on Unpublished dataset produces 22/16/0
- [ ] All 221+ original tests + new tests (invariant, property-based, config gate, CRM validation, Excel round-trip) pass
- [ ] `CHANGELOG.md` complete
- [ ] No unpublished data in repo

---

## Notes for the Lead

1. **Start with P-1** — nothing else works until the code is in this repo. 2-3 days of unglamorous copying/merging.
2. **P0 = CI + Invariant Test together** — the invariant test is what makes CI meaningful. Without it, you get green builds that corrupt data.
3. **P4 before P3** — the ADR on queryable layer is a hard gate. Don't design export until you know the target.
4. **Real dataset is a manual regression gate** — not in CI, but required before every release. Document the process.
5. **Kofi's workflow is bidirectional** — he produces Excel input (round-trip bug) AND consumes validation output. Fix both.
6. **Fatou's config-driven aliases** — key to regional adoption. Don't hardcode column names.
7. **Update `CARBONATE_CHEMISTRY_KNOWLEDGE.md` first** when domain decisions change, then propagate to skills.

---

*Revised after council review (Skeptic, Pragmatist, Critic). Original gaps identified: missing migration phase, invariant test not in P0, Excel round-trip bug omitted, CRM tag validation omitted, P4 gate for P3 missing, real dataset regression process missing, prototype-not-in-repo reality check.*

# Related Concepts
- [Carbonate Calculation Design](../prototype/carbonate-calc-design.md): Epic references carbonate calculation design for P2
- [Carbonate Methods & QC Validation](../prototype/carbonate-methods-note.md): Epic references carbonate methods for P2
- [Duplicate Precision Assessment](../prototype/duplicate-precision-methods.md): Epic references duplicate precision methods for P2
- [Notebook READMEs (Consolidated)](../prototype/notebook-readmes.md): Epic references notebook structure for P-1 migration
- [Prototype README](../prototype/prototype-readme.md): Epic references prototype README for P-1 migration
- [Requested Dataset (April 2026)](../prototype/requested-dataset.md): Epic references real dataset for manual regression gate P3.4
