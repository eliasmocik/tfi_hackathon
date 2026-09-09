"""3.1 bullet 6 - Priority vs non-priority farms: where does the ordering
cause inefficiency?

    python q6_priority.py

Rule (EirGrid grandfathering): non-priority farms are cut first; priority
farms (connected before 4 July 2019) only if that is not enough.
In the model: priority farms bid -2, non-priority -1, so the optimiser cuts
non-priority first.

Which farms are priority? From EirGrid's ECP-GSS-1 unit list
(../data/eirgrid_gss1_res_units.csv): per node, the share of MW that is
"priority". A kit generator at a node is tagged priority if most of that
node's wind MW is priority. Coarse, but it is EirGrid's own data.

Compare:  (a) everyone equal at -1  vs  (b) priority ordering.
Extra MWh cut from non-priority farms in (b) = the cost of the ordering.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common

UNITS = os.path.join(os.path.dirname(common.HERE), "data", "eirgrid_gss1_res_units.csv")

n = common.baseline()
farms = common.nw_renewables(n)

# ---- (a) everyone equal ----------------------------------------------------------
equal = common.dispatch_down(n, farms)

# ---- tag priority from EirGrid's list -------------------------------------------
units = pd.read_csv(UNITS)
units["node"] = units["node"].str.upper().str.strip()
units = units[units["gen_type"].str.lower().isin(["wind", "solar"])]
share = (units.assign(prio=units["priority"].str.contains("not|uncontrolled", case=False) == False)
         .groupby("node").apply(lambda g: (g["mec_mw"] * g["prio"]).sum() / g["mec_mw"].sum()))


def station_of(bus):
    return str(n.buses.at[bus, "station"]).upper().replace("_", " ")


tag = {}
for f in farms:
    st = station_of(n.generators.at[f, "bus"])
    key = next((k for k in share.index if k.replace("_", " ") == st or st.startswith(k)), None)
    tag[f] = "priority" if key is not None and share[key] >= 0.5 else "non-priority"
tag = pd.Series(tag, name="status")
print("tagged from EirGrid list:", tag.value_counts().to_dict())

# ---- (b) priority ordering -----------------------------------------------------------
n.generators.loc[tag.index[tag == "priority"], "marginal_cost"] = -2.0
common.solve(n)
ordered = common.dispatch_down(n, farms)

# ---- compare ---------------------------------------------------------------------------
cmp = pd.DataFrame({
    "bus": equal["bus"],
    "status": tag,
    "offered_mwh": equal["offered_mwh"],
    "cut_equal_mwh": equal["dispatch_down_mwh"],
    "cut_priority_rule_mwh": ordered["dispatch_down_mwh"].reindex(equal.index),
})
cmp["extra_cut_mwh"] = cmp["cut_priority_rule_mwh"] - cmp["cut_equal_mwh"]
cmp["station"] = [common.label(n, b) for b in cmp["bus"]]
cmp = cmp.sort_values("extra_cut_mwh", ascending=False)

tot_equal = cmp["cut_equal_mwh"].sum()
tot_rule = cmp["cut_priority_rule_mwh"].sum()
print(f"\ntotal NW dispatch-down: equal {tot_equal:,.0f} MWh, priority rule {tot_rule:,.0f} MWh "
      f"(system-wide waste changes by {tot_rule - tot_equal:+,.0f} MWh)")
print("\nby status:")
print(cmp.groupby("status")[["offered_mwh", "cut_equal_mwh", "cut_priority_rule_mwh"]].sum().round(0).to_string())
print("\nfarms that lose most under the priority rule:")
print(cmp[["station", "status", "cut_equal_mwh", "cut_priority_rule_mwh", "extra_cut_mwh"]]
      .head(10).round(0).to_string())
common.save(cmp, "q6_priority.csv")

# ---- plot ----------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.5))
top = cmp.head(12)
colors = ["tab:red" if s == "non-priority" else "tab:blue" for s in top["status"]]
ax.bar(range(len(top)), top["extra_cut_mwh"], color=colors)
ax.set_xticks(range(len(top)), top["station"], rotation=60, ha="right", fontsize=7)
ax.set_ylabel("extra MWh cut under priority rule vs equal treatment")
ax.set_title("Who pays for grandfathering (red = non-priority, blue = priority)")
fig.tight_layout()
fig.savefig(f"{common.OUT}/q6_priority.png", dpi=150)
print(f"-> {common.OUT}/q6_priority.png")
