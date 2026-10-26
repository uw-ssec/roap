---
type: Decision
title: Architecture Decision Records
description:
  "11 ADRs covering queryable layer, CI, invariant test, config aliases, Excel
  round-trip, CRM detection, property testing, regression gate, Frontiers 2021,
  single engine, notebooks as thin doors"
tags: [adr, architecture, decisions]
generated: { by: agent/cli, at: "2026-10-02T00:45:10Z" }
status: stable
---

# Architecture Decision Records (ADRs)

## ADR Index

| ID   | Title                                               | Status                      | Date       | Deciders          |
| ---- | --------------------------------------------------- | --------------------------- | ---------- | ----------------- |
| 0001 | Queryable Time-Series Layer Scope                   | Accepted (Option C: NetCDF) | 2026-10-09 | Lead, Prof. Adjei |
| 0002 | Cross-Platform CI Before GOA-ON Export              | Proposed                    | 2026-09-29 | Lead              |
| 0003 | Invariant Test in CI (Not Post-CI)                  | Accepted                    | 2026-09-29 | Lead              |
| 0004 | Config-Driven Schema Aliases                        | Proposed                    | -          | Lead, Fatou input |
| 0005 | Excel Round-Trip: Pandas Read/Write Only            | Proposed                    | -          | Lead              |
| 0006 | CRM/Std Detection by Tag Prefix Only                | Accepted                    | 2026-09-29 | Lead, Maurice     |
| 0007 | Property-Based Testing for Schema/Normalization     | Proposed                    | -          | Lead              |
| 0008 | Real Dataset as Manual Regression Gate              | Accepted                    | 2026-09-29 | Lead              |
| 0009 | Frontiers 2021 as Default Schema Standard           | Accepted                    | 2026-09-29 | Lead              |
| 0010 | Single Engine, Three Doors (CLI/GUI/Notebook)       | Accepted                    | 2026-09-29 | Lead              |
| 0011 | Notebooks Are Thin Doors; No Papermill on Main Path | Accepted                    | 2026-10-26 | Lead              |

## Key Accepted Decisions

- **ADR-0003**: Invariant test runs IN CI on every PR - catches lat/lon
  overwrite bug class
- **ADR-0006**: Tag prefix is primary detection mechanism for CRM/standard rows,
  NOT sample_type column
- **ADR-0008**: Manual regression gate before every release on April 2026
  dataset (22 PASS, 16 REVIEW, 0 FAIL)
- **ADR-0009**: Frontiers 2021 as default schema standard - clarified column
  names, 0-9 QC flags, -999 missing values
- **ADR-0001**: Queryable layer scope resolved as **Option C - NetCDF (GOA-ON
  template, CF conventions)**, superseding the earlier Option B (File Manifest).
  See `engineering-decisions.md` S1.
- **ADR-0010**: Single engine (src/roap/), three doors (CLI, GUI, Notebook) -
  all call same core
- **ADR-0011**: Each Stage exposes `run(inputs, config) -> StageResult` and
  `roap.pipeline.run_pipeline` owns Stage ordering and the output layout. CLI,
  GUI and `run_pipeline.sh` call it in-process; notebooks 02-08 only call their
  Stage's `run` and add human-facing views. Papermill leaves the main path.
  _Why_: notebooks had become the de facto orchestrator (step order, config
  merging, file names copied per notebook), which made ADR-0010's "one engine"
  untrue, let config precedence drift per door, and forced every stage-level
  test through slow subprocess runs. _Rejected_: keeping papermill as the
  orchestrator with `run` called inside each notebook (keeps Jupyter as a hidden
  part of every run's interface); retiring notebooks entirely (loses the
  per-Stage human view).

## Pending Decisions

- **ADR-0004**: Config-driven schema aliases via schema_aliases.yaml
- **ADR-0005**: Excel round-trip fix - never use openpyxl for read-modify-write
  on formula-bearing workbooks
- **ADR-0007**: Property-based testing with hypothesis for alias resolution,
  unit normalization, schema application

# Related Concepts

- [Council Review of Epic Plan](council-review.md): Council review led to new
  ADRs being created
