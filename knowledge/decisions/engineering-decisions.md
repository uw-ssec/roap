---
type: Decision
title: ROAP v1.0.0 Engineering Decisions
description:
  "Key engineering decisions for ROAP v1.0.0 implementation: ADR 0001 (NetCDF
  export), PyCO2SYS version, dataset access, GPG signing, PyPI publishing, CI
  strategy, architecture, data standard, invariant testing, config gate, package
  rename, CLI framework"
tags: [engineering, decisions, v1.0.0, adr, migration, cli]
generated: { by: agent/cli, at: "2026-10-07T00:00:00Z" }
updated: { by: agent/cli, at: "2026-10-10T00:00:00Z" }
status: stable
---

# ROAP v1.0.0 — Engineering Decisions Log

**Status**: Approved for implementation **Last Updated**: 2026-10-07
**Decider**: Lead Engineer (with Prof. Adjei / Prof. Mahu input where noted)

---

## 1. ADR 0001: Queryable Layer Scope / Export Format

### Options Considered

| Option                        | Description                                                                              | Pros                                                                        | Cons                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Option A: DuckDB**          | Queryable time-series layer with quarterly ingest + query on synthetic multi-cruise data | Full SQL query power; enables complex analytics; future-proof               | Higher implementation effort; adds DB dependency; delays P3 |
| **Option B: File Manifest**   | `manifest.csv` enables `pd.read_csv` + filter workflow for Ama/Nadia                     | Low effort; no new dependencies; meets current filtering needs; unblocks P3 | Limited query flexibility; manual CSV filtering             |
| **Option C: NetCDF (GOA-ON)** | NetCDF export following GOA-ON template with CF conventions                              | International standard; self-describing; interoperable; GOA-ON compatible   | Requires netCDF4/xarray; schema design effort               |

### Decision

**Selected: Option C — NetCDF (GOA-ON Template)** **Rationale**: GOA-ON
compatibility is a hard requirement for Nadia (P3.3); NetCDF with CF conventions
is the international standard for oceanographic data exchange; self-describing
format eliminates separate metadata manifests; unblocks P3 export design
immediately. **Supersedes**: Previous Option B decision (File Manifest).
**Decider**: Lead + Prof. Adjei ✅ **Implemented in**: P3 (Week 10-11),
`src/roap/export.py` + `roap export` CLI

---

## 2. PyCO2SYS Version

### Options Considered

| Option                              | Description                             | Pros                                               | Cons                                                             |
| ----------------------------------- | --------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| **v1 Stable**                       | Current stable release, well-tested     | Proven API; constants validated; no migration risk | Older codebase; no new features                                  |
| **v2 Beta**                         | Newer version, evaluate stability first | New features; potential performance gains          | Beta = API instability risk; constants may differ; delays v1.0.0 |
| **Need to confirm with Prof. Mahu** | Constants decision pending expert input | Ensures scientific validity                        | Adds latency to decision                                         |

### Decision

**Selected: v1 Stable** **Constants**: `opt_k_carbonic=10` (Lueker et al. 2000),
`opt_pH_scale=1` (Total scale) **Rationale**: v2 is beta with API changes; v1
constants validated with Prof. Mahu's group; upgrade path documented for
post-v1.0.0. **Decider**: Lead (confirm with Prof. Mahu if needed) ⏳
**Implemented in**: `src/roap/carbonate_calc.py` wrapper

---

## 3. Real Dataset Access (Manual Regression Gate)

### Options Considered

| Option                   | Description                                | Pros                                    | Cons                                     |
| ------------------------ | ------------------------------------------ | --------------------------------------- | ---------------------------------------- |
| **Local path available** | I have the file locally, will provide path | Immediate access; no network dependency | Must ensure path shared securely         |
| **Remote/secure access** | Need to download from secure location      | Centralized storage                     | Adds access complexity; potential delays |
| **Not yet available**    | Will be available later, note for now      | Honest about status                     | Blocks manual regression gate            |

### Decision

**Selected: Local path available** **Dataset**: April 2026 cruise, 38 samples
**Expected Result**: 22 PASS, 16 REVIEW, 0 FAIL **Protocol**: Run manually
before each release; not in CI. **Decider**: Lead ✅ **Implemented in**: P3
(Week 10-11), `docs/manual-regression.md`

---

## 4. GPG Signing for Release Tags

### Options Considered

| Option               | Description                             | Pros                                                                    | Cons                                                                      |
| -------------------- | --------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Yes, sign tags**   | Will set up GPG key for signed releases | Supply chain security; enables PyPI trusted publishing; high user trust | One-time setup effort; key management                                     |
| **No, skip signing** | Unsigned tags/releases for v1.0.0       | Zero effort; faster release                                             | No cryptographic verification; cannot use trusted publishing; lower trust |

### Decision

**Selected: Defer to post-v1.0.0 — unsigned tags for v1.0.0** **Rationale**: Key
setup is one-time but non-trivial; v1.0.0 timeline prioritizes functional
delivery; document in RELEASE.md; create follow-up issue. **Implications**:

- No cryptographic verification of tag authorship
- Cannot use GitHub Actions trusted publishing (need API token in secrets)
- Acceptable for v1.0.0 given regional deployment model **Decider**: Lead ⏳
  **Implemented in**: v1.0.0 release (Week 12), documented in `RELEASE.md`

---

## 5. PyPI Publishing

### Options Considered

| Option                           | Description                                              | Pros                                                          | Cons                                           |
| -------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------- |
| **Automated via GitHub Actions** | Configure trusted publishing / API token in repo secrets | Fully automated; reproducible; secure with trusted publishing | Requires PyPI org + trusted publishing setup   |
| **Manual publish**               | Run `pip publish` locally with credentials               | Works immediately; no CI setup needed                         | Human error risk; credentials on local machine |
| **Org/account not ready**        | Need to create PyPI org/project first                    | Honest about blocker                                          | Delays automated publishing                    |

### Decision

**Selected: Manual publish for v1.0.0 — org/account not ready** **Rationale**:
PyPI org/project creation needed; configure trusted publishing post-v1.0.0.
**Workflow**: `pixi run build` → `twine upload dist/*` with credentials
**Follow-up**: Create PyPI org, enable trusted publishing, automate via GitHub
Actions. **Decider**: Lead ⏳ **Implemented in**: v1.0.0 release (Week 12)

---

## 6. Cross-Platform CI Strategy (from PRD constraints)

**Decision**: GitHub Actions matrix: Ubuntu-latest, macOS-latest, Windows-latest
(Git Bash) **Python**: 3.11 pinned **Package Manager**: Pixi only **Quality
Gate**: `pixi run pre-commit-all` (ruff, black, mypy, pytest) **Decider**: Lead
(per PRD constraints) ✅ **Implemented in**: P0 (Week 3-4),
`.github/workflows/ci.yml`

---

## 7. Architecture: Single Engine, Three Doors

**Decision**: Core logic in `src/roap/`; CLI (`run_pipeline.sh`), GUI
(`tools/roap_app.py`), Notebooks (`notebooks/`) all call same core. **Decider**:
Council review / ADR-0010 ✅ **Implemented in**: P-1 migration (Week 1-2)

---

## 8. Data Standard: Frontiers 2021

**Decision**: Canonical schema = Frontiers 2021 clarified headers; 0–9 QC flags;
`-999` missing sentinel. **Deviations**: Document in `docs/schema-deviations.md`
if any. **Decider**: ADR-0009 ✅ **Implemented in**: P2 (Week 7-9),
`src/roap/schema.py`

---

## 9. Invariant Testing (ADR-0003)

**Decision**: Per-stage invariant test in CI — snapshot input columns → run
stage → assert untargeted columns byte-identical. **Decider**: Council review ✅
**Implemented in**: P0 (Week 3-4), `tests/test_invariants.py`

---

## 10. Config Compatibility Gate (P1.2)

**Decision**: `compatible_pipeline_version` in config YAML enforced at runtime —
stale config fails fast. **Decider**: Epic / PRD ✅ **Implemented in**: P1 (Week
5-6), `src/roap/common.py`

---

## 11. Package Rename: oa-pipeline → roap

### Context

The prototype was named `oa_pipeline` v0.2.0. The production platform is ROAP
(Reproducible Ocean Acidification Pipeline). The repo is named `roap`.

### Options Considered

| Option                          | Description                     | Pros                                       | Cons                                                |
| ------------------------------- | ------------------------------- | ------------------------------------------ | --------------------------------------------------- |
| **Keep oa-pipeline for v0.2.0** | Match prototype version exactly | Continuity with prototype                  | Inconsistent naming; repo=roap, package=oa-pipeline |
| **Rename to roap now**          | Clean break, consistent naming  | Repo=roap, package=roap, CLI=roap; citable | Requires updating all imports, tests, notebooks     |

### Decision

**Selected: Rename to roap now** **Rationale**: Consistency across repo,
package, CLI, and project name (ROAP). The rename is a one-time cost (~30 min
with find/replace) that eliminates confusion permanently. Version 0.2.0 retained
to match prototype. **Decider**: Lead ✅ **Implemented in**: P-1 migration (Week
1-2), all imports/tests/notebooks/configs updated.

---

## 12. CLI Framework: Typer

### Context

The prototype had no CLI — only `run_pipeline.sh` (bash) and notebooks. The
migration plan (P-1.6) required extracting notebook orchestration to CLI entry
points.

### Options Considered

| Option       | Description                              | Pros                                          | Cons                                     |
| ------------ | ---------------------------------------- | --------------------------------------------- | ---------------------------------------- |
| **Click**    | Mature, widely used                      | Large ecosystem; familiar                     | More boilerplate; callback-based         |
| **Typer**    | Modern, type-hint based (built on Click) | Less boilerplate; auto-completion; modern API | Newer; smaller ecosystem                 |
| **argparse** | Stdlib only                              | No dependencies                               | Verbose; no auto-completion; manual help |

### Decision

**Selected: Typer** **Rationale**: Modern Python CLI framework; minimal
boilerplate; auto-completion for users; built on Click so mature foundation;
already added as dependency in pyproject.toml. **Decider**: Lead ✅
**Implemented in**: P-1 migration (Week 1-2), `src/roap/cli.py` with `validate`
and `verify-bundle` commands.

---

## 13. GUI Rename: oa_pipeline_app.py → roap_app.py

### Decision

**Selected: Rename GUI launcher to match package** **Rationale**: Consistency
with `roap` package name; avoids confusion. Both `roap_app.py` and
`roap_app_core.py` renamed and updated. **Decider**: Lead ✅ **Implemented in**:
P-1 migration (Week 1-2).

---

## 14. Notebook Import Updates

### Decision

**Selected: Update all 11 notebooks from `oa_pipeline.*` to `roap.*`**
**Rationale**: Notebooks are executable documentation and part of the pipeline;
must use the production package name. Automated via find/replace. **Decider**:
Lead ✅ **Implemented in**: P-1 migration (Week 1-2).

---

## Related Documents

- [Council Review of Epic Plan](council-review.md)
- [Architecture Decision Records](adrs.md)
- [Prototype Migration Plan](migration-plan.md)
- [AI-Friendly PRD](../project/ai-prd.md)
- [Implementation Design](../../superpowers/specs/2026-10-05-roap-v1-implementation-design.md)
- [Implementation Plan](../../superpowers/plans/2026-10-05-roap-v1-implementation-plan.md)

---

## 15. Git History Management: Individual Commits vs Squash Merge

### Context

During P-1 through P1 milestones, four PRs were squash-merged into main,
collapsing 78 individual commits into a single mega-commit. This lost
bisectability, blame accuracy, and reviewability.

### Options Considered

| Option                           | Description                                                | Pros                                                            | Cons                                               |
| -------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------- |
| **Keep squash merge**            | Leave history as single mega-commit                        | Simple; matches GitHub default                                  | Loses bisectability, blame accuracy, reviewability |
| **Force-push rewritten history** | Rebuild main with individual commits via cherry-pick/merge | Restores bisectability, blame, reviewability; full transparency | Requires force-push; team must re-clone/rebase     |
| **Leave as-is, document refs**   | Keep mega-commit, document feature branch refs in docs     | Zero disruption; history preserved in feature branches          | Bisect/blame still broken on main                  |

### Decision

**Selected: Force-push rewritten history** **Rationale**: Restoring individual
commits restores `git bisect`, `git blame`, and per-commit reviewability.
Feature branches (`feat/p1-migration`, `feat/p0-ci-invariant-readme`,
`feat/p1-release-config-bundles`) preserved as permanent reference. Backup
branch (`backup-main`) created for rollback. **Decider**: Lead ✅ **Implemented
in**: 2026-10-18, `git push --force-with-lease` from rebuilt `main-rebuilt`
branch. **Rollback**: `git push origin backup-main:main --force` if needed.

---

## 16. CI Setup-Pixi Action Version Pinning

### Context

The CI workflow used `prefix-dev/setup-pixi@v2` which doesn't exist (the action
doesn't have a `v2` tag).

### Decision

**Selected: Pin to `v0.11.2`** **Rationale**: Explicit version pin avoids "tag
not found" failures. Latest stable at time of fix was `v0.11.2`. **Decider**:
Lead ✅ **Implemented in**: 2026-10-18, `.github/workflows/ci.yml` line 23.

---

## 17. CI Pre-Commit Caching and Timeout

### Context

CI failures on macOS/Ubuntu due to pre-commit exceeding 30-min timeout and no
caching.

### Decision

**Selected: Add `actions/cache@v4` for `~/.cache/pre-commit` + 10-min timeout on
pre-commit step** **Rationale**: Caches hooks across runs; timeout prevents
stuck jobs. **Decider**: Lead ✅ **Implemented in**: 2026-10-18,
`.github/workflows/ci.yml`.

---

## 18. CRM/TRIS Row Preservation in Stage 1B (Issue #29)

### Context

Pipeline was dropping CRM/TRIS rows in Stage 1B, losing audit trail.

### Decision

**Selected: Preserve all rows in `analysis_ready_subset()`; add
`row_classification` column (`SAMPLE`/`CRM_QC`/`STD_QC`)** **Rationale**:
CRM/TRIS rows are QC reference material; must appear in final output with
appropriate verdicts (`CRM_QC`/`STD_QC`). **Decider**: Lead ✅ **Implemented
in**: 2026-10-11, `src/roap/stage1b.py` (`classify_rows_sample`,
`analysis_ready_subset`), test `tests/test_crm_tris_preservation.py`.

---

## 19. CRM Correction Robustness Without Config (Issue #30)

### Context

`build_corrections_table()` returned `None` when `group_by` not in columns,
causing `AttributeError` in CRM correction during invariant tests (which run
without `--config-dir`).

### Decision

**Selected: Ensure `build_corrections_table()` always returns DataFrame with
fallback for non-grouped case** **Rationale**: Invariant tests run without
config; pipeline must not crash. Fallback returns overall stats. **Decider**:
Lead ✅ **Implemented in**: 2026-10-18, `src/roap/common.py:983-991` (fallback
`return pd.DataFrame(...)`).

---

## 19. Run Bundle Manifest + Verify-Bundle CLI

### Context

Need immutable run records for reproducibility (P1.3).

### Decision

**Selected: `src/roap/bundle.py` with `generate_run_bundle_manifest()` +
`verify_bundle()`; CLI `roap verify-bundle <run_dir> [--json]`** **Rationale**:
SHA256 hashes of input/config/output files; git commit + pipeline version; JSON
output for automation. **Decider**: Lead ✅ **Implemented in**: 2026-10-11,
`src/roap/bundle.py`, `src/roap/cli.py`, `run_pipeline.sh` env export.

---

## 20. Config Compatibility Gate Enforcement (Vector #4)

### Context

Stale configs could silently produce wrong results.

### Decision

**Selected: Runtime gate in `load_config()` calling
`check_config_compatibility()` with `compatible_pipeline_version` key in all 7
config YAMLs** **Rationale**: Fail fast with actionable error instead of silent
drift. **Decider**: Lead ✅ **Implemented in**: 2026-10-11,
`src/roap/common.py:594`, `tests/test_config_gate.py`.

---

## 21. Pipeline E2E Test Expectations Update

### Context

After CRM/TRIS preservation (Issue #29), pipeline output has 27 rows (20
samples + 4 CRM + 3 TRIS) instead of 20.

### Decision

**Selected: Update `EXPECTED_NON_PASS` in `tests/test_cli_pipeline.py` to
include CRM_QC (4) + STD_QC (3) rows** **Rationale**: Test must match actual
pipeline behavior post-fix. **Decider**: Lead ✅ **Implemented in**: 2026-10-18,
`tests/test_cli_pipeline.py`.

---

## 22. Pre-Commit False Positive Suppression

### Context

`detect-secrets` flagged a hex-like `git_commit` test fixture as a high-entropy
string; `codespell` flagged the short pressure variable name and a misspelling
of "present".

### Decision

**Selected: Rename test fixture to `test-commit-abc123`; fix typos in
`carbonate_calc.py`** **Rationale**: Avoid silencing security hooks; fix actual
typos instead of allowlisting. **Decider**: Lead ✅ **Implemented in**:
2026-10-18, `tests/test_run_bundle.py`, `tests/test_verify_bundle_cli.py`,
`src/roap/carbonate_calc.py`.

---

## Related Documents

- [Council Review of Epic Plan](council-review.md)
- [Architecture Decision Records](adrs.md)
- [Prototype Migration Plan](migration-plan.md)
- [AI-Friendly PRD](../project/ai-prd.md)
- [Implementation Design](../../superpowers/specs/2026-10-05-roap-v1-implementation-design.md)
- [Implementation Plan](../../superpowers/plans/2026-10-05-roap-v1-implementation-plan.md)

# Related Concepts

- [Portable notebook defaults and live package references](portable-notebook-defaults.md):
  P1 notebook defaults and live-reference cleanup follow the existing package
  rename and shared-engine decisions.
