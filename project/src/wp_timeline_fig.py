"""out/fig_timeline.png - rollout timescale, and why it does not replace the build.

The rising line is not illustrative: it is the modelled dispatch-down under
today's rule on the 2024 network and on the two 2033 cases, read from the
same summary CSVs as every other figure. The constraint grows across the
period in which the rule would be deployed.

    python project/src/wp_timeline_fig.py   ->  out/fig_timeline.png
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

INK, INK2, INK3 = "#11161c", "#5d6773", "#98a1ad"
RULE = "#2a66bd"      # what the rule does
BUILD = "#e0592a"     # what only steel does
GRID = "#e3e6ea"

STAGES = [
    (0.0,  "Now",          "Nothing to build.\nThe shift factor is\nalready computed."),
    (1.0,  "6-18 months",  "Consultation,\nCRU decision,\nGrid Code / TS&C."),
    (2.0,  "2-5 years",    "Live in the\nhigh-spread groups."),
    (3.0,  "5-10 years",   "More wind connects.\nThe recoverable gap\ngrows with it."),
    (4.0,  "10-15 years",  "Reinforcement.\nThe rule cannot\nsubstitute for it."),
]


def main() -> int:
    d = {c: pd.read_csv(os.path.join(OUT, f"{c}_summary.csv"), index_col=0).at["rule1", "D_pct"]
         for c in ("WP2024s42", "WP2033s42", "WP2033s43")}

    fig, ax = plt.subplots(figsize=(12.4, 5.4), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # The constraint, measured, rising across the same period. Values are 8-11 %,
    # so they are mapped into a band beneath the timeline rather than plotted on
    # the figure's own coordinates - the real numbers stay as the labels.
    lo, hi, band0, band1 = 8.0, 11.0, 0.55, 1.95
    sc = lambda v: band0 + (v - lo) / (hi - lo) * (band1 - band0)
    xs = [0.35, 3.45, 3.95]
    ys = [d["WP2024s42"], d["WP2033s42"], d["WP2033s43"]]
    py = [sc(v) for v in ys]
    ax.fill_between(xs, band0 - 0.12, py, color=INK3, alpha=0.10, zorder=1)
    ax.plot(xs, py, "-", color=INK3, lw=1.8, zorder=2)
    ax.scatter(xs, py, s=44, color=INK2, zorder=3, edgecolor="white", linewidth=1.4)
    for x, v, yy in zip(xs, ys, py):
        ax.annotate(f"{v:.1f}%", (x, yy), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=10.5, color=INK2, fontweight="bold")
    ax.annotate("dispatch-down under today's rule,"
                "\n2024 network to 2033 network",
                (xs[0], band0 - 0.1), xytext=(0, -12), textcoords="offset points",
                ha="left", va="top", fontsize=9.4, color=INK3)

    # the timeline
    y0 = 3.0
    ax.plot([-0.35, 4.75], [y0, y0], color=GRID, lw=2.4, zorder=2, solid_capstyle="round")
    for x, when, what in STAGES:
        col = BUILD if x >= 4.0 else RULE
        ax.scatter([x], [y0], s=150, color=col, zorder=4,
                   edgecolor="white", linewidth=2.2)
        ax.annotate(when, (x, y0), xytext=(0, 17), textcoords="offset points",
                    ha="center", fontsize=11.5, color=col, fontweight="bold")
        ax.annotate(what, (x, y0), xytext=(0, -20), textcoords="offset points",
                    ha="center", va="top", fontsize=9.6, color=INK2, linespacing=1.5)

    ax.set_xlim(-0.6, 5.0)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.set_title("The rule buys time. It does not build the network.",
                 fontsize=15, color=INK, loc="left", pad=10, fontweight="bold")
    fig.text(0.012, 0.02,
             "Dispatch-down under pro rata: 8.3 % on the 2024 network, 9.4 % and 10.6 % on the two 2033 cases "
             "- which already include reinforcement. Source: out/<case>_summary.csv",
             fontsize=8.4, color=INK3)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = os.path.join(OUT, "fig_timeline.png")
    fig.savefig(p)
    plt.close(fig)
    print(f"wrote {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
