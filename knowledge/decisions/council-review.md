---
type: Decision
title: Council Review of Epic Plan
description: Four-voice council identified missing P-1 migration phase and restructured priorities
tags: [council, decision, epic-review]
generated: { by: agent/cli, at: "2026-10-02T00:35:09Z" }
status: stable
---

# Council Review of Epic Plan

## Date: 2026-09-29
## Method: Four-voice council (Architect, Skeptic, Pragmatist, Critic)

## Consensus
All three external voices identified the same root failure: The epic assumes the pipeline code already exists in this repository. It does not. The roap repo is a project template; the actual oa_pipeline v0.2.0 lives in a separate location with its own .git/, .venv_run/, 221 tests, and 8 notebooks.

## Key Decisions from Council
1. **Added P-1 Phase (Blocking)**: Prototype migration must happen first - 2-3 days of copying/merging
2. **Merged P0 + Invariant Test**: The invariant test is what makes CI meaningful. Without it, green builds corrupt data.
3. **Moved P4 before P3**: ADR on queryable layer is a hard gate. Don't design export until target known.
4. **Added Missing Issues**: Excel round-trip fix, CRM/std tag validation, property-based testing, real dataset manual regression gate, Papermill to CLI migration, ADR before P3 export design.

## Surprises the Other Voices Missed
1. Skeptic: This repo has no src/oa_pipeline/ - CI will have nothing to test
2. Pragmatist: The real April 2026 dataset (38 samples, exact verdicts) is the only integration test that matters, but it's unpublished and excluded from CI
3. Critic: The epic describes a migration but contains zero migration tasks
