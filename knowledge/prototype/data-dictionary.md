---
type: Fact
title: Input Data Dictionary
description: "Row classification by sample_tag prefix, column aliases, accepted values, required columns, CRM batches, range bounds"
tags: [data-dictionary, schema, aliases, crm, validation, ranges]
generated: { by: agent/cli, at: "2026-10-02T00:40:29Z" }
status: stable
---

# Data Dictionary: Input Contract

## Critical Rule: Row Classification by sample_tag Prefix
**Primary detection mechanism** (ADR-0006):
- CRM rows: sample_tag starts with "RM" (e.g., RM213_1) → used for TA correction
- pH standard rows: sample_tag starts with "tris" (or "amp"/"bis") → used for pH correction
- Sample rows: sample_type = "sample" → appear in final analysis_ready.csv

sample_type column is secondary cross-check only (opt-in via ALLOW_CRM_FLAG_COL).

## Column Aliases (Canonical Candidates)
Schema resolves workbook headers to canonical names via alias map in schema.py. First match wins.

Key canonical groups:
- **Identity**: record_id (sample_tag), sample_id, cruise_id, transect_id, station_id, depth_m, sample_type, collection_mode, replicate_id, sample_date, latitude_deg, longitude_deg
- **Hydrography**: temperature_measurement_c, temperature_insitu_c, salinity, pressure_measurement_dbar, pressure_output_dbar
- **Carbonate**: ta_umol_kg, ph_observed, ph_calculated, dic_calculated_umol_kg, pco2_calc_uatm, co2aq_calc_umol_kg, hco3_calc_umol_kg, co3_calc_umol_kg, omega_calcite_calc, omega_aragonite_calc, revelle_factor_calc
- **Nutrients**: oxygen_umol_l, nitrate_nitrite_umol_l, phosphate_umol_l, silicate_umol_l, chlorophyll
- **Units/Scales/QC**: ta_units, ph_scale_observed, ph_scale_calculated, ta_qc_status, ph_qc_status, phstd_status

## Accepted Values
- pH scales: total, seawater, free, nbs (normalized to canonical)
- TA units: umol/kg, UMOLKG, umolkg-1, µmol/kg, etc. → normalized to "umol kg-1"
- sample_type: sample, crm, std (case-insensitive)

## Minimum Required Columns
- Identity: record_id, sample_id, sample_date
- Station: cruise_id, transect_id, station_id, depth_m, latitude_deg, longitude_deg
- Hydrography: temperature_insitu_c, salinity
- Carbonate minimum: ta_umol_kg, ph_observed

## CRM Certified Batches (configs/crm_certified_values.yaml)
Dickson batches: 180, 195, 200, 205, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225
Pipeline stops with clear error if CRM_BATCH not in file.

## Plausible Range Bounds
| Variable | Min | Max |
|----------|-----|-----|
| Salinity | 0.0 | 42.0 |
| TA (µmol/kg) | 1000.0 | 3000.0 |
| pH | 7.0 | 9.0 |
| Depth (m) | 0.0 | 12000.0 |
| Latitude | -90.0 | 90.0 |
| Longitude | -180.0 | 180.0 |
