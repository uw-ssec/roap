"""README consolidation validation."""
from pathlib import Path


def test_single_readme_at_root():
    readme = Path("README.md")
    assert readme.exists(), "README.md must exist at repo root"
    content = readme.read_text(encoding="utf-8")

    # Three paths documented
    assert "CLI" in content or "command line" in content.lower()
    assert "GUI" in content or "graphical" in content.lower()
    assert "notebook" in content.lower() or "papermill" in content.lower()

    # Prerequisites
    assert "pixi" in content.lower()
    assert "python" in content.lower()

    # Quickstart commands
    assert "pixi run pipeline" in content or "./run_pipeline.sh" in content
    assert "roap_app.py" in content or "python tools/roap_app.py" in content

    # Troubleshooting section
    assert "troubleshoot" in content.lower() or "faq" in content.lower()


def test_legacy_readmes_archived():
    legacy_dir = Path("docs/legacy")
    for name in ["APP_README.md", "ALKA_README.md", "SETUP_GUIDE.md"]:
        assert (legacy_dir / name).exists(), f"{name} must be archived in docs/legacy/"


def test_no_loose_scripts_at_root():
    root = Path(".")
    loose = ["oa_pipeline_app.py", "oa_pipeline_app_core.py", "stamp_carbonate_provenance.py"]
    for name in loose:
        assert not (root / name).exists(), f"{name} must be moved to tools/"


def test_readme_documents_git_bash_on_windows():
    content = Path("README.md").read_text(encoding="utf-8")
    assert "git bash" in content.lower(), "README must document Git Bash requirement on Windows"
    assert "windows" in content.lower(), "README must mention Windows explicitly"
