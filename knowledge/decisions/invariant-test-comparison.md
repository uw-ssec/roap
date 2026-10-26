---
type: Decision
title: Invariant tests compare each stage with its own input, as exact text
description:
  Untouched columns must keep exactly the same text; serialisation-only
  equivalence is allowed only for named numeric and timestamp columns.
tags: [testing, invariants, p0, adr-0003]
generated: { by: agent/richard-claude-code, at: "2026-10-26T22:05:00Z" }
status: draft
---

## Scope and status

This note refines [ADR-0003](adrs.md) and
[engineering decision 9](engineering-decisions.md) for P0 issue
[#12](https://github.com/uw-ssec/roap/issues/12). It is pending code PR review.
It was agreed during Richard/Dinesh cross-review on 2026-10-26 (maintainer
direction: direct PRs after cross-review, knowledge in separate PRs).

## What each stage is compared with

Each stage's output is compared with the file that stage actually read, not with
the original workbook. Every column outside that stage's `STAGE_TARGETS` must
keep every row's value. A difference introduced by an earlier stage is therefore
attributed to that earlier stage, not to every later stage.

`STAGE_TARGETS` includes intended transformations. For example, stage 04
canonicalises `ta_units` through `schema.normalize_ta_units`, and stage 05
resets the `preferred_*_for_analysis` columns and adds its `flag_*_missing`
flags.

## Exact text by default

Both files are read as text (`dtype=str`, `keep_default_na=False`). An untouched
column must keep **exactly the same text**. This holds even when the values look
numeric or date-like, so identifier changes such as `00123 → 123`,
`9007199254740992 → 9007199254740993`, `1 → 1.0` or
`2024-03-01 → 2024-03-01T00:00:00Z` all fail.

Serialisation-only differences are accepted **only** for columns listed per
stage in `SERIALISATION_EQUIVALENT`, each with a kind:

| Kind       | Accepts                                       | Still fails                     |
| ---------- | --------------------------------------------- | ------------------------------- |
| `float`    | re-written float within `rel_tol=1e-12`       | any larger change, cleared cell |
| `count`    | `1` vs `1.0` (exact `Decimal` equality)       | any change in value             |
| `datetime` | same instant in another ISO form, naive = UTC | any change of date or time      |

Treating naive timestamps as UTC matches `common.coerce_datetime`. Each listed
column was measured from a real run of `examples/example_data.xlsx`. Add a
column to the list only when a real run shows a serialisation-only difference
there, and never for identifiers.

_Rejected_: tolerating numeric/date re-serialisation in every column. Review
showed that this accepts real identifier mutations, and that float conversion
silently loses integers above 2^53.

Source: `tests/test_invariants.py` (`SERIALISATION_EQUIVALENT`, `_same_value`,
`assert_untouched_unchanged`, `test_checker_catches_mutation*`).

## Verification requirements

The checker has negative tests: identifier mutations in an undeclared column,
and a value change, cleared cell or non-numeric value for each declared kind. A
test also keeps `SERIALISATION_EQUIVALENT` scoped to real stages and non-target
columns. When the comparison changes, show that the new negative tests fail
against the old checker before relying on them.

Linked reference: [engineering decisions](engineering-decisions.md).
