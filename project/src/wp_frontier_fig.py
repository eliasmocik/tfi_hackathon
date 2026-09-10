"""A cleaned-up version of the fairness-against-spill frontier.

Same numbers as out/<case>_frontier_jain.png, read from the same summary CSV -
nothing is recomputed and no point moves. The changes are layout only: the
legend box is dropped in favour of direct labels, the coincident points at the
bottom-left are labelled as coincident rather than overprinted, and the b
labels are offset off the curve.

    python project/src/wp_frontier_fig.py [case]   ->  out/fig_frontier_jain.png
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
CASE = sys.argv[1] if len(sys.argv) > 1 else "WP2033s43"

INK, INK2, INK3 = "#11161c", "#5d6773", "#98a1ad"
BAND = "#e0a020"      # the band sweep
TODAY = "#2a78d6"     # rule 1
EFF = "#e0592a"       # rule 2
NODAL = "#1baf7a"     # rule 3
NPD = "#c060a0"       # rule 1N
GRID = "#e3e6ea"

BANDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10]


def main() -> int:
    s = pd.read_csv(os.path.join(OUT, f"{CASE}_summary.csv")).set_index("rule")
    x = [float(s.loc[f"band{b}", "D_pct"]) for b in BANDS] + [float(s.loc["bandinf", "D_pct"])]
    y = [float(s.loc[f"band{b}", "Jain_farm"]) for b in BANDS] + [float(s.loc["bandinf", "Jain_farm"])]
    labels = [f"b={b}" for b in BANDS] + ["b=∞"]

    fig, ax = plt.subplots(figsize=(9.4, 5.9), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(x, y, "-", color=BAND, lw=2.1, zorder=2, solid_capstyle="round")
    ax.plot(x, y, "o", color=BAND, ms=6.5, zorder=3,
            markeredgecolor="white", markeredgewidth=1.2)

    # b labels, offset consistently up-left of the curve so none sits on it
    for xi, yi, lb in zip(x, y, labels):
        ax.annotate(lb, (xi, yi), textcoords="offset points", xytext=(-7, 9),
                    ha="right", fontsize=9, color=INK2)

    def ref(rule, colour, marker, ms, text, dx, dy, ha="left"):
        px, py = float(s.loc[rule, "D_pct"]), float(s.loc[rule, "Jain_farm"])
        ax.plot([px], [py], marker, color=colour, ms=ms, zorder=4,
                markeredgecolor="white", markeredgewidth=1.3)
        ax.annotate(text, (px, py), textcoords="offset points", xytext=(dx, dy),
                    ha=ha, fontsize=10, color=colour, fontweight="medium")
        return px, py

    ref("rule1", TODAY, "o", 11, "Rule 1  pro rata\n(today)", 13, -4)
    ref("rule1N", NPD, "^", 10, "Rule 1N  non-priority first\nworse on both axes", 13, -6)
    # rule 2 and b = infinity are the same point by construction; say so once
    ref("rule2", EFF, "s", 10, "Rule 2  effectiveness order\n(= b = ∞)", 12, 6)
    ref("rule3", NODAL, "D", 9, "Rule 3  nodal optimum", -2, -25)

    ax.set_xlabel("dispatch-down, % of the group's available energy"
                  "        ← less wind spilled", fontsize=10.5, color=INK2)
    ax.set_ylabel("Jain index on farm year-end ratio"
                  "        more equal →", fontsize=10.5, color=INK2)
    ax.set_title("Every rule sits on one trade-off, and the band is the dial along it",
                 fontsize=13.5, color=INK, pad=14, loc="left", fontweight="semibold")

    ax.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK3, labelsize=9.5, length=0)
    ax.margins(x=0.10, y=0.13)

    n = int(s.loc["rule1", "N_farms"])
    fig.text(0.012, 0.015,
             f"{CASE}: simulated year, {n} farms, North-West Constraint Group 3. "
             "Jain 1 = every farm cut in equal proportion. "
             f"Source: out/{CASE}_summary.csv",
             fontsize=8.2, color=INK3)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    p = os.path.join(OUT, "fig_frontier_jain.png")
    fig.savefig(p)
    plt.close(fig)
    print(f"wrote {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
