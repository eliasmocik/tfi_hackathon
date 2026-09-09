# Verification - the band rule re-derived (b = inf pp)

The HANDOFF calls this the most valuable check: it tests the rule's logic,
not the bookkeeping. `src/rules.py` is not imported; the rule is
re-implemented from MASTER section 4 against the saved availability,
baseline dispatch, overload series and shift factors.

- case `WP2033s42`, first **500** hours, **57** cuttable farms
- relief is targeted on `FLG_SLIGO_N1` only. In the main case that is the only
  row that ever overloads, so the re-derivation is complete; in the WP2033
  cases the two Flagford transformer windings also bind, so hours driven by
  those rows are outside this re-derivation and show up as small residuals.
- hours with an overload in the window: **64**
- total cut, re-derived: **6,924.735 MW**
- total cut, `WP2033s42_cuts_bandinf.parquet`: **6,932.960 MW**
- relative difference in total: **1.186e-03**
- worst element-wise |difference|: **3.673e+01 MW**
- elements differing by more than 1e-6 MW: **7** of 28500

## Cumulative position per farm (what the results report)

- worst |cumulative cut difference| per farm: **36.733 MW** on totals of order 1,892 MW
- correlation of per-farm cumulative cut: **0.999877**
- year-to-date ratio spread, re-derived: **28.591 pp**
- year-to-date ratio spread, saved: **28.591 pp**

Largest differences:

| hour | farm | re-derived | saved | diff |
|---|---|---|---|---|
| 2030-01-20 02:00:00 | 40971-1 | 36.732737 | 0.000000 | 3.673e+01 |
| 2030-01-20 02:00:00 | 26732-1 | 0.000000 | 21.102278 | 2.110e+01 |
| 2030-01-20 02:00:00 | 26771-1 | 0.000000 | 16.137036 | 1.614e+01 |
| 2030-01-20 02:00:00 | 26773-1 | 0.000000 | 13.654415 | 1.365e+01 |
| 2030-01-20 02:00:00 | 68308-1 | 2.418985 | 0.000000 | 2.419e+00 |

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
