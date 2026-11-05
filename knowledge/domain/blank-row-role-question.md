---
type: Question
title: "Do laboratory blanks need a Row role?"
description:
  "Open domain question for issue 45: confirm whether laboratory blanks occur,
  their Tag prefix, and their treatment in correction and statistics."
tags: [row-roles, blanks, domain-review, p1-5]
generated: { by: agent/dinesh-codex, at: "2026-11-05T01:25:18Z" }
status: draft
---

# Do laboratory blanks need a Row role?

## Status and scope

**Awaiting an answer from Maurice / Prof. Mahu.** This note prepares the domain
review requested in [issue #45](https://github.com/uw-ssec/roap/issues/45). It
does not establish that laboratory blanks occur in cruise workbooks or assign
them a scientific meaning. Issue #45 stays open until that evidence is recorded.
No Blank role, prefix, or exclusion rule is approved here.

A laboratory blank is the subject of this question. A missing tag, an empty
`sample_type` cell, or an empty spreadsheet row does not by itself establish
that a measurement is a laboratory blank.

## Existing contract and implementation

The
[glossary](https://github.com/uw-ssec/roap/blob/3e293a7e26d6d1241ebab0a8d62cef7dd666dee7/GLOSSARY.md)
defines three Row roles: Sample, CRM, and Standard. The Tag prefix is the only
signal for the role, following [ADR-0006](../decisions/adrs.md). The planned
[row-role module (#40)](https://github.com/uw-ssec/roap/issues/40) uses `RM` for
CRM and `TRIS` for Standard by default. Missing or unrecognised prefixes fall
back to Sample and their count is reported. These are the requirements for #40,
rather than a claim that its module already exists.

The implementation at `3e293a7` still has an older, different rule:
[`stage1b.classify_rows_sample`](../../src/roap/stage1b.py) includes `"blank"`
among the `sample_type` labels that produce `"CRM"`. This is evidence of a
classification branch in code, not evidence that blanks are CRMs or occur in the
workbooks. Issue #40 replaces this classifier with the prefix-only contract; it
explicitly leaves Blank out of scope until #45 is answered.

## Evidence needed from the domain experts

Record the response and its date on issue #45, with a link to the source
conversation or an approved, non-sensitive example. Do not commit unpublished
cruise data to answer this question.

1. Do the workbooks processed by ROAP contain laboratory blank measurements?
   Clarify what a blank measures and how it differs from a CRM or pH Standard.
2. If so, what exact Tag prefix identifies them? Supply an approved example tag,
   whether it varies by cruise or laboratory, and whether it overlaps the
   configured CRM or Standard prefixes. An anonymised tag or synthetic example
   approved by the expert is sufficient for the public record.
3. Should those rows participate in TA correction, pH-standard checks,
   duplicate/replicate grouping, precision statistics, and carbonate
   calculations? State the expected output/QC treatment too. Do not infer that
   every CRM exclusion should apply to blanks.

## Resolution paths

- **Blanks occur and have an agreed prefix:** record the expert answer and open
  the follow-up required by #45. That issue should specify the Blank role,
  prefix configuration, any prefix conflicts, output preservation/QC status, and
  the agreed participation rules above. Add expert-approved synthetic fixtures
  for the role and affected Stage behavior before changing code. Record any
  accepted scientific-output decision in the ADRs and enumerate intended
  golden-baseline differences.
- **Blanks do not occur in the supported workbooks:** record the expert
  confirmation and its scope, then close #45 without adding a fourth role.
  Revisit the question if another laboratory supplies blanks later.
- **Blanks occur but their prefix or treatment is unresolved:** keep #45 open.
  The Sample fallback in #40 is not scientific approval to include a known
  laboratory blank in environmental statistics. Do not claim that such an input
  is supported until its role and treatment are agreed.

## Related concepts

- [Architecture Decision Records](../decisions/adrs.md): ADR-0006 governs the
  role signal; future scientific-output decisions need an explicit record.
- [Input Data Dictionary](../prototype/data-dictionary.md): historical
  classifier documentation; #40 defines the replacement contract.
