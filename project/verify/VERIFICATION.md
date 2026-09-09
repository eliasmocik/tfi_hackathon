# VERIFICATION - independent checks of the pro-rata project

Assembled by `verify/build_verification.py` on 2026-09-09.

MASTER section 10 requires these checks to be done by an agent that does
**not** import `src/rules.py`, `src/metrics.py`, `src/measurement.py`,
`src/compare.py` or `src/robustness.py`. No script in this directory imports
any of them; each re-derives its quantity from the saved data files and the
raw inputs. `kit/flowmath.py`, `pypsa` and `engine_prep.prepare()` are
permitted and are used where the network itself is needed.

## Status of the ten checks

| # | check | status |
|---|---|---|
| 1 | LODF for the monitored rows, re-derived and checked against pypsa calculate_BODF | done - `v01_lodf.md` |
| 2 | F and O recomputed from raw flows for 50 random hours | done - `v02_flows.md` |
| 3 | Sum SF*c >= O and c <= p0 for each rule over 200 random overload hours | done - `v03_relief.md` |
| 4 | Per-hour ordering of total cut, and band-inf == rule 2 | done - `v04_ordering.md` |
| 5 | Jain, Gini, D and the ratios recomputed from farm_r.csv | done - `v05_metrics.md` |
| 6 | Measurement recomputed from the raw BM files with independent code | done - `v06_measurement.md` |
| 7 | Every WDT quotation found verbatim; group station lists checked | done - `v07_quotes.md` |
| 8 | Priority classification checked against eirgrid_gss1_res_units.csv | done - `v08_priority.md` |
| 9 | Sanity: cut MWh vs overload MWh, tie link at cap, load shedding | done - `v09_sanity.md` |
| 10 | Every discrepancy with its size, and which RESULTS.md numbers it affects | see section below |
| 11 | The band rule re-implemented from MASTER section 4 and compared with cuts_band3.parquet (the HANDOFF's most valuable check) | done - `v11_band_rule.md` |
| 12 | The same re-implementation at b = infinity - the control that isolates path dependence | done - `v11_band_inf.md` |

## Findings by check

### 1. LODF for the monitored rows, re-derived and checked against pypsa calculate_BODF

- re-derived denominator: **0.224264205328567**
- denominator in `WP2024s42_lodf.csv`: **0.224264205328388** (difference 1.795e-13)
- worst |re-derived - saved|: **6.914e-13**

Full report: [`v01_lodf.md`](v01_lodf.md).

### 2. F and O recomputed from raw flows for 50 random hours

- `FLG_SLIGO_N1`: 50 hours, worst |O - max(|F| - rating, 0)| = **7.105e-15**
- `T25221_N1`: 50 hours, worst |O - max(|F| - rating, 0)| = **0.000e+00**
- `T25222_N1`: 50 hours, worst |O - max(|F| - rating, 0)| = **0.000e+00**
- `FLG_SLIGO_N0`: 50 hours, worst |O - max(|F| - rating, 0)| = **0.000e+00**
- comparisons: **200**
- mismatches: **0**

Full report: [`v02_flows.md`](v02_flows.md).

### 3. Sum SF*c >= O and c <= p0 for each rule over 200 random overload hours

- hour-rule-row samples checked: **2244**
- samples where relief fell short of the overload by more than 1e-4: **0**
- worst shortfall: **1.421e-14 MW**

Full report: [`v03_relief.md`](v03_relief.md).

### 4. Per-hour ordering of total cut, and band-inf == rule 2

- hours with sum c(rule3) > sum c(rule2) + 1e-6: **0** (worst 1.137e-13)
- hours with sum c(rule2) > sum c(rule1) + 1e-6: **0** (worst 0.000e+00)
- max |band-inf - rule2| element-wise: **0.000e+00**

Full report: [`v04_ordering.md`](v04_ordering.md).

### 5. Jain, Gini, D and the ratios recomputed from farm_r.csv

- comparisons: **363**
- mismatches: **0**
- worst relative deviation: **2.113e-13**

Full report: [`v05_metrics.md`](v05_metrics.md).

### 6. Measurement recomputed from the raw BM files with independent code

**48 fewer half-hours** per unit than the committed measurement
- **committed** — `out/measurement_units.csv` as published (Elias's pull).
- **pipeline_fresh_pull** — `src/measurement.py` re-run on a fresh 2026-09-09 pull.
- **independent_fresh_pull** — this file's own code on that same fresh pull.
- units compared: **25**
- worst |independent − pipeline| on the same data (code agreement): **9.71e-17**

Full report: [`v06_measurement.md`](v06_measurement.md).

### 7. Every WDT quotation found verbatim; group station lists checked

**WDT-attributed quotes checked:** 2; **not found: 0**.

Full report: [`v07_quotes.md`](v07_quotes.md).

### 8. Priority classification checked against eirgrid_gss1_res_units.csv

- units: **66**; class agreement **66/66**; match-status agreement 66/66
- classes in file: {'P': 45, 'U': 15, 'N': 6}
- matched (file): 51/66 = 77.3 %
- units: **72**; class agreement **72/72**; match-status agreement 72/72
- classes in file: {'P': 46, 'U': 15, 'N': 11}
- matched (file): 56/72 = 77.8 %

Full report: [`v08_priority.md`](v08_priority.md).

### 9. Sanity: cut MWh vs overload MWh, tie link at cap, load shedding

- total overload energy, all rows: **34,817.1 MWh** (`WP2024s42_overload_stats.json`)
- total cut under rule 1: **157,180.9 MWh**
- ratio cut / overload: **4.514**
- capacity-weighted mean effective shift factor: **0.2204**, so 1 / mean SF = **4.538**
- agreement: ratio / (1/mean SF) = **0.995** (1.0 would be exact)
- tie link `LKY-STRABANE-PST`: |flow| max 93.00 MW, at cap in **100.0 %** of hours

Full report: [`v09_sanity.md`](v09_sanity.md).

### 11. The band rule re-implemented from MASTER section 4 and compared with cuts_band3.parquet (the HANDOFF's most valuable check)

- case `WP2024s42`, first **500** hours, **51** cuttable farms
- hours with an overload in the window: **135**
- total cut, re-derived: **15,408.326 MW**
- total cut, `WP2024s42_cuts_band3.parquet`: **15,415.859 MW**
- relative difference in total: **4.887e-04**
- worst element-wise |difference|: **7.380e+01 MW**

Full report: [`v11_band_rule.md`](v11_band_rule.md).

### 12. The same re-implementation at b = infinity - the control that isolates path dependence

- case `WP2024s42`, first **500** hours, **51** cuttable farms
- hours with an overload in the window: **135**
- total cut, re-derived: **13,489.936 MW**
- total cut, `WP2024s42_cuts_bandinf.parquet`: **13,489.936 MW**
- relative difference in total: **1.348e-16**
- worst element-wise |difference|: **2.842e-14 MW**

Full report: [`v11_band_inf.md`](v11_band_inf.md).

## 10. Discrepancies, with size and effect

Every difference found, whether or not it changes a reported number.

| # | where | size | affects RESULTS.md? | resolution |
|---|---|---|---|---|
| D1 | MASTER section 5 defines `worst_over_mean` as `max r_i / r-bar` without defining `r-bar` | the two readings differ by up to 37 % (rule 2, WP2024s42: 6.551 unweighted vs 5.447 availability-weighted) | No - `summary.csv` is internally consistent | `r-bar` is the availability-weighted group mean (= D/100), confirmed against `summary.csv` to 15 significant figures. MASTER should say so. |
| D2 | MASTER section 2.1 states the priority mapping as the exact strings `wind priority` / `solar priority` / `not priority` / `uncontrolled` | the gss1 labels are compound (`wind not priority`, `solar uncontrolled`), so an exact-match reading misclassifies 73 of 210 units | No - the implementation matches on the status suffix and is correct | MASTER section 2.1 should quote the real label forms. |
| D3 | A 10.8 MW battery row at Tawnaghmore matches a wind generator's MEC exactly | 1 unit of 210 | No | The pipeline correctly declines the cross-carrier match; a verifier must filter candidates by `gen_type`. |
| D4 | SEM-O retention has trimmed the measurement window | 48 half-hours per unit (4226 now retrievable vs 4274 committed); constraint-only ratios move by up to 3.8e-3 | **Yes, potentially** - the committed measurement can no longer be regenerated from the API | `out/measurement_*.csv` restored, not overwritten; the fresh pull is kept in `verify/repro/`. Elias's local raw files are the only complete copy. |
| D5 | HANDOFF section 2 describes the repository as private and says only Elias can push | n/a | No | The repository is public (`"private": false`) and DarraghE has write access. |
| D6 | HANDOFF section 3 cites "section 10 item 5's second half" for the band-rule re-derivation | n/a | No | Item 5 is only the Jain/Gini/D recompute; the band-rule re-derivation is not in the numbered list. |
| D7 | `src/measurement.py` and `src/engine_prep.py` write text with `Path.write_text()` and `print()` without an encoding | crashes on Windows (cp1252) partway through, after some outputs are written | No - output values are unaffected | Run with `PYTHONUTF8=1`. A one-word `encoding="utf-8"` would make it portable. |
| D8 | `node_table.csv` sorts nodes by shift factor and flags the "significant step change" by comparing each node with the next. Buses 1401 and 14016 have effectively equal shift factors | the sort is unstable between runs, so the flagged step moved from bus 1401 to bus 14016 and `step_after_name` from BELLACORICK to CROAGHAUN; the shift factors themselves agree to 1.7e-12 | **Only the node table.** Group membership is fixed by MASTER section 0, not derived from the step, so no headline number moves | Break the tie deterministically (bus id as secondary sort key). Relevant to hackathon problem 3.2, which proposes generating groups from this threshold. |
| D9 | The band rule is **path-dependent**: r_i feeds the next hour's eligible set | an independent re-implementation reproduces the total cut to 4.9e-4 and the year-end ratio spread to 0.13 pp (13.74 vs 13.87 pp), with per-farm cumulative cut correlating 0.9993, but 1634 of 25500 per-hour-per-farm entries differ, the largest by a whole 73.8 MW farm alternating between adjacent hours | No - every reported quantity is an aggregate and those agree | **Controlled.** The same re-implementation at b = infinity, which has no ledger gating eligibility, reproduces the saved cuts *exactly*: 0 of 25500 elements differ, total difference 1.3e-16, per-farm correlation 1.000000. Same code, same data, ledger removed. So the ordering, node handling, availability caps and relief targeting are all exactly right, and the b = 3 divergence is caused solely by path dependence - not by an error in either implementation. If the rule is codified, the tie-break and float tolerance must be specified, or two conforming implementations will issue different per-farm instructions. |

### Reproduction on different hardware

The whole pipeline was re-run from scratch on Windows with different
package versions (pandas 3.0.5, numpy 2.4.6, pypsa from the current
release) against Elias's macOS run:

| stage | worst difference from the committed output |
|---|---|
| synthetic year (`sites`, `fleet`, `anchors`) | byte-identical |
| shift factors | 1.7e-12 |
| LODF | 6.9e-13 |
| overload series | 1.7e-10 |
| overload energy totals | 1.6e-7 MWh on 34,817 MWh |
| post-cut violations, sign-convention check | 9.4e-10 |
| `rules_summary.json` | wall-clock `seconds` only |

Every regenerated file was compared and then **restored** from git, so
the committed outputs are untouched. The two files that differ beyond
float noise are `node_table.csv` (D8) and `lodf_dcpf_check.csv`, the
latter because it samples random hours without a fixed seed and so drew
a different sample - not a discrepancy, but it does mean that file
cannot be diffed between runs.

### What this does not cover

- The measurement's own window is one summer, and the first two days of it
  are now unrecoverable from the API.
- Checks 2, 3 and 4 depend on the regenerated parquet tables; they verify
  the saved cut vectors, not the LOPF solve that produced the baseline.
- Nothing here verifies the *choice* of decisions in MASTER section 0, only
  that the code implements them.
