# Equilibrium (Dissociation) Constants Sets

Choice of carbonic acid dissociation constants (K1, K2) is one of the two
biggest sources of cross-lab disagreement in carbonate chemistry calculations
(the other is pH scale — see the parent skill). None of these sets is
universally "correct"; each is a published, peer-reviewed fit valid over a
specific temperature/salinity range. PyCO2SYS exposes the choice via the
`opt_k_carbonic` argument.

## Common options (PyCO2SYS `opt_k_carbonic` values)

| Code | Constants set                                         | Reference                                        | Valid range (approx.)                 | Notes                                                                                                  |
| ---- | ----------------------------------------------------- | ------------------------------------------------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1    | Roy et al. 1993                                       | Roy et al. (1993)                                | T 0-45 C, S 5-45                      | Older, less commonly used now                                                                          |
| 4    | Mehrbach et al. 1973, refit by Dickson & Millero 1987 | Mehrbach et al. (1973); Dickson & Millero (1987) | T 2-35 C, S 20-43                     | Long-standing historical default in many labs                                                          |
| 10   | Lueker, Dickson & Keeling 2000                        | Lueker et al. (2000)                             | T 2-35 C, S 19-43                     | Refit of Mehrbach data with improved pH-scale consistency; widely recommended as current best practice |
| 15   | Waters, Millero & Woosley 2014                        | Waters et al. (2014)                             | Wide T/S range including low salinity | Useful for brackish/estuarine coastal work                                                             |

## This project's default

**`opt_k_carbonic=10`** (Lueker et al. 2000) — chosen for comparability with
other GOA-ON / OA-Africa network members who have converged on this as a modern
default. **Action item:** confirm this matches what Prof. Mahu's group has used
historically in their existing spreadsheets/scripts before finalizing — if their
historical data used a different set (e.g., code 4), either:

- standardize forward on code 10 and flag historical data as using a different
  constants set in its provenance record, or
- make the constants set an explicit, required schema field per-sample rather
  than a single project-wide constant, so mixed-vintage datasets stay honest.

## Why this must be recorded in provenance

Any exported result must carry the `opt_k_carbonic` value (and `opt_pH_scale`,
see `pyco2sys-usage` skill) used to produce it. Without this, re-deriving why
two Omega_aragonite values disagree is not possible even with identical raw
DIC/TA inputs.
