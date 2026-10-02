---
type: Fact
title: PyCO2SYS Usage Reference
description: "Parameter type codes, key options (Lueker 2000, Total scale), in-situ vs measurement conditions, vectorized batch usage, ROAP integration pattern"
tags: [pyco2sys, parameter-codes, vectorized, provenance, integration]
generated: { by: agent/cli, at: "2026-10-02T00:39:06Z" }
status: stable
---

# PyCO2SYS Usage Guide

## Core Function
pyco2.sys(...) - single vectorized entry point for marine carbonate system calculations.

## Parameter Type Codes (par1_type, par2_type)
| Code | Parameter Pair |
|------|----------------|
| 1 | TA, DIC |
| 2 | TA, pH |
| 3 | TA, pCO₂ |
| 4 | TA, fCO₂ |
| 5 | TA, CO₃²⁻ |
| 6 | TA, HCO₃⁻ |
| 7 | DIC, pH |
| 8 | DIC, pCO₂ |
| 9 | DIC, fCO₂ |
| 10 | DIC, CO₃²⁻ |
| 11 | DIC, HCO₃⁻ |
| 12 | pH, pCO₂ |
| 13 | pH, fCO₂ |
| 14 | pH, CO₃²⁻ |
| 15 | pH, HCO₃⁻ |
| 16 | pCO₂, fCO₂ |
| 17 | pCO₂, CO₃²⁻ |
| 18 | pCO₂, HCO₃⁻ |
| 19 | fCO₂, CO₃²⁻ |
| 20 | fCO₂, HCO₃⁻ |
| 21 | CO₃²⁻, HCO₃⁻ |

## Key Options
- **opt_k_carbonic**: 10 = Lueker et al. 2000 (project default for OA-Africa/GOA-ON comparability)
- **opt_pH_scale**: 1 = Total scale (project default)
- **opt_k_bisulfate**: 1 = Dickson
- **opt_k_fluoride**: 1 = PerezFraga1987
- **opt_k_borate**: 1 = Lee2010

## In-Situ vs Measurement Conditions
- Samples measured at lab temperature but reported at in-situ (seafloor) temperature
- PyCO2SYS distinguishes explicitly with _out suffix fields
- Conflating them = classic quiet mistake
- This project: record carbonate_output_temperature provenance field

## Vectorized Batch Usage
- Accepts arrays/pandas Series for all parameters
- Batch entire datasets through one call (faster, prevents inconsistent settings across rows)
- Never loop row-by-row

## Integration Pattern for ROAP
- Pipeline does NOT run PyCO2SYS internally
- Calculated carbonate fields expected in input workbook or generated upstream
- Pipeline audits fields and requires provenance columns:
  - carbonate_solver
  - carbon_input_pair_used
  - carbonate_constants
  - carbonate_ph_scale
  - carbonate_output_temperature
- Helper script stamp_carbonate_provenance.py writes provenance to new workbook
