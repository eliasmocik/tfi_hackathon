# STATUS — resume point

Updated automatically at each checkpoint. Anyone can pick the project up from here; the specification is `MASTER.md`.

## Done

**Phase 0 — decisions.** `MASTER.md` §0 (fixed), `formula-decisions.md` (12 formula choices with sources), `VALIDATION_prorata_brief.md` (model validation, the tie artefact, the corrected measurement).

**Phase 1a — measurement (MASTER §6).** `src/measurement.py` → `out/measurement_*.csv`, `out/MEASUREMENT_NOTES.md`.
Reproduces the earlier hand computation exactly (max diff 9e-17 on every ratio). CG1 unit spread 4.3–9.8 % (2.27×, Jain 0.927, Gini 0.157); CG3 15 units, same range, Jain 0.950, Gini 0.130; Booltiagh 4 units at one station 2.9–7.0 %.

**Phase 1b — engine (MASTER §2, §3).** `src/engine_prep.py`, `src/run_engine.py` → per case: `_group_units.csv`, `_shift_factors.csv`, `_node_table.csv`, `_lodf.csv`, `_baseline_p.parquet`, `_avail.parquet`, `_flows.parquet`, `_overloads.csv`, `_overload_stats.json`, `ENGINE_NOTES.md`.
Overloads on Flagford–Sligo 110 kV under loss of Flagford–Srananagh 220 kV:
- WP2024s42 (main, 8,760 h): 1,308 h over, 34,797 MWh, max 84 MW over a 121 MVA rating. Flagford transformer windings never over.
- WP2033s42 (4,380 h, every 2nd hour): 712 h over on the line, plus 425 h and 344 h on the two transformer windings.
- WP2033s43: same shape (see its `_overload_stats.json`).

**Phase 2 — rules, metrics, comparison, robustness, RESULTS (MASTER §4, §5, §7, §8, §9).** `src/run_phase2.sh` runs everything in ~1 min from the engine's files:
`src/check_sf_convention.py` (sign convention check → `_sf_convention_check.csv`), `src/rules.py` (rules 1/2/3/1N and the band sweep → `_cuts_<rule>.parquet`, `_<rule>_residual.csv`, `_postcut_violations.csv`, `_rule_hourly.csv`, `_rules_summary.json`), `src/metrics.py` (→ `_summary.csv`, `_farm_r.csv`, `_station_r.csv`, `_assertions.csv`), `src/charts.py` (frontier and station-bar PNGs), `src/compare.py` (→ `comparison_*.csv`), `src/robustness.py` (→ `robustness*.csv`), `src/results_md.py` (→ `out/RESULTS.md`).
All assertions pass in all three cases (band ∞ = rule 2 element-wise; Σc rule 3 ≤ rule 2 ≤ rule 1 per hour; no residual hours). The WP2033s43 §3.4 stage had never been run; `src/engine_notes.py` now runs it when the stats file is missing.
Headline (WP2024s42, `out/WP2024s42_summary.csv`): see `out/RESULTS.md` §4–§5. The measured-vs-simulated station rank correlation is negative and not significant (`out/comparison_stats.csv`).

## Next — Phase 3 (MASTER §10)

Independent verification by a separate agent → `verify/VERIFICATION.md`. Inputs: everything under `out/`; the checks listed in MASTER §10 items 1–10.

## Phase 2 plan as executed (kept for reference)


1. `src/rules.py`: rule 1 pro rata on availability (bisection on φ), rule 2 effectiveness order (node order, pro rata inside tied nodes), rule 3 per-hour LP (`scipy.optimize.linprog`, HiGHS), rule 4 band sweep b ∈ {0,1,2,3,5,10,∞} with the year-to-date tally, rule 1N non-priority-first. Inputs are the parquet/CSV files above; nothing needs re-solving.
2. `src/metrics.py`: per farm, per station, per group; Jain, Gini, worst-farm, D, D_ratio, price of fairness. → `out/<case>_summary.csv`, `_farm_r.csv`, `_station_r.csv`.
3. Charts (§5), comparison (§7), robustness (§8) → `out/RESULTS.md`.
4. Phase 3 verification (§10) → `verify/VERIFICATION.md`.

## Regenerating the inputs that are not in git

- Raw SEM-O pulls (BM-037, BM-096, BM-101): `data/README.md` has the open JSON API and `data/semo_nw_units/pull.py`. Rolling ~3-month retention, so an old window cannot be re-pulled — keep the local copies.
- Synthetic years and the WP2024 wind-in network: `data/synth_out_extra/README.md`, `kit_build/build_wp2024_windin.py`. Needs the organisers' repo (github.com/farrencc/Hackathons) for `psse.py`, `pypsa_net.py` and the raw TYTFS cases.
- Baselines: `python project/src/run_engine.py <case>` — WP2024s42 ~25 min, the WP2033 cases ~45 min each. Per-chunk results are saved, so a killed run resumes.
