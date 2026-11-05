# tests/test_version.py
def test_version_from_metadata():
    """__version__ comes from importlib.metadata, which hatch-vcs fills from the git tag."""
    from roap import __version__
    from importlib.metadata import version as pkg_version

    assert __version__ == pkg_version("roap")
    assert isinstance(__version__, str)


def test_version_is_dynamic_from_git_tag():
    """pyproject.toml takes its version from the git tag via hatch-vcs, not a literal."""
    import tomllib

    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    assert "version" not in pyproject["project"]
    assert "version" in pyproject["project"]["dynamic"]
    assert pyproject["build-system"]["build-backend"] == "hatchling.build"
    assert "hatch-vcs" in " ".join(pyproject["build-system"]["requires"])
    assert pyproject["tool"]["hatch"]["version"]["source"] == "vcs"


def test_config_gate_orders_calver_after_semver():
    """The config gate compares CalVer and legacy SemVer numerically."""
    from roap.common import _version_satisfies

    assert _version_satisfies("2026.11.0", ">=0.2.0")
    assert _version_satisfies("2026.11.1", ">=2026.11.0")
    assert _version_satisfies("2026.10.0", ">=2026.9.0")  # not string order
    assert _version_satisfies("2026.9.0", "==2026.09.0")  # zero-padding ignored
    assert not _version_satisfies("2026.11.0", ">=2026.11.1")
    assert not _version_satisfies("0.2.0", ">=2026.11.0")


def test_config_gate_orders_git_dev_versions_before_their_release():
    """A build between tags (hatch-vcs .devN) is a pre-release of the next version."""
    from roap.common import _version_satisfies

    assert _version_satisfies("2026.11.1.dev3", ">=2026.11.0")
    assert _version_satisfies("0.2.1.dev40", ">=0.2.0")
    assert not _version_satisfies("2026.11.1.dev3", ">=2026.11.1")  # same-release minimum
    assert not _version_satisfies("2026.11.1.dev3", "==2026.11.1")  # exact pin
    assert _version_satisfies("2026.11.1.dev3", "==2026.11.1.dev3")
    assert not _version_satisfies("2026.11.1.dev3", ">=2026.12.0")


def test_config_gate_rejects_malformed_versions():
    """A typo in compatible_pipeline_version fails loudly instead of passing."""
    import pytest
    from packaging.version import InvalidVersion
    from roap.common import _version_satisfies, check_config_compatibility

    with pytest.raises(InvalidVersion):
        _version_satisfies("2026.11.0", ">=2026.11.0typo")
    with pytest.raises(SystemExit, match="invalid compatible_pipeline_version"):
        check_config_compatibility({"compatible_pipeline_version": ">=2026.11.0typo"}, "x.yaml")


def test_pixi_workspace_has_no_hardcoded_version():
    """The git tag is the only version source; pixi.toml must not carry a second copy."""
    import tomllib

    with open("pixi.toml", "rb") as f:
        assert "version" not in tomllib.load(f)["workspace"]
