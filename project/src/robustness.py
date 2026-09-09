"""MASTER §8 — robustness table across the three cases, from out/<case>_summary.csv, _station_r.csv, _overload_stats.json.
Writes out/robustness.csv (one row per case x rule with D, D_ratio, Jain, Gini, ...), out/robustness_station_rank.csv
(rank order of stations under rule 1 per case, with Spearman between cases) and out/robustness_statements.csv
(each candidate statement evaluated per case; 'holds_in_all' says whether it is a result)."""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402
import rules as R  # noqa: E402

OUT = ep.OUT
CASES = list(ep.CASES)


def main():
    rows = []
    S = {}
    for c in CASES:
        s = pd.read_csv(os.path.join(OUT, f"{c}_summary.csv"), index_col=0)
        S[c] = s
        with open(os.path.join(OUT, f"{c}_overload_stats.json")) as f:
            ov = json.load(f)
        for r in s.index:
            rows.append(dict(case=c, hours=ov["hours"], step=ov["step"], overload_hours=ov["hours_any_overload"],
                             overload_MWh=ov["total_overload_MWh_all_rows"], rule=r, D_pct=s.at[r, "D_pct"], D_ratio=s.at[r, "D_ratio"],
                             PoF_eff=s.at[r, "PoF_eff"], PoF_nodal=s.at[r, "PoF_nodal"], Jain_farm=s.at[r, "Jain_farm"],
                             Jain_station=s.at[r, "Jain_station"], Gini=s.at[r, "Gini"], worst_over_mean=s.at[r, "worst_over_mean"],
                             residual_hours=s.at[r, "residual_hours"], postcut_violations=s.at[r, "postcut_violations"]))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(OUT, "robustness.csv"), index=False)

    # station rank order under rule 1
    ranks = {}
    for c in CASES:
        st = pd.read_csv(os.path.join(OUT, f"{c}_station_r.csv"))
        st = st[st.rule == "rule1"].set_index("station")
        ranks[c] = st.r_s
    Rk = pd.DataFrame(ranks)
    for c in CASES:
        Rk[f"rank_{c}"] = Rk[c].rank(ascending=False)
    Rk = Rk.sort_values("WP2024s42", ascending=False)
    Rk.index.name = "station"
    Rk.to_csv(os.path.join(OUT, "robustness_station_rank.csv"))
    pairs = []
    for a, b in [("WP2024s42", "WP2033s42"), ("WP2024s42", "WP2033s43"), ("WP2033s42", "WP2033s43")]:
        rho, p = spearmanr(Rk[a], Rk[b])
        pairs.append(dict(case_a=a, case_b=b, spearman_rho=float(rho), p_value=float(p), N=len(Rk),
                          top_a=Rk[a].idxmax(), top_b=Rk[b].idxmax(), bottom_a=Rk[a].idxmin(), bottom_b=Rk[b].idxmin(),
                          max_over_min_a=float(Rk[a].max() / Rk[a].min()), max_over_min_b=float(Rk[b].max() / Rk[b].min())))
    pd.DataFrame(pairs).to_csv(os.path.join(OUT, "robustness_station_rank_pairs.csv"), index=False)

    # statements
    bands = ["band0", "band1", "band2", "band3", "band5", "band10", "bandinf"]
    def stmt(name, fn, fmt=None):
        vals = {c: fn(S[c]) for c in CASES}
        holds = {c: bool(v[0]) for c, v in vals.items()}
        return dict(statement=name, **{f"{c}_holds": holds[c] for c in CASES},
                    **{f"{c}_value": v[1] for c, v in vals.items()}, holds_in_all=all(holds.values()))
    st = [
        stmt("D_rule2 < D_rule1 (effectiveness order cuts less energy than pro rata)", lambda s: (s.at["rule2", "D_pct"] < s.at["rule1", "D_pct"], s.at["rule1", "D_pct"] - s.at["rule2", "D_pct"])),
        stmt("D_rule3 <= D_rule2 (LP never worse than greedy)", lambda s: (s.at["rule3", "D_pct"] <= s.at["rule2", "D_pct"] + 1e-12, s.at["rule2", "D_pct"] - s.at["rule3", "D_pct"])),
        stmt("PoF_eff(rule1) between 0.10 and 0.20", lambda s: (0.10 <= s.at["rule1", "PoF_eff"] <= 0.20, s.at["rule1", "PoF_eff"])),
        stmt("PoF_eff(rule1) > 0.10", lambda s: (s.at["rule1", "PoF_eff"] > 0.10, s.at["rule1", "PoF_eff"])),
        stmt("D_ratio(rule2) between 0.85 and 0.90", lambda s: (0.85 <= s.at["rule2", "D_ratio"] <= 0.90, s.at["rule2", "D_ratio"])),
        stmt("Jain_farm(rule1) > 0.97", lambda s: (s.at["rule1", "Jain_farm"] > 0.97, s.at["rule1", "Jain_farm"])),
        stmt("Jain_farm(rule2) < 0.35", lambda s: (s.at["rule2", "Jain_farm"] < 0.35, s.at["rule2", "Jain_farm"])),
        stmt("Gini(rule2) > 0.65", lambda s: (s.at["rule2", "Gini"] > 0.65, s.at["rule2", "Gini"])),
        stmt("worst_over_mean(rule2) > 4", lambda s: (s.at["rule2", "worst_over_mean"] > 4, s.at["rule2", "worst_over_mean"])),
        stmt("D decreases monotonically with b (band0 ... bandinf)", lambda s: (bool(np.all(np.diff(s.loc[bands, "D_pct"].values) <= 1e-12)), float(np.diff(s.loc[bands, "D_pct"].values).max()))),
        stmt("Jain_farm decreases monotonically with b", lambda s: (bool(np.all(np.diff(s.loc[bands, "Jain_farm"].values) <= 1e-12)), float(np.diff(s.loc[bands, "Jain_farm"].values).max()))),
        stmt("band3 keeps Jain_farm > 0.75", lambda s: (s.at["band3", "Jain_farm"] > 0.75, s.at["band3", "Jain_farm"])),
        stmt("band3 recovers more than a third of the rule-1 excess over rule 2 ((D1-D_b3)/(D1-D2) > 1/3)", lambda s: ((s.at["rule1", "D_pct"] - s.at["band3", "D_pct"]) / (s.at["rule1", "D_pct"] - s.at["rule2", "D_pct"]) > 1 / 3, (s.at["rule1", "D_pct"] - s.at["band3", "D_pct"]) / (s.at["rule1", "D_pct"] - s.at["rule2", "D_pct"]))),
        stmt("band3 recovers less than half of the rule-1 excess over rule 2", lambda s: ((s.at["rule1", "D_pct"] - s.at["band3", "D_pct"]) / (s.at["rule1", "D_pct"] - s.at["rule2", "D_pct"]) < 0.5, (s.at["rule1", "D_pct"] - s.at["band3", "D_pct"]) / (s.at["rule1", "D_pct"] - s.at["rule2", "D_pct"]))),
        stmt("band10 keeps Jain_farm > 0.35", lambda s: (s.at["band10", "Jain_farm"] > 0.35, s.at["band10", "Jain_farm"])),
        stmt("D_rule1N > D_rule1 (non-priority first cuts more energy than pro rata)", lambda s: (s.at["rule1N", "D_pct"] > s.at["rule1", "D_pct"], s.at["rule1N", "D_pct"] - s.at["rule1", "D_pct"])),
        stmt("Jain_farm(rule1N) < 0.5", lambda s: (s.at["rule1N", "Jain_farm"] < 0.5, s.at["rule1N", "Jain_farm"])),
        stmt("band0 within 0.3 pp of rule 1 in D", lambda s: (abs(s.at["band0", "D_pct"] - s.at["rule1", "D_pct"]) < 0.3, s.at["band0", "D_pct"] - s.at["rule1", "D_pct"])),
        stmt("no residual hours under any rule", lambda s: (int(s.residual_hours.sum()) == 0, int(s.residual_hours.sum()))),
        stmt("post-cut violations: rule 1 has none", lambda s: (int(s.at["rule1", "postcut_violations"]) == 0, int(s.at["rule1", "postcut_violations"]))),
        stmt("post-cut violations: rule 2 has none", lambda s: (int(s.at["rule2", "postcut_violations"]) == 0, int(s.at["rule2", "postcut_violations"]))),
        stmt("Jain_farm(rule3) > Jain_farm(rule2)", lambda s: (s.at["rule3", "Jain_farm"] > s.at["rule2", "Jain_farm"], s.at["rule3", "Jain_farm"] - s.at["rule2", "Jain_farm"])),
    ]
    # station-order statements
    for name, fn in [("Sligo is the most-cut station under rule 2", lambda c: (pd.read_csv(os.path.join(OUT, f"{c}_station_r.csv")).query("rule=='rule2'").set_index("station").r_s.idxmax() == "Sligo", pd.read_csv(os.path.join(OUT, f"{c}_station_r.csv")).query("rule=='rule2'").set_index("station").r_s.idxmax())),
                     ("Station max/min under rule 1 < 1.5", lambda c: (float(Rk[c].max() / Rk[c].min()) < 1.5, float(Rk[c].max() / Rk[c].min()))),
                     ("Top rule-1 station equals WP2024s42's top station", lambda c: (Rk[c].idxmax() == Rk["WP2024s42"].idxmax(), Rk[c].idxmax()))]:
        vals = {c: fn(c) for c in CASES}
        st.append(dict(statement=name, **{f"{c}_holds": bool(v[0]) for c, v in vals.items()},
                       **{f"{c}_value": v[1] for c, v in vals.items()}, holds_in_all=all(bool(v[0]) for v in vals.values())))
    ST = pd.DataFrame(st)
    ST.to_csv(os.path.join(OUT, "robustness_statements.csv"), index=False)
    print(T.pivot(index="rule", columns="case", values=["D_pct", "Jain_farm"]).to_string())
    print(Rk.to_string())
    print(pd.DataFrame(pairs).to_string(index=False))
    print(ST[["statement", "holds_in_all"] + [f"{c}_value" for c in CASES]].to_string(index=False))


if __name__ == "__main__":
    main()
