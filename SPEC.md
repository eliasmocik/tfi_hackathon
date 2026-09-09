# Project spec — Locational value of new wind capacity on the Irish grid

TPSA / TF Wind Hackathon 2026. Problem sheet items 3.1 (bullet 4: where should developers locate) and 3.7.

## 1. Goal

For every transmission bus in Ireland, answer: **if a new wind farm connected here, how much of its energy
would be dispatched down, and how much would it push onto its neighbours?** Show that the two answers
disagree, and where.

## 2. Product

1. **Two heatmaps** of Ireland (and a North-West zoom), one per index, buses coloured by rank:
   - **Private index** = MWh delivered by the new farm per MW installed. The developer's view.
   - **System index** = (MWh delivered by the new farm + change in MWh delivered by every existing
     renewable) per MW installed. The grid's view.
2. **Private-vs-system scatter**, off-diagonal buses named. The policy finding: sites that look good to a
   developer and are bad for the system.
3. **Farm-type toggle**: every result recomputed for a new farm of class A, B or C (section 5).
4. Optional, in order: capacity sweep (20/50/100/200 MW, rank reordering), N-1 version of the map,
   seed/weather-year sensitivity table.

Everything is presented as **ordinal** (ranks, relative indices). No euro. No absolute GWh unless the
weather source and scenario are printed next to the number.

## 3. Requirements

- Runs from the participant kit (PyPSA + HiGHS) with no proprietary data.
- Candidate sites = existing transmission buses (110 kV+). Stated restriction.
- Every candidate farm gets an explicit output profile (kit defaults a missing profile to 100 %).
- One shift-factor reference convention, stated once, never mixed.
- North-West numbers come from the **all-island** network filtered to NW buses (it already has the Srananagh 110/220 split and free boundary ties). The 15-node NW scope is a sandbox: it cannot be split, and its pinned ties force all export through one transformer.
- Sign of the shift factor kept: buses that *relieve* a congested circuit must be visible.
- Two tiers of computation:
  - Tier 1 screen, closed form: for bus b, exposure = Σ over circuits e and hours h of
    shadow price of e at h × SF(b,e) × farm output at h. One matrix product after one baseline solve.
  - Tier 2 confirm: for the top and bottom ~20 buses, add a real generator, re-solve, measure directly.
- Occupied-bus check before anything goes on a slide, run on the **Tier-2 system index** (Tier 1 is a
  linearisation and its top buses can be empty for a real reason). High-ranked buses should mostly already host wind.

## 4. Assumptions (say each one out loud on the slide)

1. **Per-farm dispatch-down against actual thermal limits** (what the kit's LOPF does). Constraint groups
   are treated as an approximation that converges to this. Results are an **upper bound** on achievable
   performance. Needs telemetry to every farm and per-farm compensation; "no network capital", not "no capital".
2. **DC power flow**: no voltage, reactive, losses or inertia. Voltage-stability groups and SNSP curtailment
   are out of scope.
3. **Ratings** are TYTFS planning values, one per circuit per scenario, not seasonal or dynamic limits.
4. **Weather**: either the kit's synthetic week (ordinal results only) or a real ERA5 year via Open-Meteo
   (reachable; 6 requests/year; 82 unplaced units incl. offshore need hand coordinates).
5. **Costs** are placeholders; only dispatch *order* and differences between solves are meaningful.
6. Interconnectors are fixed-efficiency links with no market coupling.
7. Scenario: WP2033 network is primary. Others are rating sensitivities, never merged into one ranking.

## 5. Farm control classes (maps onto EirGrid's real categories)

| Class | Real-world category | Dispatch-down behaviour | Model rule |
|---|---|---|---|
| **A controllable** | EirGrid Category (ii): passed remote setpoint test, responds in 10 s, 0 MW to full | Cut first, via Wind Dispatch Tool setpoint | existing farms bid −1, new A farm −0.99 (kit ships wind at 0: set every bid explicitly, avoid ties) |
| **B priority** | Priority-dispatch units under SEM-11-062 (still Category (ii)) | Cut only after all non-priority farms in the corridor; SNSP curtailment still applies. "Immune" does not exist | wind bid −2 (cut after A) |
| **C uncontrollable** | Category (i) or non-categorised: <5 MW, pre-Grid-Code, or failed controllability | No setpoint; only lever is opening the breaker, all-or-nothing | wind bid −3 (cut last); any cut flagged as a breaker trip |

Effects to show (verified on the kit): the **system index is class-invariant**; the class only moves the cut
between the new farm and its neighbours. A class-B or C farm scores well privately and pushes the whole cut
onto class-A neighbours. The A/B/C toggle is what makes the private/system divergence visible.

Source for existing farms' class: BM-037 (units that receive LOCL/CURL instructions are A or B; metered
units never instructed are C). A-vs-B needs EirGrid's non-priority-dispatch list (not yet obtained).

## 6. Data

| Item | Status | Source |
|---|---|---|
| Network: 8 PyPSA nets (4 TYTFS scenarios × all-island / north-west), ratings, reactances, lengths, coordinates | **have**, all 22 kit self-checks pass | `github.com/farrencc/Hackathons` participant kit |
| Ratings: every line and transformer rated (740/755 from RATE1, 15 couplers bounded) | **have** | kit `lines.csv`, `s_nom_source` |
| Synthetic weather, 168 h per scenario | **have** | kit |
| Real weather, ERA5 hourly, full year | **available**, not yet fetched | `profiles.py fetch --year 2023` (Open-Meteo) |
| Raw TYTFS PSS/E cases (for a full synthetic year) | **have** | repo `data/TYTFS2024_studyfiles/` |
| Real constraint-group membership, incl. outage variants | **have** (text tables) | EirGrid WDT Constraint Group Overview PDF |
| Empirical groups + firing frequency (LOCL batches) | **have**, 3 months | SEM-O BM-037, `data/BM-037_*.csv` |
| Actual dispatch-down per unit per half hour | **have**, 3 months | SEM-O BM-101 minus BM-086 (API in `data/README.md`) |
| Unit code → name, transmission station, kV (233 IE units) | **have** | `data/semo_unit_map_IE.csv` (from SEM-O CLAF 2025/26) |
| NI unit mapping (79 units) | **have** | SEM-O NI CLAF 2025/26, SONI TLAF 2026/27 xlsx (see SOURCES.md) |
| Priority / non-priority / uncontrolled status per farm (846 units, with node) | **have** (EirGrid's own assumption: priority = connected before 2019-07-04) | EirGrid ECP-GSS-1 Constraint Analysis Excel, `data/eirgrid_gss1_res_units.csv` |
| EirGrid per-node dispatch-down forecast (200 nodes, 2030/2035, 11 scenarios) — validation target for the private index | **have** | `data/eirgrid_gss1_node_results.csv` (see SOURCES.md C2) |
| Controllability category per farm (i)/(ii)/(iii), IE + NI, 291 plants | **have** | EirGrid Controllability Status Update June 2026 (see SOURCES.md) |
| Observed per-circuit loadings | **missing**; congestion hours are a model output, say so | — |

## 7. Validation

- Reproduce kit example (f) before trusting new code.
- Model reproduces EirGrid's North West Group 1 from shift factors (done: Ardnagappary, Binbane, Sorne Hill,
  Trillick, Tievebrack/Lenalea).
- Occupied-bus check (section 3).
- Tier 1 vs Tier 2 agree in sign for the clearest cases; misrankings are reported, not hidden.
- All-island vs NW-scope comparison reported (the Srananagh fold moves NW dispatch-down 3.7 → 15.7 GWh on WP2033, not the 21.6 MW → 1.7 MW quoted for WP2024).
- Re-run the final ranking on a second seed or weather year; report which buses move.

## 8. Out of scope

Curtailment/SNSP local effects, synchronous condenser siting, voltage-stability groups, euro figures,
battery MWh sizing, land/planning suitability of sites.
