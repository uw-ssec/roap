# PyCO2SYS Usage — Quick Reference

Source: `.agents/skills/pyco2sys-usage/`  
Docs: https://pyco2sys.readthedocs.io/en/latest/

---

## Core Call Shape

```python
import PyCO2SYS as pyco2

results = pyco2.sys(
    par1=2300, par1_type=1,   # TA in µmol/kg
    par2=2050, par2_type=2,   # DIC in µmol/kg
    salinity=35,
    temperature=25,           # measurement temperature (°C)
    temperature_out=15,       # in-situ temperature (°C)
    pressure_out=0,
    opt_k_carbonic=10,        # Lueker et al. 2000 (project default)
    opt_pH_scale=1,           # Total scale (project default)
)

results["pH_total"]
results["saturation_aragonite_out"]
```

---

## Parameter Type Codes (par1_type / par2_type)

| Code | Parameter | Unit |
|------|-----------|------|
| 1 | TA | µmol/kg |
| 2 | DIC | µmol/kg |
| 3 | pH | (scale per opt_pH_scale) |
| 4 | pCO₂ | µatm |
| 5 | fCO₂ | µatm |
| 6 | HCO₃⁻ | µmol/kg |
| 7 | CO₃²⁻ | µmol/kg |
| 8 | CO₂(aq) | µmol/kg |
| 9 | Ω_aragonite | — |
| 10 | Ω_calcite | — |

**Full table:** `.agents/skills/pyco2sys-usage/references/parameter-codes.md`

---

## Constants Options (opt_k_carbonic)

| Code | Set | Reference | Valid Range |
|------|-----|-----------|-------------|
| 1 | Mehrbach refit (Dickson & Millero) | 1987 | — |
| 2 | Roy et al. | 1993 | — |
| 3 | Goyet & Poisson | 1989 | — |
| 4 | Millero et al. | 2002 | — |
| 5 | Millero et al. | 2006 | — |
| 6 | Mehrbach (original) | 1973 | — |
| 7 | Lueker et al. | 2000 | **Project default (10)** |
| 8 | Millero (2010) | 2010 | — |
| 9 | Waters et al. | 2014 | — |
| 10 | Lueker et al. | 2000 | **Project default** |
| 11 | Millero (2010) + KSO4 | 2010 | — |
| 12 | Sulpis et al. | 2020 | — |

**Project default:** `opt_k_carbonic=10` (Lueker et al. 2000)

---

## pH Scale Options (opt_pH_scale)

| Code | Scale | Description |
|------|-------|-------------|
| 1 | Total | **Project default** |
| 2 | Seawater | — |
| 3 | Free | — |
| 4 | NBS | — |

**Scale mismatch = #1 silent error source in field.** Always record scale explicitly.

---

## The `_out` Suffix Convention (Critical)

PyCO2SYS distinguishes **input conditions** (measurement) from **output conditions** (in-situ):

| Field | Meaning |
|-------|---------|
| `pH_total` | pH at measurement conditions |
| `pH_total_out` | pH at in-situ conditions |
| `saturation_aragonite` | Ω at measurement conditions |
| `saturation_aragonite_out` | Ω at in-situ conditions |
| `pCO2` | pCO₂ at measurement conditions |
| `pCO2_out` | pCO₂ at in-situ conditions |

**Common silent bug:** Reporting lab-condition Ω as if it were in-situ.  
**Always be explicit** in schema/export about which condition a field represents.

---

## Vectorized Batch Usage (Required)

```python
# GOOD: Batch entire dataset in one call
results = pyco2.sys(
    par1=ta_array, par1_type=1,
    par2=ph_array, par2_type=3,
    salinity=sal_array,
    temperature=temp_array,
    temperature_out=insitu_temp_array,
    pressure_out=pressure_array,
    opt_k_carbonic=10,
    opt_pH_scale=1,
)

# BAD: Loop row-by-row (slow, risks inconsistent settings)
for i in range(len(df)):
    result = pyco2.sys(...)  # Don't do this
```

**Benefits:**
- Faster (library designed for batch)
- Prevents inconsistent `opt_k_carbonic`/`opt_pH_scale` across rows

---

## v1 vs v2

- **v1:** Stable, current release
- **v2 (beta):** Faster, improved usability
- **Decision:** Evaluate v2 stability before committing (project starts fresh, not locked to v1)

---

## Integration with Pipeline

**Current pipeline does NOT run PyCO2SYS.** It audits externally-computed carbonate fields via provenance columns:
- `carbonate_solver`
- `carbon_input_pair_used`
- `carbonate_constants`
- `carbonate_ph_scale`
- `carbonate_output_temperature`

**Missing provenance → Stage 4 FAILs every sample row.**

**Platform v1.0 will wrap PyCO2SYS** as the calculation engine (replacing external computation).