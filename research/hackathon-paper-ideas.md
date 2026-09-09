# Three verified research-paper directions on locational pricing — TPSA Hackathon 2026

Compiled 2026-09-08. Every source below was fetched and read today; extracted texts are in
`research/papers/`. "Verified" = read in the source. "Unverified" = from memory, not checked.

## 0. What the literature looks like right now (the gap map)

| Source | What it did | What it did NOT do (= our opening) |
|---|---|---|
| Nayer, Hodges, Bukhsh (Strathclyde) + Chitambo, Wijeratne (RES), *Modelling Renewable Curtailment and Constraints in Ireland's Electricity System*, arXiv 2608.24464, **25 Aug 2026** — https://arxiv.org/abs/2608.24464 | First open MILP of Irish curtailment + constraint with EirGrid's **overlapping pro-rata constraint groups** (their eq. 16-17). 446-bus TYTFS-2022 network, July 2025 half-hourly, validated vs EirGrid dispatch-down. Funded by RES, advised by Manuel Hurtado (EirGrid). | No N-1 (they say this is why constraint is under-predicted). No storage. No nodal prices. **Never benchmarks pro-rata against the optimal (nodal) dispatch**, so the cost of the rule is not quantified. Explicitly "a starting point for further open source model development". |
| Newbery & Biggar, *Marginal curtailment of wind and solar PV: transmission constraints, pricing and access regimes*, EPRG 2401 (Feb 2024), published Energy Policy 191 (2024) — https://www.jbs.cam.ac.uk/wp-content/uploads/2024/02/eprg-wp2401.pdf | Theory: under zonal/uniform price + firm access + pro-rata curtailment, VRE entry into export-constrained zones is **excessive**; nodal pricing or non-firm "last in, first curtailed" access fixes the entry signal. Marginal curtailment is 3+ times average. | Single export constraint (a stylised REZ). No meshed network, no Irish numbers. Cites EirGrid's firm-access proposal (SEM-22-068a) as a real-world instance. |
| Chyong & Newbery, *Marginal curtailment under network constraints: evidence from the 2030 GB power system*, CWPE 2581 (30 Jan 2026) — https://www.econ.cam.ac.uk/sites/default/files/publication-cwpe-pdfs/cwpe2581.pdf | First empirical map of **marginal** curtailment across space: GB split into 7 zones; marginal curtailment ≈ 50 % for new onshore wind in Scottish zones, < 25 % elsewhere; long-run marginal cost ∝ 1/(1−mc), differing by "tens of pounds per MWh" across zones. States that "a systematic measurement of how marginal curtailment varies across space in constrained systems… has been missing". | Zonal (7 zones), not nodal. GB, not Ireland. Admits curtailment allocation within zones "depend[s] on modelling conventions". |
| Newbery, *Implications of Renewable Electricity Curtailment for Delivered Costs*, EPRG 2503 (Feb 2025) — https://www.jbs.cam.ac.uk/wp-content/uploads/2025/03/eprg-wp2503.pdf | mc/ac ratio 3-9; proves reducing average curtailment does lower marginal cost. Notes 4,355 MW of Irish wind+solar applied for non-firm connections (EirGrid 2024). | Theory only. |
| JRC, Thomassen & Fuhrmanek, *Locational Price Signals in Europe*, JRC142047 (2025) — https://publications.jrc.ec.europa.eu/repository/bitstream/JRC142047/JRC142047_01.pdf | EU-wide model: LMP + locational investment signals save 26-61 bn EUR/yr in 2040; recommends LMP in the EU target model and, as a "no-regret" first step, **locational impact as a non-price criterion in renewable auctions** and a locational element in capacity markets. | Continental focus; Ireland appears only as a capacity-market precedent. No nodal Irish detail. |
| SEM Committee, *Firm Access Methodology in Ireland — decision*, SEM-23-004 (2023) — https://www.semcommittee.com/files/semcommittee/media-files/SEM-23-004%20SEMC%20Firm%20Access%20in%20Ireland%20decision.pdf | Firm access = right to constraint compensation; 5 % constraint threshold; non-firm units dispatched down without compensation. Records industry proposals for **"heat maps" of spare capacity and "nodal caps or a forward nodal CfD on constraints"**, and one respondent calling the firm threshold "a relatively binary, arbitrary and crude locational signal". RAs deferred locational signals to a later methodology paper. | The nodal-cap / nodal-CfD idea was never modelled publicly. |
| CRU, *Transmission Network Charges for Energy Storage — Minded-to Interim Decision*, CRU/202645, **15 Apr 2026** — https://consult.cru.ie/ga/system/files/materials/847/CRU202645%20Transmission%20Network%20Charges%20for%20Energy%20Storage%20Minded-to%20Interim%20Decision.pdf | Minded to move storage from D-TUoS to G-TUoS partly **to "provide locational signals for siting of ESUs"**. Admits "prospective investors currently face limited locational signals" and that G-TUoS locational charges "may not always be appropriate for ESUs" because storage near generation relieves constraints yet is charged more there. Open consultation question. | No quantitative test of whether the G-TUoS locational component points storage toward or away from constraint relief. |
| EirGrid/SONI, *Approved 2025/26 GTUoS — accompanying note* and node table (Aug/Sep 2025) — https://cms.eirgrid.ie/sites/default/files/publications/2526_Approved_GTUoS_Tariffs_IE_v1.0.pdf | Only public locational *price* in the SEM: postage stamp €6.856/kW/yr, node tariffs €3.24-€15.01/kW/yr, locational share **24 %** of €141.6 m. Built from 4 planning dispatch scenarios + a 13-year reinforcement cost file; Donegal nodes had "the greatest increases". **Per-station tariff table exists** (copied to `data/EirGrid_GTUoS_2025-26_IE_node_tariffs.txt`; NW stations all present). | It is an investment-cost signal, not a congestion signal. Nobody has compared it with nodal congestion value. |
| EirGrid ECP-GSS-1 constraint forecast (already in `data/`) | Per-node average constraint %, 2030/2035, 11 scenarios. | Average only, and **uniform inside each constraint subgroup**. No marginal, no external cost. |
| arXiv 2605.00690 (Mahuze et al., May 2026) curtailment-credit market for non-firm loads: 1.41-1.83 × served-load value vs pro-rata; arXiv 2606.17217 (Sweeney, Jun 2026) stateful fair allocation vs LMP | Shows "pro-rata vs optimal allocation" is a live 2026 topic. | Loads / IEEE test systems, not Irish generation. |
| Pollitt 2023 (EPRG 2318), Eicke & Schittekatte 2022, NESO 2022, REMA 2025 | In `research/locational-pricing-sources.md`. | GB zonal was rejected July 2025 on distribution, not physics. |

Net: **no Irish nodal study of (a) the cost of the pro-rata constraint-group rule, (b) marginal-vs-average constraint per node, or (c) whether the one locational charge Ireland has points storage the right way.** Those are the three papers.

---

## Idea 1 — "The price of pro-rata": nodal shadow-price accounting of constraint-group dispatch

> **Verified 2026-09-08, see `idea1-band-rule-verification.md`.** Two corrections to the text below: (1) non-priority-first
> cutting is NOT live (MPID 320 keeps pro-rata for both classes); (2) firm wind IS compensated for constraint, non-firm is not.
> Extension: the "equal over the year, effective in the hour" band rule, novelty verified, empirical baseline measured
> (NW Group 1 constraint burden spread 1.6 % to 9.8 % across members in summer 2026 under today's "equal" rule).

**Question.** How much wind does EirGrid's constraint-group + pro-rata rule spill compared with (i) a shift-factor-weighted split inside the same groups and (ii) full nodal optimal dispatch (the LMP solution), on the real Irish network, intact and N-1? And what is each farm's implicit congestion price, i.e. the wedge between the uniform SEM price it is paid and its nodal price?

**Why it is a paper.** Nayer et al. (Aug 2026) built pro-rata into a model but never measured what the rule costs. Newbery & Biggar (2024) prove pro-rata gives the wrong signal but only on a one-line toy. Nobody has the Irish number. The three-rung ladder (nodal → SF-weighted groups → pro-rata groups) is already in your `wind_siting_project_brief.md` §5.1; this idea is that ladder, done properly and written up.

**Method (all on the kit).**
1. Nodal optimum = kit LOPF with `assign_all_duals=True`; nodal prices `buses_t.marginal_price`, verified identity λ_b − mean(λ) = −Σ PTDF·μ (your `TOOLKIT.md` §2).
2. Pro-rata = Nayer et al. eq. 16-17 (min over the groups a farm belongs to), with groups from the WDT PDF and cross-checked against BM-037 LOCL batches (`data/empirical_constraint_groups_top20.csv`). Cheaper LP version: fix ξ_k per group per hour by bisection until the monitored line clears.
3. SF-weighted = same groups, cut in order of |SF|.
4. N-1 layer via BODF/LODF (already validated in `TOOLKIT.md`), which is exactly what Nayer et al. list as their missing piece.
5. Outputs: MWh spilled per rule per week; the efficiency-vs-fairness frontier (Gini of per-farm cut vs total MWh); nodal congestion-price map (λ_b − λ̄); per-farm "implicit tax" = (λ̄ − λ_b) × MWh.

**Headline slide.** "Pro-rata spills X % more wind than nodal dispatch; Y % of that gap is recovered by SF-weighting inside today's groups, without changing the groups." Ordinal + multi-seed, per your defensibility rules.

**Problem-sheet hooks.** 3.2 (are shift factors the right metric, one group per line?) and 3.3 (incentive structure) directly; 3.4 for the all-island run.

**Risks.** Synthetic week → report ratios not GWh. Group membership hand-typed from a PDF → publish the table, cite the PDF. Degenerate LP ties → deterministic bid jitter (`common.set_renewable_bids`).

---

## Idea 2 — Marginal vs average constraint at nodal resolution: what the firm-access threshold and a "nodal cap" would look like in Ireland

**Question.** Chyong & Newbery measured marginal curtailment at 7-zone resolution in GB and called the spatial measurement "missing". At every Irish 110 kV+ bus: what is the marginal constraint rate of the next MW (mc), how does it compare with EirGrid's own average per-node constraint (ECP-GSS-1, uniform inside subgroups), and what does the mc/ac ratio imply for (a) the 5 % firm-access threshold in SEM-23-004 and (b) the "nodal caps / forward nodal CfD on constraints" proposal that SEM-23-004 records and never modelled?

**Why it is a paper.** It translates your Tier-2 private/system index into the exact economics vocabulary the Cambridge group uses (mc, ac, LMCoE ∝ 1/(1−mc)) and applies it to a market whose regulator has an open locational-signals question. Newbery cites EirGrid's non-firm proposal as the real-world instance of his theory; you supply the numbers.

**Method.** Your `proof_siting.py` pipeline is 80 % of it:
1. Tier 1 screen (PTDF·μ exposure) on all 503 candidate buses, WP2033.
2. Tier 2 at top/bottom 40: add 20/50/100/200 MW, re-solve. Private index → **ac** of the entrant; capacity sweep slope → **mc**; external index → spillover onto neighbours (Chyong & Newbery's "spillovers raise mc for new and existing"). 
3. Compare per-node mc and ac with `data/eirgrid_gss1_node_results.csv` (their 2030 numbers are averages; show where subgroup-uniform averages hide a 5× nodal spread).
4. Policy layer: mark buses where ac < 5 % (would be granted firm access) but mc ≫ 5 %; that is the "crude binary signal" the SEM-23-004 respondent complained about, quantified. Then simulate a nodal cap: each new entrant compensated only up to a cap = its expected ac; show the transfer it removes.

**Headline slide.** Two maps (ac, mc) and one ratio map; a table of buses that pass the 5 % firm test on average but fail on the margin.

**Problem-sheet hooks.** 3.1 bullet 4 (where should developers locate), 3.4, 3.10 (offshore concentration: one 500 MW injection has a very different mc than 10 × 50 MW).

**Risks.** mc from a 168 h synthetic week is noisy → use the synthetic full year (`synthetic.py`, 5 s) and two seeds; ERA5 2023 if time. The occupied-bus check must run on the Tier-2 system index, not Tier 1 (`TOOLKIT.md` §5).

---

## Idea 3 — Which locational signal for storage? G-TUoS locational charge vs nodal congestion value, bus by bus

**Question.** CRU's April 2026 minded-to decision would charge storage the generator tariff partly *because* its locational component is a siting signal, while admitting it "may not always be appropriate for ESUs". Test it: for every Irish transmission bus, is the 2025/26 G-TUoS locational component correlated, uncorrelated, or anti-correlated with the constraint-relief value of a battery at that bus?

**Why it is a paper.** It is a live regulatory question with a consultation open in 2026, the node-level tariff table is public (now in `data/`), and no one has put the two numbers side by side. It is also the cleanest "locational pricing" story you can tell: Ireland has exactly one locational price, and you check whether it points the right way.

**Method.**
1. Signal A: node tariff minus postage stamp (€6.856/kW/yr) from `data/EirGrid_GTUoS_2025-26_IE_node_tariffs.txt`; join on station name to kit buses (NW stations all match).
2. Signal B (constraint value): kit LOPF with `gridkit.add_battery` at each bus, 50 MW / 4 h; Δ constrained MWh vs baseline (your `q2_battery.py` already does this for the NW). Signal B′ (price value): Σ_h max(0, λ_b(h) spread) from nodal prices, i.e. what a nodal market would pay the same battery.
3. Rank correlation A vs B, A vs B′, all-island and NW. Map the disagreement quadrant: high charge + high relief value = "penalised where useful".
4. Sensitivity: tariff built from 4 planning scenarios with 0 % / high wind; re-run B under the four TYTFS cases to see whether the sign of the disagreement is scenario-driven.

**Headline slide.** Scatter of tariff vs relief value with Donegal/Sligo buses labelled. Either outcome is publishable: agreement means CRU's premise holds; disagreement means the charge steers storage away from constraint relief, which is the concern CRU itself wrote down.

**Problem-sheet hooks.** 3.1 bullet 2 (battery siting/sizing), 3.7 (does storage belong at the generation node?). Your existing NW finding (even 400 MW / 8 h removes only 22 % of NW dispatch-down) is already a data point: relief value is low behind the Letterkenny–Strabane tie, and the tariff there is high, so both signals may say "not Donegal" — which is itself the result.

**Risks.** Battery MWh figures are seed-contaminated → report ranks and signs. Kit has no storage shipped, so every battery needs an explicit profile-free dispatch (fine, it is a decision variable) and per-bus solves cost ~11 s each all-island → 503 buses ≈ 90 min, or screen with Tier 1 first.

---

## Which one first (my read, not a decision)

They share one engine (LOPF + duals + PTDF/LODF, all proven in `proof_siting.py`). Idea 1 is the most novel relative to the August 2026 paper and answers 3.2/3.3 head-on. Idea 2 reuses the most existing code and speaks the economists' language. Idea 3 is the most policy-timely and the easiest to explain to a judge in one picture. A team of four can run 1 and 3 in parallel on the shared engine; 2 falls out of 1's Tier-2 sweep almost for free.

## Missing facts

- Whether ENTSO-E's 2022 LMP data items include Irish nodes at node level (the release note says "nodal granularity" but does not list regions) — would be an external validation set for the nodal price map.
- MDPI Energies 14(5):1463 (LIFO vs pro-rata non-firm access, MATPOWER) could not be fetched (403); its content is known only via Nayer et al.'s literature review.
- The detailed CRU firm-access methodology (CRU/2023/114) was not read; the 5 % threshold is taken from SEM-23-004.
