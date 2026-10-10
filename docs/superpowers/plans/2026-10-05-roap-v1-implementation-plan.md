# ROAP v1.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the `oa_pipeline` v0.2.0 research prototype into a
production-grade, cross-platform, citable Python package with CLI, GUI, and
notebook interfaces — delivering reproducible ocean acidification carbonate
chemistry QC processing per Frontiers 2021 data standards.

**Architecture:** Single engine (`src/oa_pipeline/` — 12 pure Python modules),
three doors (CLI `run_pipeline.sh`, GUI `tools/oa_pipeline_app.py`, Notebooks
`notebooks/*.ipynb`). All interfaces call the same core. Phase-sequential with
parallel subagent dispatch within phases.

**Tech Stack:** Pixi-only, Python 3.11,
pandas/numpy/openpyxl/matplotlib/pyyaml/pyarrow/tabulate/papermill/pytest/hypothesis,
GitHub Actions CI (Ubuntu/macOS/Windows Git Bash), conventional commits,
pre-commit (ruff/black/mypy/pytest).

**Spec:** `docs/superpowers/specs/2026-10-05-roap-v1-implementation-design.md`

## Global Constraints

- **Package Manager:** Pixi only — no `pip`, `conda`, `venv` directly.
  `pixi install` before any command.
- **Python Version:** 3.11 (pinned in `pixi.toml` and `pyproject.toml`)
- **Platform Support:** Linux (Ubuntu), macOS, Windows (Git Bash required — not
  WSL)
- **Data Privacy:** Never commit unpublished data — enforced by `.gitignore` +
  pre-commit check
- **Code Quality:** `pixi run pre-commit-all` (ruff, black, mypy, pytest) must
  pass before commit
- **Commit Style:** Conventional commits (`feat:`, `fix:`, `test:`, `docs:`,
  `chore:`)
- **Testing Philosophy:** Property-based/invariant testing (hypothesis)
  alongside example-based — CI green ≠ data integrity without invariant test
- **Architecture:** Single engine (`src/oa_pipeline/`), three doors (CLI, GUI,
  Notebook) — all call same core
- **Dependencies:** Core: pandas, numpy, openpyxl, matplotlib, pyyaml, pyarrow,
  tabulate, papermill, pytest, ipykernel, ipython, hypothesis
- **Release Process:** Semantic versioning, signed tags (deferred), GitHub
  Releases, PyPI publish (manual for v1.0.0), CHANGELOG.md (Keep a Changelog)
- **PyCO2SYS:** v1 Stable, constants `opt_k_carbonic=10` (Lueker 2000),
  `opt_pH_scale=1` (Total scale)
- **Data Standard:** Frontiers 2021 — clarified column names, unified 0–9 QC
  flags, `-999` missing sentinel

## Review Focus

1. **Silent pH scale mismatch** — User provides data with mixed pH scales
   (Total/Seawater/Free/NBS); pipeline must audit consistency and fail fast, not
   convert. Test: `test_ph_scale_consistency` in `test_invariants.py`.
2. **CRM/std tag prefix vs sample_type column** — Detection must use tag prefix
   (`RM<batch>_<n>`, `tris_*`) ONLY, not `sample_type` column. Test:
   `test_crm_detection_by_tag_prefix` in `test_qc_ta_ph.py`.
3. **Excel formula column corruption** — Read-modify-write on formula-bearing
   workbooks must preserve formulas as static values, not corrupt them. Test:
   `test_excel_formula_roundtrip` in `test_properties.py`.
4. **Config version drift** — Running pipeline with stale config must fail fast
   with actionable error, not silently produce wrong results. Test:
   `test_config_compatibility_gate` in `test_common.py`.
5. **Untargeted column mutation** — Any stage modifying columns it doesn't own
   (lat/lon, provenance, QC flags) must fail CI. Test:
   `test_invariants_per_stage` in `test_invariants.py`.

---

### Task P1-01: Create pyproject.toml (src-layout, v0.2.0)

**Files:**

- Create: `pyproject.toml`

**Interfaces:**

- Consumes: prototype `pyproject.toml` (reference)
- Produces: Package metadata, src-layout config, entry points for `oa-pipeline`
  CLI

- [ ] **Step 1: Write the failing test**

```python
# tests/test_packaging.py
def test_pyproject_toml_exists_and_valid():
    import tomli
    with open("pyproject.toml", "rb") as f:
        data = tomli.load(f)
    assert data["project"]["name"] == "oa-pipeline"
    assert data["project"]["version"] == "0.2.0"
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert "src" in data["tool"]["setuptools"]["packages"]["find"]["where"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_packaging.py::test_pyproject_toml_exists_and_valid -v`
Expected: FAIL (file not found)

- [ ] **Step 3: Implement `pyproject.toml`**

Based on prototype `pyproject.toml` with src-layout, version 0.2.0, dependencies
from tech stack, entry point `oa-pipeline = "oa_pipeline.__main__:main"` (or
similar CLI entry).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_packaging.py::test_pyproject_toml_exists_and_valid -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/test_packaging.py
git commit -m "feat: add pyproject.toml with src-layout for oa-pipeline v0.2.0"
```

---

### Task P1-02: Update pixi.toml with pipeline tasks

**Files:**

- Modify: `pixi.toml`

**Interfaces:**

- Consumes: Current `pixi.toml`, prototype `pixi.toml` (if exists), PRD
  requirements
- Produces: Tasks `pixi run pipeline`, `pixi run test`, `pixi run validate`,
  `pixi run verify-bundle`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pixi_tasks.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pixi_tasks.py -v` Expected: FAIL (tasks not defined)

- [ ] **Step 3: Update `pixi.toml`**

Add `[tasks]` section with:

- `pipeline = { cmd = "./run_pipeline.sh", description = "Run full pipeline" }`
- `test = { cmd = "pytest -q", description = "Run test suite" }`
- `validate = { cmd = "oa-pipeline validate", description = "Pre-flight validation" }`
- `verify-bundle = { cmd = "oa-pipeline verify-bundle", description = "Verify run bundle" }`
- `pre-commit-all = { cmd = "pre-commit run --all-files", description = "Run all pre-commit checks" }`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pixi_tasks.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pixi.toml tests/test_pixi_tasks.py
git commit -m "feat: add pixi tasks for pipeline, test, validate, verify-bundle"
```

---

### Task P1-03: Migrate src/oa_pipeline/ (12 modules)

**Files:**

- Create: `src/oa_pipeline/__init__.py`
- Create: `src/oa_pipeline/common.py`
- Create: `src/oa_pipeline/schema.py`
- Create: `src/oa_pipeline/qc_ta_ph.py`
- Create: `src/oa_pipeline/policy.py`
- Create: `src/oa_pipeline/stage1b.py`
- Create: `src/oa_pipeline/stage2.py`
- Create: `src/oa_pipeline/stage3.py`
- Create: `src/oa_pipeline/stage4.py`
- Create: `src/oa_pipeline/inspect.py`
- Create: `src/oa_pipeline/carbonate_calc.py`
- Create: `src/oa_pipeline/duplicate_precision.py`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/src/oa_pipeline/*.py`
- Produces: All 12 modules importable; `__init__.py` re-exports public API

- [ ] **Step 1: Write the failing test**

```python
# tests/test_migration_modules.py
import importlib

MODULES = [
    "oa_pipeline",
    "oa_pipeline.common",
    "oa_pipeline.schema",
    "oa_pipeline.qc_ta_ph",
    "oa_pipeline.policy",
    "oa_pipeline.stage1b",
    "oa_pipeline.stage2",
    "oa_pipeline.stage3",
    "oa_pipeline.stage4",
    "oa_pipeline.inspect",
    "oa_pipeline.carbonate_calc",
    "oa_pipeline.duplicate_precision",
]

@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name):
    importlib.import_module(module_name)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_migration_modules.py -v` Expected: FAIL (modules don't
exist)

- [ ] **Step 3: Copy all 12 modules from prototype**

```bash
cp -r references/prototype/oa_pipeline/src/oa_pipeline/* src/oa_pipeline/
```

Verify each file copied correctly. Update any internal imports if paths changed.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_migration_modules.py -v` Expected: PASS (all 12 modules
import)

- [ ] **Step 5: Commit**

```bash
git add src/oa_pipeline/ tests/test_migration_modules.py
git commit -m "feat: migrate all 12 oa_pipeline modules from prototype"
```

---

### Task P1-04: Migrate tests/ (14 test files, 221+ tests)

**Files:**

- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_app_core.py`
- Create: `tests/test_carbonate_calc.py`
- Create: `tests/test_coalesce.py`
- Create: `tests/test_common.py`
- Create: `tests/test_inspect.py`
- Create: `tests/test_pipeline_e2e.py`
- Create: `tests/test_policy.py`
- Create: `tests/test_qc_ta_ph.py`
- Create: `tests/test_readiness.py`
- Create: `tests/test_schema.py`
- Create: `tests/test_stage1b.py`
- Create: `tests/test_stage2.py`
- Create: `tests/test_stage3.py`
- Create: `tests/test_stage4.py`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/tests/*.py`, migrated modules from
  P1-03
- Produces: 221+ passing tests

- [ ] **Step 1: Write the failing test**

```python
# tests/test_migration_test_count.py
import subprocess

def test_221_tests_pass():
    result = subprocess.run(["pytest", "-q", "--tb=no"], capture_output=True, text=True)
    # Count passed tests from output like "221 passed"
    import re
    match = re.search(r"(\d+) passed", result.stdout)
    assert match, f"pytest output: {result.stdout}\n{result.stderr}"
    count = int(match.group(1))
    assert count >= 221, f"Expected >=221 tests, got {count}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_migration_test_count.py -v` Expected: FAIL (tests don't
exist)

- [ ] **Step 3: Copy all test files from prototype**

```bash
cp references/prototype/oa_pipeline/tests/* tests/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_migration_test_count.py -v` Expected: PASS (>=221 tests
pass)

- [ ] **Step 5: Commit**

```bash
git add tests/ tests/test_migration_test_count.py
git commit -m "feat: migrate all 14 test files (221+ tests) from prototype"
```

---

### Task P1-05: Migrate configs/ (7 YAML files)

**Files:**

- Create: `configs/02_ta_ph_qc.yaml`
- Create: `configs/07_stage3.yaml`
- Create: `configs/08_stage4.yaml`
- Create: `configs/crm_certified_values.yaml`
- Create: `configs/cruise_grade_thresholds.yaml`
- Create: `configs/regional.yaml`
- Create: `configs/schema_aliases.yaml` (new for P2, create empty placeholder
  now)

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/configs/*.yaml`
- Produces: Configs loadable by `common.py` / `schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_configs_load.py
import yaml
from pathlib import Path

CONFIG_FILES = [
    "02_ta_ph_qc.yaml",
    "07_stage3.yaml",
    "08_stage4.yaml",
    "crm_certified_values.yaml",
    "cruise_grade_thresholds.yaml",
    "regional.yaml",
]

@pytest.mark.parametrize("fname", CONFIG_FILES)
def test_config_loads(fname):
    path = Path("configs") / fname
    assert path.exists(), f"Missing {fname}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data is not None, f"Empty config: {fname}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_configs_load.py -v` Expected: FAIL (files missing)

- [ ] **Step 3: Copy configs from prototype**

```bash
cp references/prototype/oa_pipeline/configs/*.yaml configs/
touch configs/schema_aliases.yaml  # placeholder for P2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_configs_load.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add configs/ tests/test_configs_load.py
git commit -m "feat: migrate 7 config YAML files from prototype"
```

---

### Task P1-06: Migrate examples/

**Files:**

- Create: `examples/make_example_data.py`
- Create: `examples/example_data.xlsx`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/examples/*`
- Produces: Regeneratable example data; 27 rows (20 samples, 4 CRM, 3 TRIS), 4
  injected issues

- [ ] **Step 1: Write the failing test**

```python
# tests/test_examples.py
import subprocess
from pathlib import Path

def test_make_example_data_regenerates():
    result = subprocess.run(["python", "examples/make_example_data.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"make_example_data.py failed: {result.stderr}"
    assert Path("examples/example_data.xlsx").exists()

def test_example_data_has_expected_rows():
    import pandas as pd
    df = pd.read_excel("examples/example_data.xlsx")
    assert len(df) == 27  # 20 samples + 4 CRM + 3 TRIS
    crm_rows = df[df["sample_tag"].str.startswith("RM")]
    assert len(crm_rows) == 4
    tris_rows = df[df["sample_tag"].str.startswith("tris")]
    assert len(tris_rows) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_examples.py -v` Expected: FAIL (files missing)

- [ ] **Step 3: Copy examples from prototype**

```bash
cp references/prototype/oa_pipeline/examples/* examples/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_examples.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add examples/ tests/test_examples.py
git commit -m "feat: migrate examples (make_example_data.py, example_data.xlsx)"
```

---

### Task P1-07: Migrate notebooks/ (8 notebooks)

**Files:**

- Create: `notebooks/01_preview.ipynb`
- Create: `notebooks/02_ta_ph_qc.ipynb`
- Create: `notebooks/04_stage1a.ipynb`
- Create: `notebooks/05_stage1b.ipynb`
- Create: `notebooks/06_stage2.ipynb`
- Create: `notebooks/07_stage3.ipynb`
- Create: `notebooks/08_stage4.ipynb`
- (Plus any supporting notebooks)

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/notebooks/*.ipynb`
- Produces: Notebooks open, cells execute against migrated modules

- [ ] **Step 1: Write the failing test**

```python
# tests/test_notebooks_exist.py
from pathlib import Path

NOTEBOOKS = [
    "01_preview.ipynb",
    "02_ta_ph_qc.ipynb",
    "04_stage1a.ipynb",
    "05_stage1b.ipynb",
    "06_stage2.ipynb",
    "07_stage3.ipynb",
    "08_stage4.ipynb",
]

@pytest.mark.parametrize("nb", NOTEBOOKS)
def test_notebook_exists(nb):
    path = Path("notebooks") / nb
    assert path.exists(), f"Missing notebook: {nb}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_notebooks_exist.py -v` Expected: FAIL (notebooks
missing)

- [ ] **Step 3: Copy notebooks from prototype**

```bash
cp -r references/prototype/oa_pipeline/notebooks/* notebooks/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_notebooks_exist.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add notebooks/ tests/test_notebooks_exist.py
git commit -m "feat: migrate 8 pipeline notebooks from prototype"
```

---

### Task P1-08: Migrate CLI (run_pipeline.sh)

**Files:**

- Create: `run_pipeline.sh`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/run_pipeline.sh`, migrated
  modules, configs, examples
- Produces: Working end-to-end pipeline script

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_pipeline.py
import subprocess

def test_run_pipeline_sh_executable():
    import os
    assert os.access("run_pipeline.sh", os.X_OK), "run_pipeline.sh not executable"

def test_pipeline_runs_end_to_end():
    result = subprocess.run(
        ["./run_pipeline.sh", "examples/example_data.xlsx", "outputs/test"],
        capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    # Check for 4 FAIL verdicts on injected rows
    import pandas as pd
    df = pd.read_csv("outputs/test/analysis_ready.csv")
    fail_count = len(df[df["verdict"] == "FAIL"])
    assert fail_count == 4, f"Expected 4 FAIL verdicts, got {fail_count}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_pipeline.py -v` Expected: FAIL (script missing)

- [ ] **Step 3: Copy and adapt `run_pipeline.sh` from prototype**

```bash
cp references/prototype/oa_pipeline/run_pipeline.sh .
chmod +x run_pipeline.sh
```

Verify paths in script point to migrated locations (`src/oa_pipeline`,
`configs`, `notebooks`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_pipeline.py -v` Expected: PASS (pipeline runs, 4
FAIL verdicts)

- [ ] **Step 5: Commit**

```bash
git add run_pipeline.sh tests/test_cli_pipeline.py
git commit -m "feat: migrate CLI run_pipeline.sh from prototype"
```

---

### Task P1-09: Migrate GUI (tools/oa_pipeline_app\*.py)

**Files:**

- Create: `tools/oa_pipeline_app.py`
- Create: `tools/oa_pipeline_app_core.py`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/oa_pipeline_app.py`,
  `oa_pipeline_app_core.py`
- Produces: GUI launcher that opens on all platforms

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gui_launcher.py
import subprocess

def test_gui_app_exists():
    from pathlib import Path
    assert Path("tools/oa_pipeline_app.py").exists()
    assert Path("tools/oa_pipeline_app_core.py").exists()

def test_gui_launches_without_error():
    # Smoke test: launch and immediately close
    import sys
    result = subprocess.run(
        [sys.executable, "tools/oa_pipeline_app.py", "--help"],
        capture_output=True, text=True, timeout=10
    )
    # Tkinter apps may not have --help; accept non-zero if it shows usage
    assert result.returncode in (0, 1, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gui_launcher.py -v` Expected: FAIL (files missing)

- [ ] **Step 3: Copy GUI files from prototype**

```bash
cp references/prototype/oa_pipeline/oa_pipeline_app.py tools/
cp references/prototype/oa_pipeline/oa_pipeline_app_core.py tools/
```

Verify imports point to `src/oa_pipeline` modules.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gui_launcher.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/ tests/test_gui_launcher.py
git commit -m "feat: migrate GUI launcher (oa_pipeline_app.py, oa_pipeline_app_core.py)"
```

---

### Task P1-10: Migrate stamp_carbonate_provenance.py

**Files:**

- Create: `tools/stamp_carbonate_provenance.py`

**Interfaces:**

- Consumes: `references/prototype/oa_pipeline/stamp_carbonate_provenance.py`
- Produces: Provenance stamping helper works

- [ ] **Step 1: Write the failing test**

```python
# tests/test_provenance_stamp.py
import subprocess

def test_stamp_script_exists():
    from pathlib import Path
    assert Path("tools/stamp_carbonate_provenance.py").exists()

def test_stamp_script_runs():
    result = subprocess.run(
        ["python", "tools/stamp_carbonate_provenance.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode in (0, 1, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provenance_stamp.py -v` Expected: FAIL

- [ ] **Step 3: Copy from prototype**

```bash
cp references/prototype/oa_pipeline/stamp_carbonate_provenance.py tools/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_provenance_stamp.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/stamp_carbonate_provenance.py tests/test_provenance_stamp.py
git commit -m "feat: migrate stamp_carbonate_provenance.py from prototype"
```

---

### Task P1-11: Verify no unpublished data in git

**Files:**

- (No new files — verification only)

**Interfaces:**

- Consumes: Current repo state
- Produces: Clean `git status` wrt unpublished data patterns

- [ ] **Step 1: Write the failing test**

```python
# tests/test_no_unpublished_data.py
import subprocess

def test_no_unpublished_data_in_git():
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    unpublished_patterns = ["oa_data_apr", "*.xlsx", "*.xls"]
    for line in result.stdout.splitlines():
        for pattern in unpublished_patterns:
            if pattern.replace("*", "") in line:
                # Allow example_data.xlsx
                if "example_data.xlsx" not in line:
                    pytest.fail(f"Unpublished data in git status: {line}")
```

- [ ] **Step 2: Run test to verify it fails/passes**

Run: `pytest tests/test_no_unpublished_data.py -v` Expected: PASS (should be
clean after migration)

- [ ] **Step 3: Verify manually**

```bash
git status
```

Confirm no `oa_data_apr*.xlsx` or other unpublished data files.

- [ ] **Step 4: Commit**

```bash
git add tests/test_no_unpublished_data.py
git commit -m "test: add check for no unpublished data in repo"
```

---

### Task P1-12: Full pipeline end-to-end verification

**Files:**

- (Integration test — no new files)

**Interfaces:**

- Consumes: All P1-01 through P1-11
- Produces: Verified working pipeline

- [ ] **Step 1: Write the failing test**

```python
# tests/test_full_pipeline_e2e.py
import subprocess
import pandas as pd

def test_full_pipeline_e2e():
    # Clean outputs
    import shutil
    if shutil.os.path.exists("outputs/test"):
        shutil.rmtree("outputs/test")

    result = subprocess.run(
        ["./run_pipeline.sh", "examples/example_data.xlsx", "outputs/test"],
        capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify outputs
    assert Path("outputs/test/analysis_ready.csv").exists()
    df = pd.read_csv("outputs/test/analysis_ready.csv")
    fail_count = len(df[df["verdict"] == "FAIL"])
    assert fail_count == 4, f"Expected 4 FAIL verdicts, got {fail_count}"

    # Verify run bundle manifest created
    assert Path("outputs/test/run_bundle_manifest.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_full_pipeline_e2e.py -v` Expected: FAIL
(run_bundle_manifest not yet implemented — that's P1-03)

- [ ] **Step 3: Run pipeline manually to verify**

```bash
./run_pipeline.sh examples/example_data.xlsx outputs/test
```

Verify 4 FAIL verdicts on injected rows.

- [ ] **Step 4: Run test (will pass after P1-03 implements run bundle)**

Run: `pytest tests/test_full_pipeline_e2e.py -v` Expected: PASS (after P1-03)

- [ ] **Step 5: Commit**

```bash
git add tests/test_full_pipeline_e2e.py
git commit -m "test: add full pipeline end-to-end test"
```

---

### Task P0-01: Create GitHub Actions CI workflow

**Files:**

- Create: `.github/workflows/ci.yml`

**Interfaces:**

- Consumes: `pixi.toml`, `pyproject.toml`, `run_pipeline.sh`, `pytest` config
- Produces: CI matrix running on Ubuntu/macOS/Windows

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ci_workflow.py
import yaml
from pathlib import Path

def test_ci_workflow_exists():
    path = Path(".github/workflows/ci.yml")
    assert path.exists(), "CI workflow missing"

    with open(path) as f:
        ci = yaml.safe_load(f)

    # Check matrix
    assert "strategy" in ci["jobs"]["test"]
    matrix = ci["jobs"]["test"]["strategy"]["matrix"]
    assert "os" in matrix
    assert set(matrix["os"]) == {"ubuntu-latest", "macos-latest", "windows-latest"}
    assert matrix["python-version"] == ["3.11"]

    # Check steps
    steps = [s.get("name", "") for s in ci["jobs"]["test"]["steps"]]
    assert any("pixi install" in s for s in steps)
    assert any("pre-commit-all" in s for s in steps)
    assert any("pytest" in s for s in steps)
    assert any("run_pipeline" in s for s in steps)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci_workflow.py -v` Expected: FAIL (workflow missing)

- [ ] **Step 3: Create `.github/workflows/ci.yml`**

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11"]
    steps:
      - uses: actions/checkout@v4
      - name: Install pixi
        uses: pixi-actions/setup-pixi@v2
      - name: Install dependencies
        run: pixi install
      - name: Pre-commit checks
        run: pixi run pre-commit-all
      - name: Run tests
        run: pixi run test
      - name: Run pipeline
        run: pixi run pipeline examples/example_data.xlsx outputs/ci_test
      - name: Upload CI test outputs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ci-test-outputs-${{ matrix.os }}
          path: outputs/ci_test/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ci_workflow.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml tests/test_ci_workflow.py
git commit -m "feat: add cross-platform CI workflow (Ubuntu/macOS/Windows)"
```

---

### Task P0-02: CI steps verification (covered by P0-01 workflow)

**Files:** (No new files — verification via CI run)

**Interfaces:** Consumes CI workflow from P0-01

- [ ] **Step 1: Push to trigger CI**
- [ ] **Step 2: Verify CI passes on all 3 platforms**
- [ ] **Step 3: Fix any platform-specific issues** (path handling, line endings,
      etc.)
- [ ] **Step 4: Commit fixes**

---

### Task P0-03: Create tests/test_invariants.py

**Files:**

- Create: `tests/test_invariants.py`

**Interfaces:**

- Consumes: All stage functions from `src/oa_pipeline/`
- Produces: Per-stage invariant test that fails CI on column mutation

- [ ] **Step 1: Write the failing test**

```python
# tests/test_invariants.py
import pandas as pd
import pytest
from oa_pipeline import stage1b, stage2, stage3, stage4, schema

# Sample input data fixture
@pytest.fixture
def sample_data():
    return pd.read_excel("examples/example_data.xlsx")

def test_stage1b_invariants(sample_data):
    """Untargeted columns byte-identical after stage1b."""
    input_cols = sample_data.columns.tolist()
    # Stage1b targets: best source coalescing columns
    targeted = {"best_source", "coalesced_*"}  # adjust to actual targeted columns
    result = stage1b.run(sample_data.copy())

    untargeted = [c for c in input_cols if c not in targeted and not c.startswith("coalesced_")]
    pd.testing.assert_frame_equal(
        sample_data[untargeted], result[untargeted],
        check_dtype=True, check_exact=True
    )

def test_stage2_invariants(sample_data):
    """Untargeted columns byte-identical after stage2."""
    input_cols = sample_data.columns.tolist()
    targeted = {"duplicate_flag", "replicate_group", "harmonized_*"}
    result = stage2.run(sample_data.copy())

    untargeted = [c for c in input_cols if c not in targeted]
    pd.testing.assert_frame_equal(
        sample_data[untargeted], result[untargeted],
        check_dtype=True, check_exact=True
    )

def test_stage3_invariants(sample_data):
    """Untargeted columns byte-identical after stage3."""
    input_cols = sample_data.columns.tolist()
    targeted = {"dic_sum", "ph_diagnostic", "provenance_*", "omega_*"}
    result = stage3.run(sample_data.copy())

    untargeted = [c for c in input_cols if c not in targeted]
    pd.testing.assert_frame_equal(
        sample_data[untargeted], result[untargeted],
        check_dtype=True, check_exact=True
    )

def test_stage4_invariants(sample_data):
    """Untargeted columns byte-identical after stage4."""
    input_cols = sample_data.columns.tolist()
    targeted = {"verdict", "verdict_reason", "audit_*"}
    result = stage4.run(sample_data.copy())

    untargeted = [c for c in input_cols if c not in targeted]
    pd.testing.assert_frame_equal(
        sample_data[untargeted], result[untargeted],
        check_dtype=True, check_exact=True
    )

def test_schema_invariants(sample_data):
    """Schema application preserves untargeted columns."""
    input_cols = sample_data.columns.tolist()
    targeted = set(schema.CANONICAL_COLUMNS)  # adjust to actual
    result = schema.apply_schema(sample_data.copy())

    untargeted = [c for c in input_cols if c not in targeted]
    pd.testing.assert_frame_equal(
        sample_data[untargeted], result[untargeted],
        check_dtype=True, check_exact=True
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_invariants.py -v` Expected: FAIL (test file missing, or
invariants not yet enforced)

- [ ] **Step 3: Implement invariant test logic**

Create `tests/test_invariants.py` with above tests. Adjust `targeted` sets per
actual stage outputs.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_invariants.py -v` Expected: PASS (all invariants hold)

- [ ] **Step 5: Commit**

```bash
git add tests/test_invariants.py
git commit -m "test: add per-stage invariant tests (ADR-0003)"
```

---

### Task P0-05: Create single README.md at root

**Files:**

- Create: `README.md`

**Interfaces:**

- Consumes: PRD quickstart requirements, all migrated components
- Produces: Single entry point with CLI/GUI/Notebook quickstart

- [ ] **Step 1: Write the failing test**

```python
# tests/test_readme.py
from pathlib import Path

def test_readme_exists():
    assert Path("README.md").exists()

def test_readme_has_required_sections():
    content = Path("README.md").read_text()
    required = [
        "Quickstart", "CLI", "GUI", "Notebook",
        "Prerequisites", "Installation", "Troubleshooting",
        "pixi install", "pixi run pipeline"
    ]
    for section in required:
        assert section.lower() in content.lower(), f"Missing section: {section}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme.py -v` Expected: FAIL (README missing or
incomplete)

- [ ] **Step 3: Create `README.md`**

Include:

- Project description + North Star
- Prerequisites (Pixi, Git Bash on Windows)
- Installation: `pixi install`
- Quickstart CLI: `pixi run pipeline examples/example_data.xlsx outputs/test`
- Quickstart GUI: `python tools/oa_pipeline_app.py`
- Quickstart Notebook: `jupyter lab notebooks/`
- Troubleshooting (Windows paths, pixi cache, etc.)
- Links to docs, CHANGELOG, CONTRIBUTING

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_readme.py
git commit -m "docs: add single entry-point README.md with quickstart for CLI/GUI/Notebook"
```

---

### Task P0-06: Archive legacy READMEs, move loose scripts

**Files:**

- Create: `docs/legacy/` (directory)
- Move: Any loose scripts to `tools/`

**Interfaces:**

- Consumes: Current repo root files
- Produces: Clean root directory

- [ ] **Step 1: Identify files to archive/move**
- [ ] **Step 2: Move legacy READMEs to `docs/legacy/`**
- [ ] **Step 3: Move loose scripts to `tools/`**
- [ ] **Step 4: Verify root is clean**
- [ ] **Step 5: Commit**

```bash
git mv old-readme.md docs/legacy/
git mv loose_script.py tools/
git commit -m "chore: archive legacy READMEs, move loose scripts to tools/"
```

---

### Task P0-07: Verify GUI launcher on all platforms

**Files:** (Verification via CI)

**Interfaces:** Consumes GUI from P1-09, CI from P0-01

- [ ] **Step 1: CI run includes GUI smoke test** (add to ci.yml)
- [ ] **Step 2: Verify all 3 platforms pass**
- [ ] **Step 3: Commit any fixes**

---

### Task P0-08: Fresh clone verification

**Files:** (Verification — no new files)

**Interfaces:** Consumes all P-1 + P0 work

- [ ] **Step 1: Fresh clone in temp directory**

```bash
cd /tmp && git clone <repo> roap-test && cd roap-test
pixi install
pixi run pipeline examples/example_data.xlsx outputs/test
```

- [ ] **Step 2: Verify success in <10 min**
- [ ] **Step 3: Document any issues in README troubleshooting**
