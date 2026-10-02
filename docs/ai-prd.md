# ROAP — AI-Friendly Product Requirements Document
## Reproducible Ocean Acidification Pipeline (v1.0.0)

> **Note:** The `oa_pipeline` v0.2.0 prototype lives in a separate repository. For migration (P-1), add it as a git submodule: `git submodule add <prototype-repo-url> prototype/oa_pipeline`. References below use `prototype/oa_pipeline/` paths.

---

## 1. Objective

Build a **production-grade, cross-platform, citable platform** for ocean acidification carbonate chemistry quality control and processing that:

- Transforms the existing `oa_pipeline` v0.2.0 research prototype (8 Papermill-driven notebooks, 221 tests, Windows-only) into a packaged Python library with CLI, GUI, and notebook interfaces
- Enforces **Frontiers 2021 data standards** (clarified column names, unified 0–9 QC flags, `-999` missing sentinel) and **full provenance tagging** on every derived carbonate value
- Delivers **reproducible runs** via version-pinned releases, config compatibility gates, and immutable run bundles
- Serves four personas: **Ruu** (trainee, clean-laptop onboarding), **Kofi** (technician, Excel-only, no terminal), **Ama** (analyst, QC configurability, figure provenance), **Fatou** (regional partner, config-driven column mapping), **Nadia** (data manager, quarterly unattended runs, GOA-ON export), **Prof. Adjei** (PI, sign-off summaries, archived run bundles)

**North Star:** Fresh clone → `pixi install` → `pixi run pipeline examples/example_data.xlsx outputs/test` → `analysis_ready.csv` with expected 4 FAIL verdicts on injected rows in <10 min on Linux, macOS, and Windows.

---

## 2. Phase & Milestone Timeline

| Phase | Milestone | Target | Duration | Gate |
|-------|-----------|--------|----------|------|
| **P-1** | Prototype Migration Complete | Week 1–2 | 5–7 days | 221 tests pass; pipeline runs on synthetic data |
| **P0** | Cross-Platform CI + Invariant Test + Single Entry Point | Week 3–4 | 5–7 days | CI green on Ubuntu/macOS/Windows + invariant test fails on column mutation |
| **P1** | Tagged Release v0.2.0 + Run Bundles + Config Gate | Week 5–6 | 5–7 days | `pip install oa-pipeline==0.2.0` works; config gate enforced; run bundles produced |
| **P2** | Schema/Provenance/CRM/Excel Fixes + Property Tests | Week 7–9 | 10–14 days | Frontiers 2021 audit complete; Excel round-trip fixed; CRM/std validation fails fast; hypothesis tests in CI |
| **P4** | ADR 0001 Decided (Queryable Layer Scope) | Week 9 | 2–3 days | ADR written, reviewed, decided |
| **P3** | GOA-ON Export + Pre-Flight Validation + Manual Regression | Week 10–11 | 7–10 days | Pre-flight CLI/GUI works; GOA-ON export valid; April 2026 dataset → 22/16/0 |
| **v1.0.0** | **Tagged Release v1.0.0** | Week 12 | — | All Definition of Done criteria met |

### Milestone Dependencies

```
P-1 (BLOCKING)
    │
    ├─── P0 ──► P1 ──► P2 ──► P4 ──► P3 ──► v1.0.0
    │              │
    │              └─► (parallel) P2
    │
    └─── P4 gates P3 export design
```

**Total: 12 weeks (3 months)** with buffers for cross-platform CI flakiness, schema audit iteration, and ADR decision latency.

---

## 3. Constraints

| Category | Constraint |
|----------|------------|
| **Package Manager** | **Pixi only** — no `pip`, `conda`, `venv` directly. `pixi install` before any command. |
| **Python Version** | 3.11 (pinned in `pixi.toml` and `pyproject.toml`) |
| **Platform Support** | Linux (Ubuntu), macOS, Windows (Git Bash required — not WSL) |
| **Data Privacy** | **Never commit unpublished data** — enforced by `.gitignore` + pre-commit check |
| **Code Quality** | `pixi run pre-commit-all` (ruff, black, mypy, pytest) must pass before commit |
| **Commit Style** | Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`) |
| **Testing Philosophy** | Property-based/invariant testing (hypothesis) alongside example-based — CI green ≠ data integrity without invariant test |
| **Architecture** | Single engine (`src/oa_pipeline/`), three doors (CLI, GUI, Notebook) — all call same core |
| **Dependencies** | Core: pandas, numpy, openpyxl, matplotlib, pyyaml, pyarrow, tabulate, papermill, pytest, ipykernel, ipython |
| **Release Process** | Semantic versioning, signed tags, GitHub Releases, PyPI publish, CHANGELOG.md (Keep a Changelog) |

---

## 4. Non-Goals

| Non-Goal | Rationale |
|----------|-----------|
| **Reimplement PyCO2SYS chemistry** | 25+ year lineage (CO2SYS → CO2SYS.m → PyCO2SYS). Wrap it, don't rewrite. |
| **Queryable time-series database (v1.0)** | ADR 0001 pending — decision gates P3 export design. File-based manifest is fallback. |
| **Web-based UI** | Kofi's no-terminal need met by Tkinter GUI; web adds infra burden. |
| **Real-time/streaming processing** | Cruise data is batch (<100 bottles); no streaming requirement. |
| **Multi-tenant SaaS** | Regional network deployment model (OA-Africa hubs), not cloud service. |
| **Automated CRM certification lookup** | Certified values versioned in `configs/crm_certified_values.yaml`; human verification required. |
| **pH scale conversion engine** | Pipeline records scale, audits consistency — does not convert. Upstream tools handle conversion. |

---

## 5. Relevant Code Paths

### Prototype Location (Source of Truth for Migration — Git Submodule)
Add as submodule: `git submodule add <prototype-repo-url> references/prototype/oa_pipeline`

```
references/prototype/oa_pipeline/
├── src/oa_pipeline/          # 12 modules — CORE LOGIC
│   ├── __init__.py           # v0.2.0, public API re-exports
│   ├── common.py             # Paths, I/O, coalescing, flags, manifests
│   ├── schema.py             # Canonical schema, aliases, normalisers, export order
│   ├── qc_ta_ph.py           # TA CRM correction, pH standard correction, plots
│   ├── policy.py             # RangePolicy, range flag helpers
│   ├── stage1b.py            # Best source coalescing
│   ├── stage2.py             # Duplicate detection, replicate harmonisation
│   ├── stage3.py             # Carbonate integrity: DIC sum, pH diagnostic, provenance
│   ├── stage4.py             # Final audit, PASS/REVIEW/FAIL verdicts
│   ├── inspect.py            # Read-only output tree inspection
│   ├── carbonate_calc.py     # (Legacy — not used in current pipeline)
│   └── duplicate_precision.py # (Legacy — not used in current pipeline)
├── notebooks/                 # 8 Papermill stages (01–08)
├── tests/                     # 221 tests (14 test_*.py files)
├── configs/                   # YAML configs (crm_certified_values, stage configs)
├── examples/                  # make_example_data.py, example_data.xlsx
├── run_pipeline.sh            # Bash orchestrator (Papermill driver)
├── oa_pipeline_app.py         # Tkinter GUI launcher
├── oa_pipeline_app_core.py    # GUI-independent launcher logic
├── stamp_carbonate_provenance.py # Provenance stamping helper
├── pyproject.toml             # Package definition (src-layout, v0.2.0)
└── DATA_DICTIONARY.md         # Input contract from code
```

### Target Repository Structure (Post-Migration)
```
roap/
├── .github/workflows/ci.yml
├── .gitignore
├── AGENTS.md
├── CLAUDE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md                 # Single entry point (consolidated)
├── RELEASE.md
├── pixi.toml                 # Dev environment (pre-commit, gh-cli, onboard)
├── pyproject.toml            # oa_pipeline package (src-layout)
├── run_pipeline.sh           # Verified working
├── tools/
│   ├── oa_pipeline_app.py
│   ├── oa_pipeline_app_core.py
│   └── stamp_carbonate_provenance.py
├── configs/                  # Per-stage + reference configs
├── examples/                 # make_example_data.py, example_data.xlsx
├── notebooks/                # 8 notebooks (orchestration layer)
├── src/oa_pipeline/          # 12 modules (identical to prototype)
├── tests/                    # 221+ tests + invariant + property tests
├── docs/
│   ├── adr/
│   │   └── 0001-queryable-layer-scope.md
│   ├── ai-prd.md             # THIS FILE
│   └── manual-regression.md
└── outputs/                  # .gitignore'd run artifacts
```

---

## 6. Domain Glossary

| Term | Definition | Source |
|------|------------|--------|
| **DIC** | Dissolved Inorganic Carbon = CO₂(aq) + HCO₃⁻ + CO₃²⁻ | CARBONATE_CHEMISTRY_KNOWLEDGE.md |
| **TA** | Total Alkalinity — acid-buffering capacity of seawater | CARBONATE_CHEMISTRY_KNOWLEDGE.md |
| **pH scale** | Total / Seawater / Free / NBS — defines H⁺ activity reference; **mismatch = #1 silent error** | CARBONATE_CHEMISTRY_KNOWLEDGE.md |
| **Ω_aragonite, Ω_calcite** | Saturation states; Ω > 1 = calcification favorable | CARBONATE_CHEMISTRY_KNOWLEDGE.md |
| **CRM** | Certified Reference Material (Dickson batches) — used for TA correction | DATA_DICTIONARY.md |
| **pH standard** | Tris / AMP / BIS buffer — used for pH electrode correction | DATA_DICTIONARY.md |
| **sample_tag prefix** | **Primary detection**: `RM<batch>_<n>` = CRM, `tris_*` = pH std; NOT `sample_type` column | ADR 0006, DATA_DICTIONARY.md |
| **Frontiers 2021** | Best-practice data standard for discrete chemical oceanography — clarified column names, 0–9 QC flags, `-999` missing | data-standard.md |
| **GOA-ON** | Global Ocean Acidification Observing Network — international data portal target | data-standard.md |
| **Run bundle** | Immutable `outputs/<run>/` + `runs/<timestamp>/` with `run_bundle_manifest.json` (input SHA256, config SHA256s, git sha, version, timestamp, output hashes) | epic.md P1.3 |
| **Config compatibility gate** | `compatible_pipeline_version` in config YAML enforced at runtime — stale config fails fast | epic.md P1.2 |
| **Invariant test** | For each stage: snapshot input columns → run stage → assert untargeted columns byte-identical | ADR 0003, epic.md P0.3 |
| **Pre-flight validation** | `oa-pipeline validate INPUT_XLSX` — checks required columns, dtypes, CRM/std tags, CRM batch — runs in <5s without full pipeline | epic.md P3.1 |

---

## 7. Acceptance Criteria

### P-1: Prototype Migration (BLOCKING)
- [ ] `src/oa_pipeline/` exists with all 12 modules (`__init__.py`, `common.py`, `schema.py`, `qc_ta_ph.py`, `policy.py`, `stage1b.py`, `stage2.py`, `stage3.py`, `stage4.py`, `inspect.py`, `carbonate_calc.py`, `duplicate_precision.py`)
- [ ] `tests/` has 221+ passing tests (`pytest -q` → `221 passed`)
- [ ] `examples/example_data.xlsx` exists (or regenerates via `make_example_data.py`)
- [ ] `configs/` has all YAML configs including `07_stage3.yaml` with `ph_diag_harmonize_temperature: true`
- [ ] `./run_pipeline.sh examples/example_data.xlsx outputs/test` works end-to-end → 4 FAIL verdicts on injected rows
- [ ] Unpublished data NOT in git (`git status` clean of `oa_data_apr*.xlsx`)

### P0: Cross-Platform CI + Invariant Test + Entry Point
- [ ] GitHub Actions workflow (`.github/workflows/ci.yml`) matrix: Ubuntu-latest, macOS-latest, Windows-latest, Python 3.11
- [ ] CI steps: `pixi install` → `pixi run pre-commit-all` → `pytest -q` → `./run_pipeline.sh examples/example_data.xlsx outputs/ci_test`
- [ ] **Invariant test** (`tests/test_invariants.py`): for each stage, untargeted columns are byte-identical pre/post — fails CI on mutation
- [ ] Single `README.md` at root: quickstart (CLI/GUI/Notebook), prerequisites, troubleshooting
- [ ] Legacy READMEs archived to `docs/legacy/`; loose scripts moved to `tools/`
- [ ] GUI launcher (`python tools/oa_pipeline_app.py`) opens and runs on all three platforms
- [ ] `pixi run test` and `pixi run pipeline` tasks in `pixi.toml`
- [ ] Fresh clone → `pixi install` → `pixi run pipeline examples/example_data.xlsx outputs/test` → success in <10 min

### P1: Packaging, Releases, Version Pinning, Run Bundles
- [ ] `git tag v0.2.0` exists; `gh release create v0.2.0` published with assets
- [ ] `pip install oa-pipeline==0.2.0` works (PyPI) or `pip install git+https://github.com/reez-png/oa_pipeline@v0.2.0`
- [ ] Running pipeline with stale config (`compatible_pipeline_version: ">=0.1.0"`) against v0.2.0 code **fails fast with actionable error**
- [ ] Every run produces `run_bundle_manifest.json` with: input SHA256, config SHA256s, git commit, `oa_pipeline` version, timestamp, output file hashes
- [ ] `oa-pipeline verify-bundle <run_dir>` validates integrity
- [ ] `CHANGELOG.md` follows Keep a Changelog format

### P2: Schema/Provenance/CRM/Excel Fixes + Property-Based Testing
- [ ] `schema.py` canonical names match Frontiers 2021 clarified headers (or documented deviation in `docs/schema-deviations.md`)
- [ ] Fatou can run her 3-year archive by adding only `configs/schema_aliases.yaml` — no column renaming
- [ ] Every numeric column in output has corresponding `*_qc_flag` (0–9 scale)
- [ ] Missing values export as `-999` (not `NaN`, not empty string)
- [ ] Provenance columns present and non-empty on all sample rows with derived carbonate values
- [ ] **Excel formula columns survive read-write round-trip** (tested: workbook with formula → read → write → preserved as static)
- [ ] **CRM/std tag mismatch fails fast** with actionable error (tested: `sample_type=crm` + `sample_tag=Batch213_1` → error)
- [ ] Property-based tests (`tests/test_properties.py` with `hypothesis`) run in CI and pass:
  - Alias resolution idempotency
  - Unit normalization round-trip
  - Schema application preserves untargeted columns
  - CRM/std tag detection invariants

### P4: ADR — Queryable Time-Series Layer Scope
- [ ] ADR written (`docs/adr/0001-queryable-layer-scope.md`), reviewed, **decided** before P3 work starts
- [ ] If Option A (DuckDB): quarterly ingest + query works end-to-end on synthetic multi-cruise data
- [ ] If Option B (Files): `manifest.csv` enables `pd.read_csv` + filter workflow for Ama/Nadia

### P3: International Export + Pre-Flight Validation
- [ ] `oa-pipeline validate INPUT_XLSX --config-dir configs` catches: missing required columns, wrong dtypes, unknown CRM batch, mis-tagged CRM/std rows
- [ ] Validation runs on raw Excel **without** executing full pipeline; exits 0 (clean) or 1 (issues) + JSON report
- [ ] Kofi can validate via GUI: "Validate Only" button → pass/fail with row numbers
- [ ] Exported dataset passes GOA-ON portal ingestion (test with sandbox if available)
- [ ] Export includes all provenance metadata needed for reproducibility
- [ ] Manual regression on Unpublished dataset (April 2026, 38 samples) produces **22 PASS, 16 REVIEW, 0 FAIL** before every release

### v1.0.0 Definition of Done
- [ ] All P-1 through P3 complete per above
- [ ] All 221+ original tests + new tests (invariant, property-based, config gate, CRM validation, Excel round-trip) pass
- [ ] `CHANGELOG.md` complete
- [ ] No unpublished data in repo

---

## 8. Similar Implementations (Internal)

| Component | Location | Notes |
|-----------|----------|-------|
| **Prototype pipeline** | `references/prototype/oa_pipeline/` (git submodule) | Full v0.2.0 with 221 tests, 8 notebooks, `.venv_run/` — **source for P-1 migration** |
| **Carbonate chemistry knowledge** | `knowledge/domain/carbonate-chemistry.md` | Authoritative domain reference; update first, propagate to skills |
| **Data standard reference** | `knowledge/domain/data-standards.md` | Frontiers 2021 quick reference for schema alignment |
| **Architecture decisions** | `knowledge/decisions/adrs.md` | 10 ADRs (6 accepted, 4 proposed) |
| **Council review** | `knowledge/decisions/council-review.md` | 4-voice review that reshaped epic (added P-1, merged P0+invariant, moved P4 before P3) |
| **Personas & user stories** | `knowledge/personas/user-stories.md` | 24 stories mapped to epics with acceptance criteria |
| **Skills (ECC)** | `.agents/skills/` | `carbonate-chemistry`, `data-standard`, `pyco2sys-usage`, `tdd-workflow`, `pre-commit-and-quality`, `verification-loop`, etc. |

---

## 9. External References

| Reference | Purpose |
|-----------|---------|
| **Frontiers 2021 Paper** | https://www.frontiersin.org/articles/10.3389/fmars.2021.705638 — Data standard schema |
| **PyCO2SYS Docs** | https://pyco2sys.readthedocs.io/en/latest/ — Core math engine API |
| **PyCO2SYS v2 Beta** | Evaluate against v1 stability before committing |
| **GOA-ON Data Portal** | https://goa-on.org/ — Export target compatibility |
| **OA-Africa Network** | https://www.oa-africa.net/ — Regional adoption context |
| **Lueker et al. (2000)** | Equilibrium constants set (`opt_k_carbonic=10`) — project default |
| **Dickson CRM Batches** | NOAA OCADS — Certified TA values in `configs/crm_certified_values.yaml` |
| **Orr et al. (2005)** | Ω_aragonite undersaturation precedes calcite — biological relevance |
| **Moras et al. (2023, L&O Methods 21)** | pH scale mixing corrupts carbonate calculations — invariant for `assert_ph_scale_consistency` |
| **Keep a Changelog** | https://keepachangelog.com/ — CHANGELOG.md format |

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Prototype migration reveals hidden dependencies | Medium | High | P-1 verification step runs full test suite + pipeline before any P0 work |
| Invariant test catches latent bugs requiring schema changes | High | Medium | P0 invariant test designed to fail fast; schema changes in P2 |
| ADR 0001 decision delays P3 | Medium | High | P4 timeboxed to 1 day; file-based fallback (Option B) is low-effort |
| Cross-platform CI flakiness on Windows | Medium | Medium | Git Bash requirement documented; cache pixi env; `OA_KEEP_PYTEST_RUNS=1` debug mode |
| Unpublished dataset regression fails | Low | High | Document exact manual process; treat as release gate, not CI gate |
| Config-driven aliases break existing configs | Low | Medium | Config compatibility gate (P1.2) enforces version pinning |

---

## 11. Success Metrics (v1.0.0)

| Metric | Target |
|--------|--------|
| **Onboarding time (Ruu)** | Clean laptop → successful run on example data < 1 hour |
| **Cross-platform CI pass rate** | 100% on Ubuntu, macOS, Windows on every PR |
| **Invariant test coverage** | Catches lat/lon overwrite bug class + all column mutation classes |
| **Schema compliance** | Frontiers 2021 audit: 0 undocumented deviations |
| **Config-driven adoption** | Fatou maps 3-year archive via `schema_aliases.yaml` only |
| **Release citability** | `pip install oa-pipeline==1.0.0` + tagged GitHub Release + PyPI |
| **Reproducibility** | `oa-pipeline verify-bundle` validates any archived run |
| **Kofi workflow** | Excel validation via GUI in <5s, no terminal |
| **GOA-ON export** | Portal sandbox ingestion passes |
| **Manual regression** | April 2026 dataset → 22/16/0 before every release |

---

## 12. Open Questions Requiring Human Decision

1. **ADR 0001: Queryable Layer Scope** — DuckDB (Option A) vs File Manifest (Option B)? Decider: Lead + Prof. Adjei. **Blocks P3 export design.**
2. **PyCO2SYS version** — v1 stable vs v2 beta? Default constants (`opt_k_carbonic=10`, `opt_pH_scale=1`) confirmed with Prof. Mahu's group?
3. **Real dataset access** — April 2026 dataset location and access protocol for manual regression?
4. **GPG signing** — Sign release tags? Requires key setup.
5. **PyPI publishing** — Automated via GitHub Actions or manual? Org/account ready?

---

## 13. Appendix: Epic-to-PRD Traceability

| Epic Priority | PRD Section | Key Deliverables |
|---------------|-------------|------------------|
| P-1 | §2, §7 (P-1) | Migration complete, 221 tests pass |
| P0 | §2, §7 (P0) | 3-platform CI, invariant test, single README |
| P1 | §2, §7 (P1) | v0.2.0 tag, PyPI, config gate, run bundles |
| P2 | §2, §7 (P2) | Frontiers audit, Excel fix, CRM validation, hypothesis |
| P4 | §2, §7 (P4) | ADR 0001 decided |
| P3 | §2, §7 (P3) | Pre-flight validation, GOA-ON export, manual regression |
| v1.0.0 | §7 (v1.0.0) | All Definition of Done criteria |

---

*Generated from `knowledge/project/epic.md`, council review (`knowledge/decisions/council-review.md`), architecture decisions (`knowledge/decisions/adrs.md`), prototype codebase (`references/prototype/oa_pipeline/` as git submodule), and domain references (`knowledge/domain/carbonate-chemistry.md`, `knowledge/domain/data-standards.md`). Update `knowledge/domain/carbonate-chemistry.md` first when domain decisions change, then propagate to skills.*