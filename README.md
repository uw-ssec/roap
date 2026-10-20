# ROAP — Reproducible Ocean Acidification Pipeline

Production-grade ocean acidification carbonate chemistry QC processing per
Frontiers 2021 data standards.

## Quickstart (3 paths)

### 1. CLI — One command

```bash
pixi install
pixi run pipeline examples/example_data.xlsx outputs/test
```

Output: `outputs/test/oa_stage4_outputs/data/analysis_ready.csv` with verdicts.

### 2. GUI — No terminal

```bash
pixi install
python tools/roap_app.py
```

Click "Run Pipeline", select input, watch progress.

### 3. Notebooks — Step by step

```bash
pixi install
jupyter lab notebooks/
```

Run `01_preview.ipynb` → `08_stage4.ipynb` in order.

## Prerequisites

- Pixi (package manager): `curl -fsSL https://pixi.sh/install.sh | bash`
- Python 3.11 (managed by Pixi)
- Git Bash on Windows (required for `run_pipeline.sh`)

## Pipeline Stages

| Stage  | Notebook            | Module        | Purpose                                      |
| ------ | ------------------- | ------------- | -------------------------------------------- |
| 0      | `01_preview.ipynb`  | `inspect.py`  | Preview input workbook                       |
| 1A     | `02_ta_ph_qc.ipynb` | `qc_ta_ph.py` | TA CRM correction, pH standard correction    |
| 1B     | `04_stage1a.ipynb`  | `stage1b.py`  | Best source coalescing                       |
| 2      | `05_stage1b.ipynb`  | `stage2.py`   | Duplicate detection, replicate harmonisation |
| 3      | `06_stage2.ipynb`   | `stage3.py`   | Carbonate integrity, DIC sum, pH diagnostic  |
| 4      | `07_stage3.ipynb`   | `stage4.py`   | Final audit, PASS/REVIEW/FAIL verdicts       |
| Export | `08_stage4.ipynb`   | `export.py`   | GOA-On NetCDF export (P3)                    |

## Configuration

All configs in `configs/`:

- `02_ta_ph_qc.yaml` — TA/pH QC thresholds
- `07_stage3.yaml` — Carbonate integrity (includes
  `ph_diag_harmonize_temperature: true`)
- `08_stage4.yaml` — Audit thresholds
- `regional.yaml` — Regional partner overrides
- `schema_aliases.yaml` — Column alias mapping (Fatou's workflow)
- `crm_certified_values.yaml` — CRM batch certified values
- `cruise_grade_thresholds.yaml` — Cruise grading

## Output Structure

```
outputs/<run>/
├── oa_stage1a_outputs/
├── oa_stage1b_outputs/
├── oa_stage2_outputs/
├── oa_stage3_outputs/
├── oa_stage4_outputs/
│   └── data/analysis_ready.csv   # ← Final deliverable
└── run_bundle_manifest.json       # P1: immutable run record
```

## Expected Output (synthetic data)

Running on `examples/example_data.xlsx` produces **4 non-PASS** verdicts in
`analysis_audit_status`:

- 16 PASS
- 3 FAIL (injected bad rows)
- 1 REVIEW (borderline)

## Troubleshooting

| Problem                              | Solution                                                     |
| ------------------------------------ | ------------------------------------------------------------ |
| `ModuleNotFoundError: roap`          | Run `pixi install`                                           |
| `run_pipeline.sh: command not found` | Use Git Bash on Windows; `chmod +x run_pipeline.sh` on Unix  |
| GUI won't open                       | Ensure Tkinter installed (bundled with python.org installer) |
| Carbonate calc fails                 | PyCO2SYS v1 required; `pixi install` pulls it                |
| Config version mismatch              | Update `compatible_pipeline_version` in config YAML          |

## For Developers

- `pixi run test` — Full test suite (373 tests)
- `pixi run pre-commit-all` — Quality gate (ruff, black, mypy, pytest)
- `pytest tests/test_invariants.py -v` — Invariant test only
- See `CONTRIBUTING.md` for contribution discipline
