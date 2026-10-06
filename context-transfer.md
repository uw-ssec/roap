# ROAP v1.0.0 — Context Transfer for Implementation Agent (Claude Opus 5)

## Mission
Complete milestones **P‑1 (Prototype Migration)** and **P0 (Cross-Platform CI + Invariant Tests)** on branch **`feat/ai-prd`**.  
17 TDD tasks (P1‑04 → P0‑08), mechanical copy-from-prototype plus a handful of judgment calls (import fixing, test-failure triage, pre-commit repair).

## Repository State (already committed on feat/ai-prd)
```bash
cd /Users/vrajrajpura/Documents/SSEC/roap
git checkout feat/ai-prd
# 3 commits done:
# 0b92c5b chore: fix pre-commit config, disable codespell temporarily
# b9b7f87 feat: migrate all 12 oa_pipeline modules from prototype
# 9555941 test: update pixi task tests to use 'pixi run --help' per brief
# b252cff feat: add pixi tasks for pipeline, test, validate, verify-bundle
# b770dba feat: add pyproject.toml with src-layout for oa-pipeline v0.2.0
```

## Key Files (READ THESE FIRST)
| File | Why |
|------|-----|
| `docs/superpowers/plans/2026-10-05-roap-v1-implementation-plan.md` | **Exact TDD steps** for every task — follow verbatim |
| `docs/superpowers/specs/2026-10-05-roap-v1-implementation-design.md` | Architecture, global constraints, review-focus items |
| `.superpowers/sdd/2026-10-05-roap-v1-implementation-plan/progress.md` | Ledger — append one line per completed task |
| `decisions-vraj-for-meeting-6th-oct.md` | Decisions: ADR 0001=Option B, PyCO2SYS v1, unsigned tags, manual PyPI, etc. |
| `references/prototype/oa_pipeline/` | **Source of truth** — copy everything from here |

## Remaining Tasks (17)

### P‑1 Milestone (8 tasks — blocking)
| # | Task | Prototype source → Target |
|---|------|---------------------------|
| P1‑04 | Migrate **tests/** (14 files, ≥221 tests) | `references/prototype/oa_pipeline/tests/*` → `tests/` |
| P1‑05 | Migrate **configs/** (7 YAML) | `references/prototype/oa_pipeline/configs/*` → `configs/` |
| P1‑06 | Migrate **examples/** | `references/prototype/oa_pipeline/examples/*` → `examples/` |
| P1‑07 | Migrate **notebooks/** (8) | `references/prototype/oa_pipeline/notebooks/*` → `notebooks/` |
| P1‑08 | Migrate **CLI** `run_pipeline.sh` | `references/prototype/oa_pipeline/run_pipeline.sh` → repo root (`chmod +x`) |
| P1‑09 | Migrate **GUI** `oa_pipeline_app*.py` | `references/prototype/oa_pipeline/oa_pipeline_app*.py` → `tools/` |
| P1‑10 | Migrate **stamp_carbonate_provenance.py** | `references/prototype/oa_pipeline/stamp_carbonate_provenance.py` → `tools/` |
| P1‑11 | Verify **no unpublished data** | `git status` — no `oa_data_apr*.xlsx` |
| P1‑12 | **Full pipeline E2E** | `./run_pipeline.sh examples/example_data.xlsx outputs/test` → 4 FAIL verdicts |

### P0 Milestone (8 tasks)
| # | Task |
|---|------|
| P0‑01 | Create `.github/workflows/ci.yml` (Ubuntu/macOS/Windows matrix, Python 3.11, pixi) |
| P0‑02 | CI steps verification — run CI, fix platform quirks |
| P0‑03 | Create `tests/test_invariants.py` (per-stage column-mutation tests, ADR-0003) |
| P0‑05 | Single `README.md` at root (CLI/GUI/Notebook quickstart) |
| P0‑06 | Archive legacy READMEs → `docs/legacy/`, move loose scripts → `tools/` |
| P0‑07 | Verify GUI launcher on all 3 platforms |
| P0‑08 | Fresh-clone verification: `pixi install → pixi run pipeline …` < 10 min |

## Execution Protocol — EVERY TASK

```bash
# 1️⃣  Read the brief
cat .superpowers/sdd/2026-10-05-roap-v1-implementation-plan/task-P1-04-brief.md

# 2️⃣  Write the failing test FIRST (TDD — mandatory)
#     Test code is in the brief — copy exactly.

# 3️⃣  Run test → watch FAIL
pixi run pytest tests/test_migration_test_count.py -v

# 4️⃣  Implement (mostly COPY from prototype)
cp references/prototype/oa_pipeline/tests/* tests/

# 5️⃣  Run test → watch PASS
pixi run pytest tests/test_migration_test_count.py -v

# 6️⃣  Pre-commit (MUST pass)
pixi run pre-commit-all

# 7️⃣  Conventional commit
git add tests/ tests/test_migration_test_count.py
git commit -m "feat: migrate all 14 test files (221+ tests) from prototype"

# 8️⃣  Update ledger
echo "Task P1-04: complete (commits <base7>..<head7>, review clean)" \
  >> .superpowers/sdd/2026-10-05-roap-v1-implementation-plan/progress.md
```

## Critical Constraints (NON-NEGOTIABLE)
* **Pixi only** — never `pip`, `conda`, `venv`. `pixi install` before any command.
* **Python 3.11** pinned in `pixi.toml` & `pyproject.toml`.
* **Conventional commits** (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
* **Pre-commit must pass** — `pixi run pre-commit-all` (ruff, black, mypy, pytest).
* **No unpublished data** — enforced by `.gitignore` + pre-commit.
* **Single engine, three doors** — all interfaces call `src/oa_pipeline/`.

## Verification Gates
| Milestone | Gate Command |
|-----------|--------------|
| **P‑1 complete** | `./run_pipeline.sh examples/example_data.xlsx outputs/test` → 4 FAIL verdicts |
| **P0 complete** | CI green on Ubuntu/macOS/Windows **and** invariant test passes **and** fresh-clone < 10 min |

## Ledger
`.superpowers/sdd/2026-10-05-roap-v1-implementation-plan/progress.md`  
Append on each task completion:
```
Task P1-04: complete (commits <base7>..<head7>, review clean)
```

## If You Hit a Blocker
* **Import error / missing module** — compare prototype import paths vs. target `src/oa_pipeline/`.
* **Tests < 221** — run `pixi run pytest -q --tb=short` to see failures; fix by mirroring prototype test fixtures.
* **Pre-commit failure** — run `pixi run pre-commit-all` locally, apply fixes (ruff/black/mypy).
* **CI platform quirk** — inspect the failed GitHub Action log; usually path-separator or line-ending issue.

## PR Strategy
1. **PR #1 (already created)**: `planning-milestones-and-plans` branch → all planning docs (spec, plan, decisions, ledger)
2. **PR #2**: `feat/ai-prd` (current branch with P1-04 → P1-12) → "feat: complete P-1 prototype migration + verification"
3. **PR #3**: new branch off main for P0 tasks → "feat: cross-platform CI, invariant tests, README (P0)"

## Start Command for You
```bash
cd /Users/vrajrajpura/Documents/SSEC/roap
git checkout feat/ai-prd
pixi install
pixi run pre-commit-all   # verify clean baseline
# → Begin Task P1-04 (read brief, write failing test, implement)
```

---

## Additional Context

### Model
You are **Claude Opus 5** — use your full reasoning capability for the judgment calls (import-path fixes, test-failure triage, pre-commit repair). This is accuracy-first work.

### Budget
No dollar cap for this session. Take the time to do each TDD cycle properly.

### Reference Files Available
All planning artifacts are in the repo:
- `docs/superpowers/specs/2026-10-05-roap-v1-implementation-design.md`
- `docs/superpowers/plans/2026-10-05-roap-v1-implementation-plan.md`
- `knowledge/decisions/engineering-decisions.md`
- `knowledge/decisions/index.md`
- `decisions-vraj-for-meeting-6th-oct.md`
- `.superpowers/sdd/2026-10-05-roap-v1-implementation-plan/progress.md`

### Prototype Source
`references/prototype/oa_pipeline/` contains the complete v0.2.0 prototype with:
- `src/oa_pipeline/` — 12 modules (already migrated in P1-03)
- `tests/` — 14 test files, 221+ tests
- `configs/` — 7 YAML files
- `examples/` — make_example_data.py + example_data.xlsx
- `notebooks/` — 8 Papermill notebooks
- `run_pipeline.sh` — CLI orchestrator
- `oa_pipeline_app.py`, `oa_pipeline_app_core.py` — GUI
- `stamp_carbonate_provenance.py` — provenance helper

---

**You have everything needed. Start with Task P1-04.**
