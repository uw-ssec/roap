---
type: Fact
title: Duplicate Precision Assessment
description: "Precision = 2.2 × SD/√n per GOA-ON Cookbook; field vs analytical duplicates distinguished; weather-quality tier; computed for TA, pH, DIC independently"
tags: [duplicate-precision, goa-on, precision-statistic, field-duplicates, analytical-duplicates]
generated: { by: agent/cli, at: "2026-10-02T05:40:26Z" }
status: stable
---

# Duplicate Precision Assessment Methods

## Precision Statistic

Measurement precision assessed from duplicate samples using standard estimator per GOA-ON Cookbook and Dickson et al. (2007), SOP 22/23:

    precision = 2.2 × (SD / √n)

where SD = pooled standard deviation of duplicate pairs, n = number of pairs.
Factor 2.2 = two-sided coverage of duplicate distribution.

For paired duplicates: each pair contributes one degree of freedom; pooled SD = √(mean(s_i²)) where s_i = within-pair standard deviation.

Precision computed independently for: total alkalinity (TA), pH, dissolved inorganic carbon (DIC).

## Duplicate Type: Field vs Analytical

| Type | Description | Captures |
|------|-------------|----------|
| **Field duplicates** | Two samples collected from same site/depth on same occasion | Total measurement uncertainty: fine-scale spatial/temporal heterogeneity + sample handling/preservation + analytical error |
| **Analytical duplicates** | Single sample split and analysed twice | Analytical error only (instrument and operator) |

Field duplicates expected to exceed analytical duplicates; reported separately. Software records duplicate type per precision estimate for correct interpretation.

## Quality Tier

Data quality assessed against **weather-quality** tolerance (appropriate for research-grade coastal monitoring). If precision exceeds tolerance, data flagged for review.

## Reporting

Precision estimates reported with:
- Duplicate type (field/analytical)
- Number of pairs (n)
- Pooled SD
- Precision value (2.2 × SD/√n)
- Quality tier assessment

Follows GOA-ON Cookbook Data QA/QC Guidelines and Dickson et al. (2007).
