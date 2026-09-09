"""3.1 bullet 4 - Where should a wind developer build in the North-West?

    python q4_siting.py [NEW_MW]

Two numbers per bus for a new NEW_MW farm (default 50 MW):

  private index = MWh the new farm delivers per MW installed   (developer's view)
  system index  = (new farm MWh + change in MWh of every existing wind/solar)
                  per MW installed                              (grid's view)

Tier 1 is a cheap screen from the baseline shadow prices (no re-solve).
Tier 2 actually adds the farm at each bus and re-solves. Tier 2 is the truth;
Tier 1 shows what a static shift-factor map would have told you.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common
import flowmath

NEW_MW = float(sys.argv[1]) if len(sys.argv) > 1 else 50.0
NEW_BID = -0.99      # just above the existing farms' -1: new farm is cut first
                     # when it ties with a neighbour. State this convention.

n = common.baseline()
existing = [g for g in n.generators.index
            if n.generators.at[g, "carrier"] in common.RENEWABLE
            and g in n.generators_t.p_max_pu.columns]
base_existing_mwh = n.generators_t.p[existing].sum().sum()
candidates = common.nw_buses(n)

# ---- Tier 1: congestion cost imposed, from duals x PTDF x profile ------------
# For each hour: cost_b = sum over branches of mu_e * PTDF(e, b).
# Weighted by the farm's own output profile and summed over the week.
ptdf = flowmath.ptdf(n)                       # branches x buses
mu = common.line_duals(n)                     # hours x branches
mu = mu.reindex(columns=ptdf.index).fillna(0)
tier1 = {}
for bus in candidates:
    profile = common.nearest_wind_profile(n, bus)
    # PyPSA's mu_upper is <= 0 at +rating, so the sign is flipped: minus the
    # product gives a POSITIVE cost for a bus that loads a binding line and a
    # negative cost (a benefit) for a bus that relieves it.
    cost_per_hour = -(mu.to_numpy() @ ptdf[bus].to_numpy())   # EUR per MW, per hour
    tier1[bus] = float((cost_per_hour * profile.to_numpy()).sum())
tier1 = pd.Series(tier1, name="tier1_congestion_cost")

# ---- Tier 2: add the farm, re-solve, measure ----------------------------------
rows = []
for bus in candidates:
    name = f"NEW {NEW_MW:.0f}MW wind at {bus}"
    n.add("Generator", name, bus=bus, carrier="wind", p_nom=NEW_MW,
          marginal_cost=NEW_BID, p_max_pu=common.nearest_wind_profile(n, bus))
    common.solve(n)
    own = float(n.generators_t.p[name].sum())
    offered = float((n.generators_t.p_max_pu[name] * NEW_MW).sum())
    ext = float(n.generators_t.p[existing].sum().sum() - base_existing_mwh)
    rows.append({
        "bus": bus, "station": common.label(n, bus),
        "offered_mwh": offered,
        "private_mwh_per_mw": own / NEW_MW,
        "external_mwh_per_mw": ext / NEW_MW,
        "system_mwh_per_mw": (own + ext) / NEW_MW,
        "own_dispatch_down_pct": 100 * (offered - own) / offered if offered else np.nan,
        "tier1_congestion_cost": tier1[bus],
    })
    n.remove("Generator", name)
    print(f"  {rows[-1]['station']:22s} private {rows[-1]['private_mwh_per_mw']:6.1f}  "
          f"external {rows[-1]['external_mwh_per_mw']:6.1f}  "
          f"system {rows[-1]['system_mwh_per_mw']:6.1f}  MWh/MW")

res = pd.DataFrame(rows).set_index("station")
res["private_rank"] = res["private_mwh_per_mw"].rank(ascending=False).astype(int)
res["system_rank"] = res["system_mwh_per_mw"].rank(ascending=False).astype(int)
res["tier1_rank"] = res["tier1_congestion_cost"].rank().astype(int)   # low cost = good
res = res.sort_values("system_rank")
print(f"\nnew {NEW_MW:.0f} MW farm, ranked by SYSTEM value (best first):")
print(res[["private_mwh_per_mw", "external_mwh_per_mw", "system_mwh_per_mw",
           "own_dispatch_down_pct", "private_rank", "system_rank", "tier1_rank"]]
      .round(1).to_string())
common.save(res, "q4_siting.csv")

# ---- Plot: private vs system, plus the Tier-1 misranking -------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.scatter(res["private_mwh_per_mw"], res["system_mwh_per_mw"])
for st, r in res.iterrows():
    ax1.annotate(st.split(" ", 1)[-1], (r["private_mwh_per_mw"], r["system_mwh_per_mw"]),
                 fontsize=7, xytext=(3, 3), textcoords="offset points")
lim = [min(res["system_mwh_per_mw"].min(), 0), res["private_mwh_per_mw"].max() * 1.05]
ax1.plot(lim, lim, ls="--", c="grey", lw=0.8)
ax1.set_xlabel("private: MWh delivered per MW (developer sees this)")
ax1.set_ylabel("system: net MWh per MW incl. neighbours (grid sees this)")
ax1.set_title("Buses far below the line look good privately, bad systemically")
ax2.scatter(res["tier1_rank"], res["system_rank"])
for st, r in res.iterrows():
    ax2.annotate(st.split(" ", 1)[-1], (r["tier1_rank"], r["system_rank"]),
                 fontsize=7, xytext=(3, 3), textcoords="offset points")
ax2.plot([1, len(res)], [1, len(res)], ls="--", c="grey", lw=0.8)
ax2.set_xlabel("rank from static shift-factor screen (Tier 1)")
ax2.set_ylabel("true system rank (Tier 2)")
ax2.set_title("Where the cheap screen misranks")
fig.tight_layout()
fig.savefig(f"{common.OUT}/q4_siting.png", dpi=150)
print(f"-> {common.OUT}/q4_siting.png")
