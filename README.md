# tfi_hackathon — the price of pro-rata

TPSA / TF Wind Hackathon 2026. Cost of EirGrid's pro-rata constraint-group split versus effectiveness-ordered dispatch, and a year-to-date "band" rule between them, measured on North-West Constraint Group 3.

Start here: `project/MASTER.md` (the full specification), then `research/validation-prorata-brief-2026-09-08.md` and `research/formula-decisions-2026-09-09.md`.

Layout
- `participant-kit/` organisers' kit (networks, flowmath, gridkit). Make a venv: `python -m venv .venv && pip install -r requirements.txt`.
- `project/src/` our code: `measurement.py` (2026 SEM-O data), `engine_prep.py` + `run_engine.py` (network prep, baseline dispatch, PTDF/LODF, overloads), rules to follow.
- `project/out/` results (CSV/JSON/PNG/notes). Large parquet tables are not in git; regenerate with `python project/src/run_engine.py <case>`.
- `data/` inputs. Files over ~20 MB are git-ignored; `data/README.md` says how to pull them from SEM-O, `data/synth_out_extra/README.md` how the extra synthetic years were built.
- `research/` sources, verification notes, go/no-go tests.

Cases: `WP2024s42` (main), `WP2033s42`, `WP2033s43`. Group: NW CG3. See MASTER §0.
