# Frontiers 2021 Data Standard — Quick Reference

Source: `.agents/skills/data-standard/`  
Paper: https://www.frontiersin.org/articles/10.3389/fmars.2021.705638

---

## Three Key Adoptions

### 1. Column Headers — Clarified Names
Replace WOCE abbreviations with human-readable names:

| WOCE | Frontiers | ROAP Canonical |
|------|-----------|----------------|
| SILCAT | Silicate | silicate_umol_l |
| NH4 | Ammonium | ammonium_umol_l |
| PHSPHT | Phosphate | phosphate_umol_l |
| NTRZ | Nitrate+Nitrite | nitrate_nitrite_umol_l |
| OXYGEN | Oxygen | oxygen_umol_l |
| CHLA | Chlorophyll | chlorophyll_umol_l |
| ALKALI | Total Alkalinity | ta_umol_kg |
| TCARB | DIC | dic_calculated_umol_kg |
| PH_TOT | pH (Total) | ph_observed + ph_scale_observed |

**ROAP:** `schema.py` `canonical_candidates` maps aliases → canonical. Config-driven override via `schema_aliases.yaml`.

---

### 2. QC Flags — Unified 0-9 Scale

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

**ROAP:** Every numeric measurement → `*_qc_flag` (0-9). Default: 2 (acceptable) or 9 (missing). Not yet fully implemented (P2.4).

---

### 3. Missing Values — Universal Sentinel

| Type | Sentinel |
|------|----------|
| Numeric | `-999` |
| Text | `-999` (or empty string) |
| **Never** | `NaN`, `NA`, `N/A`, `null`, `None`, empty string (numeric) |

**ROAP:** Export normalizes to `-999`. Input accepts blanks/`NA`/`NaN` → converts on export.

---

## Provenance Metadata (Beyond Frontiers)

Frontiers covers *data*; ROAP adds *provenance* for reproducibility:

| Field | Example |
|-------|---------|
| `carbonate_solver` | `PyCO2SYS_v2.1` |
| `carbon_input_pair_used` | `TA_pH` |
| `carbonate_constants` | `Lueker2000;KSO4_Dickson;KF_PerezFraga1987;B_Lee2010` |
| `carbonate_ph_scale` | `total` |
| `carbonate_output_temperature` | `in_situ` |
| `code_version` | `1.0.0` |
| `run_timestamp` | `2026-09-29T14:30:00Z` |
| `input_checksum` | `sha256:...` |

**Required on every sample row with derived carbonate values.** Missing → Stage 4 FAIL.

---

## Schema Versioning

- Outputs carry `schema_version` (e.g., `2024.1`)
- Configs carry `compatible_pipeline_version` (e.g., `>=0.2.0`)
- Pipeline refuses to run if config pin incompatible

---

## ROAP Implementation Status

| Feature | Status |
|---------|--------|
| Clarified column names | Partial (P2.1 audit needed) |
| 0-9 QC flags | Not yet (P2.4) |
| `-999` missing values | Partial (P2) |
| Provenance columns | Yes (Stage 4 enforces) |
| Config-driven aliases | Designed (P2.2), not implemented |
| Schema versioning | Partial |

---

## GOA-ON Compatibility

Adopting Frontiers 2021 buys **GOA-ON data-portal compatibility** — export format should target this alignment (P3.3).

---

## References

- `.agents/skills/data-standard/references/qc-flags-and-columns.md` — Full tables
- `local/project-context/data-standards.md` — Detailed ROAP implementation