# MASTER — The price of pro-rata: constraint-group dispatch on the Irish grid

Complete specification of every calculation and simulation. Written 2026-09-09. Supersedes `prorata_project_brief.md` §5–§8 where they differ. Decisions and their sources are in `formula-decisions.md`; the model validation is in `VALIDATION_prorata_brief.md`. Anything not specified here is a decision the executing agent must record in `out/DECISIONS_LOG.md`, not make silently.

Presentation is out of scope. The product of this document is `out/RESULTS.md`, the CSVs and PNGs under `out/`, and `verify/VERIFICATION.md`.

## 0. Fixed decisions (do not reopen)

| Item | Decision |
|---|---|
| Simulated group | North-West Constraint Group 3 only ("Sligo to Flagford or Flagford 220/110 kV Transformer Flows", WDT Overview §3.3). Group 1 appears in the measurement only; its monitored element (a Letterkenny busbar section) is not in the model. |
| Main network and weather | `kit/WP2024_all-island_windin.nc` (organisers' WP2024 + 410 wind/solar records the case flags out of service) with `years/TYTFS2024_WP2024_V35_synthetic_2030_seed42_*`, all 8,760 hours. |
| Sensitivity networks | `kit/WP2033_all-island.nc` with seed 42 and seed 43 years, every 2nd hour (4,380 h), to show the forward-looking case and seed robustness. |
| Tie | Replace line `3581-89516-1` (Letterkenny–Strabane PST) by a Link `LKY-STRABANE-PST`, bus0 `3581`, bus1 `89516`, `p_nom` = the removed line's `s_nom` (93 MW in 2024, 123 MW in 2033), `p_min_pu = -1`, efficiency 1, marginal cost 0. |
| Contingency | Loss of `2522-5042-1` (Flagford–Srananagh 220 kV). |
| Monitored elements | `2521-4981-1` (Flagford–Sligo 110 kV, 121 MVA) post-contingency; `T2522-2521-25221-1-w1` and `T2522-2521-25222-2-w1` (Flagford 220/110 kV transformer 220 kV windings, 125 MVA each) post-contingency; `2521-4981-1` intact. Nothing else is enforced by the rules (see §4.6 for the post-cut check). |
| Shift-factor reference | One fixed remote conventional bus (§3.3). |
| Today's rule | Per-hour pro rata on availability inside the group. |
| Sensitivity rule | Non-priority-first (tier 1 non-priority pro rata, tier 2 priority pro rata), priority proxy from `data/eirgrid_gss1_res_units.csv`. No output-based state machine. |
| Tally, band centre, fallback | r_i = cumulative cut / cumulative availability; centre = availability-weighted group mean; widen one farm at a time. |
| Metrics | Jain (chart), Gini and worst-farm (table); dispatch-down as % of available energy and ratio to rule 1. |
| Comparison with 2026 data | Station level. |
| Units | MW, MWh, %, hours. No euro anywhere. |

## 1. Inputs

```
project/
  kit/            gridkit.py flowmath.py plotstyle.py test_kit.py (organisers' kit, unmodified)
                  WP2024_all-island.nc WP2033_all-island.nc (organisers')
                  WP2024_all-island_windin.nc (ours; see VALIDATION §5 and data/README in synth_out_extra)
  years/          TYTFS2024_WP2024_V35_synthetic_2030_seed42_{p_max_pu,loads_p_set,fleet,sites,anchors}.csv
                  TYTFS2024_WP2033_V35_synthetic_2030_seed42_{p_max_pu,loads_p_set}.csv
                  TYTFS2024_WP2033_V35_synthetic_2030_seed43_{...}.csv
  data/           BM-101_nw_units.csv (AvgOutturnAvail, MW, 30-min, 27 NW units, 2026-06-08..09-05)
                  BM-096_nw_units.csv (DispatchQuantity, MWh per 30 min)
                  BM-037_dispatch_instructions_2026-06-07_to_09-05.csv (all instructions, all units)
                  nw_unit_dispatchdown_2026-06-08_to_09-05.csv (earlier computation, to be reproduced)
                  semo_unit_map_IE.csv (GU code -> name, station), locl_instructions_per_unit.csv
                  eirgrid_gss1_res_units.csv (unit, node, gen_type, mec_mw, controllability, priority)
                  ctrl26.txt (EirGrid controllability status, June 2026)
                  eirgrid-wdt-constraint-group-overview-2024.txt (WDT document text; group tables §3.1, §3.3; App. 1 pro-rata; App. 2 shift factor)
                  nayer-et-al-2026-arxiv2608.24464.txt
                  q5_shift_factors_WP2033.log (earlier shift factors on the tie; reference only)
```

Python: pandas, numpy, scipy, pypsa 1.3, highspy, matplotlib. Use `kit/flowmath.py` for PTDF; do not reimplement it.

## 2. Group definition

**Stations (WDT §3.3, intact network):** Ardnagappary, Binbane, Cathaleen's Fall, Corderry, Cunghill, Garvagh, Glenree, Lenalea, Meentycat, Moy, Mulreavy, Sligo, Sorne Hill, Tawnaghmore, Trillick.

**Model buses (WP2024 wind-in, matched on `buses.psse_name`):** ARDNAGAPPARY 1571, BINBANE 1341, CATH_FALL 1701 and CATH FALL 17010 (both count as Cathaleen's Fall), CORDERRY 1631, CUNGHILL 1931, GARVAGH 2671, GLENREE 4371, LENALEA 3591, MEENTYCAT 4071, MOY 4041, MULREAVY 4091, SLIGO 4981, SORNE HILL 4991, TAWNAGHMORE 5241, TRILLICK 5361. For WP2033 re-match by `psse_name`; report any station whose bus number differs.

**Cuttable set G:** every generator with carrier `wind` or `solar` at those buses, minus units classed *uncontrolled*. Classification (§2.1). Uncontrolled units keep producing at availability and appear in flows but receive no cut and are excluded from the tally and the metrics. Report the MW in G and the MW excluded.

**Nodes for effectiveness ordering:** one node per bus. Cathaleen's Fall's two buses are two nodes (different shift factors are possible).

### 2.1 Priority / controllability classification

Match each model generator at a CG3 bus to `data/eirgrid_gss1_res_units.csv` rows whose `node` equals the station name (case-insensitive; "Cathaleen's Fall" covers both buses) and whose `mec_mw` equals the generator's `p_nom` within ±0.05 MW. If more than one row matches, take the one whose name best matches the generator's `psse_bus_name`; if none matches, class = `priority` (the conservative default: pre-2019 units are the majority in Donegal) and flag `unmatched`. From the matched row: `priority` in {"wind priority","solar priority"} → class P; "not priority" → class N; "uncontrolled" → class U (excluded from G). Write `out/group_units.csv` with columns generator, bus, station, carrier, p_nom, class, matched_name, matched_mec, match_status. Report the match rate; it must be stated in RESULTS.

## 3. Network preparation and baseline dispatch (per case)

Cases: `WP2024s42` (main), `WP2033s42`, `WP2033s43`.

### 3.1 Prepare
1. Load the network. Apply the tie replacement (§0).
2. Set snapshots to the year's index (all 8,760 for WP2024s42; every 2nd hour for the WP2033 cases).
3. `generators_t.p_max_pu` from the year file for every generator that has a column. For a wind/solar generator without a column, borrow the profile of the nearest wind generator (same carrier) that has one — by bus first, then by great-circle distance using `gridkit.placed_buses` coordinates — and log it in `out/<case>_profile_borrowing.csv`. A thermal generator without a column keeps `p_max_pu = 1`.
4. `loads_t.p_set` from the year file (all loads must match; assert).
5. For every generator with static `p_min_pu > 0` that has a year column, set `generators_t.p_min_pu[t] = min(p_min_pu, p_max_pu[t])`.
6. Renewable bids: for wind and solar, `marginal_cost = -1 - 1e-4 * i / N` in sorted-name order (removes ties; matches `problem_3_1/common.py`).
7. Multiply every line and transformer `s_nom` by 100 (unconstrained dispatch). Keep the original ratings in a Series `rating`.

### 3.2 Solve
`n.optimize(chunk, solver_name="highs")` in 168-hour chunks. Assert every chunk is optimal. Save:
- `out/<case>_baseline_p.parquet` — generator output p0_i,h (MW) for all generators;
- `out/<case>_avail.parquet` — availability a_i,h = p_max_pu × p_nom for wind/solar in G;
- `out/<case>_flows.parquet` — `lines_t.p0` and `transformers_t.p0` (MW) for all branches, and link flows.

Sanity checks to record: total wind energy / total available wind energy for the island (surplus share); hours with load shedding > 0 (should be ~0); the tie link's share of hours at its cap.

### 3.3 PTDF, LODF, shift factors
- `br = flowmath.branches(n)`, `P = flowmath.ptdf(n, br)` on the prepared network (the tie is a Link, so it is absent from the DC matrix; that is intended).
- Reference bus: the bus of the largest-`p_nom` generator with carrier `gas` in the network (expected MONEYPOINT or AGHADA area; record the name). Check |P[e, ref]| < 0.02 for every monitored element e; if not, pick the next-largest gas bus and record why.
- LODF for contingency k = `2522-5042-1`: `LODF[e,k] = (P[e,b0k] − P[e,b1k]) / (1 − (P[k,b0k] − P[k,b1k]))` with b0k, b1k the from/to buses of k. Assert |1 − (P[k,b0k] − P[k,b1k])| > 1e-6.
- Verify LODF against PyPSA: `pypsa.contingency.calculate_BODF` on the same sub-network must agree with LODF[e,k] to 1e-6 for the three monitored elements. Record the values.
- Post-contingency PTDF row for monitored e: `Pk[e,:] = P[e,:] + LODF[e,k] · P[k,:]`. For the intact monitored row use `P[e,:]`.
- Raw shift factor of generator i on monitored element m (post-contingency or intact as appropriate): `SF_raw[m,i] = Pk[m, bus(i)] − Pk[m, ref]`.
- Save `out/<case>_shift_factors.csv`: generator, bus, station, class, p_nom, SF_raw on each of the four monitored rows. Also report the WDT-style node table: one row per node, SF on the Flagford–Sligo N-1 row, sorted descending, and mark the "significant step change" (largest ratio between consecutive sorted values) — this reproduces App. 2 and is a check that the modelled group matches the document's.

### 3.4 Overload series
For each hour h and monitored row m: flow `F_m,h` = `f_e,h + LODF[e,k] · f_k,h` (post-contingency rows) or `f_e,h` (intact row), signed. Overload `O_m,h = max(0, |F_m,h| − rating_e)`. Effective shift factor with the sign that makes a cut helpful: `SF[m,i,h] = sign(F_m,h) · SF_raw[m,i]`. A cut c_i (MW removed at bus(i), added at ref) changes `|F_m|` by `−SF[m,i,h] · c_i`. Only farms with `SF[m,i,h] > 0` can relieve m.

Save `out/<case>_overloads.csv` (hour, each F_m, each O_m) and report: hours with any overload, hours by element, total overload MWh by element, the maximum overload, and the share of overload hours in which more than one row is over.

## 4. Rules

All rules run per hour on the same inputs: `p0_i,h` (baseline output, the farm's output absent the constraint), `a_i,h` (availability), `SF[m,i,h]`, `O_m,h`. A cut vector `c` (MW, per generator in G) is feasible when `Σ_i SF[m,i,h] · c_i ≥ O_m,h` for every m, with `0 ≤ c_i ≤ p0_i,h`. If a rule cannot reach feasibility with everything in G cut to zero, record the residual overload for that hour in `out/<case>_<rule>_residual.csv`; the hour still counts, with c = p0 (everything cut). Hours with no overload: c = 0.

Cuts are balanced at the reference bus (the shift-factor convention); nothing else in the dispatch changes. This is stated in RESULTS as an assumption.

### 4.1 Rule 1 — pro rata (today, with rebalancing)
Every farm in G cut to the same fraction of availability: `c_i = φ · a_i`, capped at `p0_i`. φ is the smallest value in [0, 1] such that all constraints hold, found by bisection on φ (the constraint set is monotone in φ because all SF > 0 terms increase with φ; farms with SF ≤ 0 on a row contribute nothing to that row's relief and are cut anyway — that is what pro rata does, and it is the point). Tolerance 1e-6 MW.

### 4.2 Rule 2 — effectiveness order
Nodes ordered by `SF[m*,node,h]` descending where m* is the row with the largest residual overload. Loop: pick m*; take the not-yet-fully-cut node with the highest SF on m* among those with SF > 0; cut it — fully, or by the amount that clears m*, whichever is smaller — splitting the node's cut across its farms pro rata on availability (cap at p0); recompute all residuals; repeat until no residual. If no remaining node has SF > 0 on m*, record residual and stop.

### 4.3 Rule 3 — nodal optimum
`min Σ_i c_i` subject to `Σ_i SF[m,i,h] c_i ≥ O_m,h` ∀m, `0 ≤ c_i ≤ p0_i,h`. `scipy.optimize.linprog(method="highs")`. Infeasible → same residual treatment as above (cut everything). Record solver status per hour.

### 4.4 Rule 4 — the band
State: `cum_cut_i`, `cum_avail_i` over all hours so far (availability accumulates in every hour, cut only in overload hours); `r_i = cum_cut_i / cum_avail_i` (0 when cum_avail = 0). Group centre `r̄ = Σ cum_cut / Σ cum_avail` over G. Eligible `E = {i : r_i ≤ r̄ + b}`, b in percentage points. Run rule 2 restricted to E. If a residual remains after E is exhausted, add the farm outside E with the lowest r_i and continue; repeat. Update state after the hour. Sweep `b ∈ {0, 1, 2, 3, 5, 10, ∞}` (∞ = rule 2 exactly; assert identical totals). Hours in chronological order.

### 4.5 Sensitivity — non-priority first (rule 1N)
Tier 1 = class N farms, rule-1 pro rata among them (φ_N by bisection). If tier 1 fully cut (φ_N = 1) leaves a residual, tier 2 = class P farms, rule-1 pro rata among them. Report as an extra row in every table, with tallies by class. Label everywhere "SEM-24-044 stated intent, not live".

### 4.6 Post-cut check (every rule, every hour with a cut)
Recompute the flow change on every branch in the North-West from the cut: `Δf_e = −Σ_i (P[e,bus(i)] − P[e,ref]) c_i`. Count intact branches (all NW branches, list from `psse_name` containing any CG3 station name or FLAGFORD, SRANANAGH, LETTERKENNY, CLOGHER, DRUMKEEN, CROAGHONAGH, TIEVEBRACK) whose |f + Δf| exceeds rating where |f| did not. Report the count of such hour-branch pairs per rule in RESULTS. Do not enforce them.

## 5. Metrics (per case, per rule, per band)

Per farm at year end: `r_i` (as in 4.4), also `cum_cut_i` (MWh), `cum_avail_i` (MWh), hours cut.

Per station: aggregate cut and availability over the station's farms in G, `r_s = Σcut/Σavail`.

Group:
- `D = Σ_G cum_cut / Σ_G cum_avail` (%) — dispatch-down as share of available energy (constraint only; the model has no curtailment).
- `D_ratio = D_rule / D_rule1`.
- `PoF_eff = (D_rule − D_rule2) / D_rule2`; `PoF_nodal = (D_rule − D_rule3) / D_rule3`.
- Jain on farm r_i: `J = (Σ r_i)² / (N · Σ r_i²)`, N = |G|. Also Jain on station r_s.
- Gini on farm r_i, ascending sort: `G = Σ_{i=1..N} (2i − N − 1) r_i / (N · Σ r_i)`; unweighted, no small-sample correction (state it).
- Worst farm: `max r_i / r̄`; and `max r_i / min r_i` over farms with cum_avail > 0.
- Farms with r_i = 0 stay in N if they are in G.

Output tables: `out/<case>_summary.csv` (one row per rule/band: D, D_ratio, PoF_eff, PoF_nodal, Jain_farm, Jain_station, Gini, worst_over_mean, max_over_min, residual hours, post-cut violations), `out/<case>_farm_r.csv` (rule × farm), `out/<case>_station_r.csv`.

Charts (matplotlib, `kit/plotstyle.py` if it works, else default): `out/<case>_frontier_jain.png` — x = D (%), y = Jain; points for rule 1, rule 2, rule 3, rule 1N, and the band sweep joined by a line with b labels. `out/<case>_frontier_gini.png` same with Gini. `out/WP2024s42_station_bars.png` — r_s per station for rules 1, 2, 3 and b = 3.

## 6. Measurement (2026 data)

Reproduce and extend `nw_unit_dispatchdown_2026-06-08_to_09-05.csv` from the raw files:
1. Join BM-101 and BM-096 on (ResourceName, StartTime). Per half-hour: `avail_MWh = 0.5 × AvgOutturnAvail`, `dd_MWh = max(0, avail_MWh − DispatchQuantity)`.
2. State machine from BM-037 per unit, instructions sorted by EffTime: LOCL sets `constraint = True`, LCLO clears it; CURL sets `curtail = True`, CRLO clears it. A half-hour is "under constraint" if the state at its StartTime is True. Same for curtailment. Report how the state is initialised (False at 2026-06-07 00:00) and how many units start the window mid-instruction.
3. Per unit: `avail`, `dd`, `dd_ratio`, `constraint_only_ratio` (dd in half-hours under constraint and not under curtailment ÷ avail over all half-hours), `locl_any_ratio`, `h_locl`, `h_curl`.
4. Reproduce the existing CSV to 3 decimals; report any difference.
5. Map units to stations via `semo_unit_map_IE.csv`. Assign groups by station: CG1 stations {ARDNAGAPPARY, BINBANE, LENALEA, TRILLICK} (Sorne Hill's unit sits at TRILLICK in the map — say so), CG3 = CG1 ∪ {CATHALEENS FALL, CORDERRY, CUNGHILL, GARVAGH, GLENREE, MEENTYCAT, MOY, MULREAVY, SLIGO, TAWNAGHMORE}. Tievebrack is in neither (state it).
6. Filter: avail > 250 MWh and h_locl > 0. Per group: N, min, max, max/min, Jain, Gini on `constraint_only_ratio`, at unit level and at station level (station = Σdd/Σavail). Also the four Booltiagh units as the same-shift-factor example.
7. Co-instruction check: among BM-037 LOCL rows, count batches (same InstrIssueTime to the second) whose units are all at CG3 stations; report the 10 most frequent station compositions. This is the evidence that the group fires.
8. Outputs: `out/measurement_units.csv`, `out/measurement_groups.csv`, `out/measurement_batches.csv`, `out/measurement_bars.png` (constraint-only ratio per unit, coloured by group).

Caveats to print with the numbers: 90 days, one summer; group membership inferred from station names and the Feb 2024 document; the LOCL/CURL state machine cannot tell which group fired; constraint-only is a lower bound; rebalancing (live since 26 Nov 2025) is in force for the whole window.

## 7. Comparison, simulation vs measurement (station level)

Table: station; measured constraint-only ratio (2026, 3 months); simulated r_s under rule 1 (WP2024s42, full year); rank in each; simulated r_s under rules 2, 3 and b = 3. Spearman rank correlation between measured and rule-1 simulated across stations present in both. Jain and Gini of both vectors. State: different fleets (2024 case vs 2026 units), different weather (synthetic vs real), different horizon (year vs summer), and that the model has one contingency where the tool has many; the comparison is ordinal.

## 8. Robustness

Table across `WP2024s42`, `WP2033s42`, `WP2033s43`: overload hours, D under each rule, D_ratio, Jain under each rule and band, and the rank order of stations under rule 1. Say which statements hold in all three. Statements that change sign across the WP2033 seeds are not results.

## 9. RESULTS.md

Sections: 1 what was run (cases, hours, tie, contingency, reference bus, match rates, borrowed profiles); 2 overload statistics; 3 shift-factor table with the step change; 4 rule results table per case; 5 frontier (chart + table); 6 sensitivity 1N; 7 measurement; 8 comparison; 9 robustness; 10 checks performed (§3.3 LODF check, rule ordering D_3 ≤ D_2 ≤ D_1 per hour, band ∞ = rule 2, feasibility residuals, post-cut violations, measurement reproduction); 11 assumptions and caveats (one line each: DC, synthetic weather, one contingency, cuts balanced at the reference bus, wind-in records, tie as link, priority proxy, uncontrolled exclusion, no curtailment, no unit commitment); 12 every number cited with the file it comes from.

Every number in RESULTS.md must be traceable to a CSV in `out/`. No number from memory.

## 10. Verification (independent, by a separate agent, written to `verify/VERIFICATION.md`)

1. Re-derive LODF for the three monitored rows from `P` by hand and compare with `pypsa.contingency.calculate_BODF`.
2. Load `out/WP2024s42_overloads.csv` and `..._flows.parquet`; recompute F and O for 50 random hours from raw flows; compare.
3. For each rule and 200 random overload hours: recompute Σ SF·c from the saved cuts and confirm ≥ O − 1e-4 for every row, and c ≤ p0.
4. Confirm per hour: Σc(rule 3) ≤ Σc(rule 2) ≤ Σc(rule 1) (within 1e-6), and band ∞ equals rule 2.
5. Recompute Jain, Gini, D and ratios from `farm_r.csv` independently; compare with `summary.csv`.
6. Measurement: recompute five units' constraint-only ratios from the raw BM files with independent code; compare with `measurement_units.csv` and with the original `nw_unit_dispatchdown` CSV.
7. Quote check: every quotation in RESULTS.md and MASTER.md attributed to the WDT document must be found verbatim in `data/eirgrid-wdt-constraint-group-overview-2024.txt`; every group station list must match §3.1/§3.3 of that text.
8. Priority classification: sample 15 units from `group_units.csv`, check against `eirgrid_gss1_res_units.csv` by hand.
9. Sanity: total cut MWh under rule 1 versus total overload MWh (the ratio should be of order 1/mean SF); tie link at cap share; load shedding hours.
10. List every discrepancy with its size; state which numbers in RESULTS.md are affected.

## 11. Execution order and expected runtimes

1. Measurement (§6) — independent, ~30 min.
2. Prepare + baseline for WP2024s42 (§3.1–3.2) — ~25 min solver; WP2033s42 and s43 at every 2nd hour — ~45 min each; run in background.
3. §3.3–3.4 on each case — minutes.
4. Rules (§4) — rule 1/2/4 seconds; rule 3 one LP per overload hour, ~1,800 hours → minutes.
5. Metrics, charts, comparison, robustness (§5, §7, §8).
6. RESULTS.md, then verification (§10).

## 12. Known limits to state, not fix

Letterkenny busbar sections absent (Group 1 not simulable). Voltage-driven groups invisible to a DC model. One contingency where the tool has many outage variants. Synthetic weather (all energy figures are ratios). The 2024 wind-in fleet is the TYTFS 2024 register, not the 2026 unit list. Priority status is EirGrid's own COD-based assumption, not the official list. Rebalancing is discretionary in reality; the model applies it every hour.
