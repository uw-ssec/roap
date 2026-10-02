---
type: Decision
title: Prototype Migration Plan
description: "P-1 blocking phase: copy prototype code, tests, configs, examples; create pyproject.toml; extract CLI; verify 221 tests pass"
tags: [migration, p1, prototype]
generated: { by: agent/cli, at: "2026-10-02T00:45:56Z" }
status: stable
---

# Migration Plan: Prototype to Production Repo

## Source
local/prototype/my_understanding/test/oa_pipeline/ (git submodule at references/prototype/oa_pipeline/)

## Target Structure
roap/
├── src/oa_pipeline/ (12 modules from prototype)
├── tests/ (221+ tests from prototype)
├── examples/ (make_example_data.py, example_data.xlsx)
├── configs/ (all YAML configs)
├── notebooks/ (8 Papermill notebooks)
├── tools/ (oa_pipeline_app.py, oa_pipeline_app_core.py, stamp_carbonate_provenance.py)
├── pyproject.toml (src-layout package definition)
└── run_pipeline.sh (verified working)

## Migration Tasks (P-1)
- P-1.1: Copy src/oa_pipeline/ → src/oa_pipeline/
- P-1.2: Copy tests/ → tests/ (all 221 tests)
- P-1.3: Copy examples/ → examples/
- P-1.4: Copy configs/ → configs/
- P-1.5: Create pyproject.toml for oa_pipeline package (src-layout)
- P-1.6: Extract notebook orchestration → CLI entry points (oa-pipeline command with typer/click)
- P-1.7: Add .gitignore entry for Unpublished data
- P-1.8: Verify: pixi install → pytest -q (221 pass) → ./run_pipeline.sh on synthetic data → 4 FAIL verdicts

## Success Criteria
- src/oa_pipeline/ exists with all 12 modules
- tests/ has 221+ passing tests
- examples/example_data.xlsx exists or regenerates
- configs/ has all YAML configs including 07_stage3.yaml with ph_diag_harmonize_temperature: true
- ./run_pipeline.sh works end-to-end on synthetic data
- Unpublished data NOT in git

# Related Concepts
- [Prototype Pipeline Overview](../prototype/pipeline-overview.md): Migration plan copies the prototype pipeline to this repo
- [Prototype Git Submodule](../prototype/git-submodule.md): Migration plan uses the git submodule as source
