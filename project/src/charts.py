"""MASTER §5 charts: out/<case>_frontier_jain.png, out/<case>_frontier_gini.png, out/WP2024s42_station_bars.png.
Every plotted number is read from out/<case>_summary.csv and out/<case>_station_r.csv."""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402

OUT = ep.OUT
try:
    sys.path.insert(0, ep.KIT)
    import plotstyle
    plotstyle.use()
    C = list(plotstyle.CATEGORICAL)
    INK, INK_SOFT = plotstyle.INK, plotstyle.INK_SOFT
    STYLE = "kit/plotstyle.py"
except Exception as e:  # pragma: no cover
    C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    INK, INK_SOFT = "#0b0b0b", "#52514e"
    STYLE = f"matplotlib default ({e})"

# fixed colour slots: rule 1 -> slot 0, rule 2 -> 1, rule 3 -> 2, band sweep -> 3, rule 1N -> 4 (never cycled)
SLOT = {"rule1": C[0], "rule2": C[1], "rule3": C[2], "band": C[3], "rule1N": C[4]}
LABEL = {"rule1": "Rule 1 pro rata", "rule2": "Rule 2 effectiveness order", "rule3": "Rule 3 nodal optimum (LP)",
         "rule1N": "Rule 1N non-priority first (SEM-24-044 stated intent, not live)", "band": "Rule 4 band sweep, b in pp"}
BANDS = [("band0", "0"), ("band1", "1"), ("band2", "2"), ("band3", "3"), ("band5", "5"), ("band10", "10"), ("bandinf", "inf")]
MARK = {"rule1": "o", "rule2": "s", "rule3": "D", "rule1N": "^"}


def frontier(case: str, metric: str, ylabel: str, fname: str):
    S = pd.read_csv(os.path.join(OUT, f"{case}_summary.csv"), index_col=0)
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=160)
    xs = [S.at[b, "D_pct"] for b, _ in BANDS]
    ys = [S.at[b, metric] for b, _ in BANDS]
    ax.plot(xs, ys, "-", color=SLOT["band"], lw=2, zorder=2, label=LABEL["band"])
    ax.scatter(xs, ys, s=42, color=SLOT["band"], edgecolor="white", linewidth=1.5, zorder=3)
    boff = {"0": (-30, 8), "inf": (-36, -6)}
    for (b, lab), x, y in zip(BANDS, xs, ys):
        ax.annotate(f"b={lab}", (x, y), xytext=boff.get(lab, (6, 4)), textcoords="offset points", fontsize=8, color=INK_SOFT)
    roff = {"rule1": (10, -3), "rule2": (12, -10), "rule3": (12, 8), "rule1N": (-8, 10)}
    rha = {"rule1": "left", "rule2": "left", "rule3": "left", "rule1N": "right"}
    for r in ["rule1", "rule2", "rule3", "rule1N"]:
        x, y = S.at[r, "D_pct"], S.at[r, metric]
        ax.scatter([x], [y], s=90, marker=MARK[r], color=SLOT[r], edgecolor="white", linewidth=1.5, zorder=4, label=LABEL[r])
        ax.annotate(LABEL[r].split(" (")[0], (x, y), xytext=roff[r], textcoords="offset points", fontsize=8, color=INK, ha=rha[r])
    ax.margins(x=0.12, y=0.10)
    ax.set_xlabel("D: dispatch-down as % of available energy in the group")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{case}: fairness against dispatch-down, one point per rule")
    ax.legend(loc="best", fontsize=7.5, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname))
    plt.close(fig)


def station_bars(case: str = "WP2024s42"):
    st = pd.read_csv(os.path.join(OUT, f"{case}_station_r.csv"))
    rules = [("rule1", "Rule 1 pro rata", SLOT["rule1"]), ("rule2", "Rule 2 effectiveness", SLOT["rule2"]),
             ("rule3", "Rule 3 nodal LP", SLOT["rule3"]), ("band3", "Rule 4 band b=3 pp", SLOT["band"])]
    piv = st.pivot(index="station", columns="rule", values="r_s")
    piv = piv.sort_values("rule1", ascending=False)
    n = len(piv); k = len(rules)
    fig, ax = plt.subplots(figsize=(9.6, 4.8), dpi=160)
    width = 0.8 / k
    x = np.arange(n)
    for j, (r, lab, col) in enumerate(rules):
        vals = 100 * piv[r].to_numpy()
        ax.bar(x + (j - (k - 1) / 2) * width, vals, width=width * 0.92, color=col, label=lab, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(piv.index, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("r_s: station dispatch-down, % of available energy")
    ax.set_title(f"{case}: station-level dispatch-down under four rules (full year)")
    ax.legend(fontsize=8, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"{case}_station_bars.png"))
    plt.close(fig)


if __name__ == "__main__":
    cases = sys.argv[1:] or list(ep.CASES)
    for c in cases:
        frontier(c, "Jain_farm", "Jain index on farm r_i (1 = equal)", f"{c}_frontier_jain.png")
        frontier(c, "Gini", "Gini on farm r_i (0 = equal)", f"{c}_frontier_gini.png")
        print(f"[{c}] frontier charts written ({STYLE})")
    if "WP2024s42" in cases:
        station_bars("WP2024s42")
        print("[WP2024s42] station bars written")
