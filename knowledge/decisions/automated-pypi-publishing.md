---
type: Decision
title: Automated publishing to TestPyPI and PyPI with trusted publishing
description:
  Merges to main publish CalVer dev builds to TestPyPI; published GitHub
  Releases publish to PyPI; no stored tokens.
tags: [release, pypi, ci, calver]
generated: { by: agent/richard-claude-code, at: "2026-10-26T22:05:00Z" }
status: draft
---

## Scope and status

This note supersedes the "manual publish" choice in
[engineering decision 5](engineering-decisions.md) once
[PR #66](https://github.com/uw-ssec/roap/pull/66) (issue
[#14](https://github.com/uw-ssec/roap/issues/14)) merges. Don requested
publishing to PyPI on 2026-10-26 (maintainer direction).

## Decision

- **Every push to `main`** builds a dev pre-release of the next release,
  `YYYY.0M.MICRO.devN`, and uploads it to TestPyPI. N is the number of commits
  since the last `v*` tag. The version is stamped into the build only.
  `pyproject.toml` keeps the release version written by the release skill.
- **A published GitHub Release** fails unless its tag equals `v` + the
  `pyproject.toml` version, and otherwise uploads to PyPI.
- Both uploads use PyPI trusted publishing (OIDC) through the `testpypi` and
  `pypi` GitHub environments. No API tokens are stored.
- Workflow hardening: actions are pinned to commit SHAs, top-level
  `permissions: {}`, and `id-token: write` is granted only on the two publish
  jobs. `zizmor` must report no findings.
- Builds use a minimal `build` Pixi environment
  (`python -m build --no-isolation`, `twine check --strict`). It is independent
  of the `default` environment.

_Rejected_: storing a PyPI API token (long-lived secret); publishing every
`main` push to PyPI itself (dev builds would crowd the real index).

Source: `.github/workflows/publish.yml`, `tools/release_version.py`,
`tests/test_release_version.py`, `pixi.toml` (`build` feature),
`.agents/skills/release/SKILL.md`.

## Maintainer setup

Before the first upload, a trusted publisher has to be registered on PyPI and
TestPyPI for `uw-ssec/roap`, workflow `publish.yml`, with environments `pypi`
and `testpypi`. Both environments also have to exist in the repository settings.
Until then, the publish job on `main` fails at the OIDC exchange.

## Verification requirements

Dev versions must sort above the previous release and below the next one.
`tests/test_release_version.py` covers ordering across a release. Month and year
rollover was checked in review against real tags and commit distances. The OIDC
exchange and index uploads are not exercised in PR CI.

Linked reference: [engineering decisions](engineering-decisions.md).
