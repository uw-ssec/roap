"""Tests for roap.row_roles: the single Tag-prefix rule for Row roles (ADR-0006, #40)."""

from __future__ import annotations

import pandas as pd
import pytest

from roap import row_roles
from roap.row_roles import RowRole


@pytest.mark.parametrize(
    ("tag", "prefixes", "expected"),
    [
        # Default prefixes: RM -> CRM, TRIS -> Standard, everything else -> Sample.
        ("RM213_01", None, RowRole.CRM),
        ("TRIS_A", None, RowRole.STANDARD),
        ("S001", None, RowRole.SAMPLE),
        # Case-insensitive, surrounding whitespace ignored.
        ("rm213_02", None, RowRole.CRM),
        ("  tris_b ", None, RowRole.STANDARD),
        ("Tris-certified", None, RowRole.STANDARD),
        # Prefix, not substring: a tag containing RM elsewhere is a Sample.
        ("S_RM_01", None, RowRole.SAMPLE),
        # Blank, missing and unrecognised tags are Samples.
        ("", None, RowRole.SAMPLE),
        ("   ", None, RowRole.SAMPLE),
        (None, None, RowRole.SAMPLE),
        (float("nan"), None, RowRole.SAMPLE),
        ("BLANK_01", None, RowRole.SAMPLE),
        # Configured prefixes replace the defaults; one key keeps the other default.
        ("CRM-7", {"CRM": "CRM"}, RowRole.CRM),
        ("RM213_01", {"CRM": "CRM"}, RowRole.SAMPLE),
        ("TRIS_A", {"CRM": "CRM"}, RowRole.STANDARD),
        ("std_1", {"standard": "STD"}, RowRole.STANDARD),
        ("RM213_01", {RowRole.STANDARD: "STD"}, RowRole.CRM),
    ],
)
def test_assign_row_roles_from_tag_prefix(tag, prefixes, expected) -> None:
    df = pd.DataFrame({"sample_tag": [tag]})
    assert row_roles.assign_row_roles(df, prefixes).tolist() == [expected.value]


def test_assign_ignores_sample_type_and_crm_flag_columns() -> None:
    """The Tag prefix is the only signal: sample_type / crm_or_sample are not read."""
    df = pd.DataFrame(
        {
            "sample_tag": ["S001", "RM213_01", "TRIS_A"],
            "sample_type": ["crm", "sample", "phstd"],
            "crm_or_sample": ["crm", "sample", "crm"],
        }
    )
    assert row_roles.assign_row_roles(df).tolist() == ["SAMPLE", "CRM", "STANDARD"]


def test_masks_and_legacy_labels_on_non_range_index() -> None:
    df = pd.DataFrame(
        {"sample_tag": ["TRIS_A", "S001", "RM213_01", ""]}, index=[30, 10, 20, 99]
    )
    df[row_roles.ROW_ROLE_COL] = row_roles.assign_row_roles(df)

    assert row_roles.is_sample(df).to_dict() == {30: False, 10: True, 20: False, 99: True}
    assert row_roles.is_crm(df).to_dict() == {30: False, 10: False, 20: True, 99: False}
    assert row_roles.is_standard(df).to_dict() == {30: True, 10: False, 20: False, 99: False}
    assert row_roles.is_sample(df).dtype == bool
    assert row_roles.legacy_classification(df).tolist() == ["STD", "SAMPLE", "CRM", "SAMPLE"]
    assert row_roles.summarize_row_roles(df) == {
        "SAMPLE": 2,
        "CRM": 1,
        "STANDARD": 1,
        "n_sample_tag_missing": 1,
    }


@pytest.mark.parametrize(
    "prefixes",
    [
        {"SAMPLE": "S"},  # Samples have no prefix
        {"BLANK": "BL"},  # unknown role
        {"CRM": ""},
        {"STANDARD": "   "},
        {"CRM": None},
        {"CRM": "TR", "STANDARD": "TRIS"},  # overlapping prefixes
        {"CRM": "rm", "STANDARD": "RMX"},  # overlap is case-insensitive
    ],
)
def test_parse_prefixes_rejects_invalid_config(prefixes) -> None:
    with pytest.raises(ValueError):
        row_roles.parse_prefixes(prefixes)


def test_missing_columns_raise_clear_errors() -> None:
    with pytest.raises(KeyError, match="sample_tag"):
        row_roles.assign_row_roles(pd.DataFrame({"tag": ["S001"]}))
    with pytest.raises(KeyError, match="Stage QC"):
        row_roles.is_sample(pd.DataFrame({"sample_tag": ["S001"]}))


@pytest.mark.parametrize("bad", [["SAMPLE", "BLANK"], ["SAMPLE", None], ["STD"]])
def test_masks_reject_unknown_or_missing_roles(bad) -> None:
    with pytest.raises(ValueError, match="row_role"):
        row_roles.is_crm(pd.DataFrame({row_roles.ROW_ROLE_COL: bad}))


def test_masks_accept_lowercase_stored_roles() -> None:
    df = pd.DataFrame({row_roles.ROW_ROLE_COL: ["crm", "standard", "sample"]})
    assert row_roles.is_crm(df).tolist() == [True, False, False]
