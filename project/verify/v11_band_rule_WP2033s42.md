# Verification - the band rule re-derived (b = 3 pp)

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
- total cut, re-derived: **7,334.007 MW**
- total cut, `WP2033s42_cuts_band3.parquet`: **7,352.525 MW**
- relative difference in total: **2.519e-03**
- worst element-wise |difference|: **7.374e+01 MW**
- elements differing by more than 1e-6 MW: **720** of 28500

## Cumulative position per farm (what the results report)

- worst |cumulative cut difference| per farm: **54.802 MW** on totals of order 1,402 MW
- correlation of per-farm cumulative cut: **0.998814**
- year-to-date ratio spread, re-derived: **9.012 pp**
- year-to-date ratio spread, saved: **8.875 pp**

Largest differences:

| hour | farm | re-derived | saved | diff |
|---|---|---|---|---|
| 2030-02-08 22:00:00 | 40971-1 | 73.740960 | 0.000000 | 7.374e+01 |
| 2030-02-09 00:00:00 | 40971-1 | 0.000000 | 73.704880 | 7.370e+01 |
| 2030-02-08 20:00:00 | 40971-1 | 0.000000 | 73.686840 | 7.369e+01 |
| 2030-02-09 02:00:00 | 40971-1 | 73.235840 | 0.000000 | 7.324e+01 |
| 2030-01-08 14:00:00 | 40971-1 | 0.000000 | 73.162040 | 7.316e+01 |

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
