# Regulatory verification: constraint (dispatch-down) of wind in the SEM

Verified 2026-09-08 by reading the primary documents. Local text copies were in the session scratchpad; URLs below are the primary sources.

## 1. EU Regulation 2019/943, Art. 12 and 13 — VERIFIED

Source: legislation.gov.uk mirror (https://www.legislation.gov.uk/eur/2019/943/article/13 and `/article/12`).

Art. 12 (priority dispatch): 12(1) dispatch "shall be non-discriminatory, transparent and, unless otherwise provided under paragraphs 2 to 6, market based." 12(2)(a) priority for RES "< 400 kW"; 12(5) drops to "< 200 kW" for facilities commissioned from 1 Jan 2026; 12(6) grandfathering: RES commissioned before 4 July 2019 with priority dispatch "shall continue to benefit from priority dispatch" until "significant modifications" (new connection agreement or capacity increase).

Art. 13 (redispatching): 13(1) "objective, transparent and non-discriminatory criteria"; 13(2) market-based redispatch "financially compensated"; 13(3) non-market-based redispatch only where no market-based alternative etc.; 13(5)(a)/(b) TSOs to "minimise the downward redispatching of electricity produced from renewable energy sources"; 13(6)(a) RES "shall only be subject to downward redispatching if no other alternative exists…"; 13(6)(d) "duly and transparently justified".

**13(7) verbatim:** "Where non-market based redispatching is used, it shall be subject to financial compensation by the system operator requesting the redispatching to the operator of the redispatched generation, energy storage or demand response facility **except in the case of producers that have accepted a connection agreement under which there is no guarantee of firm delivery of energy.** Such financial compensation shall be at least equal to the higher of … (a) additional operating cost … (b) net revenues from the sale of electricity on the day-ahead market … where financial support is granted … financial support that would have been received without the redispatching request shall be deemed to be part of the net revenues."

## 2. Irish/SEM implementation and compensation — VERIFIED (live legal caveat)

Key decision: **SEM-22-009**, Dispatch, Redispatch and Compensation, 22 March 2022 — https://www.semcommittee.com/files/semcommittee/media-files/SEM-22-009%20Decision%20Paper%20on%20Dispatch,%20Redispatch%20and%20Compensation%20Pursuant%20to%20Regulation%20EU%202019943.pdf

- All constraint and curtailment redispatch in the SEM, for PD and NPD units, is classified **non-market-based** (p.1–2, p.19).
- Compensation for constraints (p.20): "units are settled at the better of their complex bid/offer price or imbalance settlement price up to the level of their Firm Access Quantity. … Non-firm generation, which is constrained, pays the Balancing Market Price for the constrained volumes. For non-dispatchable priority dispatch generators, they do not receive any payment or make a payment for constraints, leaving them with their ex-ante market revenue if they are constrained below their market position."
- Art. 13(7) decision (p.2, p.26): all units compensated "where firm"; wind/solar "essentially retaining their ex-ante revenue, as such volumes are settled at a deemed decremental price of zero". Non-firm: no compensation (Art. 13(7) exception).
- Interim rule (p.26): "pro-rata treatment of constraints within a constraint group, regardless of Priority Dispatch status".

By class:
- **Firm units:** constrained-off volumes below FAQ made whole in the Balancing Market (deemed dec price 0 → keep day-ahead revenue). Cost recovered via Imperfections Charge.
- **Non-firm units:** no constraint compensation (SEM-11-062 p.30–31; SEM-23-004 p.4: "a unit which has no firm access will receive no compensation for [being] dispatched down").
- **PD vs NPD:** no difference today for constraints; both pro-rata within the group, both deemed dec price 0 (Mod_13_23 FRR p.4).

Historic: SEM-13-010 (1 March 2013) pro-rata curtailment with cessation of curtailment compensation from 1 Jan 2018; SEM-13-011 is the TSO constraint/curtailment rule set. Firm access: SEM-23-004 (25 Jan 2023), 2022 snapshot renewables 5,475 MW, ~1,000 MW (18 %) non-firm; CRU/2023/114 (8 Nov 2023) detailed methodology.

**Legal caveat:** SEM-22-009 quashed in part by the High Court (10 Nov 2023, Greencoat/Energia v CRU); Supreme Court referred 7 questions on Art. 13(7) to the CJEU on 21 Jan 2025 (Case C-36/25, Energia Group and Others; https://eur-lex.europa.eu/eli/C/2025/3259/oj/eng). EirGrid FPM Newsletter 31 (April 2026): AG Opinion issued, "process has not yet concluded". SEM-25-053 (Sept 2025) allowed €37m for Art. 13 payments in 2025/26 (TSOs asked €91m incl. €54m back-payments 2020–2025, disallowed for now).

## 3. MPID 320 / NPDR dispatch order for constraints — VERIFIED (NOT LIVE)

- MPID 320 (EirGrid, 5 Mar 2024, https://cms.eirgrid.ie/sites/default/files/publications/MPID320-NPDR.pdf): Grid Code changes so NPDRs submit COD/PNs. Quote: "for an interim implementation it would be acceptable to continue the pro-rata constraint of all controllable, non-dispatchable renewable generators (with or without priority dispatch)". It does **not** set a PD/NPD ordering.
- Enduring intent (SEM-24-044, June 2024, p.9): "non-priority dispatch units will be redispatched prior to priority dispatch units with regard to constraints. Curtailment will continue to be pro-rata." SEM-21-027 (p.4, p.36): NPDR constraints by "market-based merit order based on the bids and offers of such units".
- **Interim answer: NPD is not cut first. Pro-rata across PD and NPD within the group.** Mod_13_23 approved by Modifications Committee 15 March 2024, **no RA decision yet**.
- Status per EirGrid Future Markets newsletters 27 (Dec 2025), 28 (Jan 2026), 31 (Apr 2026), 33 (Jun 2026), 34 (Jul 2026): "We acknowledge the delay in progressing the introduction of Non-Priority Dispatch Renewables (NPDRs)"; RAs assessing Mod_13_23 and SEM-24-044; TSOs modelling; "at least 6 months" after decision; the list of NPD units is **not public** ("the TSOs are currently in the process of evaluating the NPDR status of wind and solar units", Q&A Jan 2026 A21).
- SDP-04 "Wind Dispatch Improvements" (rebalancing) went live 26 Nov 2025; "Guide to Rebalancing" published 20 Nov 2025.

## 4. Wind Dispatch Tool mechanics — VERIFIED (partly; no cadence or logging spec)

Sources: WDT Constraint Group Overview (1 Feb 2024, https://cms.eirgrid.ie/sites/default/files/publications/Wind-Dispatch-Tool-Constraint-Group-Overview_0.pdf); SEM-13-011 TSO Definition of Curtailment and Constraint (13 Feb 2013); SEM-24-044a TSO definitions (May 2024, https://www.semcommittee.com/files/semcommittee/2024-06/SEM-24-044a_TSOs%20Definitions.pdf); Wind DD Reports User Guide v1.1 (29 Jul 2016).

- Operator selects a predefined group and a MW reduction; WDT computes per-farm setpoints and issues them (Overview p.6). LOCL = local constraint, CURL = curtailment.
- Pro-rata basis is **actual output, not availability** on application (SEM-13-011 p.2; Overview App. 1 p.66–68: further constraints "will always be pro-rata based on the wind/solar farm actual output and does not consider the changing availability"); release pro-rata on headroom. 2024 wording: "pro-rata … with reference to that unit's nominal output" (SEM-24-044a p.3). Rebalancing (live Nov 2025) re-pro-rates on availability at controller discretion.
- Overview App. 1 worked example: after one deepening step the four farms sit at 75 %, 37.5 %, 62.5 %, 66.7 % of availability constrained — **pro-rata on output is not equal in availability terms even within the hour.**
- Membership by shift-factor analysis with a per-contingency threshold at "a significant step change" (App. 2 p.70–74). Temporary groups per outage condition exist. A unit in several groups gets the lower setpoint (SEM-24-044a p.5).
- Logging: instructions time-stamped with reason codes; DD reports give 30-min output/availability per farm. **No public spec on issue cadence or on WDT internal state history.**

## 5. Firm access reports — VERIFIED; per-unit lists exist, no full register

- Firm Access 2024 Review Report (6 Jun 2024): 196 committed non-firm units, 6,018 MW (conventional 1,663 / solar 3,115 / wind 1,240 MW). App. 5.1 = unit list (code, name, station, type, MEC); App. 5.2 = per-unit result year. Outcome: 2.6 GW firm immediately, 280 MW partial, 2 GW on reinforcement, 1.2 GW stays non-firm.
- Firm Access October 2025 Results (https://cms.eirgrid.ie/sites/default/files/publications/Firm_Access_October_2025_Results_Publication.pdf): 46 generators ~2.7 GW; wind ~60 MW firm on the unreinforced system; ">500 MW of committed wind … remain non-firm". Donegal units "staying non-firm": Croaghonagh 1 (Clogher) 138.1 MW (72 MW non-firm), Derrykillew 37.5 MW, Lenalea 30.1 MW, Mully Graffy 29.9 MW, Drumnahough 72 MW, Barnesmore repowering 48 MW.
- No single public register of firm/non-firm status for all wind farms. The "4,355 MW applied for non-firm" figure quoted by Newbery (2025) was **not found**; 1,240 + 3,115 = 4,355 MW is the committed non-firm wind+solar assessed in FA2024.

## 6. Latest numbers — VERIFIED

EirGrid/SONI Annual Renewable Energy Constraint and Curtailment Report 2025 (https://cms.eirgrid.ie/sites/default/files/publications/Annual-Renewable-Constraint-and-Curtailment-Report-2025-V1.0.pdf):
- All-island wind dispatch-down 2025: 13.4 % (2,139 GWh of 15,921 GWh) = constraints 8.9 % (1,425 GWh) + curtailment 4.5 % (714 GWh). Ireland wind 11.4 % (constraints 6.7 %, curtailment 4.8 %). NI wind 22.0 % (constraints 18.6 %).
- Regional controllable wind (Table 4 p.26): **NW (389 MW) 19.6 % total, 14.7 % constraints, 4.9 % curtailment** (2024: 24.5 / 20.3 / 4.1); W (1,148 MW) 15.5 / 11.2 / 4.3; MID (924 MW) 22.4 / 18.4 / 4.0; SW 7.0 / 1.5 / 5.6; SE 7.4 / 2.7 / 4.6; NE 6.1 / 0.9 / 5.3.
- Fairness statement p.18: "Controllability enables fairness of dispatch-down between wind farms and solar farms on a pro-rata basis at the time of application."

Costs: SEM-25-028 Imperfections forecast 2025/26: total €699.81m incl. €91m Art. 13(7) provision; "Constrained wind and solar" provision €34.92m (actual CDISCOUNT May 2024–Apr 2025); "Wind/solar is currently not paid for curtailment in SEM; however, it is paid for constraints" (§4.2.4). SEM-25-053 decision: Network Imperfections Charge 2025/26 €790.24m, €19.93/MWh; Art. 13 provision €37m.

## 7. "Fair / equitable" sharing rule — PARTLY (stated rationale, not codified)

- No SEM rule mandates equitable constraint sharing. Legal hooks are non-discrimination: Reg. 2019/943 Art. 12(1), 13(1); Electricity Regulation Act 1999 s.9(4)(a); SEM Act 2007 s.9.
- SEM-11-062 (2011) originally set firm-before-non-firm and date order for tie-breaks; withdrawn (SEM-11-105), replaced by SEM-13-010 (2013): "A pro rata approach to curtailment will provide certainty of equal burden sharing across all wind generators, irrespective of the level of firmness" (p.26); modelled 24 % curtailment for non-firm under grandfathering vs 4 % pro-rata. Constraint pro-rata within groups was a TSO operational choice (SEM-13-011), endorsed as interim in SEM-22-009 p.26.
- TSO fairness language: SEM-24-044 p.7 rebalancing "will ensure more equitable outcomes"; p.11 "perceived unfairness … based on the geographical dispersion of units". WDT Overview p.72: threshold ensures small-impact units "are not constrained down inefficiently, which would ultimately be inconsistent with the principles of SEM-11-062". SEM-21-027 p.34: pro-rata across units with the same COD for NPDR tie-breaks.

## Implications for the paper

- **Holds:** constraint is applied pro-rata on actual/nominal output within shift-factor-defined groups, identically for PD and NPD wind. NPD-first is only a stated enduring intent, stalled pending CJEU C-36/25 and RA decisions.
- **Fails:** any assumption that NPD is already cut first for constraints (this includes the premise of `problem_3_1/q6_priority.py`, which models a rule that is not live).
- **Fails:** "constrained-off wind is uncompensated". Firm wind keeps ex-ante revenue up to FAQ (≈ €35m/yr). **Non-firm wind gets nothing.** A "who bears the cost" model must split firm vs non-firm, not PD vs NPD.
- **Holds:** EU floor (13(1), 13(6)(a), 13(7)) and Irish non-discrimination duties exist; "equal burden sharing" is SEMC rationale (SEM-13-010) and TSO language (ARCC 2025, SEM-24-044), not law.
- **Data per unit:** firm/non-firm and FAQ year for units assessed in the 2024/2025 runs; no complete register. NPD status per unit not public; rule of thumb from Art. 12(6): commissioned before 4 July 2019 = PD unless modified. Per-unit compensation not published.
- **Numbers to cite:** 2025 all-island wind dispatch-down 13.4 % (8.9 % constraint); NW controllable wind 19.6 % (14.7 % constraint); Imperfections 2025/26 €790.24m; constrained wind/solar provision €34.92m; Art. 13(7) provision €37m.
- **Unverified/absent:** the "4,355 MW applied" wording; AG opinion date/content in C-36/25; WDT instruction cadence and internal state retention.
- **Legal-risk flag:** the compensation design is interim, partly quashed, and awaiting the CJEU; it may change retroactively.
