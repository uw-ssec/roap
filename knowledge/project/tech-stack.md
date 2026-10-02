---
type: Architecture
title: Project Tech Stack
description: "Pixi-only, Python 3.11, single engine three doors, pytest+hypothesis, cross-platform CI, conventional commits"
tags: [tech-stack, architecture, python, pixi]
generated: { by: agent/cli, at: "2026-10-02T00:38:20Z" }
status: stable
---

# Project Context: Tech Stack

## Package Manager
- **Pixi only** - no pip, conda, venv directly
- pixi install before any other Pixi command
- pixi.toml for dev environment (pre-commit, gh-cli, onboard)
- pyproject.toml for oa_pipeline package (src-layout)

## Python
- Version: 3.11 (pinned in both pixi.toml and pyproject.toml)
- Dependencies: pandas>=2.2,<3.0, numpy>=1.26,<2.5, openpyxl>=3.1,<4.0, matplotlib>=3.8,<4.0, pyyaml>=6.0,<7.0, pyarrow>=10.0,<20.0, tabulate>=0.9,<0.11, papermill>=2.4,<3.0, pytest>=8.0,<10.0, ipykernel>=6.0,<8.0, ipython>=8.0,<10.0

## Core Architecture
- Single engine: src/oa_pipeline/ (pure Python modules)
- Three doors: CLI (typer/click), GUI (Tkinter), Notebooks (Papermill)
- All interfaces call same core pipeline modules

## Testing
- pytest with 221+ tests
- Property-based testing with hypothesis (planned)
- Invariant test: untouched columns unchanged per stage
- Cross-platform CI: Ubuntu, macOS, Windows (Git Bash)
- Manual regression gate on unpublished April 2026 dataset

## Quality Gates
- pre-commit: ruff, black, mypy, pytest
- Conventional commits (feat, fix, test, docs, chore)
- Branch protection + required CI on main
- pixi run pre-commit-all must pass before commit
