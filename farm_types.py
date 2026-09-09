"""Farm control classes for the TPSA hackathon kit.

Three classes, matching EirGrid's real-world categories:

    A  controllable   Category (ii): WDT can set any MW setpoint. Cut first.
    B  priority       Priority-dispatch units (SEM-11-062): still controllable,
                      but dispatched down only after every non-priority farm in
                      the same corridor is exhausted. Curtailment (SNSP) still
                      hits them. "Immune" does not exist in practice.
    C  uncontrollable Non-categorised / Category (i): no setpoint control. The
                      only lever is opening the breaker (all-or-nothing). In the
                      LP we make them the very last to be cut and flag any cut as
                      a breaker trip.

Implementation: the kit already dispatches down by bid price (wind bids -1, so
being cut is a last resort). We tier the bid:

    A -> -1     B -> -2     C -> -3

A more negative bid means the optimiser only backs the unit off when nothing
cheaper is left. Costs are placeholders anyway; only the ORDER matters.

Usage:
    import gridkit, farm_types as ft
    n = gridkit.load("WP2033", "north-west")
    ft.set_class(n, {"Meentycat": "B", "Sorne Hill": "C"})    # by generator name
    ft.set_class_by_bus(n, {"Binbane": "C"})                   # every wind/solar at a bus
    gridkit.solve(n)
    print(ft.report(n))
"""
from __future__ import annotations

import pandas as pd

TIER = {"A": -1.0, "B": -2.0, "C": -3.0}
LABEL = {"A": "controllable", "B": "priority", "C": "uncontrollable"}
DISPATCHABLE = ("wind", "solar")


def init(network) -> None:
    """Give every wind/solar generator class A unless already set."""
    g = network.generators
    if "control_class" not in g.columns:
        g["control_class"] = "A"
    mask = g["carrier"].isin(DISPATCHABLE)
    g.loc[mask & g["control_class"].isna(), "control_class"] = "A"
    _apply(network)


def set_class(network, mapping: dict[str, str]) -> None:
    """mapping: {generator_name: 'A'|'B'|'C'}."""
    init(network)
    for name, cls in mapping.items():
        cls = cls.upper()
        if cls not in TIER:
            raise ValueError(f"class must be A, B or C, got {cls!r}")
        if name not in network.generators.index:
            raise KeyError(f"no generator named {name!r}")
        network.generators.at[name, "control_class"] = cls
    _apply(network)


def set_class_by_bus(network, mapping: dict[str, str]) -> None:
    """mapping: {bus_name: 'A'|'B'|'C'} applied to every wind/solar unit there."""
    init(network)
    g = network.generators
    for bus, cls in mapping.items():
        names = g.index[(g["bus"] == bus) & g["carrier"].isin(DISPATCHABLE)]
        if len(names) == 0:
            raise KeyError(f"no wind/solar generator at bus {bus!r}")
        set_class(network, {nm: cls for nm in names})


def _apply(network) -> None:
    g = network.generators
    mask = g["carrier"].isin(DISPATCHABLE)
    g.loc[mask, "marginal_cost"] = g.loc[mask, "control_class"].map(TIER)


def dispatch_down_by_unit(network) -> pd.DataFrame:
    """MWh available minus MWh delivered, per wind/solar unit, over all snapshots."""
    g = network.generators
    mask = g["carrier"].isin(DISPATCHABLE)
    names = g.index[mask]
    avail = (network.generators_t.p_max_pu[names] * g.loc[names, "p_nom"]).sum()
    out = network.generators_t.p[names].sum()
    df = pd.DataFrame({
        "bus": g.loc[names, "bus"],
        "class": g.loc[names, "control_class"],
        "p_nom": g.loc[names, "p_nom"],
        "available_mwh": avail,
        "delivered_mwh": out,
    })
    df["dispatched_down_mwh"] = df["available_mwh"] - df["delivered_mwh"]
    df["share"] = df["dispatched_down_mwh"] / df["available_mwh"].where(df["available_mwh"] > 0)
    return df.sort_values("dispatched_down_mwh", ascending=False)


def breaker_trips(network, tol: float = 1e-3) -> pd.DataFrame:
    """Hours where a class-C unit was cut: in reality that is a breaker trip, not a setpoint."""
    g = network.generators
    c = g.index[(g["control_class"] == "C") & g["carrier"].isin(DISPATCHABLE)]
    if len(c) == 0:
        return pd.DataFrame(columns=["unit", "snapshot", "available_mw", "delivered_mw"])
    avail = network.generators_t.p_max_pu[c] * g.loc[c, "p_nom"]
    out = network.generators_t.p[c]
    cut = (avail - out) > tol
    rows = [(u, t, float(avail.at[t, u]), float(out.at[t, u]))
            for u in c for t in network.snapshots if cut.at[t, u]]
    return pd.DataFrame(rows, columns=["unit", "snapshot", "available_mw", "delivered_mw"])


def report(network) -> str:
    df = dispatch_down_by_unit(network)
    by_class = df.groupby("class")[["available_mwh", "dispatched_down_mwh"]].sum()
    by_class["share"] = by_class["dispatched_down_mwh"] / by_class["available_mwh"]
    by_class.index = [f"{k} {LABEL[k]}" for k in by_class.index]
    trips = breaker_trips(network)
    lines = ["dispatch-down by control class (MWh over the study period)",
             by_class.round(1).to_string(), ""]
    if len(trips):
        lines.append(f"class-C units cut in {len(trips)} unit-hours -> breaker trips in reality, "
                     f"not partial setpoints: {sorted(trips['unit'].unique())}")
    else:
        lines.append("no class-C unit was cut (no breaker trips needed)")
    return "\n".join(lines)
