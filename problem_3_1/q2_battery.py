"""3.1 bullet 2 - Battery siting and sizing.

    python q2_battery.py [LINE]

Which North-West bus should host storage, and how big must it be to remove
constraint on the target line over the whole week?

Step 1 (siting):  put a 50 MW / 4 h battery at each NW bus in turn, re-solve,
                  measure how much NW dispatch-down is removed.
Step 2 (sizing):  at the best bus, sweep power and duration and report the
                  share of NW dispatch-down removed. "Eliminate constraint"
                  means that share reaching ~100 %.

Why not count hours the line binds? A battery that charges on spilled wind
and exports it later keeps the line FULL for more hours, not fewer. Binding
hours go up while wasted wind goes down. The MWh is the honest metric.

LINE defaults to the most-bound NW line from the baseline.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common
import gridkit

n = common.baseline()
base_dd = common.dispatch_down(n)["dispatch_down_mwh"].sum()

# target line: given on the command line, else the most-bound NW line
hours = common.binding_hours(n)
nw = [b for b in hours.index if b in common.nw_lines(n)]
target = sys.argv[1] if len(sys.argv) > 1 else nw[0]
print(f"target line {target}: {common.label(n, n.lines.at[target,'bus0'])} -> "
      f"{common.label(n, n.lines.at[target,'bus1'])}, "
      f"{n.lines.at[target,'s_nom']:.0f} MVA, binds {int(hours[target])} h in baseline")


def line_binding_hours(n, line):
    loading = n.lines_t.p0[line].abs() / n.lines.at[line, "s_nom"]
    return int((loading >= 0.999).sum())


# ---- Step 1: where ----------------------------------------------------------
rows = []
for bus in common.nw_buses(n):
    name = gridkit.add_battery(n, bus, p_nom=50, hours=4)
    common.solve(n)
    rows.append({
        "bus": common.label(n, bus),
        "line_binding_hours": line_binding_hours(n, target),
        "nw_dispatch_down_mwh": common.dispatch_down(n)["dispatch_down_mwh"].sum(),
        "battery_mwh_throughput": float(n.storage_units_t.p[name].abs().sum()) / 2,
    })
    n.remove("StorageUnit", name)             # take it out again
    print(f"  {rows[-1]['bus']:22s} line binds {rows[-1]['line_binding_hours']:3d} h, "
          f"NW dispatch-down {rows[-1]['nw_dispatch_down_mwh']:,.0f} MWh")
site = pd.DataFrame(rows).set_index("bus")
site["dispatch_down_removed_mwh"] = base_dd - site["nw_dispatch_down_mwh"]
site = site.sort_values("dispatch_down_removed_mwh", ascending=False)
print("\nbest hosts for a 50 MW / 4 h battery:")
print(site.head(8).round(1).to_string())
common.save(site, "q2_battery_siting.csv")

# ---- Step 2: how big ----------------------------------------------------------
best_label = site.index[0]
best_bus = best_label.split(" ")[0]
rows = []
for p in [50, 100, 200, 400]:
    for h in [2, 4, 8]:
        name = gridkit.add_battery(n, best_bus, p_nom=p, hours=h)
        common.solve(n)
        rows.append({"p_mw": p, "hours": h, "energy_mwh": p * h,
                     "line_binding_hours": line_binding_hours(n, target),
                     "nw_dispatch_down_mwh": common.dispatch_down(n)["dispatch_down_mwh"].sum()})
        n.remove("StorageUnit", name)
        print(f"  {p:4d} MW x {h} h -> line binds {rows[-1]['line_binding_hours']:3d} h")
size = pd.DataFrame(rows)
size["dispatch_down_removed_pct"] = 100 * (base_dd - size["nw_dispatch_down_mwh"]) / base_dd
common.save(size, "q2_battery_sizing.csv")
print("\nshare of NW dispatch-down removed, battery at", best_label)
print(size.pivot(index="p_mw", columns="hours", values="dispatch_down_removed_pct").round(0).to_string())
ok = size[size["dispatch_down_removed_pct"] >= 95].sort_values("energy_mwh")
if len(ok):
    r = ok.iloc[0]
    print(f"\nsmallest battery that removes >=95 % of NW dispatch-down: "
          f"{r.p_mw:.0f} MW / {r.hours:.0f} h ({r.energy_mwh:.0f} MWh)")
else:
    best = size.loc[size["dispatch_down_removed_pct"].idxmax()]
    print(f"\nno battery up to 400 MW / 8 h eliminates constraint: the best, "
          f"{best.p_mw:.0f} MW / {best.hours:.0f} h, removes {best.dispatch_down_removed_pct:.0f} %. "
          f"The line binds {int(hours[target])} of {len(n.snapshots)} hours; storage can shift "
          f"wind inside a week but cannot create export capacity that is missing 3 hours in 4.")

# ---- Plot ----------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
site["dispatch_down_removed_mwh"].head(10)[::-1].plot.barh(ax=ax1)
ax1.set_xlabel("NW dispatch-down removed by a 50 MW / 4 h battery (MWh)")
ax1.set_title("Where to put storage")
piv = size.pivot(index="p_mw", columns="hours", values="dispatch_down_removed_pct")
im = ax2.imshow(piv.values, cmap="Greens", aspect="auto", vmin=0, vmax=100)
ax2.set_xticks(range(len(piv.columns)), [f"{h} h" for h in piv.columns])
ax2.set_yticks(range(len(piv.index)), [f"{p} MW" for p in piv.index])
for i in range(len(piv.index)):
    for j in range(len(piv.columns)):
        ax2.text(j, i, f"{piv.values[i, j]:.0f}%", ha="center", va="center")
ax2.set_title(f"% of NW dispatch-down removed, battery at {best_label}")
fig.tight_layout()
fig.savefig(f"{common.OUT}/q2_battery.png", dpi=150)
print(f"-> {common.OUT}/q2_battery.png")
