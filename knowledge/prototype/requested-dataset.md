---
type: Fact
title: Requested Dataset (April 2026)
description: "38 samples, expected 22 PASS/16 REVIEW/0 FAIL, manual regression gate before every release, unpublished (not in CI), shared folder access"
tags: [requested-dataset, manual-regression, april-2026, real-data]
generated: { by: agent/cli, at: "2026-10-02T05:41:08Z" }
status: stable
---

# Requested Dataset

## April 2026 Cruise (P4506)

**Location:** Shared folder (not in repo — unpublished data)
**Samples:** 38
**Expected Verdicts:** 22 PASS, 16 REVIEW, 0 FAIL

## Manual Regression Gate

Before every release:
1. Run pipeline on April 2026 dataset from shared folder
2. Verify: 22 PASS, 16 REVIEW, 0 FAIL
3. Document in `docs/manual-regression.md` with steps and expected outputs
4. **Not in CI** (unpublished data) — but required before every release

## Purpose

This is the **only** integration test that matters for real-world validation. The synthetic example data tests code paths, but the April 2026 dataset validates the full pipeline against real carbonate chemistry data with known expected outcomes.

## Access Protocol

[TO BE DOCUMENTED: Location, access credentials, file format, sheet name]
