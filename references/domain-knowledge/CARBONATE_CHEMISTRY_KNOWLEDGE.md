# Carbonate Chemistry & PyCO2SYS Knowledge

Source-of-truth knowledge document for the reproducible coastal carbonate chemistry
platform. This doc is the authoritative reference; the `plugins/pyco2sys-dev` skills
are a distilled, Claude-facing view derived from it (mirrors how `uw-ssec/HPyX`'s
`hpx-dev` plugin was built from `docs/codebase-analysis/hpx/CODEBASE_KNOWLEDGE.md`).

When the science, the library API, or the data standard changes, update **this
document first**, then propagate the change into the relevant `SKILL.md` /
`references/*.md` files.

---

## 1. The Marine Carbonate System

Ocean acidification is driven by CO₂ dissolving into seawater:

```
CO₂ + H₂O ⇌ H₂CO₃ ⇌ H⁺ + HCO₃⁻ ⇌ 2H⁺ + CO₃²⁻
```

More dissolved CO₂ → more H⁺ → lower pH, and it shifts the equilibrium away from
carbonate ion (CO₃²⁻), the building block organisms need to calcify (shells, coral
skeletons, plankton tests).

### The four measurable parameters

The system is fully defined by **any 2 of these 4** (plus salinity, temperature,
pressure, and optionally nutrients):

| Parameter | Meaning | Typical measurement method |
|---|---|---|
| **DIC** | Dissolved Inorganic Carbon: CO₂ + HCO₃⁻ + CO₃²⁻ | Coulometry / infrared |
| **TA** | Total Alkalinity: acid-buffering capacity | Titration |
| **pH** | Hydrogen ion activity | Spectrophotometry / electrodes |
| **pCO₂** / **fCO₂** | Partial/fugacity of CO₂ | Equilibration + IR/GC |

**DIC + TA is the most common pairing** in this project because both are stable to
measure, ship, and store (unlike pH, which drifts without careful handling).

### Derived outputs (what you get back from a solve)

- pH (on the chosen scale), pCO₂, fCO₂, HCO₃⁻, CO₃²⁻, CO₂(aq)
- **Ω_aragonite and Ω_calcite** — saturation states. Ω > 1 = calcification
  thermodynamically favorable; Ω < 1 = shells/skeletons can dissolve. This is the
  number that matters biologically and is usually the headline result.
- Revelle factor — buffering capacity (how much pCO₂ rises per unit of added CO₂)

---

## 2. Why This Is a Reproducibility Problem, Not Just a Math Problem

Two labs with **identical raw DIC/TA measurements** can get meaningfully different
Ω_aragonite values purely from differing on:

1. **Which equilibrium (dissociation) constants set** is used — there are multiple
   published, peer-reviewed options (see `references/equilibrium-constants.md` in
   the `carbonate-chemistry` skill). None is universally "correct"; they differ in
   valid temperature/salinity ranges and accuracy tradeoffs.
2. **Which pH scale** the inputs/outputs are on — Total, Seawater, Free, or NBS.
   Mismatching scales is the single most common silent-error source in the field.
3. **In-situ vs. measurement conditions** — samples are often measured at a warm
   lab bench temperature but need to be reported at cold in-situ (seafloor)
   temperature. PyCO2SYS distinguishes these explicitly (`_out` suffix fields);
   conflating them is a classic quiet mistake.
4. **Whether nutrients** (phosphate, silicate) are included in the alkalinity
   budget — affects precision, often skipped by less careful workflows.

None of these choices is wrong per se — but if the choice isn't **recorded
alongside the output**, nobody downstream (a collaborator, a reviewer, future-you)
can tell why two numbers disagree. This is the actual problem the platform exists
to solve: not "do the math," but "make every number's provenance and assumptions
explicit and auditable."

---

## 3. PyCO2SYS — The Math Engine

**What it is:** the modern Python toolbox for solving the marine carbonate system.
Lineage: original CO2SYS (Lewis & Wallace, 1998, DOS) → CO2SYS.m (MATLAB/Excel,
van Heuven et al.) → **PyCO2SYS** (full Python rewrite, published in
*Geoscientific Model Development*, 2022, maintained by Matthew Humphreys/NIOZ).
This 25+ year lineage is why it's trusted as the field standard — the platform
should wrap it, never reimplement its chemistry.

- Docs: https://pyco2sys.readthedocs.io/en/latest/
- Single core entry point: `pyco2.sys(...)`
- **Vectorized**: accepts arrays/pandas Series for all parameters — batch entire
  datasets through one call rather than looping row-by-row (faster, and prevents
  accidentally using inconsistent settings across rows in the same dataset).
- A v2 beta exists that is faster with improved usability — worth evaluating
  against v1 stability before committing, since this project is starting fresh.
- Full parameter-code and option tables live in
  `plugins/pyco2sys-dev/skills/pyco2sys-usage/references/parameter-codes.md`.

### This project's standardized defaults

- **Constants set:** `opt_k_carbonic=10` (Lueker et al. 2000) — chosen for
  comparability with other OA-Africa / GOA-ON network members. Confirm this
  against Prof. Mahu's group's historical choice before finalizing.
- **pH scale:** Total scale (`opt_pH_scale=1`) unless an input dataset dictates
  otherwise — record the scale explicitly in every schema record, never assume it.

---

## 4. The Data Standard: Frontiers (2021) Best Practices

Paper: *"Best Practice Data Standards for Discrete Chemical Oceanographic
Observations"* — https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2021.705638/full

This is the closest thing the field has to a schema spec, and should directly
shape this project's Pydantic schema field names and QC flag values rather than
inventing project-specific conventions from scratch.

- **Column headers**: clarified, human-readable names replacing legacy WOCE
  Exchange abbreviations (e.g., "Silicate" not "SILCAT", "Ammonium" not "NH4").
- **QC flags**: unifies three historical WOCE flag schemes into one 0–9 scale
  (2 = acceptable, 9 = missing). Full table in
  `plugins/pyco2sys-dev/skills/data-standard/references/qc-flags-and-columns.md`.
- **Missing values**: universal sentinel `-999`.
- Adoption is **voluntary**, not mandatory — which is precisely why the field is
  fragmented today, and why this platform enforcing it by default has real value.

Adopting this standard also buys **GOA-ON data-portal compatibility** (see below)
— export format should target that alignment.

---

## 5. Community & Network Context

- **GOA-ON** (Global Ocean Acidification Observing Network,
  https://goa-on.org/) — international network (NOAA, IOC-UNESCO, GOOS, IAEA
  backed) running a global OA data portal, regional hubs, the Pier2Peer mentorship
  program, and the UN Ocean Decade-endorsed OARS initiative.
- **OA-Africa** (https://www.oa-africa.net/) — pan-African regional hub under
  GOA-ON, ~100+ scientists/students/technicians across multiple workshops. Prof.
  Mahu's group is a node in this network, not an isolated lab — this is the
  platform's realistic path to adoption beyond one PI's team, and the answer to
  "who else would actually use this."

---

## 6. Architecture Implication (Why the Platform Is Shaped This Way)

```
raw input (CSV/spreadsheet)
      │
      ▼
[ schema validation ]   ← Frontiers column names, types, units, pH-scale field required
      │
      ▼
[ QC layer ]            ← 0–9 flags, physical plausibility checks (e.g. TA/DIC ratio bounds)
      │
      ▼
[ PyCO2SYS wrapper ]    ← vectorized batch call, fixed constants/scale per project convention
      │
      ▼
[ provenance-tagged export ]  ← constants used, code version, timestamp, source checksum
      │
      ├── CLI
      ├── GUI
      └── notebook / importable API
```

**One engine, three doors.** The CLI, GUI, and notebook interfaces must call the
*same* core pipeline — if they ever compute things differently, the platform has
reintroduced the exact reproducibility bug it exists to eliminate.
