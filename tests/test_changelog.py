# tests/test_changelog.py
def test_changelog_exists_and_format():
    """CHANGELOG.md exists and follows Keep a Changelog format."""
    from pathlib import Path
    changelog = Path("CHANGELOG.md")
    assert changelog.exists(), "CHANGELOG.md missing"
    content = changelog.read_text()
    assert "## [0.2.0]" in content, "v0.2.0 entry missing"
    assert "### Added" in content or "### Fixed" in content or "### Changed" in content, "No changelog sections"


def test_version_consistency():
    """pyproject.toml, __init__.py, and git tag agree on version."""
    import tomli
    from importlib.metadata import version as pkg_version
    from pathlib import Path
    pyproject_version = tomli.loads(Path("pyproject.toml").read_text())["project"]["version"]
    init_version = pkg_version("roap")
    assert pyproject_version == init_version == "0.2.0"