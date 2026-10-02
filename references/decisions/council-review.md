# ROAP — Council Review of Epic Plan

**Date:** 2026-09-29  
**Context:** Review of initial epic breakdown (P0-P4) before P-1 migration added  
**Method:** Four-voice council (Architect, Skeptic, Pragmatist, Critic)  
**Trigger:** "Will the proposed epic breakdown actually deliver v1.0.0 that resolves all persona problems?"

---

## Original Epic (Pre-Council)

| Priority | Theme |
|----------|-------|
| P0 | Cross-platform CI + single entry point |
| P1 | Packaging, releases, version pinning |
| P2 | Schema alignment + provenance + invariant tests |
| P3 | International export + pre-flight validation |
| P4 | Queryable time-series layer (scope decision) |

**14 GitHub issues** mapped to these priorities.

---

## Council Verdict

### Consensus
**All three external voices identified the same root failure:** The epic assumes the pipeline code already exists in this repository. **It does not.** The `roap` repo is a project template; the actual `oa_pipeline` v0.2.0 lives in `local/prototype/my_understanding/test/oa_pipeline/` with its own `.git/`, `.venv_run/`, 221 tests, and 8 notebooks.

---

### Voice Positions

#### Skeptic
> **Position:** The epic has fatal gaps — it treats P0-P3 as sequentially executable when P2's invariant test and schema audit are prerequisites for P0's CI to be meaningful, and P4's unresolved scope decision makes P3's export design speculative. The plan also omits the known Excel round-trip bug fix and CRM tag validation from any priority.

**Reasoning:**
- Invariant test (P2) must precede or run parallel to P0 CI — without it, 3-platform CI passes while silently corrupting lat/lon (the exact bug that survived 221 tests). CI green ≠ data integrity.
- P4 scope decision gates P3 export design — GOA-ON export structure differs fundamentally between DuckDB-backed time-series layer and file-based manifest workflow. Building P3 before deciding P4 risks rework.
- Excel round-trip bug and CRM tag logic are missing from all priorities — the openpyxl formula-column blanking (structural risk) and `sample_tag` prefix identification (single most-repeated warning) appear nowhere in the 14 issues.

**Risk:** P0 delivers a "green CI" that passes on three platforms but produces corrupted output on real data because the invariant test and CRM/std validation don't exist yet — giving false confidence that blocks P1-P3 work.

**Surprise:** The other voices may miss that the current repo (`roap`) is a *project template*, not the `oa_pipeline` codebase itself — P1's "pip install oa-pipeline" and P0's CI must target the *vendored* oa_pipeline repo, not this template, which has no `src/oa_pipeline/` or `pyproject.toml` for the actual pipeline.

#### Pragmatist
> **Position:** The epic breakdown is structurally sound but has a fatal gap: it treats Kofi (Excel-only, no terminal) as an export consumer only, ignoring that Kofi likely *produces* input data in Excel — the round-trip bug (blanks formula columns) means Kofi's workflow is broken at ingestion, not just export.

**Reasoning:**
- P2 "schema/provenance/invariant tests" assumes the lat/lon bug is a test coverage problem, but it survived 221 tests — the testing *philosophy* (property-based/invariant vs example-based) must change, not just test count.
- P3 "export+validation" addresses Nadia/Prof. Adjei output needs but doesn't specify a no-code *input* path for Kofi (Excel template with guarded columns? Web form?); Fatou's column mapping is mentioned in P2 but not validated against Kofi's Excel reality.
- P4 "queryable layer" is correctly scoped as a decision, but the epic lacks a P0.5: "Papermill → CLI migration" — the 8-notebook architecture is the root cause of confusing entry points and Windows-only coupling.

**Risk:** The team treats P2 invariant tests as "add tests" rather than "redesign test strategy," so the lat/lon bug class survives v1.0.0.

**Surprise:** The real April 2026 dataset (38 samples, 22 PASS/16 REVIEW/0 FAIL) is the *only* integration test that matters — but it's unpublished and not in CI. The epic never mentions making this dataset a first-class regression gate.

#### Critic
> **Position:** The epic breakdown is structurally sound but has a fatal gap: P0-P3 success criteria assume the `oa_pipeline` source code already exists in this repo, but it doesn't — this is a template repo, not the actual pipeline. No issues address *migrating* the prototype (notebooks, `src/oa_pipeline`, tests, example data) into this codebase, which is the prerequisite for every P0-P3 task.

**Risk:** The team wastes weeks implementing CI, packaging, and schema alignment against a codebase that doesn't exist here. The "221 tests" and "lat/lon bug" are in a separate prototype repo that hasn't been imported.

**Surprise:** The EPIC.md reads like a greenfield plan but describes a brownfield migration. The other voices may miss that *zero* P0-P3 issues can be completed until someone does the unglamorous work of: (1) copying the prototype into `src/oa_pipeline`, (2) extracting notebooks to scripts, (3) moving 221 tests into `tests/`, (4) adding the synthetic example data — none of which are in the 14 issues.

#### Architect (Me)
> **Position:** The plan correctly sequences *capabilities* but misses the *prerequisite*: importing the prototype. P0 CI on three platforms is meaningless without the code under test. The invariant test (P2) is the highest-leverage single artifact — it catches the class of bug that survived 221 tests. P4 scope decision is indeed a gate for P3 export design.

---

## Strongest Dissent
**Critic:** "Zero P0-P3 issues can be completed until someone does the unglamorous work of: (1) copying the prototype into `src/oa_pipeline`, (2) extracting notebooks to scripts, (3) moving 221 tests into `tests/`, (4) adding synthetic example data — none of which are in the 14 issues."

---

## Premise Check (Skeptic)
**The Skeptic challenged the premise itself:** *"This repo is a project template, not the oa_pipeline codebase. P0's CI and P1's packaging must target the vendored prototype, not this template."* **This is correct and changes everything.**

---

## Surprises the Other Voices Missed
1. **Skeptic:** This repo has no `src/oa_pipeline/` — CI will have nothing to test
2. **Pragmatist:** The real April 2026 dataset (38 samples, exact verdicts) is the *only* integration test that matters, but it's unpublished and excluded from CI
3. **Critic:** The epic describes a migration but contains zero migration tasks

---

## Revised Epic Structure (Post-Council)

```
P-1: Prototype Migration (2-3 days)          ← NEW, BLOCKING
P0:  CI + Invariant Test + Entry Point       ← Merged P0+P2 critical piece
P1:  Packaging + Releases + Run Bundles
P2:  Schema/Provenance/CRM/Excel Fixes       ← Expanded
P4:  ADR: Queryable Layer (gate for P3)      ← Moved UP
P3:  Export + Validation                     ← After P4 decision
```

---

## New P-1 Phase (Blocking)

| Task | Description |
|------|-------------|
| P-1.1 | Copy `local/prototype/my_understanding/test/oa_pipeline/src/oa_pipeline/` → `src/oa_pipeline/` |
| P-1.2 | Copy `local/prototype/my_understanding/test/oa_pipeline/tests/` → `tests/` (221 tests) |
| P-1.3 | Copy `local/prototype/my_understanding/test/oa_pipeline/examples/` → `examples/` |
| P-1.4 | Copy `local/prototype/my_understanding/test/oa_pipeline/configs/` → `configs/` |
| P-1.5 | Create `pyproject.toml` for `oa_pipeline` package (src-layout) |
| P-1.6 | Extract notebook orchestration → CLI entry points (`oa-pipeline` command) |
| P-1.7 | Add `.gitignore` for unpublished data (`local/prototype/.../oa_data_apr_provenance.xlsx`) |
| P-1.8 | Verify: `pytest -q` → 221 pass; `./run_pipeline.sh` on synthetic data → 4 FAIL verdicts |

---

## Added Missing Issues (from Council)

| Issue | Priority | Source |
|-------|----------|--------|
| Excel round-trip fix (safe read/write for formula columns) | P2 | Skeptic, Pragmatist |
| CRM/std tag validation (fail fast on prefix mismatch) | P2 | Skeptic |
| Property-based testing foundation (hypothesis) | P2 | Pragmatist |
| Real dataset manual regression gate (22/16/0) | P3 | Pragmatist |
| Papermill → CLI migration | P-1 | Pragmatist |
| ADR before P3 export design | P4 | Skeptic |

---

## Key Takeaways for Lead

1. **Start with P-1** — nothing else works until code is in this repo. 2-3 days of copying/merging.
2. **P0 = CI + Invariant Test together** — the invariant test is what makes CI meaningful. Without it, green builds corrupt data.
3. **P4 before P3** — ADR on queryable layer is a hard gate. Don't design export until target known.
4. **Real dataset = manual regression gate** — not in CI, but required before every release. Document process.
5. **Kofi's workflow is bidirectional** — produces Excel input (round-trip bug) AND consumes validation output. Fix both.
6. **Fatou's config-driven aliases** — key to regional adoption. Don't hardcode column names.
7. **Update `CARBONATE_CHEMISTRY_KNOWLEDGE.md` first** when domain decisions change, then propagate to skills.

---

## Action Taken
- Created revised `EPIC.md` with P-1 phase, merged P0+invariant test, expanded P2, moved P4 before P3
- Added 24 GitHub issues (was 14)
- Committed to `epic_draft` branch, PR #3 opened
- This review saved in `local/decisions/council-review.md` for future agents