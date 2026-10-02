# Prototype
* [Prototype Pipeline Overview](pipeline-overview.md) - 8-notebook OA pipeline: CRM TA correction, pH std correction, canonical schema, best source, duplicates, carbonate diagnostics, final verdict
* [Input Data Dictionary](data-dictionary.md) - Row classification by sample_tag prefix, column aliases, accepted values, required columns, CRM batches, range bounds
* [Pipeline in Simple Words](simple-words.md) - 8-step explanation: column matching, CRM correction, pH std correction, PyCO2SYS math, replicate check, range checks, provenance stamping, verdict classification
* [OA Pipeline Orientation](orientation.md) - Three run modes, 8 notebook stages, 12 package modules, configuration system, example data, Windows Git Bash requirement
* [Prototype Git Submodule](git-submodule.md) - oa_pipeline v0.2.0 at references/prototype/oa_pipeline/ from https://github.com/reez-png/oa_pipeline - source for P-1 migration
* [Carbonate Calculation Design](carbonate-calc-design.md) - RM correction before PyCO2SYS, input pair TA+pH, project default constants (Lueker 2000, Total scale), in-situ vs measurement conditions, vectorized batch usage
* [Carbonate Methods & QC Validation](carbonate-methods-note.md) - Methods section for manuscript: constants used, RM correction (batch 213), tris buffer QC, measured vs calculated pH validation (temp effect r=-1.00, slope -0.0165/°C)
* [Duplicate Precision Assessment](duplicate-precision-methods.md) - Precision = 2.2 × SD/√n per GOA-ON Cookbook; field vs analytical duplicates distinguished; weather-quality tier; computed for TA, pH, DIC independently
* [Prototype README](prototype-readme.md) - oa_pipeline v0.2.0: 8 notebooks, 9 package modules, 3 run modes (CLI/GUI/Notebook), Windows Git Bash requirement, example data, 221 tests
* [Notebook READMEs (Consolidated)](notebook-readmes.md) - 8 notebooks: 01 viewer, 02 TA/pH QC, 03 review, 04 Stage 1A schema, 05 Stage 1B coalescing, 06 Stage 2 duplicates, 07 Stage 3 carbonate checks, 08 Stage 4 verdicts
* [Requested Dataset (April 2026)](requested-dataset.md) - 38 samples, expected 22 PASS/16 REVIEW/0 FAIL, manual regression gate before every release, unpublished (not in CI), shared folder access
