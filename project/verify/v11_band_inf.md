# Verification - the band rule re-derived (b = inf pp)

The HANDOFF calls this the most valuable check: it tests the rule's logic,
not the bookkeeping. `src/rules.py` is not imported; the rule is
re-implemented from MASTER section 4 against the saved availability,
baseline dispatch, overload series and shift factors.

- case `WP2024s42`, first **500** hours, **51** cuttable farms
- hours with an overload in the window: **135**
- total cut, re-derived: **13,489.936 MW**
- total cut, `WP2024s42_cuts_bandinf.parquet`: **13,489.936 MW**
- relative difference in total: **1.348e-16**
- worst element-wise |difference|: **2.842e-14 MW**
- elements differing by more than 1e-6 MW: **0** of 25500

## Cumulative position per farm (what the results report)

- worst |cumulative cut difference| per farm: **0.000 MW** on totals of order 2,734 MW
- correlation of per-farm cumulative cut: **1.000000**
- year-to-date ratio spread, re-derived: **55.240 pp**
- year-to-date ratio spread, saved: **55.240 pp**

The re-derivation reproduces the saved cut vector exactly.
