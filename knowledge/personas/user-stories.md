---
type: Requirement
title: Personas and User Stories
description: 24 user stories across 6 personas mapped to 6 epic priorities with acceptance criteria
tags: [personas, user-stories, requirements]
generated: { by: agent/cli, at: "2026-10-02T00:45:24Z" }
status: stable
---

# Personas and User Stories (24 Stories)

## Personas
- **Ruu**: Trainee - needs clean laptop onboarding <1 hour
- **Kofi**: Technician - Excel-only, no terminal, produces input and consumes validation
- **Ama**: Analyst - QC configurability, figure provenance, replicate checks
- **Fatou**: Regional partner - config-driven column mapping for 3-year archive
- **Nadia**: Data manager - quarterly unattended runs, GOA-ON export, time series
- **Prof. Adjei**: PI - sign-off summaries, archived run bundles, citable releases

## Story to Epic Mapping
| Epic | Stories |
|------|---------|
| P-1 Migration | — (prerequisite) |
| P0 CI/Entry Point | US-16, US-17, US-19 |
| P1 Packaging/Releases | US-06, US-09, US-10, US-15, US-18, US-21, US-22 |
| P2 Schema/Provenance/CRM/Excel | US-01, US-03, US-04, US-05, US-07, US-08, US-11, US-12, US-13 |
| P4 ADR Queryable | US-23, US-24 |
| P3 Export/Validation | US-02, US-14, US-20 |

## Key Stories by Priority
- **US-01 (P2)**: Fatou maps columns via config, not renaming
- **US-02 (P3)**: Kofi validates bench sheet immediately, no terminal
- **US-03 (P2)**: Pipeline reads input without writing back to source (Excel round-trip bug)
- **US-06 (P1)**: Prof. Adjei gets readable run summary for sign-off
- **US-10 (P1)**: Pipeline refuses stale config (config compatibility gate)
- **US-16 (P0)**: Ruu clean laptop to successful run <1 hour
- **US-19 (P0)**: Cross-platform on Linux, macOS, Windows
- **US-22 (P1)**: Fatou needs citable tagged release for methods
- **US-23/24 (P4)**: Nadia time series, Ama query by station/depth/date

## Open Questions for Engineering
1. Queryable layer scope - DB vs files (gates P3 export design)
2. Cross-platform vs international export sequencing
3. Wider codebase context (1 of 4 related codebases)
4. Data volume/performance needs

# Related Concepts
- [Personas Summary](summary.md): User stories detail the persona summaries
- [Open Questions for Engineering](../project/open-questions.md): User stories inform open questions
