# tests/test_stage1b_row_classification.py
"""Stage 1B reads Row roles from ``row_role`` instead of classifying rows (#40)."""

from __future__ import annotations

import copy

import pandas as pd
import pytest

import roap.stage1b as stage1b
from roap.stage1b import STAGE1B_DEFAULTS, add_presence_flags, add_provenance_fields


def test_crm_and_std_rows_are_not_sample_rows() -> None:
    """is_sample_row is a boolean, so CRM/STD rows are not flagged as samples (#47)."""
    df = pd.DataFrame(
        {
            "row_role": ["SAMPLE", "CRM", "STANDARD"],
            "ta_best_umolkg": [2300.0, float("nan"), float("nan")],
            "ph_best": [8.1, float("nan"), float("nan")],
        }
    )

    add_provenance_fields(df, copy.deepcopy(STAGE1B_DEFAULTS))
    # The sample row has complete core chemistry; CRM/STD rows have none.
    df["calc_salinity"] = 35.0
    df["calc_temperature_c"] = 25.0
    df["calc_pressure_dbar"] = 0.0
    add_presence_flags(df)

    assert df["is_sample_row"].tolist() == [True, False, False]
    assert df["flag_core_chemistry_missing"].tolist() == [False, False, False]


def test_sample_type_is_not_a_row_role_signal() -> None:
    """sample_type no longer decides anything: row_role is the only input (ADR-0006)."""
    df = pd.DataFrame(
        {
            "row_role": ["SAMPLE", "SAMPLE", "STANDARD"],
            "sample_type": ["crm", "phstd", "sample"],
        },
        index=[10, 3, 7],
    )
    add_provenance_fields(df, copy.deepcopy(STAGE1B_DEFAULTS))
    assert df["is_sample_row"].tolist() == [True, True, False]


def test_missing_row_role_fails_with_a_clear_message() -> None:
    df = pd.DataFrame({"sample_type": ["sample"]})
    with pytest.raises(KeyError, match="row_role"):
        add_provenance_fields(df, copy.deepcopy(STAGE1B_DEFAULTS))


def test_classify_rows_sample_is_removed() -> None:
    assert not hasattr(stage1b, "classify_rows_sample")
