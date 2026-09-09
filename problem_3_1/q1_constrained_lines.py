"""3.1 bullet 1 - Which North-West lines are constrained most often, and how
does the thermal rating change the amount of wind constrained?

    python q1_constrained_lines.py

Step 1: baseline solve, count hours each NW branch sits at its rating.
Step 2: take the three most-bound lines, scale each one's rating by
        0.8 / 0.9 / 1.1 / 1.2, re-solve, and record NW dispatch-down.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common

n = common.baseline()

# ---- Step 1: binding hours ------------------------------------------------
branches = common.nw_lines(n) + common.nw_transformers(n)
hours = common.binding_hours(n).reindex(branches).fillna(0).astype(int)
hours = hours[hours > 0].sort_values(ascending=False)

info = []
for name in hours.index:
    tab = n.lines if name in n.lines.index else n.transformers
    info.append({
        "branch": name,
        "from": common.label(n, tab.at[name, "bus0"]),
        "to": common.label(n, tab.at[name, "bus1"]),
        "rating_mva": tab.at[name, "s_nom"],
        "hours_at_rating": hours[name],
    })
table = pd.DataFrame(info).set_index("branch")
base_dd = common.dispatch_down(n)["dispatch_down_mwh"].sum()

print("\nNorth-West branches at their rating (of", len(n.snapshots), "hours):")
print(table.to_string())
print(f"\nbaseline NW renewable dispatch-down: {base_dd:,.0f} MWh")
common.save(table, "q1_binding_hours.csv")

# ---- Step 2: rating sweep on the top three lines ---------------------------
top = [b for b in table.index if b in n.lines.index][:3]
factors = [0.8, 0.9, 1.0, 1.1, 1.2]
rows = []
for line in top:
    original = float(n.lines.at[line, "s_nom"])
    for f in factors:
        if f == 1.0:
            rows.append({"line": line, "factor": f, "rating_mva": original,
                         "nw_dispatch_down_mwh": base_dd})
            continue
        n.lines.at[line, "s_nom"] = original * f
        common.solve(n)
        dd = common.dispatch_down(n)["dispatch_down_mwh"].sum()
        rows.append({"line": line, "factor": f, "rating_mva": original * f,
                     "nw_dispatch_down_mwh": dd})
        print(f"  {line} x{f:.1f} -> {dd:,.0f} MWh dispatched down")
    n.lines.at[line, "s_nom"] = original          # put it back
sweep = pd.DataFrame(rows)
common.save(sweep, "q1_rating_sweep.csv")

# ---- Plot -------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
table["hours_at_rating"].head(10)[::-1].plot.barh(ax=ax1)
ax1.set_xlabel("hours at rating (of the week)")
ax1.set_title("Most-constrained NW branches")
for line, g in sweep.groupby("line"):
    ax2.plot(g["factor"], g["nw_dispatch_down_mwh"], marker="o", label=line)
ax2.set_xlabel("rating multiplier")
ax2.set_ylabel("NW renewable dispatch-down (MWh / week)")
ax2.set_title("Effect of thermal rating")
ax2.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f"{common.OUT}/q1_constrained_lines.png", dpi=150)
print(f"-> {common.OUT}/q1_constrained_lines.png")
