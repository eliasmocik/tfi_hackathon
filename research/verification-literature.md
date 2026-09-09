# Prior-art verification: "equal over the year, effective in the hour" curtailment rule

Verified 2026-09-08 from full texts where available. Status labels: VERIFIED / PARTLY / NOT FOUND.

The rule under test: when a line binds, cut farms in the constraint group in order of shift factor, but only among farms whose year-to-date curtailment ratio (MWh cut / MWh available) is within a band of the group average; farms above the band are protected until others catch up. Band width is the fairness-efficiency dial. No payments.

## 1. Sweeney, arXiv 2606.17217 (15 Jun 2026), "A Stateful Stochastic Allocation Mechanism with Fairness Guarantees for Networked Electricity Systems" — VERIFIED

- Allocates flexible **demand** requests, not generation curtailment. "generator", "curtailment", "PTDF", "shift factor", "TSO" do not appear.
- Nodal DC-OPF relaxation; selection is stochastic: "Stage 1: Service-Level Priority Sampling", "Stage 2: Inverse-Fairness Weighting Within Tier".
- Fairness state: per-node cumulative delivery ratio F_n(t) → 1, deficit z = max(0, F* − F_n). A tally exists but it is a demand-delivery tally used as a sampling weight, not a band gate.
- Tests: IEEE 14/57/118-bus, 5000 intervals.
- **Already claims the DRR analogy:** "structurally related to weighted fair queuing (WFQ) and deficit round-robin scheduling in packet networks". Cite him for the analogy.
- Companion: Sweeney, Energy Economics 158, 109345 (2026), LMP comparison on a stylised GB network (not read).
- https://arxiv.org/abs/2606.17217

## 2. Matt, Shilov, Bolognani, arXiv 2605.03860 (5 May 2026), "A Welfarist Perspective on Fair Generation Curtailment" — VERIFIED

- Distribution only: PV curtailment in a 6-bus LV testbed (Walenstadt, CH), 5 prosumers, 15-min, 24 h.
- Classifies pro-rata on availability, equal export fraction, uniform kW cap, equal absolute MW cut as Kalai–Smorodinsky solutions with different reference points. LIFO not classified.
- No temporal fairness: "curtailment decisions are applied independently at every time step".
- https://arxiv.org/abs/2605.03860

## 3. Sweeney et al., arXiv 2606.22463 (21 Jun 2026), "Stateful Pricing and Allocation for Repeated Constrained DER Coordination in Distribution Networks" — VERIFIED

- Same lead author (Imperial). Distribution feeders, dynamic operating envelopes; carries "dual fairness states for import and export" (an export-curtailment tally) that drives prices. Benchmarks Moring, Farrell & Mathieu, "Fair-over-time distributed energy resource coordination", Allerton 2024.
- Closest published curtailment tally; distribution, price-driven, no line sensitivities.
- https://arxiv.org/abs/2606.22463

## 4. Lagos, Gatos, Manolioudakis, Dimeas, Hatziargyriou (NTUA), IFAC-PapersOnLine 2025, "A renewable energy sources curtailment strategy based on fairness considerations" — PARTLY (abstract only)

- Distribution DRES; "to avoid continuously curtailing the same DRES"; "two stepwise, coupled optimization problems that are repeated for a specific time horizon, aiming to minimize both total curtailments and inequalities". Body not accessible (403). DOI 10.1016/j.ifacol.2025.12.028.

## 5. Prior work combining cumulative fairness with effectiveness ordering at transmission level — NOT FOUND

| Paper | What it does | Difference |
|---|---|---|
| Andoni, Robu, Früh, Flynn, Applied Energy 201 (2017), arXiv 1908.10313 | Pro-rata vs LIFO vs **Fractional Round Robin** (rotation by rated capacity units) | Distribution / private wire; no line sensitivity; no ratio band |
| Lagos et al., IFAC 2025 | Coupled optimisation over a horizon to avoid repeatedly curtailing the same units | Distribution; optimisation, not a dispatch-order rule |
| Sweeney 2026 (×2) | Cumulative delivery-ratio deficit drives stochastic priority / prices | Demand or DER; no effectiveness ordering |
| Quessongo, Gebbran, Unsihuay-Vila, arXiv 2608.23444 (Aug 2026) | Multi-period operating envelopes; min Γ s.t. cumulative curtailment ratio χ_i ≤ Γ; Jain index; IEEE 33-bus | Distribution; day-ahead OPF; no PTDF ordering |
| Fraunholz, Tash, Scheben, Zillich (TransnetBW), Applied Energy 377 (2025) 124679 | Gini-based spatial and temporal fairness of demand curtailment in flow-based European dispatch | Demand (ENS), zonal |
| Nayer et al., arXiv 2608.24464 (Aug 2026) | MILP of Ireland's overlapping pro-rata groups | Status-quo baseline only; fairness not discussed |

Irish baseline quotes: "Controllability enables fairness of dispatch-down between wind farms and solar farms on a pro-rata basis at the time of application" (EirGrid ARCC 2024 p.16, ARCC 2025 p.18); "applies constraints pro-rata to all generators of the same priority status within a subgroup" (ECP-2.5 constraints forecast summary). GE patent US 8860237 (unverified, scanned) orders intra-park turbine curtailment by cumulative curtailment time.

## 6. Japan — PARTLY

- Rotation (輪番) is explicit: Kyushu T&D FAQ, old-rule online plants "選定を輪番で" (selected for curtailment by rotation); fairness set by the national guideline "出力制御の公平性の確保に係る指針"; OCCTO checks and publishes. https://www.kyuden.co.jp/td/functions/faq/renewable-energy/cotrol.html
- OCCTO (English): "verifies whether the output curtailment was conducted in a fair manner throughout the year". https://www.occto.or.jp/en/works/no2.html . OCCTO board paper: offline plants allocated "設備比率で配分" (by installed-capacity ratio).
- "Equal number of opportunities per fiscal year" wording seen only in a search snippet; METI guideline PDF blocked. **Not verbatim-verified.**
- FIT before FIP from FY2026/27: https://www.rts-pv.com/en/blogs/13660/
- Compensation tiers: 30-day rule (old), 360-hour rule (new), unlimited uncompensated (designated). https://so.shizenenergy.net/en/blog/2026_output_solar_curtailment/

## 7. Australia NEM — VERIFIED

- Constraint-equation coefficients are flow contributions from load flow (AEMO Constraint Formulation Guidelines 2021 §2.5/2.6); minimum coefficient 0.07, raised to 0.15 from 2 Dec 2025.
- AEMC: "the generator with the 0.3 coefficient could produce more power without violating the constraint than could the generator with the 0.9 coefficient" (Final Report Appendix A, introduction to congestion in the NEM).
- Dispatch prioritises by coefficient and price; ties split pro-rata by bid-band MW (AEMO FAQ 3.19).
- No compensation: constrained-off "has foregone revenues"; "no right to be dispatched" (AEMC).

## 8. Deficit round robin — VERIFIED

Shreedhar & Varghese, "Efficient fair queueing using deficit round robin", SIGCOMM '95 (doi:10.1145/217391.217453); IEEE/ACM ToN 4(3) 1996, 375–385. Per-queue deficit counter credited a quantum per round, debited by bytes sent, unused credit carried forward.

## 9. Germany Redispatch 2.0 — VERIFIED

- Selection "nach der Wirksamkeit der Anlagen zur Engpassentlastung und den Kosten" (BNetzA, 30 Nov 2020); minimum factors 10 (RES) / 5 (CHP) (Ofgem case study, 29 Jul 2021); live from 1 Oct 2021.
- Compensation §13a EnWG: operator "weder besser noch schlechter gestellt … als er ohne die Maßnahme stünde".

## Novelty verdict

**Not found in published form.** Nothing combines (a) a year-to-date curtailment-ratio band as a gate, (b) shift-factor ordering inside the band, (c) at TSO constraint-group level, (d) without payments. Real systems sit at the two poles the rule interpolates: Ireland and Japan (equal/pro-rata, no effectiveness) versus NEMDE and Redispatch 2.0 (effectiveness-ordered, Germany adding compensation). Closest academic matches are Sweeney 2026 (demand, stochastic), Quessongo et al. 2026 (distribution, day-ahead cap on cumulative ratio), Andoni et al. 2017 (rotation), and Japan's rotation practice. The DRR analogy is already claimed by Sweeney; cite, do not claim.

**Could not verify:** IFAC 2025 body; METI guideline verbatim; GE patent text; Sweeney's Energy Economics paper content.
