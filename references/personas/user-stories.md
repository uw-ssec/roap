# ROAP — User Stories (All 24)

Source: `local/Response_SSEC_Ocean_Acidification_User_Stories.pdf`  
Grouped by workflow area. Format: `As a [persona], I [want to], [so that]`

---

## Getting Data Into the Pipeline

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As **Fatou**, I want to map my spreadsheet column names onto the canonical schema (Frontiers 2021) through a configuration file rather than renaming columns, so that I can run my 3-year archive through the same QC and have regionally comparable results. | P2 |
| US-02 | As **Kofi**, I want to submit my bench sheet in the Excel/CSV layout I already use and be told immediately which required fields are missing or malformed, so that I can correct problems while session records are still in front of me. | P3 |
| US-03 | As **Ama**, I want the pipeline to read my input without writing back into the source workbook, so that formula-driven columns in the original file are never silently blanked. | P2 |

---

## Quality Control & Trust in the Numbers

| ID | Story | Priority |
|----|-------|----------|
| US-04 | As **Ama**, I want every replicate pair exceeding the agreed SD threshold to be flagged with both measured values and the size of the disagreement, so that I can judge whether it's an analytical problem or real small-scale variability rather than having the pair averaged away. | P2 |
| US-05 | As **Ama**, I want to see the CRM offset applied to each analytical session and the samples it affected, so that I can report the correction in my methods section and defend it if a reviewer asks. | P2 |
| US-06 | As **Prof. Adjei**, I want a short readable summary of each processing run that lists how many samples passed, how many need review and why, and what was excluded, so that I can sign off on a dataset without installing or running anything. | P1 |
| US-07 | As **Ama**, I want to adjust plausibility ranges and replicate thresholds in a configuration file rather than in source code, so that I can apply settings appropriate to a different estuary or season without forking the software. | P2 |

---

## Carbonate System Calculation & Provenance

| ID | Story | Priority |
|----|-------|----------|
| US-08 | As **Ama**, I want every derived carbonate variable to carry the constants, the input pair, and the software version that produced it, so that a value in a results table can always be traced back to how it was calculated. | P2 |
| US-09 | As **Fatou**, I want to regenerate an earlier result from its archived configuration file and a pinned software version, so that I can confirm a number in a paper before building on it. | P1 |
| US-10 | As **Ama**, I want the pipeline to refuse to run when a configuration file was written for an incompatible version of the schema, so that a stale setting cannot quietly produce wrong numbers. | P1 |

---

## Figures & Visual Products

| ID | Story | Priority |
|----|-------|----------|
| US-11 | As **Ama**, I want the standard QC plots to be generated automatically as part of each run, so that I am not rebuilding the same diagnostic figures by hand for every cruise. | P2 |
| US-12 | As **Ama**, I want to select which variables to plot, against which axes, and for which stations, depths and date range, from an interface rather than by editing plotting code, so that I can follow a question through the dataset without writing a new script each time. | P2 |
| US-13 | As **Ama**, I want to preview a figure on screen and then choose whether to discard it, save it to a location and file format and resolution I specify, or send it directly to print, so that I am not accumulating files I did not want. | P2 |
| US-14 | As **Kofi**, I want to plot his own session results through the same interface without using a terminal, so that he can look at a suspect run himself before passing it on. | P3 |
| US-15 | As **Prof. Adjei**, I want every figure to record the settings and the data subset that produced it, so that a figure in a submitted manuscript can be regenerated identically months later without reconstructing a plotting environment from memory. | P1 |

---

## Installing & Running the Software

| ID | Story | Priority |
|----|-------|----------|
| US-16 | As **Ruu**, I want a single documented entry point and a setup path that gets me from a clean laptop to a successful run on the example dataset in under an hour, so that I can start learning the "science" rather than debugging my environment. | P0 |
| US-17 | As **Kofi**, I want to select my input file and run the standard workflow from a simple interface, so that I can check my own session data without waiting for someone else. | P0 |
| US-18 | As **Nadia**, I want to run the full workflow unattended from a single command against a saved configuration, so that the quarterly product can be regenerated on a schedule and by a colleague who has never run it before. | P1 |
| US-19 | As **Ruu**, I want the software to behave the same way on Windows, macOS and Linux, so that the machine I happen to have does not determine whether I can take part. | P0 |

---

## Sharing, Reporting & Reuse

| ID | Story | Priority |
|----|-------|----------|
| US-20 | As **Nadia**, I want to export a processed dataset in the structure expected by the international ocean acidification reporting stream, so that national data reaches the global record without a manual reformatting step that nobody can repeat. | P3 |
| US-21 | As **Prof. Adjei**, I want each published figure and table to be linked to an archived run bundle containing the inputs, configuration and version used, so that the analysis behind a paper remains reconstructable after the student who ran it has graduated. | P1 |
| US-22 | As **Fatou**, I want a citable tagged release rather than a moving branch, so that I can state in my methods exactly which version produced my results. | P1 |

---

## Building a Record Over Time

| ID | Story | Priority |
|----|-------|----------|
| US-23 | As **Nadia**, I want each quarterly run appended to a continuous station time series (after each is given clearance) under consistent quality control, so that seasonal cycles and longer-term trends can be assessed rather than only individual snapshots. | P4 |
| US-24 | As **Ama**, I want to retrieve a consistent subset of the accumulated record by station, depth and date range, so that I can assemble an analysis dataset without rebuilding it from per-cruise files each time. | P4 |

---

## Story → Epic Mapping

| Epic | Stories |
|------|---------|
| P-1 Migration | — (prerequisite) |
| P0 CI/Entry Point | US-16, US-17, US-19 |
| P1 Packaging/Releases | US-06, US-09, US-10, US-15, US-18, US-21, US-22 |
| P2 Schema/Provenance/CRM/Excel | US-01, US-03, US-04, US-05, US-07, US-08, US-11, US-12, US-13 |
| P4 ADR Queryable | US-23, US-24 |
| P3 Export/Validation | US-02, US-14, US-20 |

---

## Open Questions from Personas (for Engineering)

1. **Queryable layer scope** — "Building a record over time" stories (US-23, US-24) imply a database. Current software writes files. Is a queryable layer in scope for v1.0?

2. **Cross-platform vs. International export sequencing** — Two capabilities the software doesn't have at all (US-19, US-20). No priority marked. Which first?

3. **Wider codebase context** — This pipeline is 1 of 4 related codebases (CTD/nitrate, CTD-bottle matching, predictive modelling, orchestration layer). Stories kept to OA pipeline alone. Does wider setting affect sequencing?

4. **Data volume / performance** — Typical cruise: <100 bottles. Full archive: small. Is performance/scale engineering needed?

---

## Acceptance Criteria per Story (for Issue Creation)

Each GitHub issue should include:
- [ ] Persona(s) served
- [ ] Workflow area
- [ ] Specific acceptance criteria (testable)
- [ ] Related stories
- [ ] Priority label (P-1, P0, P1, P2, P3, P4)