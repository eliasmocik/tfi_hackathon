#!/bin/bash
# Phase 2 (MASTER §4, §5, §7, §8, §9) from the engine's saved files. ~1 min in total.
set -e
cd "$(dirname "$0")/.."
python src/engine_notes.py
for c in WP2024s42 WP2033s42 WP2033s43; do
  python src/check_sf_convention.py $c
  python src/rules.py $c
done
python src/metrics.py
python src/charts.py
python src/compare.py
python src/robustness.py
python src/results_md.py
