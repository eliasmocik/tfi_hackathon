# Validation of `prorata_project_brief.md` as a 2-day hackathon project

Written 2026-09-08. Checked against `Hackathon_2026_Problem_Sheet-2.pdf`, `participant-kit/README.md`, the WDT Constraint Group Overview text, the data in `data/`, and two test runs on the WP2033 network with the synthetic year (scripts and logs: `research/n1_gonogo/`).

## 1. Verdict in one paragraph

The idea fits the problem sheet, is one the organisers are asking for, and the data to do it exists in the folder. Two things must change before building. First, the empirical headline is wrong: Tievebrack is not in North-West Constraint Group 1 in the Feb 2024 WDT document, so the "sixfold spread" (1.6–9.8 %) is really 2.3× (4.3–9.8 %). Second, the kit's model as shipped does not produce the constraints the WDT groups exist for: with the Letterkenny–Strabane tie modelled as a fixed line, the WDT's monitored elements never overload in a whole synthetic year, intact or N-1, and all the model's dispatch-down lands on a cross-border tie the kit itself flags as an artefact. Modelling that tie as a capped controllable link (what the phase-shifting transformer does) brings the Group 3 constraint back (Flagford 220/110 kV transformer overloaded under N-1 in ~6 % of hours). The brief's plan is a research paper, not a 2-day build; the cut-down scope in section 6 is achievable.

## 2. Does it answer what the sheet asks?

| Sheet item | Match |
|---|---|
| 3.3 "Constraint groups are used to dispatch down a set of generation nodes at once. Is there an optimal strategy to ensure a safe and effective incentive structure is enforced?" | Direct. This is the project's question. |
| Section 2, p.4: "Splitting the actual MW reduction across group members once it's invoked is a separate step (Appendix 1's pro-rata calc) and isn't part of this algorithm." | The organisers point at the pro-rata step themselves and do not ask anyone to study it. Nobody else in the room is likely to. |
| Intro p.1: "Even finding efficiencies to reduce constraint by 1-2% could save millions" | The pro-rata-vs-effectiveness gap is exactly a constraint efficiency. Report it as a ratio, not euro (brief §9 already says so). |
| 3.2 group generation ("is shift factor the best tool", "does there need to exist one group per problematic line") | Partial: the group table and the shift-factor ordering are inputs here, not the output. `problem_3_1/q5` already reproduces CG1 from shift factors. Claim 3.2 only for that. |
| 3.1 last bullet (priority / non-priority inefficiency) | Covered as a labelled sensitivity. The brief is right that NPD-first is not live; `q6_priority.py` as it stands models a rule that does not exist. |
| 3.4 full grid | Not in 2 days (section 6). |

Audience fact: Declan Nell and Seán O'Brien of EirGrid designed the problems and Nell is speaking. The WDT Overview is their document. Frame the result as "same groups, same tool, one formula changed", not as a fairness complaint. The document's own worked example (farms at 75 / 37.5 / 62.5 / 66.7 % of availability after one deepening step, App. 1 p.67, verified) is the safest opening: it is their number.

Unverified: the sheet twice calls the event a "week" (p.1 "Everyone who made the week happen"; back page "over a focused week"). The 2-day assumption in this memo comes from you. Check the timetable.

## 3. Data check, item by item

| Brief claim | Found on disk | Note |
|---|---|---|
| Networks, kit, 22 self-checks | yes (`participant-kit/`) | |
| Full synthetic year, WP2033 seed 42 | yes (`data/synth_out/`, 8,760 h, 710 generator columns) | **Not plug-in.** (a) Thermal units get an availability profile that falls to 0.15 while the network carries a static `p_min_pu` up to 0.78 → LOPF infeasible unless `p_min_pu` is clipped per hour (42 units). (b) 9 generators in the kit week have no column in the year file and would run flat-out at 1.0 (the README's own trap). (c) Only WP2033 has a year; the brief's "use the 2024 network for comparison with 2026 data" needs a WP2024 year generated with `kit_build/synthetic.py` first. |
| WDT groups, outage variants, pro-rata formula | yes (`research/papers/eirgrid-wdt-…txt`) | Verified quotes: formula p.66; "always be pro-rata based on the wind/solar farm actual output and does not consider the changing availability" p.67; "significant step change" and SEM-11-062 rationale App. 2. CG1 = Ardnagappary, Binbane, Lenalea, Sorne Hill, Trillick (intact and all four outage variants). CG3 = those plus Cathaleen's Fall, Corderry, Cunghill, Garvagh, Glenree, Meentycat, Moy, Mulreavy, Sligo, Tawnaghmore. **CG1 ⊂ CG3.** |
| Per-unit availability and dispatch quantity, 30 NW units | yes (BM-101 115,398 rows, BM-096 111,124 rows, 2026-06-08 to 09-05) | 3 of 30 units returned 0 rows (GU_403900, GU_401190, GU_400020). |
| Dispatch instructions, 3 months | yes (22 MB, LOCL/LCLO/CURL/CRLO) | No group identifier on a LOCL row; group attribution is by station name. |
| Unit map IE | yes, 233 units | NI units unmapped; the 15 most-instructed units are NI. All-island measurement is out of reach in 2 days. |
| Priority status | proxy only (COD < 4 Jul 2019) | official list not public — brief already says so. |
| Firm / non-firm | six Donegal names only | no register; keep to the policy slide. |
| ENTSO-E climate years | country-level only | not per bus; scaling them to buses is a day of work on its own. Drop. |

## 4. The empirical baseline, recomputed

From `nw_unit_dispatchdown_2026-06-08_to_09-05.csv`, 24 units with > 250 MWh available and ≥ 1 LOCL, constraint-only ratio, document membership:

| Group as in the WDT document | Units | Min | Max | Gini |
|---|---|---|---|---|
| CG1 (Binbane, Lenalea, Trillick incl. Sorne Hill) | 5 | 4.3 % (Beam Hill) | 9.8 % (Cloghervaddy 2) | 0.16 |
| CG1 as in the brief (+ Tievebrack) | 6 | 1.6 % (Cronalaght 2) | 9.8 % | 0.25 |
| CG3, document membership | 15 | 4.3 % | 9.8 % | 0.13 |
| CG3 as in the brief ("13 units", 4.8–8.9 %, Gini 0.11) | reproduces only as the 10 units at CG3-only stations | 4.8 % | 8.9 % | 0.11 |
| Booltiagh, one station | 4 | 2.9 % | 7.0 % | 0.17 |
| All 24 | 24 | 1.6 % | 9.8 % | 0.17, median 6.6 % |

Consequences. The "sixfold spread inside one group" line in brief §5 and in `research/idea1-band-rule-verification.md` §3 must go; the defensible statement is "2.3× inside CG1, 2.4× among four farms at one station with identical shift factors". Cronalaght 2 received 202 h of LOCL from some group, so either Tievebrack has been added since Feb 2024 or it sits in a group the document does not show; say "not in the 2024 document" rather than guess. The nested CG1 ⊂ CG3 structure answers brief open question 2 (a farm in two groups): the overlap in the North-West is nested, so one year-to-date tally per farm and the min-setpoint rule (Nayer et al. eq. 16) are enough; there is no "two different averages" problem here.

The method itself (0.5 × AvgOutturnAvail − DispatchQuantity; LOCL/LCLO state machine; do not use BM-086) stands. Both input files and the formula were checked.

## 5. The simulation, go/no-go test

Question: in the WP2033 network with the synthetic year, do the elements the WDT groups protect ever overload? Test: unconstrained least-cost dispatch (ratings lifted ×100, renewables bid −1, `p_min_pu` clipped) on a sample of the year, then intact flows and N-1 flows via LODF on the named elements. Sample of every 4th hour (2,190 h) for the shipped network; every 8th hour (1,095 h) with the tie changed.

| Monitored element, contingency | Shipped network: hours over rating (intact / N-1) | Tie as capped link: hours over rating (intact / N-1) |
|---|---|---|
| CG3: Flagford–Sligo 110 kV (121 MVA), loss of Flagford–Srananagh 220 kV | 0 / 0 | 0 / 2.1 % of hours, max 165 MW |
| CG3: Flagford 220/110 kV transformer T2102 (125 MVA), same contingency | 0 / 0 | 0 / 5.7 % of hours, max 183 MW |
| CG1 proxy: Drumkeen–Letterkenny 110 kV (123 MVA), loss of Binbane–Cathaleen's Fall | 13.5 % / 14.7 % | 0 / 1.1 % |
| CG1 proxy: Letterkenny–Lenalea, Letterkenny–Trillick | 0 / 0 | 0 / 0 |
| Letterkenny–Strabane tie (123 MVA) | 88 % of hours intact, max 350 MW | (capped by construction) |

Reading. As shipped, all North-West export in the model runs through the Letterkenny–Strabane tie, which the kit README lists as an unmodelled control device ("the tie terminates at a phase-shifting transformer whose tap this model holds fixed, and SONI would redispatch around a binding constraint"). Every North-West dispatch-down number in `problem_3_1/outputs` (131 of 168 h binding, "one wire is the whole NW constraint") is that artefact. The constraint groups in the WDT document are N-1 driven and never appear. Replacing the tie line with a PyPSA Link of `p_nom` = 123 MW, bidirectional, forces export south through Srananagh–Flagford, and the Group 3 constraint appears at a few hundred hours per year. Group 1's monitored element is a Letterkenny busbar section, which is not a separate bus in the kit; the nearest line proxies bind rarely. This is a WP2033 network with reinforcements; the 2024 network (tie rated 93 MVA) may bind more and is the one that matches the 2026 data. Not tested.

Implications for the brief. Rule 3 as written (kit LOPF with intact ratings) optimises against the wrong constraint. All four rules must be run against the same N-1 flows on the WDT's named elements, from the PTDF/LODF, on top of an unconstrained dispatch. That is cheaper than the LOPF anyway: the nodal optimum then becomes a small LP per hour (minimise spill subject to Σ SF_i c_i ≥ overload on each monitored element). The frequency of binding hours (2–6 % of the year in this test) also sets expectations: the year-to-date band rule has a few hundred events to work with, enough for a frontier, not enough to claim precision.

Effect size expectation, from `q5.log`: on a Donegal export constraint all Donegal stations sit at shift factors 0.36–0.51 and the Sligo side at 0.08–0.13. Inside CG1 the spread is 0.36–0.51, so the effectiveness-ordered rule can save at most ~30 % of the pro-rata spill there and several stations share one value, so ordering among them is arbitrary. Inside CG3 the spread is 4–6×, so that is where the frontier will be visible. Lead with CG3.

## 6. Scope for two days

Keep: measurement chart (corrected membership), three rules plus the band on CG3 and CG1, one synthetic year WP2033 seed 42, intact plus the two named contingencies, the frontier chart, one policy slide. Four people: one on the measurement and the group table, two on the rules engine and the N-1 flows, one on slides and the policy page.

Drop: all-island, N-1-1, ENTSO-E climate years, firm/non-firm burden table (name the six Donegal non-firm units on the policy slide instead), the WP2024 year unless it is generated on day 1 morning by the person doing the measurement.

Day 1: fix the tie (Link, `p_nom` 123), attach the year with the `p_min_pu` clip, run the unconstrained dispatch for the full year in 168-h chunks (about 25 min all-island at every-4th-hour sampling; a full year is roughly 90 min, start it early), compute PTDF/LODF once, check that T2102 and Flagford–Sligo bind. Type the two group tables. Implement rule 1 with the apply / deepen / release state machine from App. 1 — that state machine is the mechanism behind the measured inequality, so a per-hour pro-rata on availability would not be "today's rule". Rule 2 is a sort. Day 2: rule 4 with the band sweep, rule 3 as the per-hour LP, frontier chart, second seed if time, slides.

## 7. Recommended changes to the brief text

1. §0 and §5: replace the sixfold claim with the corrected table in section 4; add Tievebrack to the "say out loud" caveats.
2. §5: state CG1 ⊂ CG3 and drop open question 2 as answered.
3. §6: "Full synthetic year: have" → "have for WP2033; needs `p_min_pu` clip and profile check; no WP2024 year yet".
4. §7 Rule 3 and Contingencies: the optimum and all rules run on N-1 flows of the WDT elements via LODF; the tie is a capped link. Add this to §9 "Say out loud".
5. §7 Weather years: one year, two seeds. Remove ENTSO-E.
6. §8: replace all-island scaling with a one-line "future work".
7. §3: SEM-24-044a (May 2024) words the rule as pro-rata "with reference to that unit's nominal output" while the WDT document says "actual output"; cite both and say the model uses actual output per the WDT document.
8. Add to §9: the 2033 network includes reinforcements the 2026 data does not have; comparisons between the measured 2026 point and the simulated frontier are on different networks unless a WP2024 year is built.

## 8. Missing facts

Whether the event is 2 days or a week. Whether Tievebrack has been added to CG1 since Feb 2024. Whether the WP2024 network with a synthetic year binds on the CG3 elements (not run). The full-year (unsampled) binding-hour counts. Whether the kit's LODF for transformer branches matches PyPSA's BODF for star-point windings (validated in `TOOLKIT.md` for lines; not checked here for the T2102 windings). NI unit mapping. Official NPD and firm registers.
