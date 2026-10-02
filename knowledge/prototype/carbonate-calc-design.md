---
type: Fact
title: Carbonate Calculation Design
description: "RM correction before PyCO2SYS, input pair TA+pH, project default constants (Lueker 2000, Total scale), in-situ vs measurement conditions, vectorized batch usage"
tags: [carbonate-calc, pyco2sys, rm-correction, design, constants]
generated: { by: agent/cli, at: "2026-10-02T05:39:50Z" }
status: stable
---

# Carbonate Calculation Design

## Problem: RM Correction Applied After Chemistry

Current workflow defect:
1. Compute TA in alkalinity spreadsheet
2. Paste raw TA + measured pH into CO2SYS Excel → computes DIC, pCO2, Omega_ar, Omega_ca
3. Pipeline ingests computed chemistry, THEN computes RM correction to TA

Result: Chemistry based on raw TA, but `ta_best_umolkg` in final table is corrected TA. Internal inconsistency confirmed on J1-C1-N6: `ta_best_umolkg` = 2163.83 (corrected) but `omega_ar` = 3.02 computed from raw TA = 2173.60.

GOA-ON Cookbook: TA should be RM-corrected BEFORE entering CO2SYS.

## New Order of Operations

1. Ingest raw measured TA and measured pH (+ salinity, temperatures, pressure)
2. **RM-correct TA** (and tris-correct pH where applicable) — pipeline already computes these
3. **Compute carbonate system with PyCO2SYS** from corrected TA + pH
4. Everything downstream uses internally-computed, correction-consistent values

Benefits: genuinely reproducible end-to-end, no manual Excel step, exact constants pinned in code.

## Input Pair: TA and pH (par types 1 and 3)

PyCO2SYS solves from any two known parameters. Measured: total alkalinity and spectrophotometric pH.

- par1_type=1 (TA in µmol/kg)
- par2_type=3 (pH on total scale)

## Configuration Constants (Project Defaults)

| Parameter | Value | Source |
|-----------|-------|--------|
| opt_k_carbonic | 10 (Lueker et al. 2000) | OA-Africa/GOA-ON comparability |
| opt_k_bisulfate | 1 (Dickson 1990) | Standard |
| opt_k_fluoride | 1 (Perez & Fraga 1987) | Standard |
| opt_k_borate | 1 (Lee et al. 2010) | Standard |
| opt_pH_scale | 1 (Total scale) | Project default |

## In-Situ vs Measurement Conditions

- Input: laboratory measurement temperature
- Output: in-situ temperature and pressure (so Ω reflects benthic conditions)
- PyCO2SYS distinguishes with `_out` suffix fields

## Vectorized Batch Usage

- Accept arrays/pandas Series for all parameters
- Batch entire datasets through one call (faster, prevents inconsistent settings across rows)
- Never loop row-by-row
