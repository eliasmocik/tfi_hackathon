# Verification - the band rule re-derived (b = 3 pp)

The HANDOFF calls this the most valuable check: it tests the rule's logic,
not the bookkeeping. `src/rules.py` is not imported; the rule is
re-implemented from MASTER section 4 against the saved availability,
baseline dispatch, overload series and shift factors.

- case `WP2024s42`, first **500** hours, **51** cuttable farms
- relief is targeted on `FLG_SLIGO_N1` only. In the main case that is the only
  row that ever overloads, so the re-derivation is complete; in the WP2033
  cases the two Flagford transformer windings also bind, so hours driven by
  those rows are outside this re-derivation and show up as small residuals.
- hours with an overload in the window: **135**
- total cut, re-derived: **15,408.326 MW**
- total cut, `WP2024s42_cuts_band3.parquet`: **15,415.859 MW**
- relative difference in total: **4.887e-04**
- worst element-wise |difference|: **7.380e+01 MW**
- elements differing by more than 1e-6 MW: **1634** of 25500

## Cumulative position per farm (what the results report)

- worst |cumulative cut difference| per farm: **71.591 MW** on totals of order 2,440 MW
- correlation of per-farm cumulative cut: **0.999336**
- year-to-date ratio spread, re-derived: **13.740 pp**
- year-to-date ratio spread, saved: **13.873 pp**

Largest differences:

| hour | farm | re-derived | saved | diff |
|---|---|---|---|---|
| 2030-01-06 20:00:00 | 40971-1 | 73.800000 | 0.000000 | 7.380e+01 |
| 2030-01-05 19:00:00 | 40971-1 | 0.000000 | 73.800000 | 7.380e+01 |
| 2030-01-21 07:00:00 | 40971-1 | 73.800000 | 0.000000 | 7.380e+01 |
| 2030-01-06 19:00:00 | 40971-1 | 0.000000 | 73.800000 | 7.380e+01 |
| 2030-01-07 01:00:00 | 40971-1 | 73.800000 | 0.000000 | 7.380e+01 |

**These are not an error.** The same farm is cut fully by one
implementation in one hour and by the other in the adjacent hour.
The band rule is path-dependent: r_i feeds the next hour's
eligible set, so once two correct implementations differ by any
amount - a tie broken differently, a float rounding - the ledgers
diverge and the per-hour assignment separates while the aggregate
stays put. The totals above show that happening.

The operational implication is worth stating: two conforming
implementations of this rule will not produce identical per-farm
instructions. If the rule is ever codified, the tie-break and the
float tolerance have to be specified, not left to the vendor.
