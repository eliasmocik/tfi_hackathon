"""MASTER §7 — simulation (WP2024s42, station r_s) against the 2026 measurement (station constraint-only ratio).

Writes out/comparison_stations.csv (one row per model station) and out/comparison_stats.csv (Spearman, Jain, Gini,
N) — every number in RESULTS §8 comes from those two files.

Station-name reconciliation (model psse/WDT names -> SEM-O map names in out/measurement_units.csv):
  upper-case the WDT name; "Cathaleen's Fall" -> CATH_FALL; "Sorne Hill" -> TRILLICK (the Sorne Hill generator unit
  sits at TRILLICK in semo_unit_map_IE.csv, so the model's Sorne Hill and Trillick stations are merged into one
  comparison station TRILLICK). ARDNAGAPPARY, MOY, SLIGO have no unit in the IE map; CATH_FALL and MULREAVY units have
  no BM-101 rows: those model stations have no measured value and are excluded from the correlation.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402
from metrics import jain, gini  # noqa: E402

OUT = ep.OUT
MODEL_TO_MAP = {"Ardnagappary": "ARDNAGAPPARY", "Binbane": "BINBANE", "Cathaleen's Fall": "CATH_FALL", "Corderry": "CORDERRY",
                "Cunghill": "CUNGHILL", "Garvagh": "GARVAGH", "Glenree": "GLENREE", "Lenalea": "LENALEA",
                "Meentycat": "MEENTYCAT", "Moy": "MOY", "Mulreavy": "MULREAVY", "Sligo": "SLIGO", "Sorne Hill": "TRILLICK",
                "Tawnaghmore": "TAWNAGHMORE", "Trillick": "TRILLICK"}
SIM_RULES = ["rule1", "rule2", "rule3", "band3"]


def main(case="WP2024s42"):
    m = pd.read_csv(os.path.join(OUT, "measurement_units.csv"))
    mf = m[m.passes_filter & m.in_CG3].copy()
    mf["dd_constraint_only_MWh"] = mf.constraint_only_ratio * mf.avail_MWh
    ms = mf.groupby("station").agg(measured_dd_MWh=("dd_constraint_only_MWh", "sum"), measured_avail_MWh=("avail_MWh", "sum"),
                                   n_measured_units=("unit", "count"), measured_units=("unit", lambda s: ";".join(s)))
    ms["measured_ratio"] = ms.measured_dd_MWh / ms.measured_avail_MWh
    # consistency with measurement_groups.csv (CG3 station level) — must agree exactly
    mg = pd.read_csv(os.path.join(OUT, "measurement_groups.csv"))
    row = mg[(mg.group == "CG3") & (mg.level == "station")].iloc[0]
    assert int(row.N) == len(ms), (row.N, len(ms))
    assert abs(float(row["max"]) - ms.measured_ratio.max()) < 1e-12 and abs(float(row["min"]) - ms.measured_ratio.min()) < 1e-12

    st = pd.read_csv(os.path.join(OUT, f"{case}_station_r.csv"))
    st["map_station"] = st.station.map(MODEL_TO_MAP)
    assert st.map_station.notna().all(), st[st.map_station.isna()].station.unique()
    sim = st.groupby(["map_station", "rule"]).agg(cut_MWh=("cut_MWh", "sum"), avail_MWh=("avail_MWh", "sum"),
                                                   n_farms=("n_farms", "sum")).reset_index()
    sim["r_s"] = sim.cut_MWh / sim.avail_MWh
    piv = sim.pivot(index="map_station", columns="rule", values="r_s")[SIM_RULES]
    piv.columns = [f"sim_{r}" for r in SIM_RULES]
    nfarm = sim[sim.rule == "rule1"].set_index("map_station").n_farms
    model_names = st.groupby("map_station").station.agg(lambda s: " + ".join(sorted(set(s))))
    tab = piv.join(ms[["measured_ratio", "n_measured_units", "measured_units", "measured_avail_MWh"]], how="left")
    tab.insert(0, "model_stations", model_names)
    tab.insert(1, "n_model_farms_G", nfarm)
    tab["in_both"] = tab.measured_ratio.notna()
    both = tab[tab.in_both]
    tab["rank_measured"] = both.measured_ratio.rank(ascending=False)
    for r in SIM_RULES:
        tab[f"rank_sim_{r}"] = both[f"sim_{r}"].rank(ascending=False)
    tab = tab.sort_values("measured_ratio", ascending=False)
    tab.index.name = "station"
    tab.to_csv(os.path.join(OUT, "comparison_stations.csv"))

    stats = []
    for r in SIM_RULES:
        rho, p = spearmanr(both.measured_ratio, both[f"sim_{r}"])
        stats.append(dict(pair=f"measured_vs_sim_{r}", N=len(both), spearman_rho=float(rho), p_value=float(p)))
    S = pd.DataFrame(stats)
    vec = {"measured": both.measured_ratio.values}
    vec.update({f"sim_{r}_common": both[f"sim_{r}"].values for r in SIM_RULES})
    vec.update({f"sim_{r}_all15": tab[f"sim_{r}"].values for r in SIM_RULES})
    J = pd.DataFrame([dict(vector=k, N=len(v), jain=jain(v), gini=gini(v), max=float(np.max(v)), min=float(np.min(v)),
                           max_over_min=float(np.max(v) / np.min(v)) if np.min(v) > 0 else np.inf) for k, v in vec.items()])
    S.to_csv(os.path.join(OUT, "comparison_stats.csv"), index=False)
    J.to_csv(os.path.join(OUT, "comparison_vectors.csv"), index=False)
    print(tab.to_string())
    print(S.to_string(index=False))
    print(J.to_string(index=False))


if __name__ == "__main__":
    main()
