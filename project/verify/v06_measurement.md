# Verification §10.6 — measurement re-derived from the raw BM files

## Retention finding (acted on 2026-09-09)

The SEM-O window is no longer fully retrievable. The earliest half-hour the
API now returns for these units is **2026-06-09 23:00:00**, not 2026-06-08 00:00, and
BM-037 instructions now begin 2026-06-10. The fresh pull therefore has
**48 fewer half-hours** per unit than the committed measurement
(4226 vs 4274).

Consequences:

1. `out/measurement_*.csv` as committed **can no longer be reproduced from the
   API**. Those files and Elias's local raw pull are the only record of
   2026-06-08 to 2026-06-09.
2. The committed outputs were therefore restored, not overwritten. The fresh
   run is kept separately under `verify/repro/`.
3. The residual difference below is fully consistent with the missing leading
   days. It cannot be decomposed further without the original raw files.

MASTER §6.1–§6.3 re-implemented independently (join, LOCL/CURL state
machine, constraint-only ratio). `measurement.py` is not imported.

Three columns are compared:

- **committed** — `out/measurement_units.csv` as published (Elias's pull).
- **pipeline_fresh_pull** — `src/measurement.py` re-run on a fresh 2026-09-09 pull.
- **independent_fresh_pull** — this file's own code on that same fresh pull.

The first comparison isolates *code*; the second reflects the shorter window.

- units compared: **25**
- worst |independent − pipeline| on the same data (code agreement): **9.71e-17**
- worst |fresh − committed| (shorter window, not a code difference): **3.82e-03**

## Per unit

| unit | committed | pipeline (fresh) | independent (fresh) | code diff | vintage diff |
|---|---|---|---|---|---|
| GU_404630 | 0.098054 | 0.098976 | 0.098976 | 5.55e-17 | 9.22e-04 |
| GU_403750 | 0.089496 | 0.085680 | 0.085680 | 9.71e-17 | 3.82e-03 |
| GU_402200 | 0.084493 | 0.086157 | 0.086157 | 0.00e+00 | 1.66e-03 |
| GU_400550 | 0.081817 | 0.082784 | 0.082784 | 0.00e+00 | 9.66e-04 |
| GU_401280 | 0.079911 | 0.076140 | 0.076140 | 0.00e+00 | 3.77e-03 |
| GU_402160 | 0.078016 | 0.079304 | 0.079304 | 8.33e-17 | 1.29e-03 |
| GU_405930 | 0.075282 | 0.076542 | 0.076542 | 0.00e+00 | 1.26e-03 |
| GU_403990 | 0.074291 | 0.071394 | 0.071394 | 2.78e-17 | 2.90e-03 |
| GU_406560 | 0.074234 | 0.073370 | 0.073370 | 2.78e-17 | 8.64e-04 |
| GU_400021 | 0.071183 | 0.069840 | 0.069840 | 8.33e-17 | 1.34e-03 |
| GU_403760 | 0.070713 | 0.070264 | 0.070264 | 2.78e-17 | 4.50e-04 |
| GU_401720 | 0.070243 | 0.072856 | 0.072856 | 5.55e-17 | 2.61e-03 |
| GU_400070 | 0.061300 | 0.061765 | 0.061765 | 2.78e-17 | 4.66e-04 |
| GU_405130 | 0.058095 | 0.057526 | 0.057526 | 3.47e-17 | 5.69e-04 |
| GU_400950 | 0.057446 | 0.058793 | 0.058793 | 4.16e-17 | 1.35e-03 |
| GU_403400 | 0.055793 | 0.053761 | 0.053761 | 1.39e-17 | 2.03e-03 |
| GU_405870 | 0.053649 | 0.054133 | 0.054133 | 5.55e-17 | 4.84e-04 |
| GU_404480 | 0.051515 | 0.052983 | 0.052983 | 5.55e-17 | 1.47e-03 |
| GU_400940 | 0.050334 | 0.051568 | 0.051568 | 9.02e-17 | 1.23e-03 |
| GU_403880 | 0.048130 | 0.047796 | 0.047796 | 5.55e-17 | 3.35e-04 |
| GU_401730 | 0.046259 | 0.047676 | 0.047676 | 6.25e-17 | 1.42e-03 |
| GU_404560 | 0.043148 | 0.043431 | 0.043431 | 4.16e-17 | 2.83e-04 |
| GU_403800 | 0.028661 | 0.029454 | 0.029454 | 4.86e-17 | 7.93e-04 |
| GU_403840 | 0.015975 | 0.016250 | 0.016250 | 2.43e-17 | 2.75e-04 |
| GU_407660 | 0.000000 | 0.000000 | 0.000000 | 0.00e+00 | 0.00e+00 |

Full table: `v06_measurement.csv`.
