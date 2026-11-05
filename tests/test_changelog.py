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
    """A tagged build's version matches the newest CHANGELOG release.

    hatch-vcs takes the version from the git tag. Between tags it is a .devN
    pre-release that sorts after the newest CHANGELOG release, and a shallow
    clone without tags has no released version to compare.
    """
    import re
    from importlib.metadata import version as pkg_version
    from pathlib import Path
    from packaging.version import Version
    installed = Version(pkg_version("roap"))
    content = Path("CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## \[(\d[^\]]*)\]", content, flags=re.MULTILINE)
    assert released, "No released version in CHANGELOG.md"
    newest = Version(released[0])
    if not installed.is_devrelease:
        # Metadata normalizes zero-padding (2026.09.0 -> 2026.9.0); compare as versions.
        assert installed == newest
