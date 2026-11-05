"""Notebook-parameter helpers and the HTML table in roap.common (#42)."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.mark.parametrize(
    "value, expected",
    [(True, True), (False, False), (None, False), (float("nan"), False), ("Yes", True),
     ("on", True), (1, True), ("0", False), ("off", False), ("", False), ("None", False),
     ("null", False), (0, False)],
)
def test_as_bool_reads_common_spellings(value, expected) -> None:
    from roap.common import as_bool

    assert as_bool(value) is expected


def test_as_bool_rejects_other_text() -> None:
    from roap.common import as_bool

    with pytest.raises(SystemExit):
        as_bool("maybe")


@pytest.mark.parametrize("value", [None, "", " none ", "NULL"])
def test_is_none_like(value) -> None:
    from roap.common import is_none_like

    assert is_none_like(value)
    assert not is_none_like("0")


def test_write_html_table_writes_html_table_text(tmp_path) -> None:
    from roap.common import html_table, write_html_table

    df = pd.DataFrame({"a": ["<b>"]})
    out = tmp_path / "t.html"
    write_html_table(df, out, title="T")
    written = out.read_text(encoding="utf-8")
    assert "&lt;b&gt;" in written and "<h3>T</h3>" in written
    assert html_table(df, 1, "T").split("<p><b>Generated")[0] == written.split("<p><b>Generated")[0]
