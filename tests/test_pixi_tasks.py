"""Pixi task wiring.

``validate`` and ``verify-bundle`` shell out to the ``oa-pipeline`` console
script, whose entry point is ``oa_pipeline.__main__:main``. That module does
not exist -- the prototype never had a CLI, and no P-1 or P0 task creates one.
The spec names ``oa-pipeline verify-bundle`` only in the v1.0.0 success-metrics
table, so the CLI is later scope.

Those two tests are marked xfail rather than deleted, so the requirement stays
visible. ``xfail_strict = true`` means they will fail loudly once the CLI is
implemented, forcing the markers off.
"""

import subprocess

import pytest

CLI_NOT_IMPLEMENTED = pytest.mark.xfail(
    reason="oa_pipeline.__main__ not implemented; oa-pipeline CLI is post-P0 scope",
    raises=AssertionError,
)


def test_pixi_run_pipeline_task():
    result = subprocess.run(["pixi", "run", "pipeline", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


def test_pixi_run_test_task():
    result = subprocess.run(["pixi", "run", "test", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


@CLI_NOT_IMPLEMENTED
def test_pixi_run_validate_task():
    result = subprocess.run(["pixi", "run", "validate", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


@CLI_NOT_IMPLEMENTED
def test_pixi_run_verify_bundle_task():
    result = subprocess.run(["pixi", "run", "verify-bundle", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


def test_pixi_run_pre_commit_all_task():
    result = subprocess.run(["pixi", "run", "pre-commit-all", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
