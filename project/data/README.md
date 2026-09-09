# SEM-O dynamic reports — what is here and how it was pulled

Source: https://www.sem-o.com/market-data/dynamic-reports (JS page). The page calls an open JSON API:

```
https://reports.sem-o.com/api/v1/dynamic/<REPORT>?StartTime=>=YYYY-MM-DDT00:00:00<=YYYY-MM-DDT23:59:00&sort_by=StartTime&order_by=ASC&page=1&page_size=5000
```

No auth. `page_size` max 5000. BM-037 uses `EffTime` instead of `StartTime`. Pagination key is `totalPages`.

## Reports that matter for constraint work

| Report | Name | Grain | Retention (checked 2026-09-07) | Use |
|---|---|---|---|---|
| BM-086 | Daily Meter Data, metered generation by unit | 30 min, per unit (~342 units/day, GEN + interconnectors) | rolling ~3 months (from 2026-06-08) | actual output |
| BM-101 | Average Outturn Availability | 30 min, per unit | same window | what the unit *could* have produced |
| BM-096 | Dispatch Quantity | 30 min, per unit | same window | what it was told to produce |
| BM-033 | Forecast Availability | 30 min, per unit | same window | day-ahead availability |
| BM-037 | Daily Dispatch Instructions (D+1) | per instruction, timestamped to the second | 2026-06-07 → today (plus 371 stray rows from 2020-04) | **the WDT setpoints themselves** |
| BM-012 | Four-day rolling wind forecast per unit | 15 min | same window | wind forecast |

**Availability − Metered = dispatch-down per unit per half hour** (BM-101 − BM-086). Cross-check with BM-037.

## BM-037 instruction codes (wind)

`InstructionCode = WIND` rows carry an `InstructionCombinationCode`:

| Code | Meaning | Rows (3 months) |
|---|---|---|
| CURL | curtailment applied (system-wide SNSP) | 132,581 |
| LOCL | **local constraint applied** (a constraint group firing) | 69,191 |
| CRLO | curtailment released | 12,795 |
| LCLO | local constraint released | 7,343 |

Meaning of the codes confirmed by EirGrid's Wind Dispatch-Down Reports user guide
(cms.eirgrid.ie, "New-Wind-DD-Calc-Userguide-v1.1.pdf"). `DispatchInstructionMW` is the setpoint.

## Empirical constraint groups

Units that receive LOCL instructions at the *same issue second* were told to cut together, i.e. they are
one constraint group being invoked. `empirical_constraint_groups_top20.csv` lists the 20 most frequent
exact batch compositions with their transmission stations. Several match the WDT overview PDF directly:

- Salthill / Uggool / Knockalough / Knockranny (fired 233×) = West Constraint Group 3.
- Cunghill / Glenree / Dalton / Tawnaghmore / Srahnakilly / Bellacorick (60×) = West Groups 6/7 (Mayo).
- Corderry / Garvagh / Booltiagh / Lisheen / Trien combos = West / South West groups.

One batch of 8 units spanning Donegal to Cork (132×) is NOT geographic. Hypothesis, unverified: it is
a non-priority-dispatch ordering (newer "Phase 2" / solar units cut first), not a constraint group.

## Files

- `BM-037_dispatch_instructions_2026-06-07_to_09-05.csv` — every dispatch instruction, all units (290k rows, 22 MB).
- `semo_unit_map_IE.csv` — GU_ code → unit name, TSO id, transmission station, kV. Parsed from SEM-O's
  2025/26 Combined Loss Adjustment Factors publication (IE units only, 233 units). NI units (GU_5xxxxx)
  are NOT mapped: they belong to SONI and are absent from this file.
- `locl_instructions_per_unit.csv` — LOCL instruction counts per unit, joined with the map.
- `empirical_constraint_groups_top20.csv` — see above.

## Gaps

- NI units unmapped. The 15 most-constrained units by instruction count are all NI (GU_5xxxxx).
- Some newer IE units (e.g. GU_407670, GU_408120) are not in the CLAF list. The 2018 legacy
  "List of Registered Units" PDF (sem-o.com) covers older ones.
- Dynamic reports keep ~3 months. For history, SEM-O's static reports and EirGrid's annual
  constraint/curtailment reports are the route.
