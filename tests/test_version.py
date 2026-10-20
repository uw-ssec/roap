# tests/test_version.py
def test_version_from_metadata():
    """__version__ comes from importlib.metadata (pyproject.toml)."""
    from roap import __version__
    from importlib.metadata import version as pkg_version

    assert __version__ == pkg_version("roap")
    assert __version__ == "0.2.0"  # after P1-T1 tag
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) >= 2  # major.minor at minimum
