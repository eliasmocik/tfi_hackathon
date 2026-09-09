"""3.1 bullet 5 - Shift factor of each North-West wind farm on the most
constrained lines, and the constraint group that falls out of it.

    python q5_shift_factors.py [LINE ...]

Shift factor = MW change on the monitored line per MW the farm turns down,
with the balancing MW spread over the loads (EirGrid's convention).
Farms above a threshold form the constraint group. EirGrid picks the threshold
by eye ("a significant step change"); we use 5 % like the kit and also print
the sorted factors so you can see where the step is.

Compare with EirGrid's published groups (WDT overview PDF):
  NW Group 1: Ardnagappary, Binbane, Lenalea, Sorne Hill, Trillick
  NW Group 2: Meentycat
  NW Group 3: Sligo-Flagford  (Cunghill, Sligo, Glenree ... see the PDF)
"""
import sys

import pandas as pd

import common
import flowmath

THRESHOLD = 0.05
EIRGRID = {
    "NW Group 1": {"ARDNAGAPPARY", "BINBANE", "LENALEA", "SORNE HILL", "TRILLICK"},
    "NW Group 2": {"MEENTYCAT"},
}

n = common.baseline()
hours = common.binding_hours(n)
nw_lines = common.nw_lines(n)
if len(sys.argv) > 1:
    monitored = sys.argv[1:]
else:
    monitored = [b for b in hours.index if b in nw_lines and hours[b] > 0][:2]

frame = flowmath.branches(n)
farms = common.nw_renewables(n)
out = []
for line in monitored:
    sf = flowmath.shift_factors(n, line, reference="load", branch_frame=frame)
    sf = sf.reindex(farms).dropna(subset=["shift_factor"])
    sf["station"] = [common.label(n, b) for b in sf["bus"]]
    sf = sf.reindex(sf["shift_factor"].abs().sort_values(ascending=False).index)
    group = sf[sf["shift_factor"].abs() >= THRESHOLD]
    stations = {common.label(n, b).split(" ", 1)[-1] for b in group["bus"]}

    # EirGrid's rule: cut the list at "a significant step change". We find the
    # biggest gap between consecutive per-station factors and cut there.
    per_station = (sf.assign(a=sf["shift_factor"].abs())
                   .groupby("station")["a"].max().sort_values(ascending=False))
    gaps = per_station.diff(-1).fillna(0)            # drop to the next station
    cut_at = gaps.idxmax()
    step_group = set(s.split(" ", 1)[-1] for s in per_station.loc[:cut_at].index)

    print(f"\n=== {line}: {common.label(n, n.lines.at[line,'bus0'])} -> "
          f"{common.label(n, n.lines.at[line,'bus1'])}, binds {int(hours.get(line, 0))} h ===")
    print(sf[["station", "carrier", "p_nom", "shift_factor"]].round(3).to_string())
    print("\nper-station |SF|, sorted (look for the step):")
    print(per_station.round(3).to_string())
    print(f"\nconstraint group at |SF| >= {THRESHOLD:.0%}: {sorted(stations)}")
    print(f"constraint group by biggest step (EirGrid's rule), cut after "
          f"{cut_at} at |SF| {per_station[cut_at]:.2f}: {sorted(step_group)}")
    for gname, members in EIRGRID.items():
        hit = members & stations
        if hit:
            print(f"  overlap with EirGrid {gname}: {sorted(hit)}; "
                  f"EirGrid-only {sorted(members - stations)}; "
                  f"ours-only {sorted(stations - members)}")
    sf["monitored_line"] = line
    sf["in_group"] = sf["shift_factor"].abs() >= THRESHOLD
    out.append(sf)

common.save(pd.concat(out), "q5_shift_factors.csv")
