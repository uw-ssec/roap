# ROAP — Personas Summary

Source: `local/Response_SSEC_Ocean_Acidification_User_Stories.pdf` (extracted 2026-09-29)

## Six Personas

### 1. Ama — Carbonate Chemistry Researcher (Primary User)
- **Role:** Doctoral researcher, 4 cruises/year, ~40 carbonate bottles/cruise + CTD profiles
- **Skills:** Comfortable writing Python, not a software engineer
- **Platform:** Windows
- **Output use:** Thesis chapters, manuscripts — every correction must be defensible to reviewers
- **Key needs:**
  - Config-driven plausibility ranges & replicate thresholds (not code changes)
  - Every derived variable carries constants, input pair, software version
  - Replicate disagreements flagged with both values + disagreement size (not averaged away)
  - CRM offset per session + affected samples visible for methods section
  - Standard QC plots generated automatically
  - Figure selection via interface (not editing plotting code)
  - Figure preview → discard / save (location, format, resolution) / print

### 2. Kofi — Laboratory Analyst
- **Role:** Runs TA titrations, spectrophotometric pH, keeps CRM records
- **Skills:** Excel-only, **does not use terminal**
- **Position:** Origin of raw data, first to notice analytical session drift
- **Key needs:**
  - Submit bench sheet in existing Excel/CSV layout
  - Immediate validation of missing/malformed required fields (while records fresh)
  - Plot session results through same interface, no terminal
  - Pipeline reads input **without writing back to source workbook** (formula columns preserved)

### 3. Prof. Adjei — Principal Investigator
- **Role:** Supervises students, co-authors papers, **never runs pipeline**
- **Key needs:**
  - 10-minute readable summary per run: PASS/REVIEW/FAIL counts + reasons + exclusions
  - Every figure records settings + data subset → regenerate identically months later
  - Published figures/tables linked to archived run bundle (inputs, config, version)
  - Analysis reconstructable after student graduates

### 4. Fatou — OA Researcher at Partner Institution (West Africa)
- **Role:** University elsewhere in West Africa, active in regional network (OA-Africa)
- **Data:** 3 years of own TA/pH data in **her own spreadsheet layout**
- **Key needs:**
  - Map her column names → canonical schema (Frontiers 2021) via **config file**
  - Run her archive through same QC → regionally comparable results
  - Regenerate earlier result from archived config + pinned software version
  - **Citable tagged release** (not moving branch) for methods section

### 5. Ruu — MSc Student / New Trainee
- **Role:** First time handling carbonate data
- **Environment:** Fresh Windows laptop, **no Python installed**
- **Learning style:** Learns correct practice from software defaults
- **Key needs:**
  - Single documented entry point
  - Setup path: clean laptop → successful example run in <1 hour
  - Software behaves same on Windows, macOS, Linux

### 6. Nadia — National Monitoring Officer
- **Role:** Fisheries/environmental agency, mandate to report acidification status on fixed schedule
- **Key needs:**
  - Regeneratable quarterly product
  - Audit trail surviving staff turnover
  - Output in **international reporting stream format** (GOA-ON)
  - Run full workflow unattended from single command + saved config
  - Quarterly runs appended to continuous station time series (after clearance)
  - Retrieve consistent subset by station, depth, date range

---

## Persona × Priority Mapping

| Priority | Theme | Primary Personas | Secondary |
|----------|-------|------------------|-----------|
| P-1 | Prototype Migration | All | — |
| P0 | CI + Invariant Test + Entry Point | Ruu, Kofi, Nadia, Ama | Fatou |
| P1 | Packaging, Releases, Run Bundles | Fatou, Prof. Adjei, Nadia | Ama |
| P2 | Schema/Provenance/CRM/Excel/Property Tests | Ama, Fatou, Prof. Adjei, Kofi | Nadia |
| P4 | ADR: Queryable Layer | Nadia, Ama | Fatou |
| P3 | GOA-ON Export + Pre-flight Validation | Nadia, Kofi | Ama, Fatou |

---

## Persona-Specific Acceptance Criteria

| Persona | Must-Have for v1.0.0 |
|---------|---------------------|
| **Ama** | Config-driven thresholds, provenance on every value, replicate flagging with values, auto QC plots, figure interface |
| **Kofi** | No-terminal validation (GUI), formula columns preserved, Excel input accepted as-is |
| **Prof. Adjei** | 10-min run summary, figure provenance, archived run bundles |
| **Fatou** | Config-driven column mapping, tagged release, config+version regeneration |
| **Ruu** | <1 hour clean-laptop setup, cross-platform, single entry point |
| **Nadia** | Unattended quarterly runs, GOA-ON export, time-series append + query |