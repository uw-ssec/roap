---
type: Fact
title: Detailed Project Overview
description: "Mission, problem, solution, 6 personas, current state (prototype v0.2.0), target (v1.0.0), success metrics"
tags: [project, overview, mission, personas, success-metrics]
generated: { by: agent/cli, at: "2026-10-02T00:41:32Z" }
status: stable
---

# Project Context: Project Overview

## Mission
Build a reproducible, production-grade ocean acidification data processing platform that serves the OA-Africa network and GOA-ON community.

## Problem
Ocean acidification data from different labs/cruises uses inconsistent column names, QC practices, and provenance recording. Two labs with identical raw measurements can produce different saturation state (Ω) results due to undocumented choices in equilibrium constants, pH scale, temperature reference, and nutrient inclusion.

## Solution
ROAP enforces Frontiers 2021 data standards, wraps PyCO2SYS as the math engine, requires full provenance on every derived value, and provides three interfaces (CLI, GUI, Notebooks) calling the same core pipeline.

## Target Users (Personas)
1. **Ruu** (Trainee) - Clean laptop to successful run in <1 hour
2. **Kofi** (Technician) - Excel-only workflow, no terminal, validates bench sheets
3. **Ama** (Analyst) - Configurable QC, figure provenance, replicate analysis
4. **Fatou** (Regional Partner) - Config-driven column mapping for multi-year archives
5. **Nadia** (Data Manager) - Quarterly unattended runs, GOA-ON export, time series
6. **Prof. Adjei** (PI) - Sign-off summaries, archived run bundles, citable releases

## Current State
- Prototype: oa_pipeline v0.2.0 (221 tests, 8 notebooks, Windows-only)
- Target: ROAP v1.0.0 (cross-platform, packaged, citable, reproducible)
- Blocker: Prototype not yet migrated to this repo (P-1 phase)

## Success Metrics (v1.0.0)
- Onboarding <1 hour on clean laptop
- 100% cross-platform CI pass rate
- Invariant test catches column mutation bugs
- Frontiers 2021 schema compliance
- Config-driven adoption for regional partners
- pip install oa-pipeline==1.0.0 works
- Manual regression: April 2026 dataset → 22 PASS, 16 REVIEW, 0 FAIL
