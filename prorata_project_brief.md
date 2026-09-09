# The price of pro-rata: constraint-group dispatch on the Irish grid, and a rule that is equal over the year and effective in the hour

Project brief for an AI assistant. TPSA / TF Wind Hackathon 2026, problems 3.2 (constraint group generation), 3.3 (dispatch-down strategy), 3.4 (full grid), with 3.1 as the worked example.

Written 2026-09-08. Everything marked VERIFIED was read in the primary source that day; MEASURED was computed from public data in this repo; UNVERIFIED is stated as such. Sources and quotes are in `research/verification-regulatory.md`, `research/verification-literature.md`, `research/idea1-band-rule-verification.md`.

## 0. How to use this document

Paste this at the start of a working session. The humans are a team of second-year engineering students at Trinity College Dublin. They want short, precise, technically accurate answers, SI units, no filler. Assume competence in Python, linear algebra and mechanics; assume no power-systems background, so define jargon the first time. Section 10 is a glossary.

The single most important instruction: **do not let the project produce numbers the data cannot support.** Weather in the kit is synthetic; costs are placeholders. Present ratios, ranks and differences between runs. Every claim must survive "would this still be true if the random seed changed?"

Second instruction: **two earlier assumptions were wrong and must not creep back in.** (1) Non-priority wind farms are NOT cut before priority farms today. (2) Constrained firm wind farms ARE compensated; non-firm are not. Details in section 3.

## 1. The question

Ireland switches wind farms off when a transmission line would overload. It does this by sending one instruction to a predefined group of farms and splitting the cut between them in proportion to what each is producing. The operator calls this fair. The question is:

1. How much wind does that split waste, compared with cutting the farms that actually relieve the line?
2. How equal is the "equal" rule in practice?
3. Is there a rule that is at least as fair over a year and wastes less in every hour, without new payments?

The proposed rule: **equal over the year, effective in the hour.** When a line binds, cut farms in the group in order of effectiveness (shift factor), but only among farms whose year-to-date curtailment ratio is within a band of the group average; farms above the band are protected until the others catch up. Band width is the dial between today's rule (band zero) and pure effectiveness (band infinite).

## 2. How it works today (VERIFIED, EirGrid Wind Dispatch Tool Constraint Group Overview, Feb 2024, and SEM decisions)

**Constraint groups.** Offline, EirGrid builds a low-load, high-wind case, applies all mitigations, lists the remaining thermal and voltage violations under intact, N-1 and N-1-1 conditions, and for each violation computes a **shift factor** for every wind node: reduce one farm by 10 MW, balance at a remote conventional unit, measure the change in flow on the monitored element. Nodes above a threshold, set per violation at "a significant step change" in the sorted shift factors, form the group. The threshold rationale is efficiency: farms with "a much smaller impact are not constrained down inefficiently, which would ultimately be inconsistent with the principles of SEM-11-062" (App. 2, p.72). Outage variants of each group are listed by hand.

**Applying a cut.** The operator picks a group and a total MW reduction. The tool splits it pro-rata on **current active power output**:

    setpoint_A = output_A − (group cut) × output_A / Σ output_group

If the constraint is deepened later, the split is again on the then-current output and "does not consider the changing availability" (App. 1, p.67). Releases are pro-rata on headroom. EirGrid's own worked example (pp.66–68) ends with four farms at 75 %, 37.5 %, 62.5 % and 66.7 % of availability constrained. **So the rule is not equal in availability terms even within one event.** A farm in two groups takes the lower setpoint. Since 26 Nov 2025 a "rebalancing" step lets the controller re-split on availability at their discretion.

**The shift factor is computed to build the group and discarded at the split.** That is the inefficiency the paper measures.

**Curtailment is different.** System-wide limits (SNSP, inertia) are applied as one scalar to the whole fleet. Not locational, out of scope here except as a period to exclude from the measurement.

## 3. Rules, money and law (VERIFIED)

- **Priority vs non-priority.** EU Reg. 2019/943 Art. 12(6) grandfathers priority dispatch for renewables commissioned before 4 July 2019. For constraints, the SEM today applies **pro-rata across both classes** within a group: MPID 320 (EirGrid, Mar 2024) says "continue the pro-rata constraint of all controllable, non-dispatchable renewable generators (with or without priority dispatch)". The intent to cut non-priority units first (SEM-24-044) is stalled since 2024, pending a regulator decision and CJEU case C-36/25. The list of which units are non-priority is not public. **Model today's rule as pro-rata for all; model NPD-first only as a labelled sensitivity.**
- **Compensation.** All constraint and curtailment in the SEM is classed as non-market-based redispatch (SEM-22-009). Firm units are settled so they keep their day-ahead revenue up to their Firm Access Quantity (deemed decremental price of zero). **Non-firm units receive nothing**, which Art. 13(7) expressly allows: "except in the case of producers that have accepted a connection agreement under which there is no guarantee of firm delivery of energy." The 2025/26 provision for constrained wind and solar is €34.92m; total imperfections charge €790.24m. The compensation design was partly quashed by the High Court in 2023 and awaits the CJEU; treat it as interim.
- **Fairness.** No rule codifies equitable sharing of constraint. The legal floor is non-discrimination (Art. 12(1), 13(1); Electricity Regulation Act 1999 s.9(4)(a)) and minimisation of renewable redispatch (Art. 13(5)(b), 13(6)(a)). Pro-rata is a stated rationale: "Controllability enables fairness of dispatch-down between wind farms and solar farms on a pro-rata basis at the time of application" (EirGrid ARCC 2025, p.18); "equal burden sharing" (SEM-13-010, p.26, for curtailment). **The band rule satisfies both non-discrimination (equal ratio over the year) and minimisation (least spill in the hour) by construction.** Say that explicitly.
- **Who feels a rule change.** Firm farms keep their revenue under any split, so for them the change is physical only. Non-firm farms bear it financially. The Firm Access October 2025 results name Donegal units staying non-firm: Croaghonagh 1, Derrykillew, Lenalea, Mully Graffy, Drumnahough, Barnesmore repowering. Report burden shifts by firm status.
- **Numbers to cite.** 2025 all-island wind dispatch-down 13.4 % (constraint 8.9 %, curtailment 4.5 %). North-West controllable wind 19.6 % (constraint 14.7 %), Midlands 22.4 % (18.4 %), West 15.5 % (11.2 %), South-West 7.0 % (1.5 %), North-East 6.1 % (0.9 %). Source: EirGrid/SONI Annual Renewable Constraint and Curtailment Report 2025, Table 4.

## 4. Prior art and what is new (VERIFIED)

- **Ireland's own literature.** Nayer, Hodges, Bukhsh (Strathclyde) and RES, arXiv 2608.24464 (25 Aug 2026): first open MILP of Irish curtailment and constraint with overlapping pro-rata groups (their eq. 16–17: a unit's output is the minimum over its groups' pro-rata factors). 446-bus network, no N-1, no storage, no benchmark against optimal dispatch, fairness not discussed. It is the baseline formulation to cite and extend.
- **Theory.** Newbery & Biggar, Energy Policy 191 (2024): pro-rata plus uniform price plus firm access gives excess entry into constrained zones; nodal pricing or non-firm priority access fixes it. Single-constraint toy model. Chyong & Newbery, CWPE 2581 (Jan 2026): marginal curtailment in GB by 7 zones; spatial measurement "has been missing".
- **Other systems.** Australia's NEM dispatches by constraint coefficient (effectiveness) and bid price with no compensation and no right to be dispatched. Germany's Redispatch 2.0 (Oct 2021) selects by sensitivity and cost with minimum factors 10 (renewables) and 5 (CHP), and compensates under EnWG §13a. Japan rotates curtailment among plants ("輪番") for equal opportunities and OCCTO verifies yearly that it "was conducted in a fair manner throughout the year"; no line-effectiveness element. GB distribution schemes (Orkney, Shetland) use last-in-first-off.
- **Closest academic matches.** Sweeney, arXiv 2606.17217 (Jun 2026): stateful stochastic allocation of flexible demand with a cumulative delivery-ratio deficit; already cites weighted fair queuing and deficit round robin, so cite him for that analogy. Sweeney et al., arXiv 2606.22463: same idea for distribution DER with export tallies. Quessongo et al., arXiv 2608.23444 (Aug 2026): caps cumulative curtailment ratio in day-ahead distribution envelopes. Andoni et al., Applied Energy 2017: fractional round robin curtailment in distribution. Lagos et al., IFAC 2025: coupled optimisation to avoid repeatedly curtailing the same units (body not read).
- **Novelty claim, carefully worded.** No published work combines a year-to-date curtailment-ratio band as a gate with shift-factor ordering inside existing TSO constraint groups, without payments. The two real-world poles exist (Ireland/Japan equal, Australia/Germany effective); the rule interpolates between them. The contribution is the Irish, transmission-level, within-existing-tool application and its measured frontier.

## 5. The empirical baseline (MEASURED, 2026-06-08 to 2026-09-05, 30 North-West units)

Method: per half-hour, dispatch-down = 0.5 × AvgOutturnAvail (BM-101, MW) − DispatchQuantity (BM-096, MWh). A unit is under constraint between a LOCL instruction and the next LCLO (BM-037), under curtailment between CURL and CRLO. Constraint-only = dispatch-down in half-hours under LOCL and not CURL (lower bound). Sanity: in 63 % of half-hours the dispatch quantity equals half the availability to 0.01 MWh.

**Do not use BM-086 "MeteredMW"**: it is energy per half-hour at the meter, net of the farm's own consumption, and sits below the dispatch quantity even in unconstrained hours. Using it inflates dispatch-down by a factor of 3–4.

Results (24 units with > 250 MWh available and at least one LOCL):
- Total dispatch-down share of available energy: 4.7 % to 21.0 %. Constraint-only share: 1.6 % to 9.8 %, median 6.6 %, Gini 0.17.
- **North-West Group 1** (Trillick, Binbane, Lenalea, Tievebrack; 6 units): constraint-only 1.6 % (Cronalaght 2) to 9.8 % (Cloghervaddy 2), a sixfold spread, Gini 0.25.
- **North-West Group 3** (Sligo–Flagford; 13 units): 4.8 % to 8.9 %, Gini 0.11.
- Four farms at the single Booltiagh station (identical shift factor): 2.9 % to 7.0 %.

Reading: the rule described as fair "at the time of application" delivers a two- to six-fold spread of constraint burden inside one group over one summer. Candidate causes, to be tested in simulation: pro-rata on output rather than availability, overlapping groups, outage variants, the release rule, and units that were offline or not instructed. Caveats: membership inferred from station names, not the live tool; the instruction state machine can misattribute overlaps; 90 days, one summer.

Files: `data/semo_nw_units/nw_unit_dispatchdown_2026-06-08_to_09-05.csv`, inputs `BM-101_nw_units.csv`, `BM-096_nw_units.csv`, puller `pull.py`.

## 6. Data inventory

| Item | Where | Status |
|---|---|---|
| Networks (4 TYTFS cases × all-island / NW), ratings, reactances, coordinates | `participant-kit/networks/`, `gridkit.py`, `flowmath.py` | have; 22 self-checks pass |
| Proven pipeline: LOPF with duals, PTDF, LODF, Tier 1/2 siting | `proof_siting.py`, `TOOLKIT.md` | have |
| Full synthetic year, seed = weather year | `data/synth_out/`, generator `kit_build/synthetic.py` | have (WP2033, seed 42) |
| Real-weather country profiles, 3 climate years, 2025 fleet | `data/entsoe_lmp_2022/PEMMDB23_IE00_aggregated.xlsx` (+ UKNI) | have |
| ERA5 per-site profiles | `kit_build/profiles.py fetch --year 2023` | available, not fetched |
| WDT constraint groups, outage variants, pro-rata formula, shift-factor procedure | `Wind-Dispatch-Tool-Constraint-Group-Overview_1.pdf`; text `research/papers/eirgrid-wdt-constraint-group-overview-2024.txt` | have; groups need typing into a table |
| Dispatch instructions, all units, 3 months (LOCL/LCLO/CURL/CRLO) | `data/BM-037_dispatch_instructions_2026-06-07_to_09-05.csv` | have; 191 units received LOCL (140 IE, 51 NI) |
| Empirical co-instructed batches | `data/empirical_constraint_groups_top20.csv` | have |
| Per-unit availability and dispatch quantity | `data/semo_nw_units/` (30 NW units); API in `data/README.md`, `page_size` ≤ 5000, `ResourceName=` filter works, some pages omit `totalPages` | NW have; all-island ≈ 2 h per report |
| Unit code → name, station (IE, 233 units) | `data/semo_unit_map_IE.csv` | have; 121 of 140 IE LOCL units map |
| NI unit mapping | `data/ni_claf.txt`, `data/soni_tlaf_2627.xlsx` | have, not yet parsed |
| Controllability category per plant | `data/ctrl26.txt` | have |
| Priority status per unit | `data/eirgrid_gss1_res_units.csv` (EirGrid's own COD-based assumption) | proxy only; official NPD list not public |
| Firm / non-firm per unit | Firm Access 2024 Review App. 5.1/5.2; Firm Access Oct 2025 results | partial; no full register |
| ECP-GSS-1 per-node constraint forecast | `data/eirgrid_gss1_node_results.csv` | have (validation, averages only) |
| G-TUoS node tariffs 2025/26 | `data/EirGrid_GTUoS_2025-26_IE_node_tariffs.txt` | have (for the storage idea) |
| Regional constraint 2025 | ARCC 2025 Table 4 (quoted in `research/verification-regulatory.md`) | have |
| ENTSO-E 2022 nodal results for Ireland | public: per-node cleared generation/demand, anonymised (`data/entsoe_lmp_2022/`); nodal prices and grid model need a STUM request | partial |
| Papers and decisions (text) | `research/papers/` | have |

## 7. Method

**Notation.** For hour h, binding element e with overload O (MW above rating), group G_e, farm i with shift factor SF_i on e (per-bus PTDF difference, one reference convention chosen once and stated), availability a_i, output p_i, cut c_i ≥ 0. Feasibility: Σ SF_i c_i ≥ O.

**Rule 1, pro-rata (today).** c_i = C p_i / Σ p; C from feasibility. Deepening uses last output; release pro-rata on headroom (App. 1). A unit in two groups takes the lower setpoint (Nayer et al. eq. 16).

**Rule 2, effectiveness-ordered.** Sort by SF_i descending, cut each fully until feasible.

**Rule 3, nodal optimum.** Kit LOPF with `assign_all_duals=True`; nodal prices and line duals fall out (identity verified in `TOOLKIT.md` §2). This is what a nodal market does automatically.

**Rule 4, the band.** Maintain r_i = cumulative cut / cumulative availability, year to date. Eligible set E = {i : r_i ≤ r̄_G + b}. Apply rule 2 on E; if infeasible, add the next-lowest r_i until feasible. Update r_i after each hour. Sweep b ∈ {0, 1, 2, 3, 5, 10 percentage points, ∞}. Optionally run within firm/non-firm or priority classes.

**Contingencies.** LODF from the kit PTDF (validated to 1e-9 against PyPSA's BODF). Recompute SF and overloads for each outage variant listed in the WDT document. N-1-1 only for the named cases.

**Weather years.** Synthetic full year (two seeds) and ENTSO-E 1989 / 1995 / 2009 country profiles scaled to buses. Report which results are stable across all.

**Outputs.**
1. Spill per rule per year (MWh, as ratios to rule 1).
2. Year-end inequality per group: Gini and max/min of r_i.
3. The frontier: spill vs Gini as b sweeps, with rules 1 and 3 as the endpoints and the 2026 measurement as the observed point.
4. Burden by firm status and by priority proxy under each rule.
5. Nodal congestion price map (λ_b − mean λ) from rule 3, as the diagnostic behind the wedge.

Rules 1, 2 and 4 are vector operations per hour: seconds per year. Rule 3 is ~12 s per 168 h all-island, ~10 min per year.

## 8. Deliverables and team split

1. **Measurement** (what happens today): per-farm constraint share by group, 2026 data. One chart. Owner: data person, plus the NI mapping if going all-island.
2. **Simulation** (what the rules cost): the frontier chart. Owners: two people, one on the rules engine, one on weather years and outages.
3. **Policy page** (who pays, why it is allowed): firm vs non-firm, Art. 12/13, the band rule's compliance by construction, named non-firm farms. Owner: writer, also slides.

Order: group table → three rules on one week → full year → outages → slides. The North-West is the worked example on every slide; all-island totals are the headline if time allows.

**All-island scaling.** ~40 groups (automate from shift factors with EirGrid's step-change threshold, validate against the document and against co-instructed batches; that automation is problem 3.2), 191 units, 6 binding lines + 3 transformers in the 2033 baseline, overlapping groups everywhere, interconnectors as links. Use the 2024 network for comparison with 2026 data (groups match), 2033 for the forward-looking case (reinforcements dissolve some groups; say so).

## 9. Defensibility rules

- Robust: shift factors, PTDF/LODF, rankings, ratios between rules on the same weather, the 2026 measurement.
- Contaminated: any euro figure, any absolute annual GWh from synthetic weather, anything that changes sign across seeds.
- Say out loud: weather source and seed on every number; group table from a Feb 2024 document, not the live tool; instruction-based attribution of constraint vs curtailment; the comparison is on paper, WDT state capability unknown; compensation rules are interim pending the CJEU.
- Do not claim the deficit-round-robin analogy as new. Do not claim NPD-first is live. Do not say constrained wind is unpaid without "non-firm".

## 10. Glossary

Availability: MW a farm could produce given the wind, as declared/outturn. Constraint: dispatch-down for a local network limit. Curtailment: dispatch-down for a system-wide limit (SNSP, inertia). Constraint group: predefined set of farms sent one joint cut. Shift factor / effectiveness: change in flow on a monitored element per MW change at a node, signed. PTDF: matrix of shift factors for all elements and buses. LODF: how flow redistributes when an element trips. LOPF: linear optimal power flow, least-cost dispatch subject to line limits. Nodal price (LMP): marginal cost of one more MWh at a bus; its congestion part is −Σ PTDF × line dual. Firm access: right to compensation when dispatched down, up to a Firm Access Quantity. Priority dispatch: legacy right under Art. 12(6) for pre-July-2019 renewables. WDT: EirGrid's Wind Dispatch Tool. LOCL/LCLO: local constraint applied/released; CURL/CRLO: curtailment applied/released. Gini: 0 = everyone equal, 1 = one farm bears everything. Pro-rata: split in proportion to output.

## 11. Open questions for the assistant

1. Given that pro-rata is on output and ignores availability when deepening, what share of the measured 2026 inequality can be reproduced by that mechanism alone, before overlapping groups and outages are added?
2. How should the band rule handle a farm that sits in two groups with different averages?
3. Is a Gini on year-to-date ratios the right inequality metric, or should the frontier use max/min or the Kalai–Smorodinsky reference points from Matt, Shilov and Bolognani?
4. Can the group table be generated from shift factors closely enough to the WDT document that hand-typing is unnecessary all-island?
5. What is the cheapest way to include the worst single contingency in the band rule without recomputing shift factors for every outage each hour?
