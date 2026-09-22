# pyco2sys-dev

A Claude Code plugin providing domain knowledge for developing the reproducible
coastal carbonate chemistry / ocean acidification software platform. Modeled
directly on
[`uw-ssec/HPyX`'s `hpx-dev` plugin](https://github.com/uw-ssec/HPyX/tree/main/plugins/hpx-dev)
— same structure, same "knowledge doc first, lean skills derived from it"
methodology, confirmed by that project's own commit/PR history.

## Purpose

Keeps Claude grounded in the marine carbonate chemistry domain, the PyCO2SYS
library's calling conventions, and the field's data standard while this platform
is being designed and built — so schema, QC, and export code gets built against
the right facts instead of ad hoc assumptions.

## Directory structure

```
pyco2sys-dev/
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── skills/
    ├── carbonate-chemistry/
    │   ├── SKILL.md
    │   └── references/equilibrium-constants.md
    ├── pyco2sys-usage/
    │   ├── SKILL.md
    │   └── references/parameter-codes.md
    └── data-standard/
        ├── SKILL.md
        └── references/qc-flags-and-columns.md
```

## Skills

| Skill                 | Covers                                                                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `carbonate-chemistry` | The DIC/TA/pH/pCO2 four-parameter system, saturation states, Revelle factor, and why constants/pH-scale choice creates cross-lab irreproducibility |
| `pyco2sys-usage`      | `pyco2.sys()` call conventions, parameter type codes, the `_out` in-situ/measurement condition distinction, vectorized batch usage                 |
| `data-standard`       | The Frontiers (2021) discrete chemical oceanography data standard — column naming, unified 0-9 QC flags, `-999` missing-value sentinel             |

Each `SKILL.md` is intentionally lean (progressive disclosure) with deep tables
and citations pushed into its `references/` subfolder, following the pattern
confirmed in `hpx-dev`'s PR #112.

## Source of truth

All three skills are distilled from
[`docs/domain-knowledge/CARBONATE_CHEMISTRY_KNOWLEDGE.md`](../../docs/domain-knowledge/CARBONATE_CHEMISTRY_KNOWLEDGE.md).
When the science, the library API, or the data standard changes, update that
document first, then propagate the change into the relevant skill/reference
files here.

## Not yet included (intentionally deferred)

- **Agents** (`schema-reviewer`, `reference-validator`) — `hpx-dev`'s
  equivalents (`binding-reviewer`, `benchmark-engineer`) review real code
  against real conventions. There's no schema/QC/export code to review yet; add
  these once that code exists.
- **A `skill-create`-generated engineering-pattern skill** — `skill-create`
  mines git history for coding conventions. This repo has no commit history yet,
  and even once it does, `skill-create` should stay scoped to _engineering
  conventions_ (how we structure validators, tests, provenance records), never
  to _domain correctness_ (which pH scale, which constants set) — the latter
  must stay hand-authored and literature-backed so an undetected bug in early
  code can't get silently canonized as a "pattern."

## Installation

Standard Claude Code plugin discovery — place this directory under your
project's (or global) `plugins/` path and Claude will auto-load the skills based
on their trigger descriptions.
