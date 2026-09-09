# Problem 3.1 — Analyse the North-West

One script per bullet of problem 3.1. All use `common.py` for the shared setup.

```bash
cd tfi_hackathon/problem_3_1
../participant-kit/.venv/bin/python q1_constrained_lines.py      # ~3 min
../participant-kit/.venv/bin/python q5_shift_factors.py          # ~20 s
../participant-kit/.venv/bin/python q4_siting.py                 # ~5 min
../participant-kit/.venv/bin/python q2_battery.py                # ~8 min
../participant-kit/.venv/bin/python q3_dynamic_line_rating.py    # ~30 s
../participant-kit/.venv/bin/python q6_priority.py               # ~30 s
```

`QUICK=1 python q4_siting.py` runs on the 15-node scope instead (2 s per solve)
for fast iteration. Numbers there are a sandbox, not a result (see `common.py`).

Outputs (CSV + PNG) land in `outputs/`.

| Script | Bullet | What it answers |
|---|---|---|
| `q1_constrained_lines.py` | which lines, effect of rating | hours at rating per NW branch; dispatch-down vs rating multiplier |
| `q2_battery.py` | battery siting and sizing | best host bus for a 50 MW battery; smallest MW × h that removes constraint on the target line |
| `q3_dynamic_line_rating.py` | dynamic line rating | dispatch-down with wind-cooled overhead ratings (+30 % at full wind, stated assumption) |
| `q4_siting.py` | where should developers build | private and system MWh per MW for a new 50 MW farm at every NW bus, plus where the static shift-factor screen misranks |
| `q5_shift_factors.py` | shift factor per farm | factors on the two most-bound lines; group at 5 % vs EirGrid's published groups |
| `q6_priority.py` | priority / non-priority | extra MWh cut from non-priority farms under the grandfathering rule, tagged from EirGrid's unit list |

## Results at a glance (WP2033, synthetic week, all-island run, 2026-09-08)

- **One wire is the whole NW constraint**: Letterkenny–Strabane tie (123 MVA) at rating 131 of 168 h. −20 % rating
  adds 5.6 GWh of spill in a week; +10 % saves 0.4 GWh and +20 % saves nothing more (the next limit binds at once).
- **Storage cannot eliminate it**: best host Sorne Hill; even 400 MW / 8 h removes only 22 % of NW dispatch-down.
  The line is full 3 hours in 4; a battery shifts wind inside the week, it does not create export capacity.
- **DLR on NW overhead lines** (+30 % at full wind): −2 % NW dispatch-down, island-wide unchanged, same reason.
- **Siting**: system value ranges from 23 MWh/MW (Glenree) to 6.6 (Sorne Hill, Trillick) for a 50 MW farm. Binbane looks
  fine privately (24) but its neighbours lose 12 per MW. Tier-1 screen misranks Tievebrack (28th) vs truth (9th).
- **Shift factors** on the tie: all of Donegal sits at 0.36–0.51, Sligo side at 0.08–0.13. The 5 % rule groups the
  whole region; EirGrid's step-change rule cuts cleanly at the Cathaleen's Fall → Sligo gap.
- **Priority rule** moves 7.8 GWh of cuts from priority farms onto non-priority ones (Croaghonagh, Tievebrack,
  Letterkenny pay most); total waste is unchanged, so in Donegal the rule is distribution, not efficiency.

Caveat that applies to every number: regional totals depend on which farm the optimiser cuts when several are
equally effective. We fix that with a tiny deterministic bid offset (`common.set_renewable_bids`); the island-wide
figure is the one that is independent of it.

Setup facts baked into `common.py`:
- All-island WP2033 network filtered to the North-West stations. The 15-node scope pins its ties and folds Srananagh.
- Wind and solar bid −1 (the kit ships them at 0, which makes the cut land on an arbitrary farm).
- Solves use `assign_all_duals=True` so line shadow prices exist.
- Every new generator gets an explicit hourly profile borrowed from the nearest wind farm.
