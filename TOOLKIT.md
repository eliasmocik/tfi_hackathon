# Toolkit reference — kit API, PyPSA 1.3 facts, and the proven pipeline

Everything here was run on this Mac on 2026-09-07 (PyPSA 1.3.0, HiGHS). `proof_siting.py` in this folder
reproduces Tier 1, Tier 2, the class toggle and LODF end to end (NW in 5 s, all-island in 74 s).

```bash
TFI_KIT=<path>/Hackathons/grid_TF_Wind/participant-kit <kit>/.venv/bin/python proof_siting.py WP2033 all-island
```

## 1. Kit API (`participant-kit/gridkit.py`, `flowmath.py`)

| Call | Does | Gotcha |
|---|---|---|
| `gridkit.load(scenario, scope)` | loads `.nc`; `n.meta` has scenario/scope/anchor | generator `p_set` is NaN on purpose; the case dispatch is in `p_set_tytfs` |
| `gridkit.solve(n, **kw)` | `n.optimize` with HiGHS, quiet | pass `assign_all_duals=True` to get line duals |
| `gridkit.freeze_dispatch(n)` | copies `generators_t.p → p_set` | mandatory between `optimize` and `lpf`, else the slack supplies the island |
| `gridkit.line_loading(n)`, `gridkit.binding(n)` | `|p0|/s_nom`, hours at rating | **lines only**; transformers bind too: `n.transformers_t.p0.abs().div(n.transformers.s_nom, axis=1)` |
| `gridkit.dispatch_down(n)` | offered vs dispatched MWh per profiled generator | a generator without a `p_max_pu` column is invisible and runs at 100 % |
| `gridkit.add_line / remove_line / set_rating / add_battery` | edits | `add_line` x in ohms or from length (0.4 Ω/km) |
| `gridkit.placed_buses(n)` | buses with real coordinates | keeps 152 "neighbour mean" buses (drawing-only); flag `has_coordinates` |
| `flowmath.branches(n)` | lines + transformers with susceptance | pass as `branch_frame` to everything else |
| `flowmath.ptdf(n)` | branches × buses, uniform reference | slack-bus reference: `P.sub(P[ref], axis=0)` |
| `flowmath.shift_factors(n, circuit, reference="load")` | per generator | drop `carrier=="load shedding"`; per-bus SF = PTDF column differences |
| `flowmath.susceptibility / braess_candidates` | edge-to-edge dF/dB | Braess scan for reinforcement ideas |

## 2. PyPSA 1.3 facts that matter

- **Duals are empty after a plain `optimize()`**. Use `n.optimize(..., assign_all_duals=True)`. Then
  `n.lines_t.mu_upper` (≤ 0, dual of `s ≤ s_nom`), `n.lines_t.mu_lower` (≥ 0), same for transformers and
  generators. `|mu|` = EUR per MW of extra rating that hour (verified: +1 MVA on the binding NW line
  changed the objective by exactly −Σ|mu|).
- **Nodal price** `n.buses_t.marginal_price` is always populated. Verified identity per hour and
  sub-network: `λ_b − mean(λ) = −Σ_e PTDF(e,b)·(mu_upper+mu_lower)_e`, error 5e-10 all-island including
  transformers and the 3°/17° phase shifters. So Tier 1 can use LMPs directly.
- **Add a farm with a profile**: `n.add("Generator", name, bus=b, carrier="wind", p_nom=50,
  p_max_pu=<Series on n.snapshots>, marginal_cost=-1)`. The Series lands in `generators_t.p_max_pu`.
- **Contingency**: `pypsa.contingency` is gone. `n.determine_network_topology()`; `sn = n.sub_networks.obj[k]`;
  `sn.calculate_BODF()` → `sn.BODF` (diag −1). Kit-PTDF LODF `(PTDF@K)/(1−diag)` matches BODF to 1e-9.
  `n.lpf_contingency` **crashes** on both kit nets (one-bus sub-networks: Moy; 86221, GB_EWIC, GB_GREENLINK) — drop
  those buses or compute BODF per sub-network. SCLOPF is `n.optimize.optimize_security_constrained(snapshots, branch_outages=...)`.
- `n.lpf` ignores ratings and needs `p_set`; `n.optimize` builds a linopy model (KVL cycles, not PTDF).
- Plotting: `n.plot.map(bus_color=Series, bus_cmap=..., geomap=False)` works without cartopy; for the heatmaps the
  simpler route is `gridkit.placed_buses` + matplotlib scatter (example f), with `data/eirgrid_transmission.gpkg` as
  the line backdrop (EPSG:2157 → 4326). `n.statistics.curtailment(groupby=["bus","carrier"])` works post-solve.

## 3. Kit facts that overturn parts of the brief / spec

1. **Wind and solar `marginal_cost` ships as 0.0**, not −1. All wind at 0 = degenerate LP, the cut lands
   on an arbitrary farm. Set every wind/solar bid yourself before any Tier 2: existing farms −1, new farm by class.
2. **New farm at −1 ties with existing farms** and the tie-break is solver-arbitrary. Use a strict order
   (new class A at −0.99 or −0.5, B at −2, C at −3) and state it.
3. **The North-West scope cannot be Srananagh-split**: it is one bus wired at the 110 kV node, no transformer.
   The all-island network already has 5041 (110) / 5042 (220) with the 250 MVA transformer. Every boundary tie in
   the NW scope is pinned to its case MW, so all extra export is forced through Srananagh–Flagford. **Run NW
   results on the all-island network filtered to NW buses.** NW scope = sandbox only. Moy is an island in 2033.
4. **Candidate set on all-island**: drop `star:` buses (~100), link-end buses (GB_EWIC, GB_GREENLINK, 86221),
   converter buses (v_nom 150/260/365), import/export generators. 503 candidates remain.
5. **Transformers bind in the baseline** (Greenlink converter 75 h, T3464 20 h, EWIC 4 h). Include transformer
   duals in Tier 1.
6. **Must-run lower bounds survive from TYTFS** on 4 gas, 8 hydro, 41 "unknown" units (`p_min_pu` up to 0.78).
   They inflate surplus dispatch-down. `synthetic.binding()` zeroes them; the kit does not. Decide and state.
7. **STE rating** = 1.1 × RATE1 on most circuits → use `s_max_pu=1.1` for an emergency/N-1 variant.
8. Letterkenny–Strabane (`3581-89516-1`, the most-bound circuit all-island, 128 h) has a **scenario-dependent
   rating** (93/80/105/123 MVA) and sits behind a fixed-tap phase shifter. Say so when it shows up.
9. Line lengths are real (report.tex corrects the README). Sub-110 kV loads were folded to the nearest bus by
   least reactance; 23 % of demand had a runner-up bus.

## 4. Proven pipeline and numbers (WP2033, existing wind at −1)

**Baseline.** NW: 1 binding circuit (`5041-17010-2`, 57 h). All-island: 6 binding lines + 3 transformers,
LMPs from −15 to 157 EUR/MWh, 291 GWh of 1,136 GWh dispatched down.

**Tier 1** `exposure_b = Σ_h profile_b,h · Σ_e PTDF(e,b)·(mu+ − mu−)_e,h` (low = good).
- With one common profile it equals the LMP ranking exactly. With per-bus profiles it does not (Spearman 0.34 NW,
  −0.59 all-island) because the LMP carries the profile-weighted energy price. Use the PTDF-sum form, and
  **normalise by offered MWh** or weather dominates the ranking.
- NW: Corderry, Sligo, Glenree best; Tievebrack, Letterkenny, Ardnagappary worst. With one binding circuit the
  penalty is two-valued (Sligo side +0.58, Donegal −0.24); only the profile separates Donegal buses.

**Tier 2** (50 MW, nearest wind profile, class A):

| Net | Bus | Private (MWh/MW) | External (MWh/MW) | System |
|---|---|---|---|---|
| NW | Corderry (Tier-1 best) | 78.0 | −15.2 | 62.7 |
| NW | Tievebrack (Tier-1 worst) | 100.0 | −33.8 | 66.1 |
| All-island | 3464 (Tier-1 best) | 63.7 (44 % cut) | −14.6 | 49.1 |
| All-island | 5191 (Tier-1 worst) | 93.6 | −74.5 | 19.1 |

**Class toggle** at the worst bus: A-cut-first 66 / 25, A-tie 100 / 94, B and C 100 / 98 private; external cost
grows from 0 to −34 / −79. **The system index is class-invariant** (NW 66.1, all-island ~19). The class only
moves the cut between the new farm and its neighbours. That is the finding to plot.

**LODF.** Worst outage for the NW binding circuit is its parallel (`1701-5041-1`, LODF −1.0); prediction matches
brute-force removal to 1e-12. N-1 shift factor on Sligo side 0.58 → 0.71.

**Timing.** All-island: baseline 12 s, ~11 s per Tier-2 solve, LODF 2 s. 40 buses × 3 classes ≈ 22 min.

## 5. Two things the spec's validation must absorb

- **Occupied-bus check fails on all-island as written**: the Tier-1 top buses host 0 MW wind, yet the sign is
  verified. Tier 1 is a linearisation at the baseline and measures the congestion cost the farm *imposes*, not
  its own curtailment: bus 3464 ranks best on Tier 1 and then takes a 44 % cut at 50 MW because it creates new
  congestion. Report the Tier-1 vs Tier-2 misranking as a result, and run the occupied-bus check on the
  **Tier-2 system index**, not on Tier 1.
- The **Srananagh 21.6 → 1.7 MW** figure in the brief is the WP2024 low-wind case. On the WP2033 synthetic week
  the fold changes NW dispatch-down from 3.7 to 15.7 GWh. Not a small correction.

## 6. Weather pipelines (both work)

- Synthetic full year: `python synthetic.py build --case data/TYTFS2024_studyfiles/TYTFS2024_WP2033_V35.raw --year 2030 --seed 42 --out <dir>` (5 s; `--seed` = new weather year). Attach: `n.set_snapshots(pm.index)`, assign wind/solar columns of `p_max_pu` and `loads_t.p_set`, then `build_kit._fill_unprofiled` for the 82 unplaced units. Never assign hydro/thermal columns as `p_max_pu`.
- ERA5: `python profiles.py fetch --year 2023` (6 requests) then `profiles.py build --year 2023`. Offshore needs `--model era5` and the coordinates in `SOURCES.md` section E. No demand series: use Smart Grid Dashboard `demandactual`.
