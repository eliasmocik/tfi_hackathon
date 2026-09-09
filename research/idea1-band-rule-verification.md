# Idea 1, verified: the cost of pro-rata and the "equal over the year, effective in the hour" rule

Consolidated 2026-09-08. Detail and quotes: `verification-regulatory.md`, `verification-literature.md`,
`hackathon-paper-ideas.md`. Every claim below carries a status: VERIFIED (read in the primary source),
MEASURED (computed here from public data), PARTLY, UNVERIFIED, or WRONG (an earlier claim that failed).

## 1. Claims and their status

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | EirGrid applies constraint to a predefined group with a single MW cut, split pro-rata | VERIFIED | WDT Overview App. 1 (p.66): setpoint = output − (group cut) × (output / Σ output) |
| 2 | Pro-rata is on **actual output**, and deepening a constraint ignores changing availability | VERIFIED | App. 1 p.67: "will always be pro-rata based on the wind/solar farm actual output and does not consider the changing availability". EirGrid's own example ends with farms at 75 / 37.5 / 62.5 / 66.7 % constrained |
| 3 | Group membership is by shift factor with a per-contingency threshold at "a significant step change" | VERIFIED | App. 2 p.72; threshold rationale explicitly cites SEM-11-062 efficiency |
| 4 | Within the hour, shift factors are computed once offline and then discarded at the split step | VERIFIED | App. 1 formula contains no effectiveness term |
| 5 | Non-priority farms are cut before priority farms for constraints | **WRONG (not live)** | MPID 320: "continue the pro-rata constraint of all controllable, non-dispatchable renewable generators (with or without priority dispatch)". NPD-first is stated intent (SEM-24-044) stalled since 2024; RA decision pending; CJEU C-36/25 open. `problem_3_1/q6_priority.py` models a rule that does not exist yet |
| 6 | Constrained wind receives no compensation | **WRONG for firm units** | SEM-22-009: firm units settled at deemed dec price 0 up to FAQ, i.e. keep day-ahead revenue; non-firm get nothing (Art. 13(7) exception). Constrained wind/solar provision 2025/26: €34.92m |
| 7 | Fairness is EirGrid's stated reason for pro-rata | VERIFIED | ARCC 2025 p.18: "Controllability enables fairness of dispatch-down … on a pro-rata basis at the time of application"; SEM-13-010 p.26 "equal burden sharing" |
| 8 | No codified rule requires equitable sharing of constraint | VERIFIED | Only non-discrimination duties (Reg. 2019/943 Art. 12(1), 13(1); ERA 1999 s.9(4)(a); SEM Act 2007 s.9) |
| 9 | EU law lets non-firm producers be curtailed without compensation | VERIFIED | Art. 13(7) "except in the case of producers that have accepted a connection agreement under which there is no guarantee of firm delivery" |
| 10 | EU law requires RES to be redispatched down only when necessary and by non-discriminatory criteria | VERIFIED | Art. 13(1), 13(5)(b), 13(6)(a) |
| 11 | The band rule is not published anywhere | VERIFIED (absence after 10+ searches) | Closest: Sweeney 2026 (demand, stochastic deficit), Quessongo et al. 2026 (distribution, day-ahead cap on cumulative ratio), Andoni et al. 2017 (rotation), Japan 輪番 rotation |
| 12 | The deficit-round-robin analogy is new | **WRONG** | Sweeney 2026 already cites WFQ/DRR; cite him |
| 13 | Australia dispatches by effectiveness × price with no compensation | VERIFIED | AEMO Constraint Formulation Guidelines; AEMC "no right to be dispatched" |
| 14 | Germany selects by sensitivity and cost with minimum factors 10/5, and compensates | VERIFIED | BNetzA 30 Nov 2020; Ofgem case study; EnWG §13a |
| 15 | Japan rotates curtailment for fairness and audits it yearly | PARTLY | Kyushu FAQ "輪番"; OCCTO "fair manner throughout the year"; METI guideline verbatim not read |
| 16 | The "equal" rule produces unequal outcomes in practice | MEASURED | Section 3 below |
| 17 | The WDT could hold a running tally per farm | UNVERIFIED | Instructions are time-stamped with reason codes (DD guide); no public spec on internal state. Rebalancing (live 26 Nov 2025) already re-pro-rates on availability, so per-farm state is at least partly used |
| 18 | NW constraint is the worst on the island | VERIFIED | ARCC 2025 Table 4: NW controllable wind 19.6 % dispatch-down, 14.7 % constraint (2024: 24.5 / 20.3) |

## 2. Data located (all in this repo unless stated)

| Need | Source | Status |
|---|---|---|
| Network, ratings, reactances, PTDF/LODF, LOPF | participant kit (`participant-kit/`), `flowmath.py`, `gridkit.py` | have, 22 self-checks pass |
| Full-year profiles (synthetic, seed = weather year) | `data/synth_out/` (8760 h, WP2033), generator `kit_build/synthetic.py` | have |
| Real-weather country profiles, 3 climate years, 2025 fleet | `data/entsoe_lmp_2022/PEMMDB23_IE00_aggregated.xlsx` | have |
| ERA5 per-site profiles | `kit_build/profiles.py fetch --year 2023` (Open-Meteo, reachable) | available, not fetched |
| Constraint-group membership incl. outage variants | `Wind-Dispatch-Tool-Constraint-Group-Overview_1.pdf` (text extracted this session) | have; needs typing into a table |
| Pro-rata formula, release rule, frequency-response adjustment | same PDF, App. 1 | have |
| Empirical group firing (which units cut together, how often) | `data/BM-037_*.csv`, `data/empirical_constraint_groups_top20.csv` | have, 3 months |
| Per-unit availability and dispatch quantity, 30 NW units, 90 days | `data/semo_nw_units/BM-101_nw_units.csv`, `BM-096_nw_units.csv` (puller: `pull.py`) | have. **Use BM-096, not BM-086**: "MeteredMW" is MWh per half-hour net of own consumption; DispatchQuantity = 0.5 × availability in unconstrained hours |
| Per-unit constraint ratio, 3 months | `data/semo_nw_units/nw_unit_dispatchdown_2026-06-08_to_09-05.csv` | computed |
| Unit code → name, station | `data/semo_unit_map_IE.csv` (233 IE units); NI units unmapped | have |
| Priority status per unit | `data/eirgrid_gss1_res_units.csv` (EirGrid's own assumption: COD < 4 Jul 2019); official NPD list not public | proxy only |
| Firm / non-firm per unit | Firm Access 2024 Review App. 5.1/5.2; Firm Access Oct 2025 results table (Donegal units staying non-firm: Croaghonagh, Derrykillew, Lenalea, Mully Graffy, Drumnahough, Barnesmore) | partial, no full register |
| Compensation per unit | not published; aggregate €34.92m provision 2025/26 | aggregate only |
| Regional dispatch-down 2025 | ARCC 2025 Table 4 | have |
| ENTSO-E nodal prices for Ireland | STUM request needed; public zips have per-node cleared generation/demand (anonymised) | partial |

## 3. Empirical baseline (MEASURED, 2026-06-08 to 2026-09-05, 30 NW units)

Method: dispatch-down = 0.5 × AvgOutturnAvail − DispatchQuantity per half-hour (both MWh). A unit is "under constraint" between a LOCL and the next LCLO instruction, "under curtailment" between CURL and CRLO. "Constraint-only" = dispatch-down in half-hours under LOCL and not under CURL (a lower bound on constraint; the LOCL-any column is the upper bound). Sanity: 63 % of half-hours show zero dispatch-down and DispatchQuantity equals half the availability to 0.01 MWh.

Results (24 units with > 250 MWh available and at least one LOCL):
- Total dispatch-down ratio: 4.7 % to 21.0 % of available energy; Gini 0.15.
- Constraint-only ratio: 1.6 % to 9.8 %; median 6.6 %; Gini 0.17.
- **NW Constraint Group 1** (Trillick, Binbane, Lenalea, Tievebrack; 6 units): constraint-only 1.6 % (Cronalaght 2, Tievebrack) to 9.8 % (Cloghervaddy 2, Binbane), a 6× spread; Gini 0.25. Hours under LOCL 93 to 341.
- **NW Constraint Group 3** (Sligo–Flagford; 13 units): 4.8 % to 8.9 %; Gini 0.11.
- Booltiagh (West group; 4 units at one station, so identical shift factor): 2.9 % to 7.0 %; Gini 0.17.

Reading: the rule EirGrid describes as fair "at the time of application" produces a 2× to 6× spread of constraint burden inside one group over a single summer. Units at the same station (identical effectiveness) differ by 2.4×. Causes to test in the paper: pro-rata on output not availability (claim 2), overlapping group membership (a unit takes the lower of two setpoints), outage-variant groups, and the release rule. Caveats: group membership is inferred from station names, not from the WDT's live configuration; the LOCL/CURL state machine can misattribute overlapping periods; 90 days, one summer.

## 4. What the corrections do to the paper

- The equity story is **firm vs non-firm**, not priority vs non-priority. Firm farms are already made whole for constraint; the band rule changes who is physically cut, and only non-firm farms feel it financially. Several Donegal farms are non-firm (Oct 2025 list). The paper should report the burden shift by firm status, using the firm-access run reports.
- "No money changes hands" is correct only as "no new payments are needed". Today's payments continue unchanged under any split rule.
- Drop the NPD-first rule from the baseline. Model today's rule (pro-rata across both classes) and, as a labelled sensitivity, the stated enduring intent (NPD first).
- Add a legal framing sentence: Art. 13(1) non-discrimination and 13(5)(b) minimisation are both satisfied by the band rule by construction (equal ratio over the year; least spill in the hour). That is a stronger position than either pole.
- Cite Sweeney (2026) for the deficit-round-robin analogy and Quessongo et al. (2026) for cumulative-ratio caps; claim only the TSO-level, shift-factor-ordered, within-existing-groups application.

## 5. Build plan (what to compute, all closed-form on PTDF except rule 3)

For each hour h and each binding element e with overload O_e,h, the group G_e, shift factors SF_i (per-bus PTDF differences, one convention, stated), availability a_i,h, output p_i,h:
1. **Pro-rata (today):** cut c_i = C × p_i / Σ p; C solves Σ SF_i c_i = O_e. Deepening steps use last output, not availability (App. 1). Release pro-rata on headroom.
2. **Effectiveness-ordered:** sort by SF_i descending; cut fully in order until Σ SF_i c_i = O_e.
3. **Nodal optimum:** kit LOPF with duals (already proven in `proof_siting.py`).
4. **Band rule:** as 2, restricted to units with year-to-date ratio r_i ≤ r̄_G + b; if the eligible set cannot clear O_e, widen to the next unit; update r_i after each hour. Sweep b ∈ {0, 1, 2, 3, 5, 10 pp, ∞}.
5. **N-1 layer:** repeat with LODF-adjusted flows for the outage variants listed in the WDT document.
6. **Outputs:** MWh spilled per rule per year; Gini and max/min ratio of r_i at year-end; the frontier curve of spill vs Gini across b; burden by firm status; the same statistics computed on the 2026 empirical data as the observed point on the chart.
7. **Robustness:** two synthetic seeds and the ENTSO-E 1989/1995/2009 climate years; results as ratios and ranks.

Runtime: rules 1, 2, 4 are vector operations per hour (seconds for a year). Rule 3 is ~12 s per 168 h all-island, ~10 min per year.

## 6. Still missing or unverifiable

- Official NPD status per unit (TSOs "evaluating", Jan 2026). Proxy: COD before 4 July 2019.
- A complete firm/non-firm register (only run-report tables exist).
- Whether the WDT can carry a per-farm tally (no public spec; rebalancing suggests partial state).
- The live WDT group configuration on any given day (only the Feb 2024 document).
- Japan's METI fairness guideline verbatim; the IFAC 2025 paper body; Sweeney's Energy Economics companion paper.
- ENTSO-E Irish nodal prices (STUM request).
- Outcome of CJEU C-36/25 on Art. 13(7) compensation; present arrangements are interim.
