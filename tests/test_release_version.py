"""CalVer dev/release versioning used by the publish workflow."""

import datetime as dt
import importlib.util
import shutil
from pathlib import Path

import pytest
import yaml
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "release_version", REPO_ROOT / "tools" / "release_version.py"
)
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)

NOV = dt.date(2026, 11, 3)


def test_next_release_first_of_month() -> None:
    assert rv.next_release(NOV, ["v0.2.0"]) == "2026.11.0"


def test_next_release_after_same_month_release() -> None:
    tags = ["v0.2.0", "v2026.11.0", "v2026.11.1", "v2026.10.4"]
    assert rv.next_release(NOV, tags) == "2026.11.2"


def test_next_release_ignores_other_months_and_junk() -> None:
    tags = ["v2026.10.7", "v2025.11.3", "v2026.11.x", "2026.11.5"]
    assert rv.next_release(NOV, tags) == "2026.11.0"


def test_next_release_pads_month() -> None:
    assert rv.next_release(dt.date(2027, 2, 1), []) == "2027.02.0"


def test_dev_version_is_pep440_prerelease_of_next_release() -> None:
    dev = rv.dev_version(NOV, ["v2026.11.0"], 3)
    assert dev == "2026.11.1.dev3"
    assert Version(dev).is_devrelease
    assert Version("2026.11.0") < Version(dev) < Version("2026.11.1")


def test_dev_versions_increase_across_a_release() -> None:
    before = rv.dev_version(NOV, ["v0.2.0"], 40)
    after = rv.dev_version(NOV, ["v0.2.0", "v2026.11.0"], 1)
    assert Version(before) < Version("2026.11.0") < Version(after)


def test_write_version_stamps_only_project_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    shutil.copy(REPO_ROOT / "pyproject.toml", pyproject)
    original = pyproject.read_text(encoding="utf-8")
    rv.write_version("2026.11.0.dev3", pyproject)
    assert rv.pyproject_version(pyproject) == "2026.11.0.dev3"
    changed = [
        (a, b)
        for a, b in zip(original.splitlines(), pyproject.read_text().splitlines())
        if a != b
    ]
    assert len(changed) == 1, changed


def test_check_tag() -> None:
    rv.check_tag("v2026.11.0", "2026.11.0")
    with pytest.raises(SystemExit, match="does not match"):
        rv.check_tag("v2026.11.1", "2026.11.0")
    with pytest.raises(SystemExit):
        rv.check_tag("2026.11.0", "2026.11.0")


def test_publish_workflow_routes_main_to_testpypi_and_release_to_pypi() -> None:
    wf = yaml.safe_load((REPO_ROOT / ".github/workflows/publish.yml").read_text())
    # PyYAML reads the bare `on:` key as True.
    triggers = wf[True]
    assert triggers["push"]["branches"] == ["main"]
    assert triggers["release"]["types"] == ["published"]

    jobs = wf["jobs"]
    test_job, prod_job = jobs["publish-testpypi"], jobs["publish-pypi"]
    assert "push" in test_job["if"] and test_job["environment"]["name"] == "testpypi"
    assert "release" in prod_job["if"] and prod_job["environment"]["name"] == "pypi"
    for job in (test_job, prod_job):
        assert job["permissions"] == {"id-token": "write"}  # trusted publishing
    test_publish = next(
        s for s in test_job["steps"] if "gh-action-pypi-publish" in s.get("uses", "")
    )
    assert test_publish["with"]["repository-url"] == "https://test.pypi.org/legacy/"
    prod_publish = next(
        s for s in prod_job["steps"] if "gh-action-pypi-publish" in s.get("uses", "")
    )
    assert "repository-url" not in prod_publish.get("with", {})

    build_runs = "\n".join(s.get("run", "") for s in jobs["build"]["steps"])
    assert "release_version.py dev --write" in build_runs
    assert "release_version.py check-tag" in build_runs
