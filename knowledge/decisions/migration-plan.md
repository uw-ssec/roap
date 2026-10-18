---
type: Decision
title: Prototype Migration Plan
description:
  "P-1 blocking phase: copy prototype code, tests, configs, examples; create
  pyproject.toml; extract CLI; verify 221+ tests pass"
tags: [migration, p1, prototype]
generated: { by: agent/cli, at: "2026-10-02T00:45:56Z" }
updated: { by: agent/cli, at: "2026-10-10T00:00:00Z" }
status: complete-with-caveats
---

# Migration Plan: Prototype to Production Repo

## Source

local/prototype/my_understanding/test/oa_pipeline/ (git submodule at
references/prototype/oa_pipeline/)

## Target Structure (Actual — Renamed to `roap`)

roap/ ├── src/roap/ (12 modules from prototype, renamed from oa_pipeline) ├──
tests/ (329 tests collected, exceeds 221 target) ├── examples/
(make_example_data.py, example_data.xlsx) ├── configs/ (all 7 YAML configs) ├──
notebooks/ (11 Papermill notebooks) ├── tools/ (roap_app.py, roap_app_core.py,
stamp_carbonate_provenance.py) ├── pyproject.toml (src-layout package definition
for `roap` v0.2.0) └── run_pipeline.sh (verified working)

## Migration Tasks (P-1)

- ✅ **P-1.1**: Copy src/oa_pipeline/ → src/roap/ (12 modules, all imports
  updated)
- ✅ **P-1.2**: Copy tests/ → tests/ (373 passing; 1 failing by design — see
  P-1.7)
- ✅ **P-1.3**: Copy examples/ → examples/ (make_example_data.py,
  example_data.xlsx)
- ✅ **P-1.4**: Copy configs/ → configs/ (all 7 YAML configs including
  07_stage3.yaml with ph_diag_harmonize_temperature: true)
- ✅ **P-1.5**: Create pyproject.toml for roap package (src-layout, v0.2.0)
- ✅ **P-1.6**: Extract notebook orchestration → CLI entry points. Typer
  scaffold, `roap` console script, and both subcommands (`validate`,
  `verify-bundle`) **fully implemented** (2026-10-11, `src/roap/cli.py`,
  `src/roap/bundle.py`).
- ✅ **P-1.7**: Add .gitignore entry for Unpublished data (runs/, outputs/,
  .pytest_runs/)
- ✅ **P-1.8**: Verify: pixi install → pytest -q (373 pass, 1 by-design fail)
  → ./run_pipeline.sh on synthetic data → 4 non-PASS verdicts
  (16 PASS / 3 FAIL / 1 REVIEW), ~34s

## Success Criteria

- ✅ src/roap/ exists with all 12 modules (**init**.py, common.py, schema.py,
  qc_ta_ph.py, stage1b.py, stage2.py, stage3.py, stage4.py, policy.py,
  inspect.py, carbonate_calc.py, duplicate_precision.py)
- ✅ tests/ has 373 passing tests (exceeds 221+ target)
- ✅ examples/example_data.xlsx exists and regenerates via make_example_data.py
- ✅ configs/ has all YAML configs including 07_stage3.yaml with
  ph_diag_harmonize_temperature: true
- ✅ ./run_pipeline.sh works end-to-end on synthetic data (37s full pipeline)
- ⚠️ Unpublished data NOT in **this repo's** git history — verified by
  scanning every blob in `551a51b..HEAD`. However
  `test_no_unpublished_data.py::test_prototype_submodule_has_no_stored_outputs`
  **fails by design**: the pinned upstream submodule
  (`reez-png/oa_pipeline@3d125b3`, public) carries executed notebook outputs
  embedding real measurements. We hold read-only access; raised with the
  collaborator.

## Key Decisions Made During Migration

1. **Package rename**: `oa-pipeline` → `roap` (aligns with project name ROAP =
   Reproducible Ocean Acidification Pipeline)
2. **CLI implementation**: Added typer-based `roap` command with `validate` and
   `verify-bundle` subcommands (P-1.6 complete)
3. **GUI rename**: `oa_pipeline_app.py` → `roap_app.py`,
   `oa_pipeline_app_core.py` → `roap_app_core.py`
4. **Notebook updates**: All 11 notebooks updated from `from oa_pipeline.*` to
   `from roap.*`
5. **Test updates**: All 329 tests updated to import from `roap` package
5. **Pixi tasks**: Fixed `pipeline` task to use `./run_pipeline.sh`; `validate`
   and `verify-bundle` now use `roap` CLI
6. **History restoration**: Squash-merged PRs (#26, #28, #31, #32) were
   deconstructed; 44 individual commits restored to `main` via force-push
   (2026-10-18). Backup branch `backup-main` created at original mega-commit
   (`463f2a9`). Feature branches preserved for reference.

## GitHub Issues Resolved (P-1 Migration)

| Issue | Title                                                                       | Status  |
| ----- | --------------------------------------------------------------------------- | ------- |
| #6    | feat(p1): Package setup — pyproject.toml, pixi.toml tasks                   | ⚠️ Partial (stub CLI) |
| #7    | feat(p1): Core modules — migrate src/oa_pipeline/ (12 modules)              | ✅ Done |
| #8    | test(p1): Tests & configs — migrate tests/, configs/, examples/, notebooks/ | ✅ Done |
| #9    | feat(p1): CLI & GUI — migrate run_pipeline.sh, app, stamp scripts           | ⚠️ Partial (stub CLI) |
| #10   | test(p1): Verification — no unpublished data, full pipeline E2E             | ✅ Done (submodule exposure escalated) |

## Related Concepts

- [Prototype Pipeline Overview](../prototype/pipeline-overview.md): Migration
  plan copies the prototype pipeline to this repo
- [Prototype Git Submodule](../prototype/git-submodule.md): Migration plan uses
  the git submodule as source
- [Engineering Decisions](engineering-decisions.md): Records the package rename
  and CLI framework choice
