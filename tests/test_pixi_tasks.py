import subprocess


def test_pixi_run_pipeline_task():
    result = subprocess.run(["pixi", "run", "pipeline", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


def test_pixi_run_test_task():
    result = subprocess.run(["pixi", "run", "test", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


def test_pixi_run_validate_task():
    result = subprocess.run(["pixi", "run", "validate", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


def test_pixi_run_verify_bundle_task():
    result = subprocess.run(["pixi", "run", "verify-bundle", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


def test_pixi_run_pre_commit_all_task():
    result = subprocess.run(["pixi", "run", "pre-commit-all", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
