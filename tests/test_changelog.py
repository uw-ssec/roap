# tests/test_changelog.py
def test_changelog_exists_and_format():
    """CHANGELOG.md exists and follows Keep a Changelog format."""
    from pathlib import Path
    changelog = Path("CHANGELOG.md")
    assert changelog.exists(), "CHANGELOG.md missing"
    content = changelog.read_text(encoding="utf-8")
    assert "## [Unreleased]" in content, "[Unreleased] section missing"
    assert "### Added" in content or "### Fixed" in content or "### Changed" in content, "No changelog sections"


def test_version_consistency():
    """pyproject.toml, package metadata, and the newest CHANGELOG release agree."""
    import re
    import tomli
    from importlib.metadata import version as pkg_version
    from pathlib import Path
    from packaging.version import Version
    pyproject_version = tomli.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    init_version = pkg_version("roap")
    content = Path("CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## \[(\d[^\]]*)\]", content, flags=re.MULTILINE)
    assert released, "No released version in CHANGELOG.md"
    # Metadata normalizes zero-padding (2026.09.0 -> 2026.9.0); compare as versions.
    assert Version(pyproject_version) == Version(init_version) == Version(released[0])
