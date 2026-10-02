---
type: Fact
title: Personas Summary
description: "Six personas (Ruu, Kofi, Ama, Fatou, Nadia, Prof. Adjei) with goals, pains, mapped stories, and priority epics"
tags: [personas, summary, ruu, kofi, ama, fatou, nadia, adjei]
generated: { by: agent/cli, at: "2026-10-02T00:44:04Z" }
status: stable
---

# Personas Summary

## Six Personas

### Ruu (Trainee)
- **Goal**: Clean laptop → successful run on example data in <1 hour
- **Pain**: Environment setup, confusing entry points, Windows-only
- **Stories**: US-16 (onboarding), US-19 (cross-platform)
- **Priority**: P0

### Kofi (Technician)
- **Goal**: Validate bench sheet in Excel without terminal; run standard workflow from simple interface
- **Pain**: Excel round-trip bug blanks formula columns; no pre-flight validation
- **Stories**: US-02 (pre-flight validation), US-03 (no write-back), US-14 (GUI plotting), US-17 (simple interface)
- **Priority**: P0 (entry), P3 (validation)

### Ama (Analyst)
- **Goal**: Configurable QC thresholds, replicate analysis with measured values, figure provenance, query subsets
- **Pain**: Hardcoded thresholds, averaged-away replicates, manual figure rebuilding
- **Stories**: US-04 (replicate flags), US-05 (CRM offset visibility), US-07 (config thresholds), US-08 (provenance), US-11/12/13 (figures), US-24 (query subsets)
- **Priority**: P1 (provenance), P2 (schema/figures), P4 (queryable)

### Fatou (Regional Partner)
- **Goal**: Map 3-year archive columns via config (schema_aliases.yaml), citable tagged releases, regionally comparable results
- **Pain**: Manual column renaming, moving branch not citable
- **Stories**: US-01 (config-driven aliases), US-09 (regenerate from config), US-22 (citable release)
- **Priority**: P1 (packaging), P2 (schema aliases)

### Nadia (Data Manager)
- **Goal**: Quarterly unattended runs, GOA-ON export, continuous station time series, consistent QC
- **Pain**: Manual reformatting for GOA-ON, no time series accumulation, colleague can't run it
- **Stories**: US-18 (unattended runs), US-20 (GOA-ON export), US-21 (archived run bundles), US-23 (time series)
- **Priority**: P1 (run bundles), P3 (export), P4 (time series)

### Prof. Adjei (PI)
- **Goal**: Readable run summaries for sign-off, archived run bundles for reproducibility, citable versions
- **Pain**: No run summary, can't reconstruct analysis after student graduates
- **Stories**: US-06 (run summary), US-10 (config gate), US-15 (figure provenance), US-21 (archived bundles), US-22 (citable release)
- **Priority**: P1 (packaging/run bundles)
