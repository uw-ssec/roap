---
type: Fact
title: "Data Standards: Frontiers 2021"
description: "Clarified column names, unified 0-9 QC flags, -999 missing sentinel, provenance metadata, schema versioning"
tags: [data-standard, frontiers2021, qc-flags, provenance, goa-on]
generated: { by: agent/cli, at: "2026-10-02T00:45:31Z" }
status: stable
---

# Project Context: Data Standards

## Frontiers 2021 Best Practice Data Standard
Paper: https://www.frontiersin.org/articles/10.3389/fmars.2021.705638

## Three Key Adoptions for ROAP

### 1. Column Headers - Clarified Names
Replace WOCE abbreviations with human-readable names:
- SILCAT → Silicate → silicate_umol_l
- NH4 → Ammonium → ammonium_umol_l
- PHSPHT → Phosphate → phosphate_umol_l
- NTRZ → Nitrate+Nitrite → nitrate_nitrite_umol_l
- OXYGEN → Oxygen → oxygen_umol_l
- CHLA → Chlorophyll → chlorophyll_umol_l
- ALKALI → Total Alkalinity → ta_umol_kg
- TCARB → DIC → dic_calculated_umol_kg
- PH_TOT → pH (Total) → ph_observed + ph_scale_observed

ROAP Implementation: schema.py canonical_candidates maps aliases → canonical. Config-driven override via schema_aliases.yaml.

### 2. QC Flags - Unified 0-9 Scale
| Flag | Meaning | Replaces |
|------|---------|----------|
| 0 | Not evaluated | — |
| 1 | Good | WOCE 2 |
| 2 | Acceptable | WOCE 2/3 |
| 3 | Questionable | WOCE 3/4 |
| 4 | Bad | WOCE 4/5 |
| 5 | Changed | — |
| 6 | Below detection | — |
| 7 | Excessive value | — |
| 8 | Interpolated | — |
| 9 | Missing | WOCE 9 |

ROAP: Every numeric measurement → *_qc_flag (0-9). Default: 2 (acceptable) or 9 (missing). Not yet fully implemented (P2.4).

### 3. Missing Values - Universal Sentinel
- Numeric: -999
- Text: -999 (or empty string)
- Never: NaN, NA, N/A, null, None, empty string (numeric)

ROAP: Export normalizes to -999. Input accepts blanks/NA/NaN → converts on export.

## Provenance Metadata (Beyond Frontiers)
Required on every sample row with derived carbonate values:
- carbonate_solver (e.g., PyCO2SYS_v2.1)
- carbon_input_pair_used (e.g., TA_pH)
- carbonate_constants (e.g., Lueker2000;KSO4_Dickson;KF_PerezFraga1987;B_Lee2010)
- carbonate_ph_scale (e.g., total)
- carbonate_output_temperature (e.g., in_situ)
- code_version, run_timestamp, input_checksum

Missing → Stage 4 FAIL.

## Schema Versioning
- Outputs carry schema_version (e.g., 2024.1)
- Configs carry compatible_pipeline_version (e.g., >=0.2.0)
- Pipeline refuses to run if config pin incompatible

## GOA-ON Compatibility
Adopting Frontiers 2021 buys GOA-ON data-portal compatibility (P3.3 export target).

# Related Concepts
- [Reference Links](../references/links.md): Data standards reference external links
