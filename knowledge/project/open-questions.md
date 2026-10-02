---
type: Fact
title: Open Questions for Engineering
description: "8 open questions: queryable layer scope (gates P3), PyCO2SYS version, real dataset access, GPG signing, PyPI publishing, cross-platform vs export, wider codebase, data volume"
tags: [open-questions, adr, pyco2sys, dataset, gpg, pypi, sequencing, performance]
generated: { by: agent/cli, at: "2026-10-02T00:44:29Z" }
status: stable
---

# Open Questions for Engineering

## 1. Queryable Layer Scope (ADR-0001) - GATES P3
**Question**: DuckDB (Option A) vs File-based manifest (Option B)?
- Option A: `oa-pipeline ingest RUN_DIR` → DB; SQL query interface
- Option B: `archive/<cruise>/analysis_ready.csv` + `manifest.csv`; pandas/duckdb on files
**Decider**: Lead + Prof. Adjei
**Criteria**: Team capacity, Nadia's timeline, Fatou's reuse needs, maintenance burden
**Blocks**: P3 export design (GOA-ON structure differs fundamentally)

## 2. PyCO2SYS Version
**Question**: v1 stable vs v2 beta?
- v1: Stable, known behavior
- v2: Faster, improved usability, but beta
**Need**: Confirm default constants (opt_k_carbonic=10, opt_pH_scale=1) with Prof. Mahu's group

## 3. Real Dataset Access
**Question**: April 2026 dataset location and access protocol for manual regression?
- 38 samples → expected 22 PASS, 16 REVIEW, 0 FAIL
- Unpublished - not in CI
- Required before every release
**Need**: Document exact process in docs/manual-regression.md

## 4. GPG Signing
**Question**: Sign release tags with GPG?
- Requires key setup
- Adds trust to releases

## 5. PyPI Publishing
**Question**: Automated via GitHub Actions or manual?
- Need org/account ready
- Part of release checklist (RELEASE.md)

## 6. Cross-Platform vs Export Sequencing
**Question**: Two capabilities software lacks entirely (US-19, US-20). Which first?
**Decision**: Cross-platform CI first (P0), then GOA-ON export (P3 after P4) - per ADR-0002

## 7. Wider Codebase Context
**Question**: This pipeline is 1 of 4 related codebases (CTD/nitrate, CTD-bottle matching, predictive modelling, orchestration). Does wider setting affect sequencing?
**Status**: Stories kept to OA pipeline alone for now.

## 8. Data Volume / Performance
**Question**: Typical cruise <100 bottles. Full archive small. Is performance/scale engineering needed?
**Status**: Likely not for v1.0.0.
