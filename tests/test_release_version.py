"""CalVer dev/release versioning used by the publish workflow."""

import datetime as dt
import importlib.util
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


def test_check_tag() -> None:
    rv.check_tag("v2026.11.0")
    rv.check_tag("v2026.09.12")
    for bad in ("2026.11.0", "v2026.9.0", "v2026.13.0", "v2026.11", "v2026.11.0rc1"):
        with pytest.raises(SystemExit):
            rv.check_tag(bad)


def _dist(tmp_path: Path, *names: str) -> Path:
    tmp_path.mkdir(exist_ok=True)
    for name in names:
        (tmp_path / name).touch()
    return tmp_path


def test_check_dist_accepts_tag_version_with_normalized_month(tmp_path: Path) -> None:
    dist = _dist(tmp_path, "roap-2026.9.0.tar.gz", "roap-2026.9.0-py3-none-any.whl")
    assert len(rv.check_dist("v2026.09.0", dist)) == 2


def test_check_dist_rejects_wrong_or_missing_version(tmp_path: Path) -> None:
    dev = _dist(tmp_path / "dev", "roap-2026.11.1.dev3.tar.gz", "roap-2026.11.1.dev3-py3-none-any.whl")
    with pytest.raises(SystemExit, match="is not version"):
        rv.check_dist("v2026.11.0", dev)
    wheel_only = _dist(tmp_path / "wheel", "roap-2026.11.0-py3-none-any.whl")
    with pytest.raises(SystemExit, match="one sdist and one wheel"):
        rv.check_dist("v2026.11.0", wheel_only)


def test_publish_workflow_routes_main_to_testpypi_and_release_to_pypi() -> None:
    wf = yaml.safe_load((REPO_ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8"))
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
    assert "release_version.py dev" in build_runs
    assert "SETUPTOOLS_SCM_PRETEND_VERSION" in build_runs
    assert "--write" not in build_runs
    assert "release_version.py check-tag" in build_runs
    assert "release_version.py check-dist" in build_runs
