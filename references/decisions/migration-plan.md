# ROAP — P-1 Prototype Migration Plan

**Status:** Ready to execute  
**Duration:** 2-3 days  
**Blocker:** All P0-P4 work depends on this

---

## Source → Destination Map

| Source | Destination | Notes |
|--------|-------------|-------|
| `local/prototype/my_understanding/test/oa_pipeline/src/oa_pipeline/` | `src/oa_pipeline/` | 11 modules |
| `local/prototype/my_understanding/test/oa_pipeline/tests/` | `tests/` | 221 tests |
| `local/prototype/my_understanding/test/oa_pipeline/examples/` | `examples/` | Synthetic data + generator |
| `local/prototype/my_understanding/test/oa_pipeline/configs/` | `configs/` | YAML configs |
| `local/prototype/my_understanding/test/oa_pipeline/notebooks/` | `notebooks/` | 8 notebooks + READMEs |
| `local/prototype/my_understanding/test/oa_pipeline/pyproject.toml` | `pyproject.toml` | Package metadata |
| `local/prototype/my_understanding/test/oa_pipeline/requirements.txt` | — | Merge into pixi.toml/pyproject.toml |
| `local/prototype/my_understanding/test/oa_pipeline/run_pipeline.sh` | `run_pipeline.sh` | Verify works |
| `local/prototype/my_understanding/test/oa_pipeline/oa_pipeline_app.py` | `tools/oa_pipeline_app.py` | GUI launcher |
| `local/prototype/my_understanding/test/oa_pipeline/oa_pipeline_app_core.py` | `tools/oa_pipeline_app_core.py` | GUI core |
| `local/prototype/my_understanding/test/oa_pipeline/stamp_carbonate_provenance.py` | `tools/stamp_carbonate_provenance.py` | Provenance stamper |
| `local/prototype/my_understanding/test/oa_pipeline/oa_plots.py` | `src/oa_pipeline/viz/` | Extract to module |

---

## Step-by-Step Execution

### Day 1: Core Migration

#### 1.1 Copy Source Package
```bash
cp -r local/prototype/my_understanding/test/oa_pipeline/src/oa_pipeline src/
```
**Verify:** `ls src/oa_pipeline/` shows 11 `.py` files + `__init__.py`

#### 1.2 Copy Tests
```bash
cp -r local/prototype/my_understanding/test/oa_pipeline/tests tests/
```
**Verify:** `ls tests/` shows 14 test files + `conftest.py`

#### 1.3 Copy Examples
```bash
cp -r local/prototype/my_understanding/test/oa_pipeline/examples examples/
```
**Verify:** `examples/make_example_data.py` and `examples/example_data.xlsx` exist

#### 1.4 Copy Configs
```bash
cp -r local/prototype/my_understanding/test/oa_pipeline/configs configs/
```
**Verify:** `configs/07_stage3.yaml` has `ph_diag_harmonize_temperature: true`

#### 1.5 Copy Notebooks
```bash
cp -r local/prototype/my_understanding/test/oa_pipeline/notebooks notebooks/
```

### Day 2: Packaging & CLI

#### 2.1 Create `pyproject.toml` for `oa_pipeline` Package
Base on `local/prototype/my_understanding/test/oa_pipeline/pyproject.toml` but adjust for this repo structure.

**Key differences from prototype:**
- This repo uses `pixi.toml` for dev env (pre-commit, gh-cli)
- `pyproject.toml` only for `oa_pipeline` package distribution
- Keep `src/oa_pipeline` src-layout

```toml
# pyproject.toml (new, for oa_pipeline package)
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "oa-pipeline"
version = "0.2.0"
description = "Ocean acidification quality control and processing pipeline"
readme = "README.md"
license = { file = "LICENSE" }
authors = [
    { name = "Prof. R. Mahu" },
    { name = "Maurice Oti Edusei" },
]
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.2,<3.0",
    "numpy>=1.26,<2.5",
    "openpyxl>=3.1,<4.0",
    "matplotlib>=3.8,<4.0",
    "pyyaml>=6.0,<7.0",
    "pyarrow>=10.0,<20.0",
    "tabulate>=0.9,<0.11",
    "papermill>=2.4,<3.0",
]

[project.optional-dependencies]
test = ["pytest>=8.0,<10.0"]
notebook = ["ipykernel>=6.0,<8.0", "ipython>=8.0,<10.0"]
dev = ["pytest>=8.0,<10.0", "ipykernel>=6.0,<8.0", "ipython>=8.0,<10.0", "ruff", "black", "mypy"]

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]
include = ["oa_pipeline*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
pythonpath = ["src"]
xfail_strict = true
addopts = ["-ra", "--strict-markers", "--strict-config"]
filterwarnings = ["default::FutureWarning", "default::DeprecationWarning"]
```

#### 2.2 Update `pixi.toml` (Dev Environment Only)
Keep minimal — only dev tools. Runtime deps in `pyproject.toml`.

```toml
# pixi.toml (update)
[workspace]
channels = ["conda-forge"]
platforms = ["osx-arm64", "linux-64", "win-64"]

[environments]
default = { features = ["pre-commit", "gh-cli"], solve-group = "default" }
onboard = { features = ["pre-commit", "gh-cli", "onboard"], solve-group = "default" }

[dependencies]
python = "3.11.*"

[feature.pre-commit.dependencies]
pre-commit = ">=4.3.0"
ruff = ">=0.6.0"
black = ">=24.0.0"
mypy = ">=1.10.0"

[feature.gh-cli.dependencies]
gh = ">=2.0.0"

[feature.onboard.pypi-dependencies]
ssec-cli = { git = "https://github.com/uw-ssec/ssec-cli.git" }

[feature.onboard.tasks]
ssec-setup = { cmd = "ssec --install-completion", description = "Set up shell completion" }
onboard = { cmd = "ssec onboard", description = "Run onboarding", depends-on = ["pre-commit-install", "ssec-setup"] }

[tasks]
pre-commit-install = { cmd = "pre-commit install", description = "Install pre-commit hooks" }
pre-commit-all = { cmd = "pre-commit run --all-files", description = "Run pre-commit on all files" }
test = { cmd = "pytest -q", description = "Run test suite" }
pipeline = { cmd = "./run_pipeline.sh examples/example_data.xlsx outputs/test", description = "Run pipeline on example data" }
```

#### 2.3 Extract Notebook Logic → CLI
Create `src/oa_pipeline/cli.py` with `typer`:

```python
# src/oa_pipeline/cli.py
import typer
from pathlib import Path

app = typer.Typer(help="oa-pipeline: Reproducible Ocean Acidification Pipeline")

@app.command()
def validate(
    input_xlsx: Path = typer.Argument(..., help="Input Excel workbook"),
    config_dir: Path = typer.Option("configs", help="Config directory"),
):
    """Pre-flight validation without running full pipeline."""
    # TODO: Implement
    raise typer.Exit(code=1)

@app.command()
def export(
    input_csv: Path = typer.Argument(..., help="Analysis ready CSV"),
    format: str = typer.Option("goa-on", help="Export format"),
    output: Path = typer.Option(None, help="Output path"),
):
    """Export to GOA-ON / Frontiers 2021 format."""
    # TODO: Implement
    raise typer.Exit(code=1)

@app.command()
def verify_bundle(
    run_dir: Path = typer.Argument(..., help="Run directory to verify"),
):
    """Verify run bundle integrity."""
    # TODO: Implement
    raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
```

Add to `pyproject.toml` `[project.scripts]`:
```toml
[project.scripts]
oa-pipeline = "oa_pipeline.cli:app"
```

#### 2.4 Move GUI Scripts to `tools/`
```bash
mkdir -p tools
mv local/prototype/my_understanding/test/oa_pipeline/oa_pipeline_app.py tools/
mv local/prototype/my_understanding/test/oa_pipeline/oa_pipeline_app_core.py tools/
mv local/prototype/my_understanding/test/oa_pipeline/stamp_carbonate_provenance.py tools/
mv local/prototype/my_understanding/test/oa_pipeline/oa_plots.py src/oa_pipeline/viz/
```

#### 2.5 Add `.gitignore` for Unpublished Data
```bash
# Append to .gitignore
echo "local/prototype/my_understanding/test/requested_dataset/oa_data_apr_provenance.xlsx" >> .gitignore
```

### Day 3: Verification

#### 3.1 Install & Test
```bash
pixi install
pixi run pre-commit-install
pytest -q
# Expect: 221 passed
```

#### 3.2 Run Pipeline on Synthetic Data
```bash
pixi run pipeline
# Or manually:
./run_pipeline.sh examples/example_data.xlsx outputs/test
```
**Verify:** `outputs/test/oa_stage4_outputs/data/analysis_ready.csv` exists with 4 FAIL verdicts on injected rows (S005, S007, S010, S015).

#### 3.3 Verify GUI Launcher
```bash
python tools/oa_pipeline_app.py
# Should open Tkinter window
```

#### 3.4 Verify No Unpublished Data in Git
```bash
git status
# Should NOT show oa_data_apr_provenance.xlsx
```

---

## Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Source package copied | `ls src/oa_pipeline/*.py | wc -l` | 11 |
| Tests copied | `ls tests/test_*.py | wc -l` | 14 |
| Examples copied | `ls examples/` | `make_example_data.py`, `example_data.xlsx` |
| Configs copied | `ls configs/` | YAML files incl `07_stage3.yaml` |
| Notebooks copied | `ls notebooks/` | 8 notebooks + READMEs |
| `pyproject.toml` created | `cat pyproject.toml` | Valid TOML, src-layout |
| `pixi.toml` updated | `cat pixi.toml` | Dev env only |
| CLI created | `cat src/oa_pipeline/cli.py` | Typer app with 3 commands |
| GUI in tools/ | `ls tools/` | 3 files |
| Plotting in viz/ | `ls src/oa_pipeline/viz/` | `oa_plots.py` |
| Gitignore updated | `grep oa_data_apr_provenance .gitignore` | Present |
| Tests pass | `pytest -q` | 221 passed |
| Pipeline runs | `./run_pipeline.sh ...` | analysis_ready.csv with 4 FAIL |
| GUI opens | `python tools/oa_pipeline_app.py` | Window opens |

---

## Rollback Plan
If migration breaks:
```bash
git checkout main -- src/ tests/ examples/ configs/ notebooks/ pyproject.toml pixi.toml tools/ .gitignore
```
Prototype remains untouched in `local/prototype/`.

---

## Post-Migration
1. Commit migration as single commit: `feat: migrate oa_pipeline v0.2.0 prototype into repo`
2. Tag `v0.2.0-migration` for reference
3. Begin P0: CI + Invariant Test + Entry Point