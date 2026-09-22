---
name: data-standard
description:
  The Frontiers (2021) best-practice data standard for discrete chemical
  oceanographic observations - column naming conventions, the unified QC flag
  scale, and missing-value conventions this platform's schema should adopt. Use
  when the user asks about "schema", "column names", "QC flags", "quality
  control flags", "data standard", "missing value", "-999", "WOCE format",
  "export format", "provenance", or is designing the platform's input/output
  schema.
---

# Discrete Chemical Oceanography Data Standard

## Source of truth

This skill is a distilled view of
`docs/domain-knowledge/CARBONATE_CHEMISTRY_KNOWLEDGE.md`. If the two disagree,
that document wins — update it first, then this file.

## The paper

_"Best Practice Data Standards for Discrete Chemical Oceanographic
Observations"_ (Frontiers in Marine Science, 2021):
https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2021.705638/full

This is the closest thing the field has to a schema spec. **Adopt it as the
platform's schema/QC naming source rather than inventing project-specific
conventions.** Doing so buys two things for free: credibility with reviewers who
know this paper, and interoperability with datasets that already follow it —
including potential GOA-ON data-portal compatibility (see the
`carbonate-chemistry` skill for GOA-ON/OA-Africa network context).

## Key recommendations to encode in the schema

1. **Column headers** — use clarified, human-readable names instead of legacy
   WOCE Exchange abbreviations. E.g. "Silicate" not "SILCAT", "Ammonium" not
   "NH4". Full mapping table in `references/qc-flags-and-columns.md`.

2. **QC flags** — a single unified 0-9 scale, replacing three historical
   competing WOCE flag schemes. Flag `2` = acceptable, flag `9` = missing. Full
   flag-meaning table in `references/qc-flags-and-columns.md`.

3. **Missing values** — universal sentinel `-999`, not `NaN`, not an empty
   string, not `null`. Every schema field that can be absent must use this exact
   sentinel for consistency with the standard.

4. **Adoption is voluntary, not mandatory** — which is exactly why the field is
   fragmented today. This platform enforcing the standard **by default** (not as
   an opt-in) is a real piece of the value proposition, not just a nice-to-have.

## Practical implication for schema design

When defining the Pydantic (or equivalent) input/output schema:

- Field names should match the standard's clarified column headers, not whatever
  a specific lab's legacy spreadsheet happened to call them. Build an explicit
  **input mapping layer** so legacy spreadsheet headers get translated to
  standard names at ingestion, rather than forcing users to rename columns by
  hand before upload.
- Every numeric field needs an associated QC flag field (0-9 scale).
- Missing-value handling must normalize to `-999` on export, regardless of how
  the value was represented in the raw input (blank cell, `NA`, `NaN`, etc.).
- Every export must also carry provenance metadata (see `carbonate-chemistry`
  and `pyco2sys-usage` skills): which `opt_k_carbonic` and `opt_pH_scale` were
  used, source file checksum, code version, timestamp. The Frontiers standard
  covers _data_ fields; provenance covers _how the data was produced_ — both are
  required for real reproducibility.

## Additional resources

- **`references/qc-flags-and-columns.md`** — full 0-9 QC flag meaning table and
  standardized column name mapping.
