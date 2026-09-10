# HANDOFF — pro-rata constraint-group project

For a Claude agent picking this up on different hardware. Written 2026-09-09. Everything here is checked against the files; nothing is from memory.

---

## 1. What the project is

TPSA / TF Wind Hackathon 2026 (Trinity College Dublin, problem sheet §3.3). EirGrid manages transmission overloads by sending one joint MW cut to a predefined **constraint group** of wind farms and splitting it **pro rata on output**. The shift factor (each farm's MW of relief per MW cut) is computed to *build* the group and then discarded at the split. This project measures what that costs, and proposes a middle rule.

Four rules are compared over a simulated year on **North-West Constraint Group 3**:

1. **Pro rata** — today's rule.
2. **Effectiveness order** — cut the highest shift factor first.
3. **Nodal optimum** — per-hour LP, the least-spill floor.
4. **The band rule** (the contribution) — effectiveness order, but only among farms whose *year-to-date* curtailment ratio is within `b` percentage points of the group average; farms above the band are protected until others catch up. `b` sweeps from 0 (≈ today) to ∞ (pure effectiveness), tracing an efficiency-vs-fairness frontier.

Plus a labelled sensitivity, **rule 1N** (non-priority farms cut first — SEM-24-044's stated intent, not live).

The novelty claim, verified against the literature: nobody combines a cumulative-ratio fairness gate with shift-factor ordering inside existing TSO constraint groups, without new payments.

---

## 2. Where everything is

**GitHub: `https://github.com/eliasmocik/tfi_hackathon` (private).** Owner Elias Mocik, elias.mocik@icloud.com. Two commits: the initial import and a Phase-2 checkpoint. Working tree clean as of the handoff.

**Local clone on Elias's Mac:** `~/Desktop/aiOS/tfi_hackathon`.

Read in this order: `README.md` → `project/MASTER.md` (the specification everything follows) → `project/STATUS.md` (resume point) → `project/out/RESULTS.md` (the findings) → `project/out/DECISIONS_LOG.md` (every judgement call made while executing).

```
tfi_hackathon/
  README.md  PUSH_TO_GITHUB.md  .gitignore
  Hackathon_2026_Problem_Sheet-2.pdf          the brief
  Wind-Dispatch-Tool-Constraint-Group-Overview_1.pdf   EirGrid's WDT document
  prorata_project_brief.md                    the original idea (superseded by MASTER §0 where they differ)
  IDEAS.md  SPEC.md  SOURCES.md  TOOLKIT.md   earlier exploration
  participant-kit/         organisers' PyPSA kit: networks/, gridkit.py, flowmath.py, test_kit.py
  problem_3_1/             earlier per-bullet scripts for sheet §3.1 (superseded; see §9 caveat below)
  kit_build/               organisers' build tooling + our build_wp2024_windin.py
  research/                verification notes, papers/ (extracted text), n1_gonogo/ (the go/no-go test)
  data/                    SEM-O pulls, unit maps, WDT text, synth_out_extra/
  project/                 THE WORK
    MASTER.md  STATUS.md  sync.sh  formula-decisions.md  VALIDATION_prorata_brief.md
    src/     measurement.py engine_prep.py run_engine.py check_sf_convention.py
             rules.py metrics.py charts.py compare.py robustness.py results_md.py
             engine_notes.py run_baselines.sh run_phase2.sh
    out/     all results (see §5)
    verify/  empty — Phase 3 goes here
    kit/ years/ data/   local copies the scripts read (git-ignored, see §7)
```

`project/sync.sh` commits and pushes; run it as `bash project/sync.sh ["message"]` from anywhere in the repo. **Only Elias can push** — the assistant session has no GitHub write credentials (a session is bound to its repositories at creation; this one was created against a local folder). Checkpoint into the folder, then ask him to run sync.

---

## 3. State: done, and what is next

### Done

**Phase 0 — decisions.** `MASTER.md` §0 lists the fixed decisions. `formula-decisions.md` gives twelve formula choices with primary sources and a certainty label (settled / common practice / judgement call). `VALIDATION_prorata_brief.md` is the model validation that caught the tie artefact and corrected the empirical baseline.

**Phase 1a — measurement of the real 2026 data** (`src/measurement.py` → `out/measurement_*.csv`, `out/MEASUREMENT_NOTES.md`). Reproduces the earlier hand computation to 9e-17 on every ratio.

**Phase 1b — engine** (`src/engine_prep.py`, `src/run_engine.py`). Network preparation, unconstrained baseline dispatch, PTDF/LODF, shift factors, overload series, for three cases.

**Phase 2 — rules, metrics, charts, comparison, robustness, RESULTS** (`src/run_phase2.sh`, ~1 minute from the engine's saved files).

### Next

**Phase 3 — independent verification.** `MASTER.md` §10 lists ten checks; the output is `project/verify/VERIFICATION.md`. It must be done by an agent that does **not** import `src/rules.py`, `src/metrics.py`, `src/measurement.py`, `src/compare.py` or `src/robustness.py` — the point is independent re-derivation from the saved data files and raw inputs. Importing `kit/flowmath.py`, `pypsa`, and `src/engine_prep.py`'s `prepare()` for network preparation is allowed. The single most valuable check is §10 item 5's second half: re-implement the band rule for `b = 3` over the first 500 hours from scratch and compare with `out/WP2024s42_cuts_band3.parquet` — that tests the rule's logic, not just the bookkeeping.

A first attempt at Phase 3 was cut off by a rate limit after ~15 tool calls and produced nothing; `verify/` is empty. Start fresh.

**After Phase 3:** the presentation, which is explicitly out of scope of MASTER.md.

---

## 4. The findings so far

All from `project/out/WP2024s42_summary.csv` (main case: WP2024 network with wind switched in, full synthetic year seed 42, 8,760 h, 51 cuttable farms, 686 MW).

| rule | dispatch-down % of available | ratio to today | Jain (farms) | Gini |
|---|---|---|---|---|
| rule 1 pro rata (today) | 8.343 | 1.000 | 0.992 | 0.048 |
| rule 2 effectiveness | 7.141 | 0.856 | 0.209 | 0.811 |
| rule 3 nodal optimum | 7.141 | 0.856 | 0.227 | 0.796 |
| rule 1N non-priority first | 8.416 | 1.009 | 0.379 | 0.428 |
| band 0 pp | 8.344 | 1.000 | 1.000 | 0.001 |
| band 1 | 8.193 | 0.982 | 0.959 | 0.076 |
| band 2 | 8.094 | 0.970 | 0.883 | 0.177 |
| band 3 | 8.026 | 0.962 | 0.789 | 0.279 |
| band 5 | 7.936 | 0.951 | 0.609 | 0.444 |
| band 10 | 7.742 | 0.928 | 0.381 | 0.645 |
| band ∞ | 7.141 | 0.856 | 0.209 | 0.811 |

**Headline: pro rata spills 16.8 % more wind than necessary.** The band recovers 26 % of that excess at `b = 3` while keeping Jain at 0.79 (in the 2033 cases the same band recovers 46–53 %, so the *recovery share* is not a stable result — the shape of the curve is).

Other findings:
- Rule 2 equals rule 3 exactly in the main case (only one row ever binds, so greedy = LP), but their Jain differs (0.209 vs 0.227) because the LP splits the last partially-cut node arbitrarily rather than pro rata.
- **Rule 1N spills *more* than pro rata** in all three cases (+0.07 to +0.28 pp): the non-priority fleet has a lower capacity-weighted shift factor, so clearing through it first is less effective per MW. That is a real finding about SEM-24-044's stated intent.
- Post-cut violations are zero for rule 1 but 7–12 hour-branch pairs for rules 2/3 and wide bands in the WP2033 cases, almost all on Drumkeen–Clogher 110 kV: concentrating cuts re-routes flow. Nothing is ever pushed onto a monitored row.
- **The measured-vs-simulated station rank correlation is negative and not significant** (Spearman −0.567, n = 9, p = 0.112; `out/comparison_stats.csv`). The simulated pro-rata spread is tiny (station max/min 1.18) against a measured 1.64, so the real-world spread comes from mechanisms the model does not have: overlapping groups, outage variants, deepening on output, and units that were offline. Report this as a limitation, not a validation failure.
- 2026 measurement: CG1 5 units, constraint-only 4.3–9.8 % (2.27×, Jain 0.927, Gini 0.157); CG3 15 units, same range, Jain 0.950, Gini 0.130; four Booltiagh units at one station (identical shift factor) 2.9–7.0 %.

---

## 5. The files under `project/out/`

Per case (`WP2024s42`, `WP2033s42`, `WP2033s43`):

| file | what it holds |
|---|---|
| `_group_units.csv` | the group's generators with class P / N / U and the match to EirGrid's unit list |
| `_shift_factors.csv` | raw signed SF per generator on the four monitored rows |
| `_node_table.csv` | the WDT-style node table with the "significant step change" |
| `_lodf.csv`, `_lodf_dcpf_check.csv` | LODF and its independent check |
| `_ptdf_full.parquet`, `_ptdf_rows.parquet`, `_ptdf_summary.json` | PTDF and the reference-bus test |
| `_baseline_p.parquet`, `_avail.parquet`, `_flows.parquet` | unconstrained dispatch, availability, all branch flows |
| `_overloads.csv`, `_overload_stats.json` | signed flow F and overload O per hour per monitored row |
| `_cuts_<rule>.parquet` | the cut vector, hour × generator, MW, for each of the 11 rules |
| `_<rule>_residual.csv`, `_rule3_status.csv`, `_rule1N_tiers.csv`, `_band<b>_widen.csv` | per-rule diagnostics |
| `_rule_hourly.csv`, `_rules_summary.json` | hourly totals and the rule-level summary |
| `_summary.csv`, `_farm_r.csv`, `_station_r.csv` | the metrics of MASTER §5 |
| `_assertions.csv` | the 15 internal assertions (all pass in all cases) |
| `_postcut_violations.csv`, `_postcut_by_branch.csv`, `_nw_branches.csv` | the §4.6 post-cut check |
| `_sf_convention_check.csv` | the sign-convention proof |
| `_frontier_jain.png`, `_frontier_gini.png` | the frontier charts |

Shared: `measurement_*.csv`, `measurement_bars.png`, `comparison_*.csv`, `robustness*.csv`, `WP2024s42_station_bars.png`, `RESULTS.md`, `ENGINE_NOTES.md`, `MEASUREMENT_NOTES.md`, `DECISIONS_LOG.md`.

`RESULTS.md` has 12 sections and cites, for every number, the file it came from. Nothing in it was typed by hand.

---

## 6. Fixed decisions — do not reopen

From `MASTER.md` §0, each settled after research or testing:

| | |
|---|---|
| **Simulated group** | NW Constraint Group 3 only. Group 1's monitored element is a *Letterkenny busbar section*, which the kit's model does not represent, so nothing ever overloads there; Group 1 appears in the measurement only. CG3 contains every CG1 station anyway. |
| **Main case** | `kit/WP2024_all-island_windin.nc` + `years/TYTFS2024_WP2024_V35_synthetic_2030_seed42_*`, all 8,760 h. |
| **Sensitivities** | `WP2033_all-island.nc` with seed 42 and seed 43, every 2nd hour. |
| **The tie** | Line `3581-89516-1` (Letterkenny–Strabane) **must** be replaced by a `Link` with `p_nom` = the line's `s_nom`, `p_min_pu = -1`. Without this, all North-West export runs through a fixed-tap phase-shifter the kit itself flags as unmodelled, and the real WDT constraints never bind. |
| **Contingency** | Loss of `2522-5042-1` (Flagford–Srananagh 220 kV). |
| **Monitored rows** | `2521-4981-1` (Flagford–Sligo 110 kV, 121 MVA) post-contingency and intact; the two Flagford 220/110 kV transformer windings `T2522-2521-25221-1-w1` and `T2522-2521-25222-2-w1` post-contingency. |
| **Shift-factor reference** | one fixed remote conventional bus (EirGrid's own procedure; AEMO the same). |
| **Today's rule** | per-hour pro rata **on availability** — rebalancing has been live since 26 Nov 2025 and the whole 2026 measurement window sits under it. The pre-2025 output-based apply/deepen/release state machine was dropped. |
| **Tally / band centre / fallback** | `r_i` = cumulative cut ÷ cumulative availability; centre = availability-weighted group mean; widen one farm at a time by ascending `r_i`, never fall back to pro rata. |
| **Metrics** | Jain on the chart, Gini and worst-farm in the table; dispatch-down as % of available energy plus the ratio to rule 1. No euro, ever. |
| **Comparison** | station level. |

`formula-decisions.md` gives the source for each. The two genuine judgement calls, which must be stated on any slide: the band centre, and one-at-a-time widening.

---

## 7. Environment and data

Python 3.11+. Installed versions here: pypsa 1.3.0, highspy 1.15.1, pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, pyarrow 25.0.1, matplotlib 3.10.9, netCDF4 1.7.4, geopandas 1.1.4.

```bash
pip install pypsa highspy pandas numpy scipy pyarrow matplotlib netCDF4
```

**These are git-ignored and must be present locally** (`project/data/`, `project/years/`, `project/kit/`, and the repo's own `data/`):

| not in git | size | how to get it |
|---|---|---|
| `BM-037_dispatch_instructions_2026-06-07_to_09-05.csv` | 22 MB | SEM-O open JSON API, `data/README.md` + `data/semo_nw_units/pull.py`. **Retention is ~3 months rolling — the June–September 2026 window may no longer be pullable. Keep the local copies; they are the only ones.** |
| `BM-101_nw_units.csv`, `BM-096_nw_units.csv` | 10 + 8.5 MB | same |
| synthetic years (`years/*_p_max_pu.csv`, `*_loads_p_set.csv`) | 166 MB | `kit_build/` + the organisers' repo `github.com/farrencc/Hackathons` (needs `psse.py`, `pypsa_net.py`, the raw TYTFS cases). Gzipped copies are in `data/synth_out_extra/`. |
| `WP2024_all-island_windin.nc` | 1 MB | `kit_build/build_wp2024_windin.py`, same prerequisites. Also gzipped in `data/synth_out_extra/`. |
| `*.parquet` under `out/` | ~500 MB | regenerate: `python project/src/run_engine.py <case>` — 25 min for WP2024s42, ~45 min each for the WP2033 cases. Per-chunk results are saved, so a killed run resumes. |

Everything else — all code, all CSV/JSON/PNG results, all notes — **is** in git.

---

## 8. Traps that cost hours here. Do not rediscover them.

1. **The synthetic year's thermal availability falls below the network's static `p_min_pu`**, so the LOPF is infeasible unless you clip per hour: `p_min_pu[t] = min(static p_min_pu, p_max_pu[t])` for every generator with a year column. 42–80 units per case.
2. **Do not scale `s_nom` to lift ratings.** In PyPSA a transformer's reactance is per-unit on its own `s_nom`, so multiplying `s_nom` by 100 divides every transformer impedance by 100 and makes the solved flows inconsistent with the PTDF. Set `s_max_pu = 100` instead. (`DECISIONS_LOG.md`, `[engine]`.)
3. **The kit's shipped WP2024, SV2024 and SV2033 networks carry no wind fleet** (10 MW or less): the TYTFS winter-peak case flags 374 wind and 36 solar records `STAT = 0` and the converter drops them. Only WP2033 is usable as shipped. `build_wp2024_windin.py` adds those records back with `p_min_pu = 0` — a deliberate deviation from the kit that must be stated on any slide using the main case.
4. **The tie replacement (§6) is not optional.** Without it the WDT's monitored elements never overload in a whole year, and all the model's dispatch-down lands on an artefact.
5. **Never use BM-086 "MeteredMW"** for dispatch-down: it is energy per half-hour at the meter, net of the farm's own consumption, and sits below the dispatch quantity even in unconstrained hours — it inflates dispatch-down 3–4×. Use BM-096 `DispatchQuantity`.
6. **Tievebrack is not in NW Constraint Group 1** in the Feb 2024 WDT document. An earlier draft included it, which turned a 2.3× spread into a false "sixfold spread". Check group membership against `data/eirgrid-wdt-constraint-group-overview-2024.txt` §3.1 and §3.3, not against memory.
7. **CG1 ⊂ CG3** (intact network). The overlap in the North-West is nested, so one year-to-date tally per farm suffices — there is no "two different group averages" problem.
8. Kit traps the organisers document and that still bite: `gridkit.freeze_dispatch` between `optimize` and `lpf`; buses at 0°N 0°E (use `gridkit.placed_buses`); **a generator with no `p_max_pu` profile silently runs flat out at 1.0**.
9. **Sign convention.** `out/<case>_shift_factors.csv` holds *raw signed* PTDF differences in PyPSA `p0` orientation. The effective shift factor is `SF_eff = sign(F_m,h) · SF_raw`, so that a positive value means a cut relieves the row. This was verified numerically (1 MW cut at each CG3 bus reduces |F| by exactly `SF_eff`, max deviation 1.3e-14) and is recorded in `_sf_convention_check.csv`. Every farm in the group has `SF_eff > 0` on every row that is ever over, in all three cases.

---

## 9. Open issues and honest caveats

- `problem_3_1/` contains earlier scripts whose North-West numbers are built on the un-replaced tie, so **they are artefacts** and must not be quoted. `VALIDATION_prorata_brief.md` §5 explains why.
- Priority classification matches only 51 of 66 units (77 %); unmatched units default to class P per MASTER §2.1. Several are near-misses listed in `ENGINE_NOTES.md` (aggregate capacities, 30.5 vs 30.1 MW). The official non-priority list is not public — this is EirGrid's own commissioning-date proxy.
- The weather is synthetic. **Only ratios and ranks are reportable**; no absolute GWh, and every chart must name the seed.
- One contingency is modelled where the real tool has many outage variants.
- Cuts are balanced at the reference bus; nothing else in the dispatch responds. Stated as an assumption.
- WP2033 borrows 82 profiles / 7,770 MW from nearest neighbours, which makes those pairs perfectly correlated when they should not be.
- The tie link sits at its cap in 100 % of hours in every case — worth a sentence in any write-up.
- The robustness thresholds in `robustness_statements.csv` were chosen after seeing the main case; a statement counts as a result only when `holds_in_all` is True.

---

## 10. Working agreement to keep

- **No number is ever typed by hand.** Every figure in a document is printed by a script from a saved file, and the file is named next to it. `src/results_md.py` regenerates `RESULTS.md` entirely.
- **Every unspecified choice gets one line in `out/DECISIONS_LOG.md`**, prefixed with the phase (`[measurement]`, `[engine]`, `[rules]`, `[verify]`).
- **Checkpoint after every step, not every phase**: write code, outputs and notes into the folder, update `STATUS.md`, then tell Elias to run `bash project/sync.sh`. Work that lives only in a sandbox is lost when the session ends.
- Elias prefers short answers and dislikes padding. He is a first-year engineering student at Trinity — competent in Python and maths, no power-systems background, so define jargon once.
- Judges include EirGrid staff who wrote the tool being analysed. The framing is "same groups, same tool, one formula changed" — never "your fair rule is unfair".
