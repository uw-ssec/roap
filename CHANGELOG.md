# Changelog

Releases use [CalVer](https://calver.org/) `YYYY.0M.MICRO` (as
[xarray](https://github.com/pydata/xarray) does), tagged `vYYYY.0M.MICRO`.
`0.2.0` was the last SemVer release.

## [Unreleased]

### Changed

- Versioning switches from SemVer to CalVer `YYYY.0M.MICRO`; the first CalVer
  release will be tagged `v2026.11.0` or later
- Config compatibility gate compares every version component, so CalVer releases
  and same-month MICRO releases order correctly

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
