# tfi_hackathon — the price of pro-rata

TPSA / TF Wind Hackathon 2026. Cost of EirGrid's pro-rata constraint-group split versus effectiveness-ordered dispatch, and a year-to-date "band" rule between them, measured on North-West Constraint Group 3.

Start here: `project/MASTER.md` (the full specification), then `research/validation-prorata-brief-2026-09-08.md` and `research/formula-decisions-2026-09-09.md`.

Headline results, in the order a reader wants them:
- `project/out/EVIDENCE_PACK.md` — the argument, consultation-shaped.
- `project/out/WP_RESULTS.md` — the equal-relief replay on **real** 2026 data. Pro rata spilled 8.57 % more than an effectiveness-ordered cut delivering identical flow relief.
- `project/out/RESULTS.md` — the synthetic-year simulation (the earlier, weaker line of evidence; keep for the frontier shape).
- `project/verify/VERIFICATION.md` — the ten independent checks of MASTER §10, and every discrepancy found (D1–D9).

Layout
- `participant-kit/` organisers' kit (networks, flowmath, gridkit). Make a venv: `python -m venv .venv && pip install -r requirements.txt`.
- `project/src/` our code: `measurement.py` (2026 SEM-O data), `engine_prep.py` + `run_engine.py` (network prep, baseline dispatch, PTDF/LODF, overloads), rules to follow.
- `project/out/` results (CSV/JSON/PNG/notes). Large parquet tables are not in git; regenerate with `python project/src/run_engine.py <case>`.
- `data/` inputs. Files over ~20 MB are git-ignored; `data/README.md` says how to pull them from SEM-O, `data/synth_out_extra/README.md` how the extra synthetic years were built.
- `project/verify/` independent verification (MASTER §10). None of these scripts imports `rules.py`, `metrics.py`, `measurement.py`, `compare.py` or `robustness.py`.
- `research/` sources, verification notes, go/no-go tests.

Cases: `WP2024s42` (main), `WP2033s42`, `WP2033s43`. Group: NW CG3. See MASTER §0.

Two things that will bite a new machine:
- **Windows:** run everything with `PYTHONUTF8=1`, and `git config core.longpaths true` before cloning.
- **SEM-O retention:** the 2026-06-08 window can no longer be pulled in full (the API now starts 2026-06-09 23:00), so `out/measurement_*.csv` cannot be regenerated from the API. Keep the local raw BM files. See `project/verify/v06_measurement.md`.
