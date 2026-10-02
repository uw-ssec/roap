---
type: Architecture
title: ROAP Project Overview
description: Production-grade OA pipeline from research prototype
tags: [project, overview, architecture]
generated: { by: agent/cli, at: "2026-10-02T00:45:42Z" }
status: stable
---

# ROAP Project Overview

The Reproducible Ocean Acidification Pipeline (ROAP) transforms the oa_pipeline v0.2.0 research prototype into a production-grade, cross-platform, citable platform for ocean acidification carbonate chemistry quality control and processing.

## Key Objectives
- Enforce Frontiers 2021 data standards (clarified column names, unified 0-9 QC flags, -999 missing sentinel)
- Full provenance tagging on every derived carbonate value
- Reproducible runs via version-pinned releases, config compatibility gates, immutable run bundles
- Serve six personas: Ruu (trainee), Kofi (technician), Ama (analyst), Fatou (regional partner), Nadia (data manager), Prof. Adjei (PI)

## North Star
Fresh clone -> pixi install -> pixi run pipeline examples/example_data.xlsx outputs/test -> analysis_ready.csv with expected 4 FAIL verdicts in <10 min on Linux, macOS, and Windows.

# Related Concepts
- [ROAP v1.0.0 Epic Delivery Plan](epic.md): Epic details the delivery plan for the project overview
- [AI-Friendly PRD](ai-prd.md): AI-PRD is the detailed requirements document for the project
- [Detailed Project Overview](overview-detailed.md): Detailed overview expands on the project overview
