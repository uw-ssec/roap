# Decisions

- [Council Review of Epic Plan](council-review.md) - Four-voice council
  identified missing P-1 migration phase and restructured priorities
- [Architecture Decision Records](adrs.md) - 10 ADRs covering NetCDF export, CI,
  invariant test, config aliases, Excel round-trip, CRM detection, property
  testing, regression gate, Frontiers 2021, single engine
- [Prototype Migration Plan](migration-plan.md) - P-1 blocking phase: copy
  prototype code, tests, configs, examples; create pyproject.toml; extract CLI;
  verify 221 tests pass
- [ROAP v1.0.0 Engineering Decisions](engineering-decisions.md) - ADR 0001
  (Option B: File Manifest), PyCO2SYS v1 stable, dataset access, GPG deferral,
  manual PyPI, CI strategy, single engine, Frontiers 2021, invariant tests,
  config gate

* [Portable notebook defaults and live package references](portable-notebook-defaults.md) -
  P1 notebooks use repository-local inputs while Papermill overrides and
  historical prototype references remain intact.

* [Invariant tests compare each stage with its own input, as exact text](invariant-test-comparison.md) -
  Untouched columns keep exact text; serialisation-only equivalence only for
  named numeric and timestamp columns.

* [Automated publishing to TestPyPI and PyPI with trusted publishing](automated-pypi-publishing.md) -
  Merges to main publish CalVer dev builds to TestPyPI; GitHub Releases publish
  to PyPI.
