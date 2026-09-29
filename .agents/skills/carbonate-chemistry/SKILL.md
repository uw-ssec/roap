---
name: carbonate-chemistry
description:
  Explains the marine carbonate system underlying ocean acidification research -
  the DIC/TA/pH/pCO2 four-parameter system, saturation states, and why
  equilibrium constant and pH-scale choices create reproducibility problems. Use
  when the user asks about "carbonate chemistry", "ocean acidification", "DIC",
  "TA", "total alkalinity", "dissolved inorganic carbon", "pH scale",
  "saturation state", "omega aragonite", "omega calcite", "Revelle factor",
  "equilibrium constants", "pCO2", "fCO2", or mentions why two labs get
  different results from the same raw data.
---

# Marine Carbonate Chemistry

## Source of truth

This `SKILL.md` and its `references/` subfolder are the current source of truth
for this domain. If a future dedicated domain-knowledge document is created,
update it and this skill together.

## The system

```
CO2 + H2O <-> H2CO3 <-> H+ + HCO3- <-> 2H+ + CO3--
```

More dissolved CO2 -> more H+ -> lower pH, and the equilibrium shifts away from
carbonate ion (CO3--), the building block organisms need to calcify (shells,
coral skeletons, plankton tests). That shift, not pH alone, is why saturation
state is usually the headline biological metric.

## The four measurable parameters

The system is fully defined by **any 2 of these 4**, plus salinity, temperature,
pressure, and optionally nutrients:

| Parameter   | Meaning                                         | Typical method                 |
| ----------- | ----------------------------------------------- | ------------------------------- |
| DIC         | Dissolved Inorganic Carbon: CO2 + HCO3- + CO3-- | Coulometry / infrared            |
| TA          | Total Alkalinity: acid-buffering capacity       | Titration                        |
| pH          | Hydrogen ion activity                           | Spectrophotometry / electrodes   |
| pCO2 / fCO2 | Partial / fugacity of CO2                       | Equilibration + IR/GC             |

**DIC + TA** is the standard pairing for this project — both are stable to
measure, ship, and store, unlike pH, which drifts without careful handling.

## Derived outputs

- pH (on the chosen scale), pCO2, fCO2, HCO3-, CO3--, CO2(aq)
- **Omega_aragonite / Omega_calcite** — saturation states. Omega > 1 means
  calcification is thermodynamically favorable; Omega < 1 means shells/skeletons
  can dissolve.
- Revelle factor — how much pCO2 rises per unit of added CO2 (buffering
  capacity)

## Why this is a reproducibility problem, not just a math problem

Two labs with identical raw DIC/TA can get meaningfully different
Omega_aragonite purely from differing on:

1. **Which equilibrium constants set** is used (Mehrbach/Dickson-Millero refit,
   Lueker et al. 2000, etc.) — see `references/equilibrium-constants.md` for the
   full comparison and this project's chosen default.
2. **Which pH scale** — Total, Seawater, Free, or NBS. Scale mismatches are the
   single most common silent-error source in this field.
3. **In-situ vs. measurement conditions** — samples are often measured at warm
   lab-bench temperature but must be reported at cold in-situ (seafloor)
   temperature. See the `pyco2sys-usage` skill for the `_out` suffix convention
   that keeps these separate.
4. **Whether nutrients** (phosphate, silicate) are folded into the alkalinity
   budget.

None of these choices is inherently wrong — the failure mode is when the choice
isn't **recorded alongside the output**. If a schema record doesn't carry which
constants and pH scale produced it, nobody downstream can explain a disagreement
between two numbers. This is the core problem this platform's schema/provenance
layer exists to solve.

## Additional resources

- **`references/equilibrium-constants.md`** — full comparison table of published
  constants sets, their valid ranges, citations, and this project's default.
