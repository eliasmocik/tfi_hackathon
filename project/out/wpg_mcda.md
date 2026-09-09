# WP-G - options and criteria, weights blank

The team does not select the weights. The SEM Committee, CRU or DECC does.
This table is the transfer function; the weights are the policy choice.

Window: 2026-06-09 23:00:00 to 2026-09-05 23:30:00 (88.0 days, 638 half-hours with relief, 15 units).
Annualised columns scale the window linearly, which assumes the summer
constraint pattern is representative. It is one summer; state that.

| criterion | serves | Today (pro rata) | Band 2 pp | Band 3 pp | Band 5 pp | Pure effectiveness | weight |
|---|---|---|---|---|---|---|---|
| Spill, MWh (window) | Generators, carbon, consumers | 10818.9 | 10519.5 | 10437.8 | 10317.2 | 9915.3 |  |
| Spill saved vs today, MWh | All | 25.5 | 325.0 | 406.6 | 527.2 | 929.2 |  |
| Spill saved, % | All | 0.24 | 3.00 | 3.75 | 4.86 | 8.57 |  |
| Spill saved, MWh/yr (scaled) | All | 106 | 1348 | 1686 | 2186 | 3853 |  |
| Consumer EUR at 40/MWh (UNVERIFIED rate) | Consumers, taxpayers | 1021 | 13000 | 16265 | 21090 | 37167 |  |
| Consumer EUR at 60/MWh (UNVERIFIED rate) | Consumers, taxpayers | 1531 | 19499 | 24398 | 31635 | 55750 |  |
| Consumer EUR at 80/MWh (UNVERIFIED rate) | Consumers, taxpayers | 2042 | 25999 | 32530 | 42180 | 74333 |  |
| Consumer EUR at 100/MWh (UNVERIFIED rate) | Consumers, taxpayers | 2552 | 32499 | 40663 | 52725 | 92917 |  |
| Consumer EUR at 120/MWh (UNVERIFIED rate) | Consumers, taxpayers | 3063 | 38999 | 48795 | 63270 | 111500 |  |
| Equity: guaranteed bound, pp | Generators | 6.22 | 8.22 | 9.22 | 11.22 | inf |  |
| Equity: realised divergence, pp | Generators | 5.80 | 5.80 | 6.13 | 9.52 | 45.24 |  |
| Feasibility escapes (of 638 hh) | Generators, TSO | 100 | 7 | 2 | 0 | 0 |  |
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
| 0.05 | 0.95 | Band 2 pp | Today (pro rata) |
| 0.10 | 0.90 | Band 3 pp | Today (pro rata) |
| 0.15 | 0.85 | Band 3 pp | Today (pro rata) |
| 0.20 | 0.80 | Band 3 pp | Today (pro rata) |
| 0.25 | 0.75 | Band 3 pp | Today (pro rata) |
| 0.30 | 0.70 | Band 3 pp | Today (pro rata) |
| 0.35 | 0.65 | Band 3 pp | Today (pro rata) |
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
