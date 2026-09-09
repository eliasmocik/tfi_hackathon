# Formula decisions for the pro-rata project

Written 2026-09-09 from four literature searches (power-flow conventions, WDT mechanics, fair-allocation rules, metrics). Each decision states its certainty: **settled** (a primary source defines it), **common practice** (several sources agree), or **judgement call** (no source decides it; the choice is ours and must be stated on the slide). "100 % certainty" is not available for the judgement calls; they are marked so nobody claims otherwise. Quotes were checked against the local texts in `research/papers/` where they exist.

Two decisions change from the brief: Q1 (single remote slack, not load-spread) and Q3 (per-hour pro rata on availability is now "today's rule", the output-based state machine becomes a sensitivity).

| # | Decision | Choice | Certainty |
|---|---|---|---|
| 1 | Shift-factor reference | One fixed remote conventional bus, far from the violation | settled |
| 2 | Overload definition | Post-contingency flow via LODF, two named N-1 cases; intact checked too | settled |
| 3 | Today's rule | Per-hour pro rata on availability within the group ("WDT with rebalancing"); output-based apply/deepen/release as sensitivity | settled basis, judgement on rebalancing frequency |
| 4 | Ties in effectiveness order | Treat same-station farms as one node; split pro rata on availability inside it | common practice |
| 5 | Fairness tally | r_i = cumulative MWh cut / cumulative MWh available | settled for an Irish audience |
| 6 | Band centre | Availability-weighted group mean = the group's own aggregate dispatch-down % | judgement call |
| 7 | Overlapping groups | Farm takes the lower setpoint; one tally per farm | settled |
| 8 | Fallback when the band starves the group | Widen one farm at a time by ascending r_i; never snap to pro rata | common practice |
| 9 | Inequality metric | Jain's index on r_i (chart); Gini and worst-farm ratio (table) | common practice |
| 10 | Efficiency metric | % of available energy, plus ratio to pro-rata baseline; constraint reported separately from curtailment | settled form |
| 11 | Nodal optimum | Per-hour LP on the same PTDF/LODF linearisation; SCLOPF cross-check on a few hours | common practice |
| 12 | Frontier chart | Fairness index (y) vs dispatch-down % (x), one point per band width, endpoints labelled | common practice |

## 1. Shift-factor reference — single remote slack

EirGrid's procedure: reduce one farm by 10 MW, "balance this decrease in generation by adding 10 MW to another conventional generator far removed from the Transmission issue", and repeat "ensuring the remote balancing generator is always the same" (WDT Overview App. 2, local lines 3418, 3435). AEMO does the same: coefficients "relative to a single bus (known as a swing bus)" at the regional reference node (Constraint Formulation Guidelines 2021, p. 9). In DC terms SF = PTDF[e, n] − PTDF[e, ref]; changing the reference adds the same constant to every farm on a line (MATPOWER manual, H_w = H_k(I − w·1ᵀ)). So the ranking is invariant but the inclusion test ("0 or below … not effective", line 3455) and the step-change threshold are not. Pick a remote conventional bus whose PTDF on the monitored element is ≈ 0, state it once, and show load-distributed slack as a sensitivity if asked. Kit: `flowmath.shift_factors(n, monitored, reference="<bus name>")`.

## 2. Overload — N-1 via LODF

The WDT document defines effectiveness relative to "the 'base case', 'N-1' or 'N-1-1' overload" and limits flows "pre-contingency to ensure that the post-contingency flows are within acceptable limits" (p. 5). Post-contingency flow f_e^(k) = f_e + LODF_{e,k} · f_k with LODF_{e,k} = PTDF_{e,k} / (1 − PTDF_{k,k}), LODF_{k,k} = −1 (PyPSA contingencies docs; MATPOWER manual). Singular when PTDF_{k,k} = 1 (radial element). For the North-West use loss of Flagford–Srananagh 220 kV (monitor Flagford–Sligo 110 kV and the Flagford 220/110 kV transformer) and loss of Binbane–Cathaleen's Fall (monitor the Letterkenny lines as a busbar proxy). N-1-1 only by recomputing PTDF on the outaged topology; drop it for the hackathon. Nayer et al. 2026 name missing N-1 as their main limitation, so including it is a visible step beyond the published baseline.

## 3. Today's rule — pro rata on availability per hour, state machine as sensitivity

Basis at each step, all quoted. Initial application: on actual output, which "for the initial application of the constraint, is also equal to the available active power" (WDT App. 1, p. 66). SEM-24-044a's "nominal output" is the same thing: "When a unit is not regulating for frequency, nominal output is equal to its Actual Active Power Output." Deepening: "always be pro-rata based on the wind/solar farm actual output and does not consider the changing availability" (p. 67). Release: pro rata on headroom. Rebalancing, live since 26 Nov 2025 (FPM Newsletter 27): "Unit Setpoint = Group MW Target × (Unit Reference Quantity / Sum of Reference Quantities)" on current availability, "initiated at the discretion of the Control Centre" (Guide to Rebalancing, Nov 2025).

Consequences. Your 2026 measurement sits entirely under the rebalancing regime. Nayer et al. model pro rata as one scalar per group per period (eq. 16, ξ_k applied to each unit's upper bound), a published precedent for the simple form. So: main run = per-hour pro rata on availability, labelled "WDT with rebalancing"; sensitivity = output-based apply/deepen/release, labelled "pre-Nov-2025 WDT". Whether the state machine reproduces the measured 2.3× spread is then a result, not an assumption. This also removes a day of coding.

## 4. Ties — one node, pro rata inside

"Wind/solar farms connected at the same transmission station will generally have the same effectiveness … so they are grouped together" (WDT p. 5); "Only one wind farm per node requires studying as each will have the same effectiveness" (line 3421). AEMO breaks coefficient-and-price ties pro rata: tied terms "will be dispatched in proportion to the MW sizes of the respective marginal bid bands" (AEMO Constraint FAQ; NER 3.8.1(b)). Germany publishes no tie rule. So order nodes by shift factor, split each node's cut pro rata on availability among its farms.

## 5. Tally — MWh cut over MWh available

EirGrid reports dispatch-down as "% of total available energy" (ARCC 2025 §1.2 and Table 4). Both 2026 cumulative-fairness papers use the same state variable: Quessongo et al. χ_i = (E_av − E_acc)/E_av (eq. 10); Sweeney et al. "cumulative export realised relative to cumulative export available" (eq. 3). Per-MW-installed penalises windy sites; per-MWh-produced has a denominator that shrinks as you cut; event counts (Japan's rotation, "制御回数が均等") ignore depth. Availability declarations can be gamed (Sweeney uses min(forecast, physics estimate)); EirGrid's declared availability plays that role. Say so once.

## 6. Band centre — availability-weighted group mean (judgement call)

r̄_G = Σ cut / Σ available over the group. It equals the group's aggregate dispatch-down % that EirGrid already publishes, so "within b points of the group figure" reads naturally, and it is the weighted-fair-queuing analogue (quantum ∝ weight). No paper uses a mean-centred band: Quessongo caps the maximum ratio (min Γ s.t. χ_i ≤ Γ), Sweeney tracks a deficit against a target of 1. Unweighted mean lets one small farm move the centre; a fleet mean mixes groups with different exposure. State this as our choice.

## 7. Overlapping groups — lower setpoint, one tally

SEM-24-044a: "the setpoint issued to the unit is the lower setpoint." Nayer et al. eq. 16: p_g = min over the unit's groups. The document's intact-network tables give NW Group 1 = {Ardnagappary, Binbane, Lenalea, Sorne Hill, Trillick} ⊂ NW Group 3 (15 stations); outage variants modify both, so assert the subset for intact definitions only. One year-to-date tally per farm; the band test uses the centre of whichever group is firing.

## 8. Fallback — widen, never switch principle

Every Irish and GB precedent is a cascade, not a switch: EirGrid ECP-2.5 studies allocate "amongst non-priority generators, and then priority generators should the constraint not be resolved"; the WDT uses "a secondary group … of less effective nodes" (§6.2); Orkney LIFO curtails the next-connected farm only when the previous cannot resolve (Kane et al. CIRED 2013). So admit the next-lowest r_i one at a time, keep shift-factor order inside the widened set; when all are admitted the rule has become pure effectiveness order and the secondary group applies. Slide wording: "the band never blocks security, it only orders who goes first." One-at-a-time vs tier-at-a-time is a judgement call; one-at-a-time is simpler.

## 9. Inequality metric — Jain primary, Gini and worst farm secondary

Curtailment-fairness papers use Jain's index and Gini, often both (Gupta & Molzahn 2024; Quessongo et al. 2026, JFI = (Σ η_i)² / (N Σ η_i²); Liu et al. IEEE TSG 2020; Fraunholz et al. Applied Energy 2025 uses Gini). Jain is bounded 0–1, 1 = equal, so "up = fairer"; CoV adds nothing (JFI = 1/(1+CV²)). Gupta & Molzahn found the two can rank rules differently, hence report both. Add the worst-farm ratio as the plain-language column.

Pre-empt one objection. Matt, Shilov, Bolognani, "A Welfarist Perspective on Fair Generation Curtailment" (arXiv 2605.03860, May 2026) show that minimising Jain or Gini "can favor curtailment decisions that are not Pareto optimal" and that pro rata is a Kalai–Smorodinsky solution for one reference point. Answer: we do not optimise the index; every rule on the curve is effectiveness-ordered within its band, and the x-axis already shows the efficiency cost. That paper is distribution-level with no cumulative term; cite it as the theory behind why pro rata feels fair.

## 10. Efficiency metric — % of available, plus ratio to baseline

ARCC 2025 form: "dispatch-down energy … 1,476 GWh … equivalent to 11.4 % of the total available wind energy", constraint and curtailment kept separate by definition ("localised network reasons, where only a subset … can contribute" vs "system-wide reasons"). Report group dispatch-down as % of available energy and, in the table, absolute MWh and the ratio to the pro-rata run (1.00 = status quo). With synthetic weather the absolute MWh carries no meaning; the two ratios are invariant to wind scaling. Never mix curtailment in.

## 11. Nodal optimum — per-hour LP on the same linearisation

min Σ c_i subject to f_e^(k) − Σ_i SF^(k)_{e,i} c_i ≤ rating_e for every (element, contingency) pair, 0 ≤ c_i ≤ availability_i. This is the shift-factor LP structure that AEMO's dispatch and ENTSO-E's redispatch guideline use ("min Σ c(k,t)·Δp(k,t)"), and it shares every assumption with rules 1, 2 and 4, so the gap is purely the allocation rule. Cross-check on a handful of hours with PyPSA `optimize_security_constrained(branch_outages=[…])`; full-year SCLOPF over all outages is unnecessary and slow, and it cannot outage Links. Call the result a lower bound on spill (no unit commitment, no time coupling, DC).

## 12. Frontier chart — precedent exists

Gupta & Molzahn 2024 plot "Pareto curves depicting fairness (a) JFI and (b) Gini versus PV curtailments" by sweeping a weight; Quessongo et al. report the two poles (technical allocation 2.11 MWh vs fairness-constrained 5.72 MWh). Same axes here: dispatch-down % (x), Jain (y), one point per band width, pro rata and pure effectiveness as labelled endpoints, nodal optimum as the x-floor, the 2026 measurement as the observed point. Single-number summary for the table: price of fairness = (MWh under rule − MWh under effectiveness order) / MWh under effectiveness order (Li et al. arXiv 2403.15616).

## Novelty, re-checked

No source combines a cumulative energy-ratio gate with effectiveness ordering inside TSO constraint groups. Nearest: Quessongo (cap, distribution, day-ahead), Sweeney (deficit-weighted stochastic priority, demand), Andoni 2017 (rotation by capacity units, "does not take into account … actual contribution to the network constraint"). Safest framing for an EirGrid audience: Ireland already runs "gate, then allocate" (ECP-2.5's priority-status gate plus pro rata); we replace a static gate with a cumulative one and pro rata with shift-factor order — two dials in a structure they already have.

## Sources not fully verified

SEM-13-010(ii) is the file on the SEMC site; the "SEM-13-011" label in the brief could not be confirmed. METI's fairness guideline and Lagos et al. IFAC 2025 bodies not read. Guo, Fu, Tylavsky (IEEE TPS 2009) LODF paper not opened; the formula is confirmed from PyPSA and MATPOWER docs instead. Liu et al. 2020 and Fraunholz et al. 2025 quoted from abstracts. German tie-break rule: none published.

## Primary URLs

WDT Constraint Group Overview: https://cms.eirgrid.ie/sites/default/files/publications/Wind-Dispatch-Tool-Constraint-Group-Overview_0.pdf · SEM-24-044a: https://www.semcommittee.com/files/semcommittee/2024-06/SEM-24-044a_TSOs%20Definitions.pdf · Guide to Rebalancing: https://www.sem-o.com/sites/semo/files/2025-11/Guide%20to%20Rebalancing_0.pdf · ARCC 2025: https://cms.eirgrid.ie/sites/default/files/publications/Annual-Renewable-Constraint-and-Curtailment-Report-2025-V1.0.pdf · ECP-2.5 constraints summary: https://cms.eirgrid.ie/sites/default/files/publications/Constraints-Forecast-Studies-for-ECP-2.5-Ireland_summary.pdf · AEMO Constraint Formulation Guidelines: https://www.aemo.com.au/-/media/files/electricity/nem/security_and_reliability/congestion-information/2021/constraint-formulation-guidelines.pdf · AEMO Constraint FAQ: https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/system-operations/congestion-information-resource/constraint-faq · PyPSA contingencies: https://docs.pypsa.org/latest/user-guide/optimization/contingencies/ · MATPOWER shift factors: https://matpower.app/manual/matpower/LinearShiftFactors.html · ENTSO-E redispatch CBA guideline: https://eepublicdownloads.blob.core.windows.net/public-cdn-container/tyndp-documents/TYNDP2020/FINAL/TYNDP2020_CBA_Implementation_Guideline_Redispatch_final.pdf · Nayer et al. 2026: https://arxiv.org/abs/2608.24464 · Quessongo et al. 2026: https://arxiv.org/abs/2608.23444 · Sweeney 2026: https://arxiv.org/abs/2606.17217 and https://arxiv.org/abs/2606.22463 · Andoni et al. 2017: https://arxiv.org/abs/1908.10313 · Gupta & Molzahn 2024: https://arxiv.org/abs/2404.00394 · Matt, Shilov, Bolognani 2026: https://arxiv.org/abs/2605.03860 · Li et al. 2024: https://arxiv.org/abs/2403.15616 · de Carvalho et al. 2026 survey: https://arxiv.org/abs/2604.27669 · Kane et al. CIRED 2013: https://strathprints.strath.ac.uk/44700/2/CIRED_Full_Paper_20130107.pdf
