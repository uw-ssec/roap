---
type: Decision
title: ROAP v1.0.0 Engineering Decisions
description:
  "Key engineering decisions for ROAP v1.0.0 implementation: ADR 0001 (NetCDF
  export), PyCO2SYS version, dataset access, GPG signing, PyPI publishing, CI
  strategy, architecture, data standard, invariant testing, config gate"
tags: [engineering, decisions, v1.0.0, adr]
generated: { by: agent/cli, at: "2026-10-07T00:00:00Z" }
status: stable
---

# ROAP v1.0.0 — Engineering Decisions Log

**Status**: Approved for implementation **Last Updated**: 2026-10-07
**Decider**: Lead Engineer (with Prof. Adjei / Prof. Mahu input where noted)

---

## 1. ADR 0001: Queryable Layer Scope / Export Format

### Options Considered

| Option                      | Description                                                                              | Pros                                                                        | Cons                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Option A: DuckDB**        | Queryable time-series layer with quarterly ingest + query on synthetic multi-cruise data | Full SQL query power; enables complex analytics; future-proof               | Higher implementation effort; adds DB dependency; delays P3 |
| **Option B: File Manifest** | `manifest.csv` enables `pd.read_csv` + filter workflow for Ama/Nadia                     | Low effort; no new dependencies; meets current filtering needs; unblocks P3 | Limited query flexibility; manual CSV filtering             |
| **Option C: NetCDF (GOA-ON)** | NetCDF export following GOA-ON template with CF conventions                             | International standard; self-describing; interoperable; GOA-ON compatible   | Requires netCDF4/xarray; schema design effort               |

### Decision

**Selected: Option C — NetCDF (GOA-ON Template)** **Rationale**: GOA-ON
compatibility is a hard requirement for Nadia (P3.3); NetCDF with CF
conventions is the international standard for oceanographic data exchange;
self-describing format eliminates separate metadata manifests; unblocks P3
export design immediately. **Supersedes**: Previous Option B decision (File
Manifest). **Decider**: Lead + Prof. Adjei ✅ **Implemented in**: P3 (Week
10-11), `src/oa_pipeline/export.py` + `oa-pipeline export` CLI

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
**Implemented in**: `src/oa_pipeline/carbonate_calc.py` wrapper

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

**Decision**: Core logic in `src/oa_pipeline/`; CLI (`run_pipeline.sh`), GUI
(`tools/oa_pipeline_app.py`), Notebooks (`notebooks/`) all call same core.
**Decider**: Council review / ADR-0010 ✅ **Implemented in**: P-1 migration
(Week 1-2)

---

## 8. Data Standard: Frontiers 2021

**Decision**: Canonical schema = Frontiers 2021 clarified headers; 0–9 QC flags;
`-999` missing sentinel. **Deviations**: Document in `docs/schema-deviations.md`
if any. **Decider**: ADR-0009 ✅ **Implemented in**: P2 (Week 7-9),
`src/oa_pipeline/schema.py`

---

## 9. Invariant Testing (ADR-0003)

**Decision**: Per-stage invariant test in CI — snapshot input columns → run
stage → assert untargeted columns byte-identical. **Decider**: Council review ✅
**Implemented in**: P0 (Week 3-4), `tests/test_invariants.py`

---

## 10. Config Compatibility Gate (P1.2)

**Decision**: `compatible_pipeline_version` in config YAML enforced at runtime —
stale config fails fast. **Decider**: Epic / PRD ✅ **Implemented in**: P1 (Week
5-6), `src/oa_pipeline/common.py`

---

## Related Documents

- [Council Review of Epic Plan](council-review.md)
- [Architecture Decision Records](adrs.md)
- [Prototype Migration Plan](migration-plan.md)
- [AI-Friendly PRD](../project/ai-prd.md)
- [Implementation Design](../../superpowers/specs/2026-10-05-roap-v1-implementation-design.md)
- [Implementation Plan](../../superpowers/plans/2026-10-05-roap-v1-implementation-plan.md)
