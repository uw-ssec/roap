---
type: Decision
title: GUI and notebooks launch through Pixi, with JupyterLab locked
description:
  README and launcher guidance use `pixi run` for the GUI, notebooks and tests,
  and `jupyterlab >=4,<5` is a locked dependency, so onboarding needs no pip or
  system Python.
tags: [onboarding, pixi, gui, notebooks, p0, milestone-4]
generated: { by: agent/richard-claude-code, at: "2026-10-27T16:10:00Z" }
status: draft
---

## Scope and status

This note records the onboarding decision implemented by Dinesh in
[#69](https://github.com/uw-ssec/roap/pull/69) under P0 issue
[#12](https://github.com/uw-ssec/roap/issues/12), reviewed by Richard. It stays
`draft` until #69 merges.

## What was wrong at `be62c1a`

- After `pixi install --frozen`, `jupyterlab` was not installed, so the README's
  `jupyter lab notebooks/` step failed.
- The README launched the GUI as `python tools/roap_app.py`. With the system
  Python, the app's own setup check then told users to `pip install -e ".[dev]"`
  and `pip install ipykernel`, which contradicts the Pixi-only rule.
- The launcher docstring said the app must sit in the project root, but it lives
  in `tools/`.

## Decision

- All entry points run through Pixi: `pixi run python tools/roap_app.py`,
  `pixi run jupyter lab notebooks/` and `pixi run pytest …`.
- `jupyterlab >=4,<5` is a locked dependency.
- The launcher's setup messages point to `pixi install` and the Pixi launch
  command, and its docstring describes the `tools/` layout.

## Lock-file note

Pixi 0.82 rewrites `pixi.lock` in format 7, which older Pixi clients cannot
read ([prefix.dev: lock file v7](https://prefix.dev/blog/lock-file-v7)). For #69
the lock was regenerated with Pixi 0.65 to stay in format 6. The diff only adds
lines (+1,341): every existing package artifact is kept, and JupyterLab 4.6.4
resolves on all four platforms. Any PR that moves the lock to format 7 must be
re-locked after #69 lands.

## Verification

JupyterLab served HTTP 200 with `notebooks/` as root. A real Tk mainloop started
with no setup warnings. `pixi install --locked` passes, and the full suite gives
401 passed with one existing expected failure (macOS).
