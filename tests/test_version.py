# tests/test_version.py
import re

# CalVer YYYY.0M.MICRO (e.g. 2026.11.0), or the legacy SemVer 0.2.0 that
# predates the first CalVer release.
VERSION_RE = re.compile(r"^(\d{4}\.(0[1-9]|1[0-2])\.\d+|0\.2\.0)$")


def test_version_from_metadata():
    """__version__ comes from importlib.metadata (pyproject.toml)."""
    from roap import __version__
    from importlib.metadata import version as pkg_version

    assert __version__ == pkg_version("roap")
    assert isinstance(__version__, str)
    # Metadata normalizes zero-padding (2026.09.0 -> 2026.9.0), so check the
    # pyproject.toml string for the CalVer format.
    import tomllib
    with open("pyproject.toml", "rb") as f:
        pyproject_version = tomllib.load(f)["project"]["version"]
    assert VERSION_RE.match(pyproject_version), pyproject_version


def test_config_gate_orders_calver_after_semver():
    """The config gate compares CalVer and legacy SemVer numerically."""
    from roap.common import _version_satisfies

    assert _version_satisfies("2026.11.0", ">=0.2.0")
    assert _version_satisfies("2026.11.1", ">=2026.11.0")
    assert _version_satisfies("2026.10.0", ">=2026.9.0")  # not string order
    assert _version_satisfies("2026.9.0", "==2026.09.0")  # zero-padding ignored
    assert not _version_satisfies("2026.11.0", ">=2026.11.1")
    assert not _version_satisfies("0.2.0", ">=2026.11.0")
