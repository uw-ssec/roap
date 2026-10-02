---
type: Fact
title: Meeting Prep 2026-09-15
description: "Council review preparation, prototype location blocker, priority restructuring, real dataset regression gate, Kofi bidirectional workflow"
tags: [meeting, prep, council-review, blocker]
generated: { by: agent/cli, at: "2026-10-02T00:45:31Z" }
status: stable
---

# Meeting Prep: 2026-09-15

## Context
Preparation meeting for ROAP project planning and council review.

## Key Discussion Points
1. **Prototype Location**: The actual oa_pipeline v0.2.0 codebase lives in a separate repository, not in the roap template repo. This is the critical blocker for all P0-P4 work.

2. **Council Review Method**: Four-voice council (Architect, Skeptic, Pragmatist, Critic) to review epic breakdown before implementation.

3. **Priority Restructuring**: 
   - Added P-1 (Prototype Migration) as blocking phase
   - Merged P0 + Invariant Test (CI meaningless without it)
   - Moved P4 (ADR Queryable Layer) before P3 (Export) as hard gate
   - Expanded P2 to include Excel round-trip fix, CRM/std validation, property-based testing

4. **Real Dataset**: April 2026 dataset (38 samples) is the only meaningful integration test but is unpublished. Must be manual regression gate before every release.

5. **Kofi's Bidirectional Workflow**: Produces Excel input (affected by round-trip bug) AND consumes validation output. Must fix both.

6. **Fatou's Config-Driven Aliases**: Key to regional adoption. Don't hardcode column names.

7. **Knowledge Management**: Update CARBONATE_CHEMISTRY_KNOWLEDGE.md first when domain decisions change, then propagate to skills.

## Action Items
- Create revised EPIC.md with P-1 phase
- Add 24 GitHub issues (was 14)
- Open PR for council review
- Begin P-1 migration work

# Related Concepts
- [Council Review of Epic Plan](../decisions/council-review.md): Meeting prep led to council review
