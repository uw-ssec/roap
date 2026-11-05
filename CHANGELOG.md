# Changelog

Releases use [CalVer](https://calver.org/) `YYYY.0M.MICRO` (as
[xarray](https://github.com/pydata/xarray) does), tagged `vYYYY.0M.MICRO`.
`0.2.0` was the last SemVer release.

## [Unreleased]

### Fixed

- Stage 1B stores `is_sample_row` as a boolean again, so CRM and standard rows
  are no longer treated as samples and no longer get
  `flag_core_chemistry_missing` (#47)
- Stage 1B `classify_rows_sample` no longer raises `NameError` on rows with a
  blank or unrecognised `sample_type`, or `IndexError` on frames without a
  `RangeIndex`; such rows fall back to the CRM/pH-standard QC flags (#38)
- Notebook 06 (Stage 2) no longer silently drops user config keys that are not
  in `STAGE2_DEFAULTS`, such as `required_stage2_input_columns` (#39)

## [2026.11.0] - 2026-11-04

### Added

- Automated publishing: every merge to `main` uploads a CalVer dev build
  (`YYYY.0M.MICRO.devN`) to TestPyPI, and a published GitHub Release uploads the
  release to PyPI (trusted publishing, no stored tokens)

- Each stage notebook (02, 04–08) writes `run_bundle_manifest.json` into its
  `OUT_DIR`, recording the stage's input, configs and outputs, so a notebook run
  by hand without `run_pipeline.sh` can be checked with `roap verify-bundle`

### Changed

- Versioning switches from SemVer to CalVer `YYYY.0M.MICRO`, starting with
  `v2026.11.0`
- Config compatibility gate compares every version component, so CalVer releases
  and same-month MICRO releases order correctly
- The package version comes from the `vYYYY.0M.MICRO` git tag (hatchling and
  hatch-vcs replace setuptools); `pyproject.toml` and `pixi.toml` no longer
  hardcode it, and a release needs no version-bump commit

### Fixed

- `roap verify-bundle` now checks the SHA256 of the input, config and output
  files recorded in `run_bundle_manifest.json`, reports each missing or changed
  file, and exits 1 when any check fails (it was a stub that always exited 0);
  `--json` prints the per-file report
- `run_pipeline.sh` now records the git commit in `run_bundle_manifest.json`; it
  was always `unknown` because `GIT_COMMIT` was never exported
- Notebook 02 finds `configs/crm_certified_values.yaml` when run from
  `notebooks/` (as JupyterLab does); the default path was relative to the
  working directory, so a direct run failed
- A run without `--config-dir` now records the configuration it used in
  `run_bundle_manifest.json`: each stage's `logs/effective_config.json` and the
  CRM certified-values YAML that notebook 02 loads. It previously recorded no
  config files, so a changed config passed `roap verify-bundle`
- Desktop launcher: Cancel, Quit and closing the window now stop the whole
  pipeline process tree, including the Jupyter kernel, instead of leaving
  papermill running in the background, and force-stop anything still running 5
  seconds later; quitting mid-run asks first
- Desktop launcher: a cancelled run is reported as having incomplete outputs
  that must not be used
- Desktop launcher: the output folder is no longer created when input validation
  fails

## [0.2.0] - 2026-10-11

### Added

- Config compatibility gate enforcement
- Run bundle manifest generation
- `verify-bundle` CLI command
- `__version__` sourced from `importlib.metadata`
- CRM/TRIS row preservation in Stage 1B audit trail
- CRM correction robustness without config

### Changed

- Updated pipeline to use `importlib.metadata` for version
- Improved error handling in config validation
- Enhanced stage1b row classification logic

### Fixed

- CRM/TRIS row preservation in Stage 1B audit trail (Issue #29)
- CRM correction robustness without config (Issue #30)
- Config version drift prevention

### Deprecated

- None

### Removed

- None

### Security

- None
