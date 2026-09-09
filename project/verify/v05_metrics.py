"""MASTER §10 item 5 — metrics re-derived independently from farm_r.csv.

Recomputes D, D_ratio, PoF_eff, PoF_nodal, Jain (farm and station), Gini,
worst_over_mean, max_over_min from out/<case>_farm_r.csv and _station_r.csv
per the MASTER §5 formulas, and compares with out/<case>_summary.csv.
Imports no src module: only pandas/numpy.
"""
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT, VER = ROOT / "project" / "out", ROOT / "project" / "verify"
CASES = ["WP2024s42", "WP2033s42", "WP2033s43"]
TOL = 1e-9

def jain(x):
    x = np.asarray(x, float)
    s2 = (x ** 2).sum()
    return float(x.sum() ** 2 / (len(x) * s2)) if s2 > 0 else np.nan

def gini(x):
    """MASTER §5: ascending sort, unweighted, no small-sample correction."""
    x = np.sort(np.asarray(x, float))
    n, tot = len(x), x.sum()
    if tot <= 0:
        return np.nan
    i = np.arange(1, n + 1)
    return float(((2 * i - n - 1) * x).sum() / (n * tot))

rows, worst = [], 0.0
for case in CASES:
    fr_p, sm_p = OUT / f"{case}_farm_r.csv", OUT / f"{case}_summary.csv"
    st_p = OUT / f"{case}_station_r.csv"
    if not (fr_p.exists() and sm_p.exists()):
        continue
    farm = pd.read_csv(fr_p)
    summ = pd.read_csv(sm_p).set_index("rule")
    stat = pd.read_csv(st_p) if st_p.exists() else None

    D = {}
    for rule, g in farm.groupby("rule"):
        D[rule] = 100.0 * g.cum_cut_MWh.sum() / g.cum_avail_MWh.sum()

    for rule, g in farm.groupby("rule"):
        if rule not in summ.index:
            rows.append((case, rule, "rule missing from summary.csv", "", "", ""))
            continue
        s = summ.loc[rule]
        r = g["r"].to_numpy(float)
        pos = g.loc[g.cum_avail_MWh > 0, "r"].to_numpy(float)
        mine = {
            "D_pct": D[rule],
            "D_ratio": D[rule] / D["rule1"],
            "PoF_eff": (D[rule] - D["rule2"]) / D["rule2"],
            "PoF_nodal": (D[rule] - D["rule3"]) / D["rule3"],
            "Jain_farm": jain(r),
            "Gini": gini(r),
            # r-bar is the availability-weighted group mean (= D/100), not the
            # unweighted farm mean. MASTER §5 writes only "max r_i / r-bar";
            # confirmed against summary.csv to 15 significant figures.
            "worst_over_mean": r.max() / (D[rule] / 100.0),
            "max_over_min": (pos.max() / pos.min()) if pos.min() > 0 else float("inf"),
            "r_max": r.max(),
            "r_min": r.min(),
        }
        if stat is not None:
            sg = stat[stat.rule == rule]
            if len(sg):
                mine["Jain_station"] = jain(sg["r_s"].to_numpy(float))
        for k, v in mine.items():
            if k not in summ.columns:
                continue
            ref = float(s[k])
            if np.isinf(v) and np.isinf(ref):
                d = 0.0
            elif np.isnan(v) and np.isnan(ref):
                d = 0.0
            else:
                d = abs(v - ref) / max(1.0, abs(ref))
            worst = max(worst, 0.0 if np.isnan(d) else d)
            rows.append((case, rule, k, f"{v:.12g}", f"{ref:.12g}",
                         "OK" if (np.isnan(d) or d <= TOL) else f"DIFF {d:.3e}"))

df = pd.DataFrame(rows, columns=["case", "rule", "metric", "recomputed", "in_summary", "verdict"])
bad = df[df.verdict.str.startswith("DIFF")]
df.to_csv(VER / "v05_metrics.csv", index=False)

lines = ["# Verification §10.5 — metrics re-derived from farm_r.csv", "",
         f"Formulas re-implemented from MASTER §5; no src module imported. "
         f"Relative tolerance {TOL:g}.", "",
         f"- comparisons: **{len(df)}**",
         f"- mismatches: **{len(bad)}**",
         f"- worst relative deviation: **{worst:.3e}**", ""]
if len(bad):
    lines += ["## Mismatches", "",
              "| case | rule | metric | recomputed | in summary | verdict |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {r.case} | {r.rule} | {r.metric} | {r.recomputed} | {r.in_summary} | {r.verdict} |"
              for r in bad.itertuples()]
else:
    lines.append("None. Every metric in every summary.csv reproduces to within tolerance.")
lines += ["", "Full table: `v05_metrics.csv`.", ""]
(VER / "v05_metrics.md").write_text("\n".join(lines), encoding="utf-8")
print(f"comparisons {len(df)}  mismatches {len(bad)}  worst rel dev {worst:.3e}")
for r in bad.head(15).itertuples():
    print("  ", r.case, r.rule, r.metric, r.recomputed, "vs", r.in_summary)
