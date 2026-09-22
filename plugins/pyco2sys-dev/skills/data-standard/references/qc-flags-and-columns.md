# QC Flag Scale & Column Naming Reference

> **Confirmed vs. needs verification:** the paper explicitly confirms flag `2` =
> acceptable and flag `9` = missing, and that it consolidates three prior
> WOCE-era flag schemes into one 0-9 scale. The full flag-by-flag table below is
> the conventional WOCE/GO-SHIP-derived interpretation used broadly across the
> discrete chemical oceanography community; **verify each value directly against
> the paper's actual flag table before hardcoding it into schema validation
> logic.** Do not treat this table as a direct quote of the paper.

## QC flag scale (0-9)

| Flag | Conventional meaning                                       |
| ---- | ---------------------------------------------------------- |
| 1    | Sample drawn but not analyzed                              |
| 2    | **Acceptable measurement** (confirmed by paper)            |
| 3    | Questionable / suspect measurement                         |
| 4    | Bad measurement                                            |
| 5    | Not reported                                               |
| 6    | Mean of replicate measurements                             |
| 7    | Manually integrated chromatographic peak (method-specific) |
| 8    | Irregular digital chromatographic peak (method-specific)   |
| 9    | **Missing** (confirmed by paper)                           |

Flag `0` is typically reserved as "no QC performed yet" in similar schemes —
confirm this against the paper before relying on it.

## Column naming — legacy vs. standard

Examples of the clarification the paper recommends (confirmed pattern from the
paper's stated examples — extend this table as more legacy-to-standard mappings
are identified during the codebase audit):

| Legacy WOCE Exchange abbreviation | Standard clarified name            |
| --------------------------------- | ---------------------------------- |
| `SILCAT`                          | Silicate                           |
| `NH4`                             | Ammonium                           |
| `PHSPHT`                          | Phosphate _(verify against paper)_ |
| `NITRAT`                          | Nitrate _(verify against paper)_   |

## Missing value sentinel

`-999` — universal across all fields, regardless of data type. On export,
normalize any of the following raw representations to `-999`:

- Blank / empty cell
- `NA`, `N/A`, `NaN`
- `null` / `None`

## Action item for the codebase audit (Phase 1)

Build the full legacy-to-standard column mapping table by cross-referencing:

1. The existing spreadsheet/script column headers (from the codebase audit)
2. The paper's complete recommended naming table
3. GOA-ON data portal's expected field names, if published separately

This becomes the input mapping layer referenced in the parent `SKILL.md`.
