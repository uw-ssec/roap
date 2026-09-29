---
name: pyco2sys-usage
description:
  How to correctly call the PyCO2SYS library - the pyco2.sys() function
  signature, parameter type codes, pH scale and constants options, vectorized
  batch usage, and the in-situ vs measurement conditions convention. Use when
  the user asks about "PyCO2SYS", "pyco2.sys", "par1_type", "par2_type",
  "K1K2CONSTANTS", "opt_k_carbonic", "opt_pH_scale", "CO2SYS", batch-processing
  carbonate samples, or wrapping/integrating this library into the platform's
  pipeline.
---

# Using PyCO2SYS

## Source of truth

This `SKILL.md` and its `references/` subfolder are the current source of truth
for this domain. If a future dedicated domain-knowledge document is created,
update it and this skill together.

## What it is

The modern Python toolbox for solving the marine carbonate system. Lineage:
original CO2SYS (Lewis & Wallace 1998, DOS) -> CO2SYS.m (MATLAB/Excel, van
Heuven et al.) -> **PyCO2SYS** (full Python rewrite, published in _Geoscientific
Model Development_, 2022, maintained by Matthew Humphreys / NIOZ). Docs:
https://pyco2sys.readthedocs.io/en/latest/

**This platform wraps PyCO2SYS — it never reimplements its chemistry.** All
domain-correctness trust comes from PyCO2SYS's 25+ year validated lineage.

## Core call shape

```python
import PyCO2SYS as pyco2

results = pyco2.sys(
    par1=2300, par1_type=1,   # TA in umol/kg
    par2=2050, par2_type=2,   # DIC in umol/kg
    salinity=35,
    temperature=25,           # measurement temperature, deg C
    temperature_out=15,       # in-situ temperature for "out" conditions
    pressure_out=0,
    opt_k_carbonic=10,        # Lueker et al. 2000 — this project's default
    opt_pH_scale=1,           # Total scale — this project's default
)

results["pH_total"]
results["saturation_aragonite_out"]
```

Full `par1_type` / `par2_type` / `opt_k_carbonic` / `opt_pH_scale` code tables
are in `references/parameter-codes.md` — do not guess these codes, look them up.

## The `_out` suffix convention

PyCO2SYS distinguishes **input conditions** (where the sample was measured,
often a warm lab) from **output conditions** (in-situ, e.g. cold seafloor), and
computes both. Fields with an `_out` suffix are the in-situ values.

**Common silent bug:** reporting a lab-condition Omega as if it were in-situ.
Always be explicit in the schema/export about which condition a given field
represents — never assume the reader knows.

## Vectorized batch usage

`pyco2.sys()` accepts arrays / pandas Series for `par1`, `par2`, `salinity`,
`temperature`, etc., and returns arrays back. **Batch entire datasets through
one call** rather than looping row-by-row:

- Faster (this is how the library is designed to be used)
- Prevents accidentally using inconsistent `opt_k_carbonic` / `opt_pH_scale`
  settings across rows within the same dataset — a real risk if each row is
  processed in its own loop iteration with settings threaded through by hand

## v1 vs v2

A v2 beta exists that is reported faster with improved usability. Evaluate its
stability against v1 before committing, since this project is starting fresh and
isn't locked into v1 by legacy code.

## This project's standardized defaults

- **Constants set:** `opt_k_carbonic=10` (Lueker et al. 2000)
- **pH scale:** `opt_pH_scale=1` (Total scale)

See `carbonate-chemistry/references/equilibrium-constants.md` for the rationale
and the action item to confirm this against Prof. Mahu's group's historical
convention.

## Additional resources

- **`references/parameter-codes.md`** — full `par1_type`/`par2_type` code table
  and `opt_k_carbonic` / `opt_pH_scale` option tables.
