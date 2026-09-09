# MEASUREMENT_NOTES — MASTER §6, run of src/measurement.py

Every number below is printed by `src/measurement.py`; the file is the log of one run.

## Method

1. Inner join BM-101 (AvgOutturnAvail, MW average over the half hour) and BM-096 (DispatchQuantity, MWh per half hour) on (ResourceName, StartTime); `avail_MWh = 0.5 × AvgOutturnAvail`, `dd_MWh = max(0, avail_MWh − DispatchQuantity)`.
2. State machine per unit from BM-037 WIND rows sorted by EffTime (ties by InstrIssueTime): LOCL → constraint=True, LCLO → False; CURL → curtail=True, CRLO → False. State False for all units at 2026-06-07 00:00:00; rows with EffTime before that (stray 2020-04 rows) dropped. A half-hour is under a state if the state at its StartTime is True (convention chosen by the reproduction check below).
3. Per unit: avail, dd, dd_ratio, constraint_only_ratio (dd in half-hours constrained and not curtailed ÷ avail over all half-hours), locl_any_ratio, curl_only_ratio, h_locl, h_curl.
4. Reproduction against data/nw_unit_dispatchdown_2026-06-08_to_09-05.csv.
5. Stations from semo_unit_map_IE.csv; CG1 = {ARDNAGAPPARY, BINBANE, LENALEA, TRILLICK}; CG3 = CG1 ∪ {CATH_FALL, CORDERRY, CUNGHILL, GARVAGH, GLENREE, MEENTYCAT, MOY, MULREAVY, SLIGO, TAWNAGHMORE} (map spellings).
6. Filter avail > 250 MWh and h_locl > 0; N, min, max, max/min, Jain, Gini on constraint_only_ratio at unit and station level; Jain = (Σr)²/(N Σr²); Gini = Σ(2i−N−1) r_i / (N Σ r_i) on the ascending sort, unweighted, no small-sample correction.
7. LOCL batches = rows sharing InstrIssueTime to the second; a batch is 'all-CG3' if every unit in it maps to a CG3 station (NI / unmapped units count as non-CG3).

## Headline numbers (from this run)

- Reproduction of the earlier CSV: PASS; convention EffTime <= StartTime; max abs diff on ratio/hour columns 9.71e-17; avail_MWh/dd_MWh differ by at most 0.4620 / 0.4845 MWh because the earlier file stored them rounded to integers (difference after rounding: 0).
- State machine: False at 2026-06-07 00:00:00; units under LOCL at window start 2026-06-08 23:00:00: 0; under CURL: 0; units whose first LOCL/LCLO instruction is a release: 0; first CURL/CRLO a release: 0.
- Units with 0 rows in BM-101 (absent): ['GU_401190'] (BM-096 only); see the run log for map units at CG1/CG3 stations with no BM-101 rows.
- Filter avail > 250 MWh and h_locl > 0 keeps 24 of 25 units.

Group table (constraint_only_ratio):

| group | level | N | min | max | max/min | Jain | Gini | min member | max member |
|---|---|---|---|---|---|---|---|---|---|
| CG1 | unit | 5 | 0.043148 | 0.098054 | 2.2725 | 0.9273 | 0.1568 | GU_404560 | GU_404630 |
| CG1 | station | 3 | 0.074886 | 0.081486 | 1.0881 | 0.9985 | 0.0190 | TRILLICK | BINBANE |
| CG3 | unit | 15 | 0.043148 | 0.098054 | 2.2725 | 0.9504 | 0.1301 | GU_404560 | GU_404630 |
| CG3 | station | 9 | 0.054518 | 0.089496 | 1.6416 | 0.9804 | 0.0798 | GARVAGH | TAWNAGHMORE |
| Booltiagh | unit | 4 | 0.028661 | 0.070243 | 2.4508 | 0.9167 | 0.1652 | GU_403800 | GU_401720 |
| Booltiagh | station | 1 | 0.041707 | 0.041707 | 1.0000 | 1.0000 | 0.0000 | BOOLTIAGH | BOOLTIAGH |
| all_filtered | unit | 24 | 0.015975 | 0.098054 | 6.1378 | 0.9177 | 0.1670 | GU_403840 | GU_404630 |
| all_filtered | station | 14 | 0.015975 | 0.089496 | 5.6021 | 0.9271 | 0.1477 | TIEVEBRACK | TAWNAGHMORE |

LOCL batches: 8734 distinct InstrIssueTime; all-CG3 batches 449 (of which >= 2 units 253, all-CG1 30); batches mixing CG3 and non-CG3 units 1647.

Top-10 all-CG3 station compositions:

| rank | stations | batches | units/batch |
|---|---|---|---|
| 1 | CORDERRY | 131 | 1 |
| 2 | BINBANE+MULREAVY | 114 | 2 |
| 3 | CORDERRY+GARVAGH | 84 | 2 |
| 4 | MULREAVY | 30 | 1 |
| 5 | BINBANE | 21 | 1 |
| 6 | GARVAGH | 13 | 1 |
| 7 | BINBANE+LENALEA+MEENTYCAT+MULREAVY+TRILLICK | 12 | 5 |
| 8 | BINBANE+LENALEA+MEENTYCAT+TRILLICK | 10 | 4 |
| 9 | LENALEA+MEENTYCAT+TRILLICK | 9 | 3-4 |
| 10 | MEENTYCAT+MULREAVY+TRILLICK | 9 | 3-4 |

## Caveats

- 90 days, one summer (2026-06-08 to 2026-09-05); no seasonal coverage.
- Group membership is inferred from station names in semo_unit_map_IE.csv and the Feb 2024 WDT Constraint Group Overview; groups may have changed since (Tievebrack receives LOCL but is in neither CG1 nor CG3 in the document).
- The LOCL/CURL state machine cannot tell which constraint group fired; a unit at a CG1 station may be constrained by CG1, CG3 or an outage variant.
- constraint-only is a lower bound: half-hours that are under both a LOCL and a CURL instruction are excluded from the numerator, and the state machine misses spells that began before 2026-06-07 (a unit whose first instruction is a release would be under-counted; the count of such units is in the run log).
- Rebalancing (live since 26 Nov 2025) is in force for the whole window, so the measured spread is the with-rebalancing regime.
- Availability (BM-101) is the TSO's outturn availability estimate; dd = max(0, avail − dispatch quantity) treats every shortfall of dispatch quantity below availability as dispatch-down.
- Units with 0 rows in BM-101 are absent (listed in the run log); ARDNAGAPPARY, MOY and SLIGO have no unit in the IE map, so CG3 is measured on the stations that do.

## Run log

```
==============================================================================
§6.1  Join BM-101 (AvgOutturnAvail, MW) and BM-096 (DispatchQuantity, MWh/30min)
BM-101 rows 115398, units 27, window 2026-06-08 23:00:00 .. 2026-09-05 23:30:00
BM-096 rows 111124, units 26, window 2026-06-08 23:00:00 .. 2026-09-05 23:30:00
units in BM-101 but not BM-096: ['GU_400030', 'GU_404930']
units in BM-096 but not BM-101 (0 rows in BM-101 -> no availability, dropped): ['GU_401190']
inner join rows 106850, units 25
half-hours per unit: min 4274, max 4274
measurement window (StartTime): 2026-06-08 23:00:00 .. 2026-09-05 23:30:00, 89.0208 days between first and last StartTime
==============================================================================
§6.2  State machine from BM-037
BM-037 rows 290357; EffTime 2020-04-26 23:00:00 .. 2026-09-05 22:57:52
rows with EffTime before state initialisation 2026-06-07 00:00:00 (stray 2020-04 rows, dropped): 371
WIND rows by combination code: CURL=132581, LOCL=69191, CRLO=12795, LCLO=7343
state initialised False for every unit at 2026-06-07 00:00:00; instructions from 2026-06-07 onward are replayed before the window opens at 2026-06-08 23:00:00
units under LOCL constraint at window start 2026-06-08 23:00:00: 0 []
units under CURL curtailment at window start: 0 []
units whose FIRST constraint instruction in BM-037 is a release (LCLO), i.e. they entered the file mid-instruction and the state machine misses that first spell: 0 []
units whose FIRST curtailment instruction is a release (CRLO): 0 []
units with no LOCL/LCLO instruction at all in BM-037: ['GU_407660']
==============================================================================
§6.3/6.4  Per-unit table and reproduction of the existing CSV
-- comparison [EffTime <= StartTime]: old rows 25, matched 25
   avail_MWh                max|new-old| = 0.462  (unit GU_401280); after rounding new to integer: 0
   dd_MWh                   max|new-old| = 0.4845  (unit GU_403760); after rounding new to integer: 0
   dd_ratio                 max|new-old| = 8.32667e-17  (unit GU_400950)
   constraint_only_ratio    max|new-old| = 9.02056e-17  (unit GU_403400)
   locl_any_ratio           max|new-old| = 8.32667e-17  (unit GU_405130)
   curl_only_ratio          max|new-old| = 9.71445e-17  (unit GU_402200)
   h_locl                   max|new-old| = 0  (unit GU_404630)
   h_curl                   max|new-old| = 0  (unit GU_404630)
   halfhours                max|new-old| = 0  (unit GU_404630)
-- comparison [EffTime <  StartTime]: old rows 25, matched 25
   avail_MWh                max|new-old| = 0.462  (unit GU_401280); after rounding new to integer: 0
   dd_MWh                   max|new-old| = 0.4845  (unit GU_403760); after rounding new to integer: 0
   dd_ratio                 max|new-old| = 8.32667e-17  (unit GU_400950)
   constraint_only_ratio    max|new-old| = 9.02056e-17  (unit GU_403400)
   locl_any_ratio           max|new-old| = 8.32667e-17  (unit GU_405130)
   curl_only_ratio          max|new-old| = 9.71445e-17  (unit GU_402200)
   h_locl                   max|new-old| = 0  (unit GU_404630)
   h_curl                   max|new-old| = 0  (unit GU_404630)
   halfhours                max|new-old| = 0  (unit GU_404630)
half-hours whose StartTime equals an instruction EffTime exactly (where the two conventions differ): 1650
max abs diff over ratio/hour columns: inclusive 9.71e-17, exclusive 9.71e-17
convention used from here on: EffTime <= StartTime
reproduction to 3 decimals on ratio and hour columns: PASS
old CSV avail_MWh/dd_MWh are whole numbers: True (old file rounded MWh to integers; ratios in the old file were computed from unrounded values, see dd_ratio diff above)
units in the raw data but absent from the old CSV: []
==============================================================================
§6.5  Stations and groups
units without a station in the map: []
   station ARDNAGAPPARY in map: False; units in map: []
   station BINBANE      in map: True; units in map: ['GU_401190', 'GU_405870', 'GU_404630']
   station CATH_FALL    in map: True; units in map: ['GU_401820', 'GU_400220', 'GU_400221']
   station CORDERRY     in map: True; units in map: ['GU_402200', 'GU_402160']
   station CUNGHILL     in map: True; units in map: ['GU_400021', 'GU_400020']
   station GARVAGH      in map: True; units in map: ['GU_403820', 'GU_400950', 'GU_400940']
   station GLENREE      in map: True; units in map: ['GU_403880', 'GU_403990', 'GU_401280']
   station LENALEA      in map: True; units in map: ['GU_405930']
   station MEENTYCAT    in map: True; units in map: ['GU_400070']
   station MOY          in map: False; units in map: []
   station MULREAVY     in map: True; units in map: ['GU_401930', 'GU_401920']
   station SLIGO        in map: False; units in map: []
   station TAWNAGHMORE  in map: True; units in map: ['GU_403750', 'GU_404550', 'GU_400780', 'GU_400781']
   station TRILLICK     in map: True; units in map: ['GU_404560', 'GU_400550']
Sorne Hill Generator Unit (GU_400550) sits at TRILLICK in the map; the WDT document lists Sorne Hill and Trillick as separate stations. Both are CG1, so nothing changes.
TIEVEBRACK (Cronalaght 2, GU_403840) is in neither CG1 nor CG3 in the Feb 2024 document.
Cathaleen's Fall is spelled CATH_FALL in the map; ARDNAGAPPARY, MOY and SLIGO have no unit in the IE map, so no measured unit can be assigned to them.
units per group label: CG3-only=10, CG1=5, Booltiagh=5, other=5
map units at CG1/CG3 stations with 0 rows in BM-101 (absent from the measurement):
   GU_401820 Acres Windfarm (CATH_FALL)
   GU_401190 Clady Generating Station (BINBANE)  [has BM-096 rows only]
   GU_403820 Derrysallagh Windfarm (GARVAGH)
   GU_400220 Erne 3 Generator Unit (CATH_FALL)
   GU_400221 Erne 4 Generator Unit (CATH_FALL)
   GU_404550 Killala Battery (TAWNAGHMORE)
   GU_400020 Kingsmountain Generator Unit (CUNGHILL)
   GU_401930 Mulreavy Windfarm (MULREAVY)
   GU_401920 Meenadreen South 2 Windfarm (MULREAVY)
   GU_400780 Tawnaghmore Peaking 1 Generator Unit (TAWNAGHMORE)
   GU_400781 Tawnaghmore Peaking 3 Generator Unit (TAWNAGHMORE)
==============================================================================
§6.6  Filter avail_MWh > 250.0 and h_locl > 0
units passing: 24 of 25; excluded: GU_407660 Crossmore Wind Farm (avail 7974.6 MWh, h_locl 0.0)
group table (constraint_only_ratio; station = Σdd_constraint_only / Σavail):
       group   level  N      min      max  max_over_min     jain     gini min_member  max_member
         CG1    unit  5 0.043148 0.098054      2.272497 0.927303 0.156817  GU_404560   GU_404630
         CG1 station  3 0.074886 0.081486      1.088142 0.998470 0.018995   TRILLICK     BINBANE
         CG3    unit 15 0.043148 0.098054      2.272497 0.950373 0.130069  GU_404560   GU_404630
         CG3 station  9 0.054518 0.089496      1.641576 0.980439 0.079760    GARVAGH TAWNAGHMORE
   Booltiagh    unit  4 0.028661 0.070243      2.450804 0.916709 0.165246  GU_403800   GU_401720
   Booltiagh station  1 0.041707 0.041707      1.000000 1.000000 0.000000  BOOLTIAGH   BOOLTIAGH
all_filtered    unit 24 0.015975 0.098054      6.137797 0.917659 0.166984  GU_403840   GU_404630
all_filtered station 14 0.015975 0.089496      5.602087 0.927053 0.147713 TIEVEBRACK TAWNAGHMORE
station-level members and ratios:
  [CG1] BINBANE: 0.081486 (n=2); LENALEA: 0.075282 (n=1); TRILLICK: 0.074886 (n=2)
  [CG3] BINBANE: 0.081486 (n=2); CORDERRY: 0.081767 (n=2); CUNGHILL: 0.071183 (n=1); GARVAGH: 0.054518 (n=2); GLENREE: 0.066407 (n=3); LENALEA: 0.075282 (n=1); MEENTYCAT: 0.061300 (n=1); TAWNAGHMORE: 0.089496 (n=1); TRILLICK: 0.074886 (n=2)
  [Booltiagh] BOOLTIAGH: 0.041707 (n=4)
  [all_filtered] BELLACORICK: 0.074234 (n=1); BINBANE: 0.081486 (n=2); BOOLTIAGH: 0.041707 (n=4); CORDERRY: 0.081767 (n=2); CUNGHILL: 0.071183 (n=1); DALTON_A1: 0.055793 (n=1); GARVAGH: 0.054518 (n=2); GLENREE: 0.066407 (n=3); LENALEA: 0.075282 (n=1); MEENTYCAT: 0.061300 (n=1); SRAHNAKILLY: 0.064229 (n=2); TAWNAGHMORE: 0.089496 (n=1); TIEVEBRACK: 0.015975 (n=1); TRILLICK: 0.074886 (n=2)
==============================================================================
§6.7  LOCL co-instruction batches (same InstrIssueTime to the second)
LOCL rows 69191, of which at CG3 stations 7443; LOCL rows with no station in the IE map (NI or unmapped units): 35886
batches (distinct InstrIssueTime): 8734; batches with >= 2 units: 6214
batches containing any CG3 unit: 2096; batches whose units are ALL at CG3 stations: 449; of those, ALL at CG1 stations: 30
all-CG3 batches with >= 2 units: 253; single-unit all-CG3 batches: 196
batches mixing CG3 and non-CG3 units: 1647
10 most frequent station compositions among all-CG3 batches:
                                   stations  batches  units_per_batch_min  units_per_batch_max  all_CG1
                                   CORDERRY      131                    1                    1    False
                           BINBANE+MULREAVY      114                    2                    2    False
                           CORDERRY+GARVAGH       84                    2                    2    False
                                   MULREAVY       30                    1                    1    False
                                    BINBANE       21                    1                    1     True
                                    GARVAGH       13                    1                    1    False
BINBANE+LENALEA+MEENTYCAT+MULREAVY+TRILLICK       12                    5                    5    False
         BINBANE+LENALEA+MEENTYCAT+TRILLICK       10                    4                    4    False
                 LENALEA+MEENTYCAT+TRILLICK        9                    3                    4    False
                MEENTYCAT+MULREAVY+TRILLICK        9                    3                    4    False
of the 1647 mixed batches, 578 include an unmapped (NI or non-CLAF) unit and 1069 mix CG3 with other mapped IE stations
for context, the 10 most frequent compositions among ALL LOCL batches (any station):
                                                          stations  batches  units_per_batch  all_cg3  all_cg1
                                                      COOMAGEARLAH      350                1    False    False
                                                           LISHEEN      319                2    False    False
  DERRYIRON+KINNEGAD+TIMAHOE+UNMAPPED:GU_407670+UNMAPPED:GU_408120      313                5    False    False
                                                            UGGOOL      251                1    False    False
                            KNOCKALOUGH+KNOCKRANNY+SALTHILL+UGGOOL      233                4    False    False
                                               LODGEWOOD+WATERFORD      222                2    False    False
                                                       SRAHNAKILLY      218                1    False    False
                                      RATHKEALE+UNMAPPED:GU_404570      216                2    False    False
KILCUMBER+UNMAPPED:GU_401690+UNMAPPED:GU_407330+UNMAPPED:GU_408060      188                4    False    False
                                                         RATHKEALE      147                1    False    False
all-CG3 batches by number of units: 1=196, 2=200, 3=25, 4=14, 5=12, 9=2
==============================================================================
§6.8  Outputs
written: /home/claude/project/out/measurement_units.csv, /home/claude/project/out/measurement_groups.csv, /home/claude/project/out/measurement_batches.csv, /home/claude/project/out/measurement_bars.png, /home/claude/project/out/measurement_reproduction_check.csv
```
