# WP-G - options and criteria, weights blank

The team does not select the weights. The SEM Committee, CRU or DECC does.
This table is the transfer function; the weights are the policy choice.

Window: 2026-06-08 23:00:00 to 2026-09-05 23:30:00 (89.0 days, 670 half-hours with relief, 15 units).
Annualised columns scale the window linearly, which assumes the summer
constraint pattern is representative. It is one summer; state that.

| criterion | serves | Today (pro rata) | Band 2 pp | Band 3 pp | Band 5 pp | Pure effectiveness | weight |
|---|---|---|---|---|---|---|---|
| Spill, MWh (window) | Generators, carbon, consumers | 11060.1 | 10728.6 | 10658.2 | 10529.6 | 10127.0 |  |
| Spill saved vs today, MWh | All | 11.9 | 343.4 | 413.8 | 542.4 | 945.0 |  |
| Spill saved, % | All | 0.11 | 3.10 | 3.74 | 4.90 | 8.53 |  |
| Spill saved, MWh/yr (scaled) | All | 49 | 1408 | 1697 | 2224 | 3875 |  |
| Consumer EUR at 40/MWh (UNVERIFIED rate) | Consumers, taxpayers | 477 | 13736 | 16552 | 21695 | 37799 |  |
| Consumer EUR at 60/MWh (UNVERIFIED rate) | Consumers, taxpayers | 715 | 20604 | 24827 | 32543 | 56699 |  |
| Consumer EUR at 80/MWh (UNVERIFIED rate) | Consumers, taxpayers | 954 | 27472 | 33103 | 43391 | 75599 |  |
| Consumer EUR at 100/MWh (UNVERIFIED rate) | Consumers, taxpayers | 1192 | 34339 | 41379 | 54238 | 94498 |  |
| Consumer EUR at 120/MWh (UNVERIFIED rate) | Consumers, taxpayers | 1431 | 41207 | 49655 | 65086 | 113398 |  |
| Equity: guaranteed bound, pp | Generators | 22.41 | 24.11 | 25.11 | 27.11 | inf |  |
| Equity: realised divergence, pp | Generators | 21.23 | 21.23 | 21.23 | 21.23 | 71.77 |  |
| Feasibility escapes (of 638 hh) | Generators, TSO | 101 | 6 | 3 | 0 | 0 |  |
| Operator actions per event | TSO | 1 | 1 | 1 | 1 | 1 |  |
| Security | All | invariant | invariant | invariant | invariant | invariant |  |
| Carbon, tCO2 (UNVERIFIED factor) | Third parties, State | - | - | - | - | - |  |
| Community CBF EUR (RESS subset unidentified) | Host communities | - | - | - | - | - |  |

Cells marked `-` are criteria whose input the verification queue has
not cleared (design brief v2 section 8). They are deliberately left
empty rather than filled with a plausible number.

## Which weight vector selects which option

Spill and realised equity divergence are the only two criteria in real
tension; the euro, carbon and community columns are monotone transforms
of spill, and security and operator burden are invariant across options.
So the sensitivity reduces to one dial.

| weight on spill | weight on equity | winner (realised equity) | winner (guaranteed bound) |
|---|---|---|---|
| 0.00 | 1.00 | Today (pro rata) | Today (pro rata) |
| 0.05 | 0.95 | Band 5 pp | Today (pro rata) |
| 0.10 | 0.90 | Band 5 pp | Today (pro rata) |
| 0.15 | 0.85 | Band 5 pp | Today (pro rata) |
| 0.20 | 0.80 | Band 5 pp | Today (pro rata) |
| 0.25 | 0.75 | Band 5 pp | Today (pro rata) |
| 0.30 | 0.70 | Band 5 pp | Today (pro rata) |
| 0.35 | 0.65 | Band 5 pp | Today (pro rata) |
| 0.40 | 0.60 | Band 5 pp | Today (pro rata) |
| 0.45 | 0.55 | Band 5 pp | Today (pro rata) |
| 0.50 | 0.50 | Band 5 pp | Today (pro rata) |
| 0.55 | 0.45 | Band 5 pp | Pure effectiveness |
| 0.60 | 0.40 | Band 5 pp | Pure effectiveness |
| 0.65 | 0.35 | Band 5 pp | Pure effectiveness |
| 0.70 | 0.30 | Pure effectiveness | Pure effectiveness |
| 0.75 | 0.25 | Pure effectiveness | Pure effectiveness |
| 0.80 | 0.20 | Pure effectiveness | Pure effectiveness |
| 0.85 | 0.15 | Pure effectiveness | Pure effectiveness |
| 0.90 | 0.10 | Pure effectiveness | Pure effectiveness |
| 0.95 | 0.05 | Pure effectiveness | Pure effectiveness |
| 1.00 | 0.00 | Pure effectiveness | Pure effectiveness |

Full tables: `wpg_mcda.csv`, `wpg_weight_sensitivity.csv`.
