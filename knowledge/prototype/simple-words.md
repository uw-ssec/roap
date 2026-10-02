---
type: Fact
title: Pipeline in Simple Words
description: "8-step explanation: column matching, CRM correction, pH std correction, PyCO2SYS math, replicate check, range checks, provenance stamping, verdict classification"
tags: [simple-words, pipeline-explanation, stages]
generated: { by: agent/cli, at: "2026-10-02T00:40:55Z" }
status: stable
---

# Pipeline in Simple Words

## 8-Step Process
1. **Column matching (schema resolution)** — Different cruises/analysts name columns differently (pH_lab vs ph_observed). An alias map translates whatever comes in to one standard set of names.

2. **CRM correction** — Before trusting TA numbers, the pipeline checks known reference-material samples (RM213) measured in the same batch. If the instrument was reading a known sample wrong, it corrects everyone else's TA by that same offset.

3. **pH standard correction** — Same idea for pH: checks the pH electrode against Tris buffer standards (chemicals with known "answers") run in the same session, and corrects the sample pH readings against that.

4. **The math (PyCO2SYS)** — Takes the corrected TA + pH and computes the rest of the carbonate system: DIC, pCO2, aragonite/calcite saturation states, Revelle factor. Note: on the real dataset tested, this step had already been done by someone else's tool before the file reached the pipeline — the pipeline's job was to check that work, not redo it.

5. **Replicate check** — Many samples were measured twice (duplicates). This step compares the pair and decides if they agree closely enough using accepted scientific threshold (GOA-ON), or if they disagree enough to be flagged.

6. **Range/sanity checks** — Every computed value gets checked against physically plausible bounds (e.g., pCO2 must fall between 50-4000 µatm). Anything outside gets flagged.

7. **Provenance stamping** — Records, per sample, exactly which corrections were applied, which solver/constants computed the chemistry, and what values fed into it. If that record is missing, the pipeline won't trust the row.

8. **Verdict classification** — Combines everything above into one final PASS / REVIEW / FAIL per sample, with a written reason (e.g., "replicate disagreement," "missing provenance," "out of range").

## Summary
Column matching → two correction steps (TA via CRM, pH via Tris) → PyCO2SYS math → duplicate-agreement check → range check → provenance record → final verdict. The math is one step in the middle; most of the pipeline is making sure the inputs to that step, and the trust in its outputs, are solid.
