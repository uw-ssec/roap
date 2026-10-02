---
type: Requirement
title: ROAP v1.0.0 Epic Delivery Plan
description: Revised priority matrix with P-1 migration blocking all work
tags: [epic, priority, council-review]
generated: { by: agent/cli, at: "2026-10-02T00:45:04Z" }
status: stable
---

# Epic: ROAP v1.0.0 Delivery Plan

## Revised Priority Matrix (Post-Council Review)

| Priority | Theme | Personas Served | Rationale |
|----------|-------|-----------------|-----------|
| P-1 | Prototype Migration (BLOCKING) | All | Code must exist in this repo before CI, packaging, or schema work |
| P0 | Cross-Platform CI + Invariant Test + Entry Point | Ruu, Kofi, Nadia, Ama | CI is meaningless without invariant test (lat/lon bug survived 221 tests) |
| P1 | Packaging, Releases, Version Pinning, Run Bundles | Fatou, Prof. Adjei, Nadia | Citable releases + config compatibility gate + reproducible run records |
| P2 | Schema/Provenance/CRM/Excel Fixes + Property-Based Testing | Ama, Fatou, Prof. Adjei, Kofi | Core reproducibility + fix structural bugs missing from original plan |
| P4 | ADR: Queryable Time-Series Layer Scope (GATE for P3) | Nadia, Ama | Must decide before designing P3 export (DB vs file changes everything) |
| P3 | International Export + Pre-Flight Validation | Nadia, Kofi | GOA-ON export + no-code validation for Kofi (after P4 decision) |

## Critical Finding from Council Review
This repository (roap) is a project template. The actual oa_pipeline v0.2.0 codebase lives in local/prototype/my_understanding/test/oa_pipeline/ with its own .git/, .venv_run/, 221 tests, 8 notebooks, and src/oa_pipeline/ modules. Zero P0-P4 work can begin until the prototype is migrated into this repo.

# Related Concepts
- [Council Review of Epic Plan](../decisions/council-review.md): Council review reshaped the epic priorities
- [Prototype Migration Plan](../decisions/migration-plan.md): Migration plan details the P-1 blocking phase from epic
- [Architecture Decision Records](../decisions/adrs.md): ADRs document architecture decisions for epic implementation
