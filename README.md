# ROAP — Reproducible Ocean Acidification Pipeline

ROAP runs quality control and processing for discrete ocean acidification
carbonate-chemistry data, working toward the Frontiers in Marine Science (2021)
best-practice data standard. It takes a bench-sheet Excel workbook through TA
reference-material and pH-standard QC, then through staged checks to an
analysis-ready table with a PASS / REVIEW / FAIL verdict per sample. Every run
writes a run bundle you can verify later.

## Status

- **Version:** `2026.11.0`, the first CalVer release (not yet on PyPI). Versions
  use [CalVer](https://calver.org/) `YYYY.0M.MICRO`; see
  [CHANGELOG.md](CHANGELOG.md).
- **Install from a repository checkout.** The pipeline runs notebooks and
  `run_pipeline.sh` from the repository, so the Pixi workflow below is the
  supported way to run it. The PyPI package (`pip install roap`) ships the
  `roap` library and CLI, but not the notebooks or runner. Each merge to `main`
  publishes a dev build to [TestPyPI](https://test.pypi.org/p/roap), and a
  GitHub Release publishes to PyPI.
- **Not done yet:** `roap validate` is a stub that only reads the workbook
  ([#19](https://github.com/uw-ssec/roap/issues/19)). GOA-ON export isn't
  implemented. A single in-process engine behind the CLI, GUI and shell is
  tracked in [#43](https://github.com/uw-ssec/roap/issues/43).

## Quickstart

Install [Pixi](https://pixi.sh/latest/#installation) 0.83 or newer (run
`pixi self-update` to upgrade an older install). Then clone the repository with
its submodule and install the locked environment. Pixi manages Python 3.11 and
every dependency.

```bash
git clone --recurse-submodules https://github.com/uw-ssec/roap.git
cd roap
pixi install --locked
```

Older Pixi versions misread `pixi.lock` and reject `--locked` with "lock file
not up-to-date", on every operating system. Upgrade Pixi rather than switching
to `--frozen`: `--frozen` skips the check that the lock file matches
`pixi.toml`.

On Windows, run the pipeline and the tests from Git Bash, because
`run_pipeline.sh` is a Bash script. From PowerShell or cmd, the task can exit
with code 127 if Git Bash is absent from PATH; running from Git Bash provides
the required environment. Use Git for Windows' Bash, not WSL's
`C:\Windows\System32\bash.exe`.

### 1. Command line

```bash
pixi run pipeline examples/example_data.xlsx outputs/test
```

The final deliverable is
`outputs/test/oa_stage4_outputs/data/analysis_ready.csv`. Run
`./run_pipeline.sh --help` for options such as `--config-dir`, `--start-from`,
`--no-parquet` and `--dry-run`.

### 2. Desktop GUI

```bash
pixi run python tools/roap_app.py
```

The launcher pre-fills the example workbook and an output folder. Click **Run
pipeline** and watch the progress log. **Cancel** stops the whole pipeline and
warns that the partial outputs must not be used.

### 3. Notebooks

```bash
pixi run jupyter lab notebooks/
```

Start with `quickstart.ipynb` for a guided end-to-end run. To run stages by
hand, run the numbered notebooks in order. Each has a `*_README.md` next to it.

## Pipeline Stages

`run_pipeline.sh` runs these notebooks with Papermill. Each stage reads the
previous stage's output.

| Notebook                    | Stage    | Output folder                 | Purpose                                           |
| --------------------------- | -------- | ----------------------------- | ------------------------------------------------- |
| `01_excel_viewer.ipynb`     | Optional | `oa_viewer_outputs/`          | Preview the input workbook (`--include-viewer`)   |
| `02_ta_ph_qc.ipynb`         | QC       | `oa_prelim_data__qc_outputs/` | TA reference-material (CRM) QC and pH-standard QC |
| `03_qc_output_review.ipynb` | Optional | —                             | Review the QC outputs (`--include-review`)        |
| `04_stage1a.ipynb`          | 1A       | `oa_stage1a_outputs/`         | Canonical schema and presence flags               |
| `05_stage1b.ipynb`          | 1B       | `oa_stage1b_outputs/`         | Best-source analysis fields                       |
| `06_stage2.ipynb`           | 2        | `oa_stage2_outputs/`          | Replicate harmonisation and duplicate checks      |
| `07_stage3.ipynb`           | 3        | `oa_stage3_outputs/`          | Carbonate-system integrity checks                 |
| `08_stage4.ipynb`           | 4        | `oa_stage4_outputs/`          | Analysis audit and PASS / REVIEW / FAIL verdicts  |

The logic lives in the `roap` package under `src/roap/`.

## Configuration

Default configs live in `configs/`. `run_pipeline.sh --config-dir DIR` picks up
per-stage files named after the notebook (`02_ta_ph_qc.yaml`, `04_stage1a.yaml`
… `08_stage4.yaml`, or `.yml` / `.json`):

- `02_ta_ph_qc.yaml`: TA and pH QC thresholds
- `07_stage3.yaml`: carbonate integrity, including
  `ph_diag_harmonize_temperature`
- `08_stage4.yaml`: audit thresholds

These shared files are also in `configs/`:

- `crm_certified_values.yaml`: certified values per CRM batch
- `schema_aliases.yaml`: column alias mapping
- `regional.yaml`: regional partner overrides
- `cruise_grade_thresholds.yaml`: cruise grading

The runner doesn't load `regional.yaml` or `cruise_grade_thresholds.yaml` on its
own. Configs declare a `compatible_pipeline_version`, and a run stops if the
installed version doesn't satisfy it.

## Outputs and Run Bundles

```
outputs/<run>/
├── oa_prelim_data__qc_outputs/
├── oa_stage1a_outputs/
├── oa_stage1b_outputs/
├── oa_stage2_outputs/
├── oa_stage3_outputs/
└── oa_stage4_outputs/
    ├── data/analysis_ready.csv    # final deliverable
    ├── reports/report.md          # stages 1A–4 each write a report
    └── run_bundle_manifest.json   # each stage writes a manifest

runs/<timestamp>_pid<N>/
├── *.run.ipynb                    # executed notebooks
└── run_bundle_manifest.json       # manifest for the whole run
```

A manifest records the SHA256 of the input, the configs and every output, plus
package versions and the git commit. To check that nothing has changed since the
run:

```bash
pixi run verify-bundle runs/<timestamp>_pid<N>        # whole run
pixi run verify-bundle outputs/<run>/oa_stage4_outputs # one stage
```

It exits 0 when every file matches. Notebooks run by hand also write a manifest,
so a stage run without `run_pipeline.sh` can be verified the same way.

## Expected Output (example data)

`examples/example_data.xlsx` is a synthetic workbook. Running the pipeline on it
gives these `analysis_audit_status` values in `analysis_ready.csv`:

- **20 samples:** 16 PASS, 3 FAIL (injected bad rows) and 1 REVIEW (borderline)
- **7 reference rows:** 4 `CRM_QC` and 3 `STD_QC`

Matching these counts, and a clean `roap verify-bundle`, shows the pipeline ran
and its outputs are intact. It does not show the results are scientifically
correct for your data. When trying a real lab workbook, compare units, reference
values, verdicts and carbonate outputs against your own manual QC and
independently checked chemistry. `roap validate` can't do this yet: it only
reads the first sheet and reports `status: stub`, so an exit code of 0 doesn't
mean the workbook passed validation.

## Troubleshooting

| Problem                                                | Solution                                                        |
| ------------------------------------------------------ | --------------------------------------------------------------- |
| `ModuleNotFoundError: roap`                            | Run `pixi install` from the repository root                     |
| `requires pixi '>=0.83'` or `lock file not up-to-date` | Run `pixi self-update`, then `pixi install --locked`            |
| `pixi run pipeline` exits with 127 on Windows          | Run it from Git Bash                                            |
| `run_pipeline.sh: command not found`                   | Use Git Bash on Windows; run `chmod +x run_pipeline.sh` on Unix |
| GUI won't open                                         | Run `pixi install`, then `pixi run python tools/roap_app.py`    |
| Carbonate calculation fails                            | PyCO2SYS 1.x is required; `pixi install` provides it            |
| Config version mismatch                                | Update `compatible_pipeline_version` in that config's YAML      |

## For Developers

- `pixi run test`: the full test suite. Some tests need the prototype submodule.
  If you cloned without `--recurse-submodules`, run
  `git submodule update --init --recursive`
- Some tests start `pixi` and `run_pipeline.sh` in child processes, so Pixi and
  Bash must be on the PATH the tests inherit. On Windows, run the tests from Git
  Bash. Pointing an IDE such as PyCharm at the Pixi Python interpreter doesn't
  put Pixi or Bash on that PATH
- `pixi run pre-commit-all`: formatting, spelling, workflow and secret-scanning
  hooks. Run it before every PR
- `pixi run pytest tests/test_invariants.py -v`: the invariant tests only
- See [CONTRIBUTING.md](CONTRIBUTING.md), and [AI_POLICY.md](AI_POLICY.md) for
  AI-assisted contributions

## Citation

If you use ROAP in your research, please cite it. The citation metadata is in
[`CITATION.cff`](CITATION.cff), and GitHub's "Cite this repository" button
generates APA and BibTeX from it.

## Support

See [SUPPORT.md](SUPPORT.md) for where to ask questions, report bugs and raise
security concerns.

## License

BSD 3-Clause. See [LICENSE](LICENSE).
