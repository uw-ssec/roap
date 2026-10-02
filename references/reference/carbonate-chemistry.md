# Carbonate Chemistry — Quick Reference

Source: `local/prototype/my_understanding/test/docs/domain-knowledge/CARBONATE_CHEMISTRY_KNOWLEDGE.md`  
Skills: `.agents/skills/carbonate-chemistry/`

---

## The Marine Carbonate System

```
CO₂ + H₂O ⇌ H₂CO₃ ⇌ H⁺ + HCO₃⁻ ⇌ 2H⁺ + CO₃²⁻
```

More dissolved CO₂ → more H⁺ → lower pH, shifts equilibrium away from CO₃²⁻ (calcification building block).

### Four Measurable Parameters (any 2 define the system + T, S, P)

| Parameter | Meaning | Method |
|-----------|---------|--------|
| **DIC** | Dissolved Inorganic Carbon (CO₂ + HCO₃⁻ + CO₃²⁻) | Coulometry / IR |
| **TA** | Total Alkalinity (acid-buffering capacity) | Titration |
| **pH** | Hydrogen ion activity | Spectrophotometry / electrodes |
| **pCO₂/fCO₂** | Partial/fugacity of CO₂ | Equilibration + IR/GC |

**DIC + TA** = standard pairing (stable to measure, ship, store; unlike pH which drifts).

### Derived Outputs
- pH (on chosen scale), pCO₂, fCO₂, HCO₃⁻, CO₃²⁻, CO₂(aq)
- **Ω_aragonite, Ω_calcite** — saturation states (Ω > 1 = calcification favorable)
- **Revelle factor** — buffering capacity (ΔpCO₂ per ΔCO₂)

---

## Why Reproducibility Problem, Not Just Math

Two labs with **identical raw DIC/TA** get different Ω_aragonite from differing on:

1. **Equilibrium constants set** — multiple peer-reviewed options, different T/S ranges
2. **pH scale** — Total, Seawater, Free, NBS (scale mismatch = #1 silent error)
3. **In-situ vs measurement conditions** — lab temp vs seafloor temp (PyCO2SYS `_out` suffix)
4. **Nutrients in alkalinity budget** — phosphate, silicate (often skipped)

**Failure mode:** Choice not recorded alongside output → nobody can explain disagreement.

---

## Project Defaults (Provisional — Confirm with Prof. Mahu)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `opt_k_carbonic` | 10 (Lueker et al. 2000) | OA-Africa/GOA-ON comparability |
| `opt_k_bisulfate` | Dickson | Standard |
| `opt_k_fluoride` | PerezFraga1987 | Standard |
| `opt_k_borate` | Lee2010 | Standard |
| `opt_pH_scale` | 1 (Total scale) | Project default |
| pCO₂ plausibility | 50–4000 µatm | Lefevre et al. 2008 |

---

## Key References

- Lueker et al. (2000) — Constants
- Lefevre et al. (2008) — pCO₂ bounds
- Orr et al. (2005) — Ω_aragonite undersaturation precedes calcite
- Dickson et al. — Guide to Best Practices (SOP conventions)
- GOA-ON — Replicate agreement thresholds

---

## Network Context

- **GOA-ON** — Global OA Observing Network (NOAA, IOC-UNESCO, GOOS, IAEA)
- **OA-Africa** — Pan-African hub under GOA-ON (~100+ scientists)
- **Prof. Mahu's group** — Node in OA-Africa network
- Platform's adoption path: regional network, not isolated lab