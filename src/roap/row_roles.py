"""Row roles: what each row in a cruise dataset represents (ADR-0006).

A row is a Sample, a CRM or a Standard. The role is decided once, at Stage QC,
from the row's Tag prefix only, and saved as the ``row_role`` column. Every
later Stage asks this module which rows have which role instead of re-deriving
it from ``sample_type`` or QC flags.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping, Optional

import pandas as pd

from .common import safe_str_series

__all__ = [
    "DEFAULT_PREFIXES",
    "ROW_ROLE_COL",
    "RowRole",
    "assign_row_roles",
    "is_crm",
    "is_sample",
    "is_standard",
    "legacy_classification",
    "parse_prefixes",
    "summarize_row_roles",
]

ROW_ROLE_COL = "row_role"


class RowRole(str, Enum):
    """The role of one row. The value is what the ``row_role`` column stores."""

    SAMPLE = "SAMPLE"
    CRM = "CRM"
    STANDARD = "STANDARD"


# Tag prefixes for the non-Sample roles. Every other row is a Sample.
DEFAULT_PREFIXES: dict[RowRole, str] = {RowRole.CRM: "RM", RowRole.STANDARD: "TRIS"}


def parse_prefixes(prefixes: Optional[Mapping[str, str]] = None) -> dict[RowRole, str]:
    """Validate a ``{"CRM": ..., "STANDARD": ...}`` mapping, filling in defaults.

    Keys are role names (case-insensitive) or ``RowRole`` members. Prefixes
    must be non-empty, and neither may start with the other: an overlapping
    pair would make some tags match both roles.
    """
    out = dict(DEFAULT_PREFIXES)
    for key, prefix in (prefixes or {}).items():
        try:
            role = RowRole(str(getattr(key, "value", key)).strip().upper())
        except ValueError:
            role = None
        if role is None or role is RowRole.SAMPLE:
            raise ValueError(
                f"Unknown row-role prefix key {key!r}; expected 'CRM' or 'STANDARD'. "
                "Rows matching neither prefix are Samples."
            )
        text = "" if prefix is None else str(prefix).strip()
        if not text:
            raise ValueError(f"The {role.value} tag prefix must not be empty.")
        out[role] = text

    crm, std = out[RowRole.CRM].upper(), out[RowRole.STANDARD].upper()
    if crm.startswith(std) or std.startswith(crm):
        raise ValueError(
            f"CRM prefix {out[RowRole.CRM]!r} and Standard prefix "
            f"{out[RowRole.STANDARD]!r} overlap, so some tags would match both."
        )
    return out


def assign_row_roles(
    df: pd.DataFrame,
    prefixes: Optional[Mapping[str, str]] = None,
    tag_col: str = "sample_tag",
) -> pd.Series:
    """Return each row's role (``RowRole`` values) decided from its Tag prefix.

    Matching is case-insensitive and ignores surrounding whitespace. A missing,
    blank or unrecognised tag gives the Sample role; ``summarize_row_roles``
    reports how many rows that was.
    """
    resolved = parse_prefixes(prefixes)
    if tag_col not in df.columns:
        raise KeyError(f"Tag column {tag_col!r} not found; cannot decide row roles.")

    tag = safe_str_series(df[tag_col]).str.upper()
    roles = pd.Series(RowRole.SAMPLE.value, index=df.index, dtype="string")
    for role, prefix in resolved.items():
        roles[tag.str.startswith(prefix.upper())] = role.value
    return roles


def summarize_row_roles(
    df: pd.DataFrame, tag_col: str = "sample_tag"
) -> dict[str, int]:
    """Count rows per role, and the Sample rows that have no tag at all."""
    roles = _roles(df)
    counts = {role.value: int(roles.eq(role.value).sum()) for role in RowRole}
    if tag_col in df.columns:
        blank = safe_str_series(df[tag_col]).eq("")
        counts["n_sample_tag_missing"] = int((blank & roles.eq(RowRole.SAMPLE.value)).sum())
    return counts


def _roles(df: pd.DataFrame) -> pd.Series:
    if ROW_ROLE_COL not in df.columns:
        raise KeyError(
            f"Column {ROW_ROLE_COL!r} not found. Stage QC (notebook 02) decides "
            "row roles; rerun it on this input."
        )
    roles = df[ROW_ROLE_COL].astype("string").str.upper()
    unknown = sorted(set(roles.dropna()) - {r.value for r in RowRole})
    if unknown or roles.isna().any():
        raise ValueError(
            f"Column {ROW_ROLE_COL!r} has missing or unknown values: "
            f"{unknown or ['<missing>']}. Expected {[r.value for r in RowRole]}."
        )
    return roles


def is_sample(df: pd.DataFrame) -> pd.Series:
    """Boolean mask of Sample rows."""
    return _roles(df).eq(RowRole.SAMPLE.value).astype(bool)


def is_crm(df: pd.DataFrame) -> pd.Series:
    """Boolean mask of CRM rows."""
    return _roles(df).eq(RowRole.CRM.value).astype(bool)


def is_standard(df: pd.DataFrame) -> pd.Series:
    """Boolean mask of Standard (pH standard) rows."""
    return _roles(df).eq(RowRole.STANDARD.value).astype(bool)


# The deprecated ``row_classification`` labels, kept for one release (#40).
_LEGACY_LABELS = {RowRole.SAMPLE.value: "SAMPLE", RowRole.CRM.value: "CRM", RowRole.STANDARD.value: "STD"}


def legacy_classification(df: pd.DataFrame) -> pd.Series:
    """Deprecated ``row_classification`` labels (SAMPLE/CRM/STD) from ``row_role``."""
    return _roles(df).map(_LEGACY_LABELS).astype(object)
