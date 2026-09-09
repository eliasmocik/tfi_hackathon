"""MASTER §5 — per-farm, per-station and group metrics for every rule and band, per case.

    python src/metrics.py [case ...]

Reads out/<case>_cuts_<rule>.parquet, _avail.parquet, _group_units.csv, _<rule>_residual.csv, _postcut_violations.csv.
Writes out/<case>_summary.csv, out/<case>_farm_r.csv, out/<case>_station_r.csv, out/<case>_assertions.csv.
Assertions (reported, never hidden): band-inf cuts identical to rule 2; per hour sum c(rule3) <= sum c(rule2) <= sum c(rule1) + 1e-6.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402
import rules as R  # noqa: E402

OUT = ep.OUT
ORDER_TOL = 1e-6


def jain(x):
    x = np.asarray(x, float)
    N = len(x)
    s2 = (x ** 2).sum()
    return float(x.sum() ** 2 / (N * s2)) if s2 > 0 else np.nan


def gini(x):
    """Unweighted, no small-sample correction: G = sum_i (2i - N - 1) x_(i) / (N sum x), ascending sort, i = 1..N."""
    x = np.sort(np.asarray(x, float))
    N = len(x)
    s = x.sum()
    if s <= 0:
        return np.nan
    i = np.arange(1, N + 1)
    return float(((2 * i - N - 1) * x).sum() / (N * s))


def case_metrics(case: str):
    step = ep.CASES[case]["step"]
    units = pd.read_csv(os.path.join(OUT, f"{case}_group_units.csv"), dtype={"bus": str})
    u = units[units["class"] != "U"].reset_index(drop=True)
    G = u.generator.tolist()
    a = pd.read_parquet(os.path.join(OUT, f"{case}_avail.parquet"))[G]
    cum_avail = a.sum(axis=0) * step                       # MWh per farm over the year
    pc = pd.read_csv(os.path.join(OUT, f"{case}_postcut_violations.csv")).set_index("rule")
    farm_rows, station_rows, summ = [], [], []
    D = {}
    cuts = {}
    for rule in R.RULES:
        fp = os.path.join(OUT, f"{case}_cuts_{rule}.parquet")
        if not os.path.exists(fp):
            continue
        C = pd.read_parquet(fp)[G]
        cuts[rule] = C
        cum_cut = C.sum(axis=0) * step
        hours_cut = (C > R.EPS).sum(axis=0)
        r = np.where(cum_avail > 0, cum_cut / cum_avail.replace(0, np.nan), 0.0)
        r = pd.Series(np.nan_to_num(r), index=G)
        fr = pd.DataFrame(dict(rule=rule, generator=G, bus=u.bus.values, station=u.station.values,
                               **{"class": u["class"].values}, cum_cut_MWh=cum_cut.values, cum_avail_MWh=cum_avail.values,
                               r=r.values, hours_cut=hours_cut.values))
        farm_rows.append(fr)
        st = fr.groupby("station").agg(cut_MWh=("cum_cut_MWh", "sum"), avail_MWh=("cum_avail_MWh", "sum"), n_farms=("generator", "count"))
        st["r_s"] = st.cut_MWh / st.avail_MWh
        st.insert(0, "rule", rule)
        station_rows.append(st.reset_index())
        Dv = cum_cut.sum() / cum_avail.sum()
        D[rule] = Dv
        rbar = Dv
        pos = cum_avail > 0
        summ.append(dict(rule=rule, D_pct=100 * Dv, cut_MWh=cum_cut.sum(), avail_MWh=cum_avail.sum(),
                         hours_with_cut=int((C.sum(axis=1) > R.EPS).sum()), N_farms=len(G),
                         Jain_farm=jain(r.values), Jain_station=jain(st.r_s.values), Gini=gini(r.values),
                         worst_over_mean=float(r.max() / rbar) if rbar > 0 else np.nan,
                         max_over_min=float(r[pos].max() / r[pos].min()) if r[pos].min() > 0 else np.inf,
                         r_max=float(r.max()), r_min=float(r[pos].min()), farm_r_max=r.idxmax(), farm_r_min=r[pos].idxmin(),
                         farms_r_zero=int((r[pos] == 0).sum()),
                         cut_MWh_N=float(cum_cut[u["class"].values == "N"].sum()), cut_MWh_P=float(cum_cut[u["class"].values == "P"].sum()),
                         residual_hours=int(pc.at[rule, "residual_hours"]), postcut_violations=int(pc.at[rule, "postcut_violations"]),
                         monitored_rows_newly_over=int(pc.at[rule, "monitored_rows_newly_over"])))
    S = pd.DataFrame(summ).set_index("rule")
    S["D_ratio"] = S.D_pct / S.at["rule1", "D_pct"]
    S["PoF_eff"] = (S.D_pct - S.at["rule2", "D_pct"]) / S.at["rule2", "D_pct"]
    S["PoF_nodal"] = (S.D_pct - S.at["rule3", "D_pct"]) / S.at["rule3", "D_pct"]
    S["label"] = ["SEM-24-044 stated intent, not live" if r == "rule1N" else "" for r in S.index]
    cols = ["D_pct", "D_ratio", "PoF_eff", "PoF_nodal", "Jain_farm", "Jain_station", "Gini", "worst_over_mean", "max_over_min",
            "residual_hours", "postcut_violations", "monitored_rows_newly_over", "cut_MWh", "avail_MWh", "hours_with_cut", "N_farms",
            "r_max", "r_min", "farm_r_max", "farm_r_min", "farms_r_zero", "cut_MWh_N", "cut_MWh_P", "label"]
    S = S[cols]
    S.to_csv(os.path.join(OUT, f"{case}_summary.csv"))
    pd.concat(farm_rows).to_csv(os.path.join(OUT, f"{case}_farm_r.csv"), index=False)
    pd.concat(station_rows).to_csv(os.path.join(OUT, f"{case}_station_r.csv"), index=False)
    # ---- assertions
    A = []
    if "bandinf" in cuts and "rule2" in cuts:
        d = (cuts["bandinf"].to_numpy() - cuts["rule2"].to_numpy())
        A.append(dict(check="bandinf_equals_rule2_elementwise", max_abs_diff=float(np.abs(d).max()),
                      total_diff_MWh=float(d.sum() * step), passed=bool(np.abs(d).max() == 0.0)))
    if all(k in cuts for k in ("rule1", "rule2", "rule3")):
        s1, s2, s3 = (cuts[k].sum(axis=1).to_numpy() for k in ("rule1", "rule2", "rule3"))
        v32 = s3 - s2; v21 = s2 - s1
        A.append(dict(check="per_hour_rule3_le_rule2", max_violation=float(v32.max()), hours_violating=int((v32 > ORDER_TOL).sum()),
                      passed=bool((v32 <= ORDER_TOL).all()), tol=ORDER_TOL))
        A.append(dict(check="per_hour_rule2_le_rule1", max_violation=float(v21.max()), hours_violating=int((v21 > ORDER_TOL).sum()),
                      passed=bool((v21 <= ORDER_TOL).all()), tol=ORDER_TOL))
        A.append(dict(check="hours_rule2_equals_rule3_within_1e-9", hours=int((np.abs(v32) <= 1e-9).sum()),
                      hours_rule2_gt_rule3=int((v32 < -1e-9).sum()), passed=True))
    # every rule: cuts within [0, p0], feasibility on saved cuts, for every overload hour
    cd = R.CaseData(case)
    for rule, C in cuts.items():
        Cn = C.to_numpy()
        over_p0 = float((Cn - cd.p0).max())
        neg = float(Cn.min())
        worst = 0.0
        for t in cd.over_hours:
            SF, O, p0, a, active = cd.hour(t)
            res = R.residuals(SF, O, Cn[t], active)
            worst = max(worst, float(res.max()))
        cut_no_over = float(Cn[(cd.O > 0).any(axis=1) == False].sum())
        A.append(dict(check=f"{rule}_cuts_valid", max_c_minus_p0=over_p0, min_c=neg, max_residual_MW=worst,
                      cut_MW_in_hours_without_overload=cut_no_over,
                      passed=bool(over_p0 <= 1e-9 and neg >= -1e-12 and worst <= R.TOL_MW and cut_no_over == 0.0)))
    Adf = pd.DataFrame(A)
    Adf.insert(0, "case", case)
    Adf.to_csv(os.path.join(OUT, f"{case}_assertions.csv"), index=False)
    print(f"[{case}] summary:\n{S[['D_pct','D_ratio','PoF_eff','PoF_nodal','Jain_farm','Jain_station','Gini','worst_over_mean','max_over_min','residual_hours','postcut_violations']].to_string()}")
    print(f"[{case}] assertions:\n{Adf.to_string(index=False)}")
    return S, Adf


if __name__ == "__main__":
    for c in (sys.argv[1:] or list(ep.CASES)):
        case_metrics(c)
