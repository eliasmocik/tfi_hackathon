"""Shared setup for problem 3.1 (North-West analysis).

Every q*.py script starts with:   n = common.baseline()
and then works on the North-West subset of the all-island network.

Why all-island and not the 15-node "north-west" scope?
  The 15-node scope pins every boundary tie at a fixed MW and folds Srananagh
  into one bus, so all extra export is forced through one transformer. The
  all-island network has free ties and the real 110/220 kV split. We use it and
  simply filter results to the North-West stations.  Set QUICK=1 in the shell
  to use the small scope for fast iteration (2 s per solve instead of 12 s).
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(os.path.dirname(HERE), "participant-kit")
sys.path.insert(0, KIT)
import gridkit   # noqa: E402  (the organisers' helpers)
import flowmath  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

SCENARIO = "WP2033"                                   # the constrained case
SCOPE = "north-west" if os.environ.get("QUICK") else "all-island"

# Stations on the brochure's Figure 3 (EirGrid NW constraint groups 1-3).
# Names as they appear in n.buses["station"] of the all-island network.
NW_STATIONS = [
    "ARDNAGAPPARY", "BINBANE", "CATH_FALL", "CATH FALL", "CATH", "CLIFF",
    "CLOGHER", "CORDERRY", "CROAGHONAGH", "CUNGHILL", "DRUMKEEN", "GLENREE",
    "GOLAGH", "LENALEA", "LETTERKENNY", "MEENTYCAT", "MOY", "SLIGO",
    "SORNE HILL", "SRANANAGH", "TIEVEBRACK", "TRILLICK",
]

RENEWABLE = ("wind", "solar")
WIND_BID = -1.0     # existing wind/solar bid. Kit ships 0.0, which makes the
                    # optimiser indifferent about WHICH farm to cut. -1 means
                    # "being cut is a last resort" and matches the brochure.


def baseline(scenario=SCENARIO, scope=SCOPE, verbose=True):
    """Load the network, set renewable bids, solve, freeze dispatch."""
    gridkit.quiet()
    n = gridkit.load(scenario, scope)
    set_renewable_bids(n, WIND_BID)
    solve(n)
    if verbose:
        print(f"loaded {scenario} {scope}: {len(n.buses)} buses, "
              f"{len(n.lines)} lines, {len(n.snapshots)} hours")
    return n


def set_renewable_bids(n, cost, jitter=1e-4):
    """Give every wind/solar unit the same bid, plus a tiny fixed offset.

    With identical bids the optimiser is indifferent about WHICH farm to
    cut when a shared line binds, and regional totals (like "North-West
    dispatch-down") jump around between otherwise identical solves. A
    deterministic offset of at most 0.01 EUR/MWh removes the tie without
    changing anything physical. Order is by name, so it is reproducible.
    """
    g = n.generators
    names = sorted(g.index[g["carrier"].isin(RENEWABLE)])
    for i, name in enumerate(names):
        g.at[name, "marginal_cost"] = cost - jitter * i / max(len(names), 1)


def solve(n):
    """Least-cost dispatch with line duals kept (needed for shadow prices).

    Do NOT call gridkit.freeze_dispatch() between solves: it copies the
    dispatch into p_set, and PyPSA 1.x treats a non-null generator p_set as a
    FIXED dispatch in the next optimisation. Every re-solve would then return
    the baseline unchanged. We read flows from lines_t.p0 (written by the
    optimiser), so nothing here needs lpf().
    """
    unfreeze(n)
    gridkit.solve(n, assign_all_duals=True)


def unfreeze(n):
    """Clear any fixed set-points so the optimiser is free to re-dispatch."""
    for comp in ("generators", "storage_units", "links"):
        static = getattr(n, comp)
        if "p_set" in static.columns:
            static["p_set"] = np.nan
        dyn = getattr(n, comp + "_t")
        if "p_set" in dyn and len(dyn.p_set.columns):
            dyn.p_set = dyn.p_set.iloc[:, :0]


# ---- North-West subset helpers -------------------------------------------

def nw_buses(n):
    """Bus names whose station is in the North-West list."""
    if SCOPE == "north-west":
        return list(n.buses.index)
    st = n.buses["station"].fillna("").str.upper()
    return list(n.buses.index[st.isin(NW_STATIONS)])


def nw_lines(n):
    """Lines with at least one end in the North-West (includes the ties out)."""
    b = set(nw_buses(n))
    return list(n.lines.index[n.lines["bus0"].isin(b) | n.lines["bus1"].isin(b)])


def nw_transformers(n):
    if len(n.transformers) == 0:
        return []
    b = set(nw_buses(n))
    return list(n.transformers.index[n.transformers["bus0"].isin(b)
                                     | n.transformers["bus1"].isin(b)])


def nw_renewables(n):
    """Wind/solar generators sitting at North-West buses."""
    g = n.generators
    return list(g.index[g["bus"].isin(nw_buses(n)) & g["carrier"].isin(RENEWABLE)])


def label(n, bus):
    """'3581 LETTERKENNY' - a readable bus label."""
    st = n.buses.at[bus, "station"] if "station" in n.buses else ""
    return f"{bus} {st}" if isinstance(st, str) and st else str(bus)


# ---- results helpers ------------------------------------------------------

def binding_hours(n, threshold=0.999):
    """Hours each line AND transformer sits at its rating."""
    hours = gridkit.binding(n, threshold)                # lines only
    if len(n.transformers):
        load = n.transformers_t.p0.abs().div(n.transformers["s_nom"], axis=1)
        hours = pd.concat([hours, (load >= threshold).sum()])
    return hours.sort_values(ascending=False)


def dispatch_down(n, gens=None):
    """MWh offered minus MWh delivered, per generator, over the week."""
    gens = list(gens) if gens is not None else nw_renewables(n)
    gens = [g for g in gens if g in n.generators_t.p_max_pu.columns]
    p_nom = n.generators.loc[gens, "p_nom"]
    offered = (n.generators_t.p_max_pu[gens] * p_nom).sum()
    delivered = n.generators_t.p[gens].sum()
    df = pd.DataFrame({"offered_mwh": offered, "delivered_mwh": delivered})
    df["dispatch_down_mwh"] = df["offered_mwh"] - df["delivered_mwh"]
    df["dispatch_down_pct"] = 100 * df["dispatch_down_mwh"] / df["offered_mwh"].replace(0, np.nan)
    df["bus"] = n.generators.loc[gens, "bus"]
    return df.sort_values("dispatch_down_mwh", ascending=False)


def system_dispatch_down_mwh(n):
    """Island-wide renewable MWh dispatched down. Report this next to the NW
    figure: the optimiser minimises SYSTEM cost, so a change that helps the
    island can move dispatch-down into or out of the North-West."""
    g = n.generators
    gens = [x for x in g.index[g["carrier"].isin(RENEWABLE)]
            if x in n.generators_t.p_max_pu.columns]
    return float(dispatch_down(n, gens)["dispatch_down_mwh"].sum())


def nearest_wind_profile(n, bus):
    """Borrow the hourly profile of the closest existing wind farm.

    A new generator with no profile would run at 100 % every hour (PyPSA
    default), which is the classic trap in this kit.
    """
    wind = n.generators.index[(n.generators["carrier"] == "wind")
                              & n.generators.index.isin(n.generators_t.p_max_pu.columns)]
    if len(wind) == 0:
        raise RuntimeError("no wind farm with a profile in this network")
    xy = n.buses.loc[n.generators.loc[wind, "bus"], ["x", "y"]].to_numpy()
    here = n.buses.loc[bus, ["x", "y"]].to_numpy(dtype=float)
    d = np.hypot(xy[:, 0] - here[0], xy[:, 1] - here[1])
    return n.generators_t.p_max_pu[wind[int(np.argmin(d))]].copy()


def line_duals(n):
    """Shadow price per branch per hour, EUR per MW of extra rating.

    PyPSA gives mu_upper <= 0 (flow at +rating) and mu_lower >= 0 (flow at
    -rating). Their sum keeps the sign of the flow direction, which is what a
    PTDF product needs. Includes transformers.
    """
    mu = n.lines_t.mu_upper + n.lines_t.mu_lower
    if len(n.transformers):
        mu = pd.concat([mu, n.transformers_t.mu_upper + n.transformers_t.mu_lower], axis=1)
    return mu


def save(df, name):
    path = os.path.join(OUT, name)
    df.to_csv(path)
    print(f"-> {path}")
