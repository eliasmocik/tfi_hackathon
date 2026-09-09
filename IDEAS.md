# TPSA / TF Wind Hackathon 2026 — idea sheet

Source: `Hackathon_2026_Problem_Sheet-2.pdf`, `Wind-Dispatch-Tool-Constraint-Group-Overview_1.pdf`,
kit at `github.com/farrencc/Hackathons` (`grid_TF_Wind/participant-kit`), novogrid.com product pages.

## 0. What the kit actually gives us (drives what is feasible)

- 8 PyPSA networks: 4 TYTFS scenarios (WP/SV × 2024/2033) × 2 scopes (all-island ~700 buses,
  north-west 15 nodes). **WP2033 is the one with constraint** (42.6 GW connected vs 8.8 GW peak).
- 168 hourly snapshots per network. **Time series are synthetic** (spatially correlated random
  field, L = 400 km). Fine for ranking/relative results, useless for absolute MWh claims. Say so on the slide.
- DC power flow only: no voltage, no reactive, no losses, no inertia. So voltage-stability groups
  (e.g. West CG4 Cauteen, SW CG4 Ballylickey) and curtailment/SNSP are out of reach of this model.
- `flowmath.py` already has PTDF, edge-to-edge susceptibility, and `shift_factors()` (three
  reference conventions; ranking is stable across them). `gridkit.py` has `add_line`,
  `set_rating`, `add_battery`, `dispatch_down`, `binding`, `freeze_dispatch`.
- NW 15-node network: buses Ardnagappary, Binbane, Cathaleen's Fall, Clogher, Corderry,
  Croaghonagh, Drumkeen, Glenree, Letterkenny, Moy, Sligo, Sorne Hill, Srananagh 220, Tievebrack,
  Trillick. ~1.15 GW wind across them, 18 circuits, 91–210 MVA ratings. **No storage shipped.**
- Known trap: Srananagh folded into one node hides a 250 MVA transformer (up to 21.6 MW flow
  error). Split it back to 110/220 kV (16 nodes) if flows near Sligo/Srananagh matter.
- Kit uses a flat 5 % shift-factor threshold. EirGrid uses a per-violation threshold chosen at a
  "significant step change" in the SF list (Appendix 2 of the WDT doc). That gap is exploitable.

## 1. How EirGrid does it today (the thing to beat)

Per WDT doc Appendix 1 + 2 and Algorithm 0 in the brief:

1. Offline, low-load summer case, all renewables at max, EWIC exporting. Dispatch down
   conventional plant, sectionalise where possible. List residual N / N-1 / N-1-1 violations.
2. **One constraint group per violation.** For each node feeding the violation, perturb one farm
   by −10 MW, balance at a fixed remote conventional unit, measure Δflow on the monitored element
   → shift factor. Include nodes above a hand-picked threshold.
3. Real time: operator picks the predefined group + a total MW cut. WDT splits it **pro rata on
   current output** (not on effectiveness). Releases are pro rata on headroom.
4. Outages: manually maintained "temporary group" variants per outage condition (the doc lists
   these one by one for NW CG1 etc).

Three visible inefficiencies to attack:
- **Pro-rata split ignores effectiveness.** A farm with SF 0.9 and one with SF 0.3 in the same
  group get cut in proportion to output, so relieving X MW on the line costs more wind than needed.
- **Groups are static and per-line.** Membership drifts under outages and is patched by hand.
- **Threshold is judgement.** Include-or-exclude is binary; a farm at SF 0.29 vs 0.31 is treated
  completely differently.

## 2. Direction A — constraint group optimisation (problems 3.2 + 3.3)

### A1. Effectiveness matrix instead of one SF per group
Build the full matrix `E[farm, (element, contingency)]` = shift factor of every wind/solar farm
on every circuit under intact, every N-1 (via LODF from the PTDF), and selected N-1-1. Each farm
is now a vector, not a scalar. Then:
- **Cluster farms in E-space** (spectral clustering / Louvain on a |E|-similarity graph) →
  groups that are stable across contingencies. Compare cluster count and membership to
  EirGrid's published NW groups 1–3 (ground truth is in the WDT PDF, stations listed).
- **Correlation map** (3.2 bullet 1): plot |E| for a given circuit on the island map to show
  non-local effects; overlay the synthetic wind correlation field so you can see farms that are
  both electrically coupled *and* meteorologically coupled (those are the ones that bind together).
- Question "is SF the right metric": compare SF ranking vs. "MWh of dispatch-down actually
  avoided over the week when that farm is cut first" (from repeated LOPF). If rankings disagree,
  that is a finding.

### A2. Quantify the pro-rata penalty (headline number)
For each binding hour on a NW circuit, compute the MW cut needed under three split rules:
1. EirGrid pro-rata on output (Appendix 1 formula).
2. SF-weighted (cut farms in order of effectiveness).
3. LOPF optimum (`gridkit.solve`, what the kit already does).
Report wind MWh lost per rule over the week. "Pro-rata wastes X % more wind than
effectiveness-weighted dispatch" is a clean, defensible slide, and it feeds 3.3 (incentive
structure): the fairness-vs-efficiency frontier. Extend with priority / non-priority farms
(cut non-priority first, then priority) and show where that ordering costs efficiency.

### A3. Minimum group cover instead of one-group-per-line
Set-cover formulation: pick the smallest set of groups such that every violation (element,
contingency) has a group with ≥ X MW of relief capacity at the anchor hour. Shows whether
"one group per problematic line" is necessary (brief explicitly asks this).

### A4. Outage-robust groups, automated
Recompute groups for every N-1 outage in the region, tabulate membership churn. Output a
"core members / conditional members" table per group. This directly automates the manual
"Outage Condition 1..4" tables in the WDT doc. Easy to demo, obviously useful to a control room.

## 3. Direction B — where developers should build (3.1 bullet 4, 3.7)

This is the GridScreen / GridAtlas gap for Ireland (see §5). Two layers:

### B1. Fast screen: constraint exposure index per bus (closed form)
New farm at bus n adds `PTDF[e, n] · P` to circuit e. Exposure(n) = Σ_e max(PTDF[e,n], 0) ×
(hours circuit e is binding). Instant, all-island, no solver. Rank every bus. Also compute
"which existing constraint group would a new farm here fall into" (SF ≥ threshold).

### B2. Marginal verification with LOPF
For the top/bottom candidates, add a 10–50 MW wind generator with the local synthetic profile,
re-solve, measure marginal dispatch-down MWh per MW installed. Do the same for BESS
(`gridkit.add_battery` at each bus, measure reduction in constrained MWh). Also sweep MW to
show headroom decay: "first 20 MW fine, at 60 MW you are in NW CG1 and cut Y % of hours".

### B3. Output a developer-facing map
One map: dots = expected capture factor (1 − exposure), rings = BESS value per MW, colour =
group membership. That is the demo. Tie it to problem 3.7 by testing the hypothesis "battery
at the generation node is optimal" vs. battery at the constrained boundary (Srananagh 220,
Cathaleen's Fall). Expect the boundary to win for constraint, the gen node for surplus.

A and B share the same machinery (PTDF/LODF + LOPF loop), so one team can own the engine
and two people can own the two front ends.

## 4. Other ideas worth a look

- **Dynamic line rating (3.1 bullet 3).** Scale `s_nom` of each overhead line by a cooling
  proxy from the wind profile at its endpoints (high wind → cooler conductor → more headroom,
  exactly when constraint bites). Cheap to implement, likely large effect, physically motivated.
  Line-vs-cable is separable in the kit (reactance per km).
- **Braess paradox scan.** Example (e) already gives edge-to-edge susceptibility. Find
  reinforcements that *increase* loading on the constrained line, and the single best
  reinforcement per euro (use line length as a cost proxy).
- **Priority vs non-priority (3.1 last bullet).** Assign priority status to a subset (older
  REFIT farms in reality), re-run the split rules, map where priority ordering causes extra
  dispatch-down on non-priority farms.
- **Full-grid extension (3.4).** Same exposure index on all-island WP2033; include the
  interconnectors as controllable links (Moyle/EWIC/Greenlink are already Links).
- **Artery identification (3.8).** Edge betweenness / min-cut on the transmission graph,
  weighted by rating; flag single edges whose loss islands a region. The distribution gpkg
  files in `data/` allow a hospital-proximity overlay if someone wants the resilience angle.
- **Offshore concentration (3.10).** Add a 500 MW injection at one east-coast node, show how the
  effectiveness matrix and group structure changes vs. the same MW spread over 10 onshore nodes.

Out of reach with this kit (DC only, no inertia): curtailment/SNSP local effects (3.5),
synchronous condenser siting (3.6), voltage-stability groups. Don't pick those unless someone
brings a dynamic model.

## 5. Companies / positioning

- **NovoGrid** (Dublin). **Grid-Cast is not a wind-farm development tool**: it is congestion
  forecasting for energy traders (30-min intervals, 18 h horizon, API for balancing-mechanism
  bids). Their siting products are **GridAtlas** (map database of grid supply points, GB only,
  subscription) and **GridScreen** (site-specific connection + curtailment report, 10 working
  days, GB). **GridBoost** is reactive-power optimisation on live farms.
  → Nobody offers the Irish, open, instant version of GridScreen driven by the actual
  constraint-group logic. That is Direction B's pitch.
- **EirGrid WDT doc** is the ground truth for group membership (NW CG1: Ardnagappary, Binbane,
  Lenalea, Sorne Hill, Trillick; NW CG2: Meentycat; CG3: Sligo–Flagford). Use it as the
  validation set for Direction A: does your algorithm reproduce their groups, and where it
  differs, can you argue why yours is better?

## 6. Suggested day-1 plan

1. Clone + run the kit (`python examples/f_shift_factors.py WP2033 north-west`), confirm the
   NW groups roughly match the WDT PDF.
2. Split Srananagh to 16 nodes if flows there matter.
3. Build the effectiveness matrix E (intact + all N-1 via LODF). Everything else hangs off it.
4. Fork: one pair on A2 (pro-rata penalty number), one pair on B1 → B3 (exposure map).
5. Slide 1 = the headline number, slide 2 = the map, slide 3 = "here is what EirGrid does
   today and what changes".
