# ROAP — Open Questions for Engineering

Source: `local/Response_SSEC_Ocean_Acidification_User_Stories.pdf` (Part 3)

---

## 1. Queryable Data Layer Scope

**Stories affected:** US-23 (Nadia: quarterly runs → continuous time series), US-24 (Ama: retrieve subset by station/depth/date)

**Current state:** Pipeline writes files (`outputs/`, `runs/`). No database, no query API.

**Question:** Is a queryable layer (SQLite/DuckDB/PostgreSQL) in scope for v1.0.0?

**Options:**
- **A. In scope:** Add `oa-pipeline ingest RUN_DIR` → appends to DB; `oa-pipeline query --station --depth-range --date-range`
- **B. Out of scope:** File-based workflow with `archive/manifest.csv` index; document `pandas`/`duckdb` querying on files

**Impact:** Gates P3 export design (DB-friendly vs file-friendly GOA-ON export)

**Decision needed before:** P3 work starts

**Decider:** [Lead] + [Prof. Adjei input]

---

## 2. Cross-Platform vs. International Export Sequencing

**Capabilities the software does NOT have at all:**
- Cross-platform behavior (US-19: Windows/macOS/Linux parity)
- International reporting export (US-20: GOA-ON format)

**Current state:** Windows + Git Bash only. No GOA-ON export.

**Question:** Which to tackle first? No priority marked in stories.

**Considerations:**
- Cross-platform enables Ruu (trainee) and Nadia (quarterly on any machine)
- GOA-ON export enables Nadia (reporting) and Fatou (interoperability)
- CI (P0) requires cross-platform anyway
- GOA-ON export design depends on P4 queryable layer decision

**Recommendation:** Cross-platform first (enables CI), then GOA-ON export after P4 decision

---

## 3. Wider Codebase Context

**Context:** This pipeline is 1 of 4 related codebases:
1. **OA Pipeline** (this one) — carbonate chemistry QC
2. **CTD/Nitrate Profile Processing** — hydrographic profiles
3. **CTD-Bottle Matching** — linking CTD casts to bottle samples
4. **Predictive Modelling** — full-depth carbonate profiles
5. **Orchestration Layer** — under construction, wraps above

**Current decision:** Stories deliberately kept to OA pipeline alone.

**Question:** Does the wider setting affect how we sequence work?

**Considerations:**
- Shared schema? Shared config? Shared provenance?
- Orchestration layer may need consistent interfaces
- Shared `oa_pipeline.common` utilities?

**Recommendation:** Keep v1.0 focused on OA pipeline. Define clean interfaces (CLI, file formats) for future integration. Document assumptions.

---

## 4. Data Volume & Performance Engineering

**Current scale:**
- Typical cruise: <100 carbonate bottles
- Full archive: small (few thousand rows max)
- April 2026 dataset: 53 rows (38 samples, 7 CRM, 8 std)

**Question:** Does this project require performance/scale engineering?

**Considerations:**
- Pandas handles 10K-100K rows easily
- PyCO2SYS vectorized batch call is fast
- Bottlenecks likely I/O (Excel) or plotting, not computation
- Premature optimization risks complexity

**Recommendation:** No performance engineering for v1.0. Optimize when/if needed. Use Parquet for larger intermediates.

---

## 5. CRM Batch Certification Process

**Current:** `configs/crm_certified_values.yaml` has Dickson batches 180-225 (NOAA-sourced).

**Question:** How to handle new CRM batches?

**Options:**
- Manual YAML update + PR (current)
- Automated fetch from NOAA OCADS API
- User-provided override in config

**Recommendation:** Manual YAML for v1.0 (low frequency, high stakes). Document process clearly.

---

## 6. pH Scale Handling for Mixed-Vintage Data

**Current:** Default `accepted_ph_scales = ["total"]`. Other scales flagged.

**Question:** Support mixed pH scales in same dataset?

**Considerations:**
- Historical data may use NBS or Seawater scale
- Conversion requires temperature/salinity
- Schema could carry per-row `ph_scale_observed`

**Recommendation:** Per-row `ph_scale_observed` field (already in schema). Conversion in Stage 1A if needed. Flag non-total scales for review.

---

## 7. Nutrient Inclusion in Alkalinity Budget

**Current:** Not included in TA correction.

**Question:** Include phosphate/silicate in alkalinity budget?

**Considerations:**
- Affects precision (typically <1 µmol/kg)
- Frontiers standard includes nutrient columns
- PyCO2SYS supports `opt_k_phosphate`, `opt_k_silicate`

**Recommendation:** Accept nutrient columns in schema (Frontiers), but default to not including in TA correction. Config option for advanced users.

---

## 8. Figure Regeneration / Plotting Environment

**Stories:** US-12, US-13, US-15 (Ama: figure interface, preview, save; Prof. Adjei: figure provenance)

**Current:** `oa_plots.py` + notebooks `oa_figures.ipynb`, `oa_figures_extended.ipynb`

**Question:** Rebuild plotting as reusable library vs keep notebook-based?

**Considerations:**
- Notebook-based: flexible, hard to version
- Library + CLI: reproducible, less flexible
- Hybrid: library functions called from notebooks

**Recommendation:** Extract plotting functions to `src/oa_pipeline/viz/` with CLI (`oa-pipeline plot ...`). Notebooks import library.

---

## 9. Data Governance / Sovereignty

**Stories:** US-20 (Nadia: international reporting), US-21 (Prof. Adjei: archived bundles)

**Context:** Ghana shelf data, University of Ghana, doctoral research.

**Question:** Any data-sharing/sovereignty constraints for test fixtures?

**Current:** April 2026 dataset unpublished — kept in shared folder, not in repo. Synthetic data for CI.

**Recommendation:** Continue: synthetic data only in public repo/CI. Real data in shared private storage. Document in `CONTRIBUTING.md`.

---

## 10. Definition of "User-Validated" for v1.0

**Proposal says:** "user-validated" — but validated by whom, against what criteria?

**Question:** Explicit validation criteria for v1.0 release.

**Suggested criteria:**
- [ ] Ama: Runs April 2026 dataset → 22/16/0, can defend corrections
- [ ] Kofi: Validates bench sheet via GUI, no terminal, formula columns intact
- [ ] Prof. Adjei: Reads run summary in 10 min, signs off
- [ ] Fatou: Runs her 3-year archive via config aliases, gets comparable results
- [ ] Ruu: Clean laptop → running in <1 hour on all 3 platforms
- [ ] Nadia: Quarterly run unattended, GOA-ON export valid

**Decider:** Prof. Adjei (PI) + Maurice (maintainer)

---

## Tracking

| Question | Status | Decision | Date |
|----------|--------|----------|------|
| Queryable layer scope | Open | — | — |
| Cross-platform vs export | Open | — | — |
| Wider codebase impact | Open | — | — |
| Performance engineering | Open | — | — |
| CRM batch process | Open | — | — |
| Mixed pH scales | Open | — | — |
| Nutrients in TA budget | Open | — | — |
| Plotting architecture | Open | — | — |
| Data governance | Open | — | — |
| v1.0 validation criteria | Open | — | — |

*Update this table as decisions are made. Each decision → ADR in `decisions/architecture-decisions.md`*