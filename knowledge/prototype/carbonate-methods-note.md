---
type: Fact
title: "Carbonate Methods & QC Validation"
description: "Methods section for manuscript: constants used, RM correction (batch 213), tris buffer QC, measured vs calculated pH validation (temp effect r=-1.00, slope -0.0165/°C)"
tags: [carbonate-methods, qc-validation, manuscript, constants, tris-buffer]
generated: { by: agent/cli, at: "2026-10-02T05:40:02Z" }
status: stable
---

# Carbonate System Methods & QC Validation Note

## Methods Section (Carbonate Chemistry)

Carbonate system parameters calculated from total alkalinity (TA) and spectrophotometric pH (total scale) using CO2SYS program (v25b06, Excel implementation). Calculations used:
- Carbonic acid dissociation constants: Lueker et al. (2000)
- Bisulfate dissociation constant: Dickson (1990)
- Hydrogen fluoride constant: Perez and Fraga (1987)
- Boron-to-salinity ratio: Lee et al. (2010)

Input conditions: laboratory measurement temperature
Output parameters (including CO2(aq), bicarbonate, carbonate ion, DIC, pCO2, Ω_ca, Ω_ar): computed at in situ temperature and pressure

Total alkalinity quality-controlled against certified reference material (Dickson CRM batch 213); alkalinity correction applied per laboratory SOP.

Spectrophotometric pH measurements checked against tris buffer standards (n=8) prepared and measured across working temperature range; mean standard residual within acceptance threshold (|Δ| < 0.02 pH units), confirming electrode performance.

## QC Validation Note (Internal — Measured vs Calculated pH)

Directly measured pH (reported at laboratory temperature) compared with CO2SYS-derived pH (reported at in situ temperature). Mean difference: 0.06 pH units.

Offset fully explained by temperature difference between laboratory and in situ conditions:
- pH difference and laboratory-minus-in-situ temperature difference perfectly anti-correlated (r = -1.00, n = 38)
- Implied slope: -0.0165 pH units per degree Celsius
- Consistent with known thermodynamic temperature sensitivity of seawater pH (~ -0.015 to -0.017 pH units/°C)
- No residual scale or measurement discrepancy after accounting for temperature

For downstream ecological analysis: in situ-referenced calculated parameters (Ω_ar, Ω_ca, pCO2) used, as these represent chemical environment relevant to organisms.

## Reference List
- Lueker et al. (2000)
- Dickson (1990)
- Perez & Fraga (1987)
- Lee et al. (2010)
- Dickson et al. (2007) SOP 22/23
- GOA-ON Ocean Acidification Cookbook
