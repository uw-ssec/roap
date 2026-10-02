---
type: Requirement
title: AI-Friendly PRD
description: "Complete PRD for ROAP v1.0.0: objective, 12-week timeline, constraints, non-goals, code paths, glossary, acceptance criteria, references, risks, metrics, open questions"
tags: [ai-prd, requirements, prd, approval-gate]
generated: { by: agent/cli, at: "2026-10-02T00:45:17Z" }
status: stable
---

# AI-Friendly Product Requirements Document

## Source
docs/ai-prd.md (this repository)

## Purpose
Single source of truth for AI agents working on ROAP. Synthesized from epic.md, council review, architecture decisions, prototype codebase, domain knowledge, and personas.

## Structure
1. **Objective** - North star: fresh clone → working run <10 min on 3 platforms
2. **Phase & Milestone Timeline** - 12 weeks: P-1 → P0 → P1 → P2 → P4 → P3 → v1.0.0
3. **Constraints** - Pixi-only, Python 3.11, cross-platform, no unpublished data, conventional commits
4. **Non-Goals** - No PyCO2SYS rewrite, no queryable DB in v1.0, no web UI, no streaming
5. **Relevant Code Paths** - Prototype source (git submodule) + target repo structure
6. **Domain Glossary** - 15 key terms (DIC, TA, pH scale, Ω, CRM, sample_tag prefix, Frontiers 2021, etc.)
7. **Acceptance Criteria** - Testable checkboxes for each phase (P-1 through v1.0.0)
8. **Similar Implementations** - Internal (prototype, ADRs, council review) + External (Frontiers, PyCO2SYS, GOA-ON)
9. **External References** - Papers, tools, networks
10. **Risk Register** - 6 risks with likelihood/impact/mitigation
11. **Success Metrics** - 10 quantifiable v1.0.0 targets
12. **Open Questions** - 5 decisions needing human input (ADR 0001, PyCO2SYS version, dataset access, GPG, PyPI)
13. **Epic-to-PRD Traceability** - Maps each epic priority to PRD sections

## Approval Gate
Implements Approval Gate 2: AI-Friendly PRD review before milestone issues created.

## Key Decisions Reflected
- P-1 migration blocking all work (council review finding)
- 12-week timeline with buffers (reviewer feedback)
- Git submodule for prototype (reviewer feedback)
- Invariant test in CI (ADR-0003)
- Frontiers 2021 as default schema (ADR-0009)
- Single engine three doors (ADR-0010)

# Related Concepts
- [Personas and User Stories](../personas/user-stories.md): AI-PRD includes user stories as acceptance criteria
- [Data Standards: Frontiers 2021](../domain/data-standards.md): AI-PRD references Frontiers 2021 data standards
- [Carbonate Chemistry Fundamentals](../domain/carbonate-chemistry.md): AI-PRD references carbonate chemistry fundamentals
- [PyCO2SYS Usage Reference](../domain/pyco2sys-usage.md): AI-PRD references PyCO2SYS usage patterns
- [Prototype Pipeline Overview](../prototype/pipeline-overview.md): AI-PRD references prototype pipeline architecture
- [Project Tech Stack](tech-stack.md): AI-PRD documents the tech stack
- [Open Questions for Engineering](open-questions.md): AI-PRD lists open questions requiring human decisions
