# PyCO2SYS Parameter & Option Codes

> **Verify before relying on these in code.** The concepts and the low-numbered
> codes below are stable across PyCO2SYS versions, but always cross-check the
> exact integer codes against the installed version's docs
> (https://pyco2sys.readthedocs.io/en/latest/) before shipping a call that
> depends on them — especially for `opt_k_carbonic`, which has the most values
> and the most version-to-version documentation churn. Treat this file as a map
> for orientation, not a substitute for the source docs.

## `par1_type` / `par2_type`

Identifies which physical quantity each of `par1`/`par2` represents:

| Code | Parameter                        | Typical unit                                |
| ---- | -------------------------------- | ------------------------------------------- |
| 1    | Total Alkalinity (TA)            | umol/kg                                     |
| 2    | Dissolved Inorganic Carbon (DIC) | umol/kg                                     |
| 3    | pH                               | dimensionless (scale set by `opt_pH_scale`) |
| 4    | Partial pressure of CO2 (pCO2)   | uatm                                        |
| 5    | Fugacity of CO2 (fCO2)           | uatm                                        |
| 6    | Carbonate ion (CO3--)            | umol/kg                                     |
| 7    | Bicarbonate ion (HCO3-)          | umol/kg                                     |
| 8    | Aqueous CO2                      | umol/kg                                     |

This project's standard pairing: `par1_type=1` (TA), `par2_type=2` (DIC).

## `opt_pH_scale`

| Code | Scale          |
| ---- | -------------- |
| 1    | Total scale    |
| 2    | Seawater scale |
| 3    | Free scale     |
| 4    | NBS scale      |

This project's default: `opt_pH_scale=1` (Total).

## `opt_k_carbonic`

Selects the carbonic acid dissociation constants set. There are many valid
options (roughly a dozen-plus across PyCO2SYS's history) — see
`../../carbonate-chemistry/references/equilibrium-constants.md` for the subset
relevant to this project and their citations. **Confirm the exact code-to-set
mapping against the installed version's docs before hardcoding a value.**

This project's default: `opt_k_carbonic=10` (Lueker, Dickson & Keeling 2000).

## Other notable options

- `opt_k_bisulfate` — bisulfate dissociation constant choice (affects total pH
  scale conversions specifically).
- `opt_total_borate` — total borate estimation method (affects alkalinity
  speciation slightly).
- `opt_buffers_mode` — controls whether/how buffer factors (e.g. Revelle factor)
  are computed.

These are lower-impact than `opt_k_carbonic` / `opt_pH_scale` for this project's
purposes but should still be recorded in provenance if set explicitly rather
than left at PyCO2SYS defaults.
