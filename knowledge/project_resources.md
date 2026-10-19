# ROAP Project Resources — Context Transfer Document

**Purpose**: Enable a new human + agent team to pick up this project with full context.  
**Status as of 2026-10-18**: P-1, P0, P1 **COMPLETE**. P2, P4, P3, v1.0.0 **REMAINING**.

---

## 1. What Is ROAP?

**ROAP** = Reproducible Ocean Acidification Pipeline.  
Transforms the `oa_pipeline` v0.2.0 research prototype (8 Jupyter notebooks, 221 tests, Windows-only) into a **production-grade, cross-platform, citable platform** for ocean acidification carbonate chemistry QC and processing.

**North Star** (from `knowledge/project/overview.md`):
> Fresh clone → `pixi install` → `pixi run pipeline examples/example_data.xlsx outputs/test` → `analysis_ready.csv` with expected 4 non-PASS verdicts in **<10 min on Linux, macOS, and Windows**.

**Six Personas** (from `knowledge/personas/user-stories.md`):
| Persona | Role | Key Need |
|---------|------|----------|
| Ruu | Trainee | Clean laptop → successful run in <1 hour |
| Kofi | Technician | Excel-only, no terminal; produces input + consumes validation |
| Ama | Analyst | QC configurability, provenance, replicate checks |
| Fatou | Regional partner | Config-driven column mapping for 3-year archive |
| Nadia | Data manager | Quarterly unattended runs, GOA-ON export, time series |
| Prof. Adjei | PI | Sign-off summaries, archived run bundles, citable releases |

---

## 2. Prototype → ROAP: What Changed

| Aspect | Prototype (`oa_pipeline` v0.2.0) | ROAP (this repo) |
|--------|----------------------------------|------------------|
| **Package name** | `oa_pipeline` | `roap` |
| **Repo** | Git submodule at `references/prototype/oa_pipeline/` | `uw-ssec/roap` (this repo) |
| **CLI** | `run_pipeline.sh` only | `roap` (Typer) + `run_pipeline.sh` + GUI |
| **GUI** | `oa_pipeline_app.py` | `tools/roap_app.py` |
| **Tests** | 221 passing | 376 passing + 1 xfail (submodule has executed notebooks) |
| **CI** | None | GitHub Actions: Ubuntu/macOS/Windows (Git Bash) |
| **Invariant test** | Missing (lat/lon bug survived 221 tests) | `tests/test_invariants.py` runs in CI |
| **Config gate** | None | `compatible_pipeline_version` enforced at runtime |
| **Run bundles** | None | `run_bundle_manifest.json` + `roap verify-bundle` CLI |
| **Release** | None | `v0.2.0` tagged, CHANGELOG, manual PyPI publish ready |

---

## 3. Milestone Status (from GitHub + `knowledge/log.md`)

| Milestone | Status | Key Deliverables | GitHub Issues |
|-----------|--------|------------------|---------------|
| **P-1: Prototype Migration** | ✅ **COMPLETE** (merged PR #26) | `src/roap/` (12 modules), 376 tests, `pyproject.toml`, CLI stubs, notebooks migrated, pipeline runs E2E | #6⚠️, #7✅, #8✅, #9⚠️, #10✅ |
| **P0: Cross-Platform CI + Invariant + README** | ✅ **COMPLETE** (merged PR #28) | CI matrix (3 platforms), invariant test (7 tests), single `README.md`, legacy docs archived | #11✅, #12✅ |
| **P1: v0.2.0 Release + Config Gate + Run Bundles** | ✅ **COMPLETE** (merged PR #32, history restored) | Config gate on 7 configs, run bundle manifest + `roap verify-bundle`, CHANGELOG v0.2.0 | #13✅, #14✅ |
| **P2: Schema/Provenance/CRM/Excel + Property Tests** | 🔄 **IN PROGRESS** (4 open issues) | Frontiers 2021 audit, Excel round-trip fix, CRM/std tag validation, hypothesis tests | #15, #16, #17, #27 |
| **P4: ADR 0001 Decision** | 🔄 **OPEN** (1 issue) | ADR written, reviewed, **decided** (gate for P3) | #18 |
| **P3: GOA-ON Export + Pre-Flight + Manual Regression** | ⏳ **BLOCKED** on P4 (2 issues) | Pre-flight CLI/GUI, GOA-ON NetCDF export, April 2026 dataset → 22/16/0 | #19, #20 |
| **v1.0.0: Final Release** | ⏳ **BLOCKED** on P2/P3/P4 (1 issue) | All DoD met, v1.0.0 tag, PyPI, fresh-clone verification | #21 |

**Also open (no milestone):** #29, #30 — **FIXED** per log.md (CRM/TRIS preservation, CRM correction robustness)

---

## 4. Repository Structure (Key Paths)

```
roap/
├── src/roap/                    # Core pipeline (12 modules + alka GUI subpackage)
│   ├── __init__.py              # __version__ = "0.2.0"
│   ├── common.py                # I/O, config loading, config gate, CRM correction, bundle manifest
│   ├── schema.py                # Canonical schema, aliases, normalizers, export order
│   ├── qc_ta_ph.py              # CRM TA correction, pH standard correction, QC plots
│   ├── stage1b.py               # Best source coalescing, sample ready filtering
│   ├── stage2.py                # Duplicate detection, replicate harmonisation
│   ├── stage3.py                # Carbonate integrity: DIC sum, pH diagnostic, provenance
│   ├── stage4.py                # Final audit, PASS/REVIEW/FAIL verdicts
│   ├── policy.py                # RangePolicy, range configuration
│   ├── inspect.py               # Read-only output tree inspection
│   ├── carbonate_calc.py        # PyCO2SYS wrapper (opt_k_carbonic=10, opt_pH_scale=1)
│   ├── duplicate_precision.py   # Duplicate precision assessment
│   ├── cli.py                   # Typer CLI: validate, verify-bundle
│   ├── bundle.py                # Run bundle manifest generation + verification
│   └── alka/                    # GUI app (Tkinter)
├── tests/                       # 376 passing + 1 xfail
│   ├── test_invariants.py       # P0.3: untouched columns unchanged per stage (7 tests)
│   ├── test_config_gate.py      # P1.2: config compatibility gate
│   ├── test_cli_pipeline.py     # E2E pipeline test (27 rows: 16 PASS/3 FAIL/1 REVIEW/4 CRM_QC/3 STD_QC)
│   ├── test_crm_tris_preservation.py  # Issue #29 fix
│   ├── test_run_bundle.py       # Run bundle manifest
│   └── test_verify_bundle_cli.py # verify-bundle CLI
├── configs/                     # 7 YAML configs + reference files
│   ├── 02_ta_ph_qc.yaml
│   ├── 04_stage1a.yaml
│   ├── 05_stage1b.yaml
│   ├── 06_stage2.yaml
│   ├── 07_stage3.yaml           # ph_diag_harmonize_temperature: true
│   ├── 08_stage4.yaml
│   ├── cruise_grade_thresholds.yaml
│   ├── regional.yaml
│   └── crm_certified_values.yaml
├── examples/
│   ├── make_example_data.py     # Generates 27-row synthetic workbook (20 samples + 4 CRM + 3 TRIS)
│   └── example_data.xlsx
├── notebooks/                   # 11 Papermill notebooks (01-11), all imports updated to `roap.*`
├── tools/
│   ├── roap_app.py              # GUI launcher (Tkinter)
│   ├── roap_app_core.py         # GUI core logic
│   └── stamp_carbonate_provenance.py
├── run_pipeline.sh              # Main CLI entry point (bash, calls notebooks via papermill)
├── pyproject.toml               # Package definition (src-layout, `roap` v0.2.0, Typer CLI)
├── pixi.toml                    # Dev environment (pre-commit, gh-cli, pixi tasks)
├── pixi.lock                    # Pinned dependencies
├── .github/workflows/ci.yml     # CI: Ubuntu/macOS/Windows matrix, pixi cache, 10-min pre-commit timeout
├── CHANGELOG.md                 # Keep a Changelog format, v0.2.0 entry
├── README.md                    # Single entry point (quickstart: CLI, GUI, notebooks)
├── knowledge/                   # OKF v0.2 knowledge base (this context source)
│   ├── project/                 # epic.md, ai-prd.md, tech-stack.md, personas/
│   ├── prototype/               # pipeline-overview.md, prototype-readme.md, notebook-readmes.md
│   ├── decisions/               # migration-plan.md, engineering-decisions.md, adrs.md
│   ├── domain/                  # carbonate-chemistry.md, data-standards.md, pyco2sys-usage.md
│   └── log.md                   # Chronological work log (source of truth for status)
└── outputs/ runs/               # Generated (gitignored)
```

---

## 5. Key Technical Decisions (from `knowledge/decisions/engineering-decisions.md`)

| # | Decision | Status |
|---|----------|--------|
| 1 | **ADR-0001: NetCDF (GOA-ON template, CF conventions)** for queryable layer | ✅ Accepted (supersedes Option B) |
| 2 | PyCO2SYS v1 stable, constants: Lueker2000, Total pH scale | ✅ Implemented |
| 3 | Real dataset: local April 2026 cruise, manual regression gate (22/16/0) | ✅ Decided |
| 4 | GPG signing: **deferred** post-v1.0.0 | ⏳ Deferred |
| 5 | PyPI publishing: **manual** for v1.0.0 (org not ready) | ⏳ Manual |
| 6 | CI: GitHub Actions matrix, Python 3.11, Pixi only, pre-commit-all | ✅ Implemented |
| 7 | Architecture: Single engine (`src/roap/`), three doors (CLI/GUI/Notebook) | ✅ Implemented |
| 8 | Data standard: Frontiers 2021 (clarified names, 0-9 QC flags, -999 missing) | 🔄 P2 |
| 9 | Invariant test in CI (per-stage column mutation check) | ✅ Implemented |
| 10 | Config compatibility gate: `compatible_pipeline_version` in all 7 configs | ✅ Implemented |
| 11 | Package rename: `oa-pipeline` → `roap` (v0.2.0 retained) | ✅ Implemented |
| 12 | CLI framework: **Typer** (type-hint based, auto-completion) | ✅ Implemented |
| 13 | GUI rename: `oa_pipeline_app.py` → `roap_app.py` | ✅ Implemented |
| 14 | Notebook imports: all 11 updated to `roap.*` | ✅ Implemented |
| 15 | Git history: force-pushed rebuilt `main` with 44 individual commits (2026-10-18) | ✅ Done |
| 16 | CI: `setup-pixi@v0.11.2` (not v2), pre-commit cache + 10-min timeout | ✅ Fixed |
| 17 | CRM/TRIS rows preserved in Stage 1B with `row_classification` (Issue #29) | ✅ Fixed |
| 18 | `build_corrections_table()` fallback returns DataFrame (Issue #30) | ✅ Fixed |
| 19 | Run bundle manifest + `roap verify-bundle` CLI | ✅ Implemented |
| 20 | Config gate enabled on all 7 configs (`>=0.2.0`) | ✅ Enabled |
| 21 | E2E test expectations updated for 27 rows (CRM_QC + STD_QC) | ✅ Updated |
| 22 | Pre-commit false positives fixed (typos, secret fixture renamed) | ✅ Fixed |

---

## 6. Current Verified State (from `knowledge/log.md`, 2026-10-18)

```
pixi run pytest -q        → 376 passed, 1 xfail
Pipeline E2E (synthetic)  → 27 rows: 16 PASS / 3 FAIL / 1 REVIEW / 4 CRM_QC / 3 STD_QC (~34s)
Invariant tests           → 7/7 pass (lat/lon + provenance preservation)
CI                        → PASSING on Ubuntu/macOS/Windows
Pre-commit                → All hooks pass
```

**Known gaps carried forward:**
- `run_bundle_manifest.json` generation deferred to P1 (now done)
- ruff/black/mypy not wired into pre-commit — deferred to P0 (now done in CI)
- Carbonate calc on `example_data.xlsx` FAILs all 20 rows (fixture has no RM-corrected TA) — filed as P2 issue (#27)
- Submodule test `test_prototype_submodule_has_no_stored_outputs` fails by design (upstream submodule has executed notebooks with real data)

---

## 7. Remaining Work by Milestone

### P2: Schema/Provenance/CRM/Excel + Property Tests (4 issues)
| Issue | Title | Key Work |
|-------|-------|----------|
| #15 | Schema audit + aliases — Frontiers 2021 compliance | Map `canonical_candidates` → standard names; add `schema_aliases.yaml` config-driven override; document deviations |
| #16 | QC flags + provenance + Excel round-trip fix | Add `*_qc_flag` (0-9) on all numeric columns; export `-999` for missing; implement `read_excel_safe()`/`write_excel_safe()` using pandas (never openpyxl read-modify-write); test formula column preservation |
| #17 | CRM/std validation + property-based tests (hypothesis) | Validate `sample_tag` prefix: `RM*` for CRM, `tris/amp/bis*` for STD; fail fast with actionable error; add hypothesis tests for alias resolution (idempotent), unit normalization (round-trip), schema application (preserves untargeted columns) |
| #27 | Carbonate calc skip leaves DIC/species inconsistent | Fix strict DIC audit: when carbonate calc skipped, DIC stays fixture-authored while species come from PyCO2SYS → all rows FAIL; need consistent behavior |

### P4: ADR 0001 Decision (1 issue)
| Issue | Title | Key Work |
|-------|-------|----------|
| #18 | ADR 0001 — Queryable Layer Scope | **Already decided in engineering-decisions.md as Option C (NetCDF)**. Need to formalize ADR document at `docs/adr/0001-queryable-layer-scope.md`, get review sign-off. This unblocks P3 export design. |

### P3: GOA-ON Export + Pre-Flight + Manual Regression (2 issues) — **BLOCKED on P4**
| Issue | Title | Key Work |
|-------|-------|----------|
| #19 | Pre-flight validation — CLI `oa-pipeline validate` + GUI "Validate Only" | Standalone validation (<5s on 50 rows): required columns (via aliases), dtypes plausible, CRM/std tags correct, `CRM_BATCH` in certified values. Human-readable + JSON output. GUI button in `roap_app.py`. |
| #20 | GOA-ON export + manual regression (April 2026 dataset → 22/16/0) | NetCDF export following GOA-ON template with CF conventions (per ADR-0001). `oa-pipeline export-analysis-ready`. Document manual regression process in `docs/manual-regression.md` (not in CI). |

### v1.0.0: Final Release (1 issue)
| Issue | Title | Key Work |
|-------|-------|----------|
| #21 | Final release — all DoD, v1.0.0 tag, PyPI, fresh-clone verification | Tag `v1.0.0`, GitHub Release, manual PyPI publish, `CHANGELOG.md` complete, fresh clone verification on 3 platforms, all 221+ original + new tests pass. |

---

## 8. How to Run / Verify

```bash
# Setup (one-time)
pixi install

# Run tests
pixi run pytest -q

# Run pipeline on synthetic data
./run_pipeline.sh examples/example_data.xlsx outputs/test

# Output: outputs/test/oa_stage4_outputs/data/analysis_ready.csv
# Expected: 27 rows, 16 PASS, 3 FAIL, 1 REVIEW, 4 CRM_QC, 3 STD_QC

# Verify run bundle
roap verify-bundle outputs/test --json

# Run GUI
python tools/roap_app.py
```

**Pixi tasks** (from `pixi.toml`):
- `pixi run test` → `pytest -q`
- `pixi run pipeline` → `./run_pipeline.sh`
- `pixi run validate` → `roap validate`
- `pixi run verify-bundle` → `roap verify-bundle`
- `pixi run pre-commit-all` → ruff, black, mypy, pytest

---

## 9. Domain Knowledge References (in `knowledge/`)

| File | Purpose |
|------|---------|
| `knowledge/project/epic.md` | Full delivery plan with priority matrix, action items, success criteria |
| `knowledge/project/ai-prd.md` | AI-friendly PRD: 12-week timeline, constraints, acceptance criteria, risk register |
| `knowledge/project/tech-stack.md` | Pixi, Python 3.11, dependencies, testing, quality gates |
| `knowledge/prototype/pipeline-overview.md` | 8-notebook flow, module table, configs, testing, deployment |
| `knowledge/prototype/prototype-readme.md` | Original prototype README (3 run modes, Windows Git Bash) |
| `knowledge/decisions/migration-plan.md` | P-1 task checklist, success criteria, issues resolved |
| `knowledge/decisions/engineering-decisions.md` | 22 numbered decisions with rationale, deciders, implementation refs |
| `knowledge/decisions/adrs.md` | 10 ADRs (5 accepted, 3 pending) |
| `knowledge/domain/carbonate-chemistry.md` | Marine carbonate system, 4 parameters, derived outputs, reproducibility challenges, PyCO2SYS |
| `knowledge/domain/data-standards.md` | Frontiers 2021: clarified columns, 0-9 QC flags, -999 missing, provenance metadata |
| `knowledge/domain/pyco2sys-usage.md` | PyCO2SYS API reference (parameter codes, option tables) |
| `knowledge/personas/user-stories.md` | 24 user stories mapped to epic priorities |
| `knowledge/log.md` | Chronological work log (source of truth for what was done when) |

---

## 10. Critical Context for Next Team

1. **P-1/P0/P1 are DONE**. Do not re-do migration, CI, or packaging. The code is in `src/roap/`, tests pass, CI is green on 3 platforms.

2. **P4 (ADR 0001) is the immediate gate**. The decision is **already made** (Option C: NetCDF/GOA-ON) in `engineering-decisions.md` S1. Just needs formal ADR document + review sign-off to unblock P3.

3. **P2 is the largest remaining milestone** (4 issues). Frontiers 2021 schema audit, Excel round-trip fix (structural, affects Kofi), CRM/std tag validation (silent corruption vector), and hypothesis property tests.

4. **Real dataset regression gate** (April 2026 cruise, 38 samples, expected 22/16/0) is **manual, not in CI**. Document process in `docs/manual-regression.md` and run before every release.

5. **Carbonate chemistry defaults** are provisional (Lueker2000, Total scale) — confirm with Prof. Mahu if possible.

6. **Windows requires Git Bash** (not WSL). Documented in README and CI.

7. **Never commit unpublished data**. Enforced by `.gitignore` + pre-commit check.

8. **Update `knowledge/log.md`** when you complete work — it's the project's institutional memory.

9. **Follow AGENTS.md rules**: Pixi only, verify before claiming, change surgically, ask instead of assuming, contribution-discipline.md for PRs.

---

## 11. Quick Links

- **Repo**: https://github.com/uw-ssec/roap
- **Milestones**: https://github.com/uw-ssec/roap/milestones
- **Issues**: https://github.com/uw-ssec/roap/issues
- **CI**: https://github.com/uw-ssec/roap/actions
- **Prototype submodule**: https://github.com/reez-png/oa_pipeline (pinned at `3d125b3`)

---

## 12. Suggested Next Steps for New Team

1. **Read** `knowledge/log.md` (full history) and `knowledge/project/epic.md` (full plan)
2. **Run** `pixi install && pixi run pytest -q` to verify environment
3. **Run** `./run_pipeline.sh examples/example_data.xlsx outputs/test` to verify pipeline
4. **Start with P4** (#18): Write formal ADR 0001 at `docs/adr/0001-queryable-layer-scope.md`, get sign-off
5. **Then P2** (#15-17, #27): Schema audit → Excel fix → CRM validation → hypothesis tests
6. **Then P3** (#19-20): Pre-flight validation → NetCDF export → manual regression doc
7. **Finally v1.0.0** (#21): Tag, release, PyPI, fresh-clone verification

---

*Generated 2026-10-18 from OKF knowledge base + GitHub milestones/issues. This document is the context transfer artifact for project handoff.*