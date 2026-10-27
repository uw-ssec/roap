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

* [GUI Cancel and Quit stop the whole pipeline process tree](gui-cancel-stops-process-tree.md) -
  Process-group launch, detached-descendant sweep, SIGKILL after 5 s; cancelled
  runs are flagged incomplete, not deleted.

* [GUI and notebooks launch through Pixi, with JupyterLab locked](pixi-launch-and-jupyterlab.md) -
  `pixi run` entry points and a locked `jupyterlab` dependency; no pip or system
  Python in onboarding.
