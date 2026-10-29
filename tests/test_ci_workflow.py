"""CI workflow validation."""
import yaml
from pathlib import Path


def test_ci_workflow_exists_and_valid():
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.exists(), "CI workflow file must exist"

    with workflow_path.open() as f:
        workflow = yaml.safe_load(f)

    # Matrix strategy
    assert "strategy" in workflow["jobs"]["test"]
    matrix = workflow["jobs"]["test"]["strategy"]["matrix"]
    assert "os" in matrix
    assert set(matrix["os"]) == {
        "blacksmith-2vcpu-ubuntu-2404",
        "blacksmith-6vcpu-macos-15",
        "blacksmith-2vcpu-windows-2025",
    }

    # Python 3.11
    setup_python_step = next(s for s in workflow["jobs"]["test"]["steps"]
                             if s.get("uses", "").startswith("actions/setup-python"))
    assert setup_python_step["with"]["python-version"] == "3.11"

    # Pixi install
    pixi_step = next(s for s in workflow["jobs"]["test"]["steps"]
                     if "pixi" in s.get("run", "").lower() or "pixi" in s.get("uses", "").lower())
    assert "pixi install" in pixi_step.get("run", "") or "setup-pixi" in pixi_step.get("uses", "")

    # pre-commit-all runs
    precommit_step = next(s for s in workflow["jobs"]["test"]["steps"]
                          if "pre-commit-all" in s.get("run", ""))
    assert "pixi run pre-commit-all" in precommit_step["run"]

    # pytest runs
    pytest_step = next(s for s in workflow["jobs"]["test"]["steps"]
                       if "pytest" in s.get("run", ""))
    assert "pytest -q" in pytest_step["run"]

    # Pipeline E2E runs
    pipeline_step = next(s for s in workflow["jobs"]["test"]["steps"]
                         if "run_pipeline" in s.get("run", ""))
    assert "./run_pipeline.sh" in pipeline_step["run"]
    assert "examples/example_data.xlsx" in pipeline_step["run"]
    assert "outputs/ci_test" in pipeline_step["run"]

    # Artifact upload
    artifact_step = next(s for s in workflow["jobs"]["test"]["steps"]
                         if "upload-artifact" in s.get("uses", ""))
    assert "analysis_ready.csv" in artifact_step.get("with", {}).get("path", "")


def test_cold_install_workflow_is_manual_uncached_and_timed():
    workflow_path = Path(".github/workflows/cold-install.yml")
    with workflow_path.open() as f:
        workflow = yaml.safe_load(f)

    # PyYAML parses the bare `on:` key as boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert "workflow_dispatch" in triggers
    assert triggers["pull_request"]["paths"] == [".github/workflows/cold-install.yml"]
    assert "push" not in triggers

    job = workflow["jobs"]["cold-install"]
    assert set(job["strategy"]["matrix"]["os"]) == {
        "blacksmith-4vcpu-ubuntu-2404",
        "blacksmith-6vcpu-macos-15",
        "blacksmith-4vcpu-windows-2025",
    }
    assert job["env"]["BUDGET_SECONDS"] == "600"

    steps = job["steps"]
    assert not any("actions/cache" in s.get("uses", "") for s in steps)
    setup = next(s for s in steps if "setup-pixi" in s.get("uses", ""))
    assert setup["with"]["run-install"] is False
    assert setup["with"]["cache"] is False

    runs = [s.get("run", "") for s in steps]
    cache_step = next(r for r in runs if "PIXI_CACHE_DIR=" in r)
    assert "RATTLER_CACHE_DIR=" in cache_step
    assert "already exists" in cache_step

    # Clone, install and pipeline each record their own timing, in order.
    timed = [r for r in runs if "timings" in r and "start=$(date +%s)" in r]
    assert [t.split("echo \"")[1].split("|")[0] for t in timed] == [
        "Fresh clone",
        "pixi install",
        "Example pipeline",
    ]
    assert "git clone" in timed[0]
    # Fork PR heads are not in the base clone, so the PR ref is fetched first.
    fetch = timed[0].index('fetch origin "refs/pull/$PR_NUMBER/head"')
    assert fetch < timed[0].index('checkout --detach "$SHA"')
    assert "pixi install" in timed[1]
    assert "pixi run pipeline examples/example_data.xlsx outputs/test" in timed[2]

    summary = steps[-1]
    assert summary["if"] == "always()"
    assert '"$total" -gt "$BUDGET_SECONDS"' in summary["run"]
