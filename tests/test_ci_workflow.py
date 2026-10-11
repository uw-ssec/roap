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
    assert set(matrix["os"]) == {"ubuntu-latest", "macos-latest", "windows-latest"}
    
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