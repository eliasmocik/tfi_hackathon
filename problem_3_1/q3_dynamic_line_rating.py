"""3.1 bullet 3 - How much could Dynamic Line Rating (DLR) cut constraint?

    python q3_dynamic_line_rating.py

Idea: an overhead conductor is cooled by wind. High wind = more current
allowed = extra headroom exactly when wind farms are producing most.
We do not have wind speed, so we use the local wind farms' capacity factor as
a proxy for how windy it is at each line, and let the rating rise linearly:

    rating(h) = static rating x (1 + DLR_GAIN x local wind capacity factor(h))

DLR_GAIN = 0.3 means up to +30 % at full wind. That is a stated assumption,
in the range of published DLR uplift figures, not a measured value.
Cables are not cooled by wind, so only overhead lines get DLR.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common

DLR_GAIN = 0.3
OVERHEAD_X_PER_KM = 0.25     # ohm/km above this = overhead line (cables are lower)

n = common.baseline()
base_dd = common.dispatch_down(n)
base_sys = common.system_dispatch_down_mwh(n)
base_hours = common.binding_hours(n)

# ---- Which NW lines are overhead? ------------------------------------------
lines = n.lines.loc[common.nw_lines(n)]
has_len = lines["length"].fillna(0) > 0
x_per_km = (lines["x"] / lines["length"]).where(has_len)
overhead = list(lines.index[(x_per_km > OVERHEAD_X_PER_KM) | ~has_len])
print(f"{len(overhead)} of {len(lines)} NW lines treated as overhead")

# ---- Local wind capacity factor per line ------------------------------------
wind = n.generators[(n.generators["carrier"] == "wind")
                    & n.generators.index.isin(n.generators_t.p_max_pu.columns)]


def local_wind_cf(bus0, bus1):
    """Mean capacity factor of wind farms at the two ends (or nearest one)."""
    at_ends = wind.index[wind["bus"].isin([bus0, bus1])]
    if len(at_ends):
        return n.generators_t.p_max_pu[at_ends].mean(axis=1)
    return common.nearest_wind_profile(n, bus0)


# ---- Apply DLR as a time-varying s_max_pu and re-solve -----------------------
smax = pd.DataFrame(1.0, index=n.snapshots, columns=overhead)
for line in overhead:
    cf = local_wind_cf(n.lines.at[line, "bus0"], n.lines.at[line, "bus1"])
    smax[line] = 1.0 + DLR_GAIN * cf
n.lines_t.s_max_pu = smax           # PyPSA reads a per-hour rating from here
common.solve(n)
dlr_dd = common.dispatch_down(n)
dlr_sys = common.system_dispatch_down_mwh(n)
dlr_hours = common.binding_hours(n)

# ---- Compare ------------------------------------------------------------------
# Two numbers: the North-West alone, and the whole island. The optimiser
# minimises island cost, so relaxing NW lines can export more NW wind AND let
# the island re-arrange where it spills; judge DLR on the island figure.
total_base = base_dd["dispatch_down_mwh"].sum()
total_dlr = dlr_dd["dispatch_down_mwh"].sum()
print(f"\nNW renewable dispatch-down:     static {total_base:,.0f} MWh -> "
      f"DLR {total_dlr:,.0f} MWh  ({100*(total_dlr-total_base)/total_base:+.0f} %)")
print(f"island renewable dispatch-down: static {base_sys:,.0f} MWh -> "
      f"DLR {dlr_sys:,.0f} MWh  ({100*(dlr_sys-base_sys)/base_sys:+.0f} %)")

cmp = pd.DataFrame({
    "static_hours_at_rating": base_hours.reindex(overhead).fillna(0).astype(int),
    "dlr_hours_at_rating": dlr_hours.reindex(overhead).fillna(0).astype(int),
})
cmp = cmp[cmp.max(axis=1) > 0].sort_values("static_hours_at_rating", ascending=False)
print("\nbinding hours per overhead line, static vs DLR:")
print(cmp.to_string())
common.save(cmp, "q3_dlr_binding_hours.csv")

per_farm = pd.DataFrame({"static_mwh": base_dd["dispatch_down_mwh"],
                         "dlr_mwh": dlr_dd["dispatch_down_mwh"].reindex(base_dd.index)})
common.save(per_farm, "q3_dlr_per_farm.csv")

# ---- Plot ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
cmp.head(10).plot.bar(ax=ax)
ax.set_ylabel("hours at rating")
ax.set_title(f"DLR (+{DLR_GAIN:.0%} at full wind): dispatch-down "
             f"{total_base:,.0f} -> {total_dlr:,.0f} MWh")
fig.tight_layout()
fig.savefig(f"{common.OUT}/q3_dlr.png", dpi=150)
print(f"-> {common.OUT}/q3_dlr.png")
