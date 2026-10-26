# ROAP

ROAP turns raw ocean-acidification cruise workbooks into quality-controlled,
analysis-ready carbonate-chemistry datasets.

## Pipeline

**Stage**: One named step of the pipeline (QC, 1A, 1B, 2, 3, 4) that takes the
previous Stage's dataset and produces the next one. _Avoid_: step, notebook,
phase

**Range policy**: The plausible-value limits a Stage applies to each measured
variable. Each Stage owns its own defaults; a Stage's config may override them.
_Avoid_: thresholds, bounds, limits

## Rows

**Row role**: What a row in a cruise dataset represents: a Sample, a CRM, or a
Standard. Decided once from the Tag prefix and carried by every Stage. _Avoid_:
row classification, row type, sample type

**Sample**: A row holding a measurement of environmental seawater. _Avoid_:
water sample, environmental sample

**CRM**: A row holding a measurement of a certified reference material, used to
check and correct total-alkalinity (TA) accuracy. _Avoid_: RM, reference sample

**Certified value**: The published reference value of a CRM batch that measured
CRM values are compared against. It is reference input to a Stage, not data
flowing between Stages. _Avoid_: CRM value, reference value

**Standard**: A row holding a measurement of a pH standard (e.g. TRIS buffer),
used to check pH accuracy. _Avoid_: STD, TRIS row, phstd

**Tag prefix**: The leading characters of a row's tag that identify its Row
role. It is the only signal used to decide the Row role. _Avoid_: label, code
