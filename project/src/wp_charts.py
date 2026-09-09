"""Charts for the real-data replay (design brief v2, presentation item 7).

The efficiency-equity frontier measured on 2026 SEM-O data, rather than on the
synthetic year. Uses the kit's own validated palette so these read as one set
with the existing frontier charts.

    python project/src/wp_charts.py

Outputs out/wpa_frontier_real.png and out/wpa_station_real.png.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
sys.path.insert(0, os.path.join(ROOT, "kit"))

try:
    import plotstyle
    plotstyle.use()
    C = list(plotstyle.CATEGORICAL)
    INK, INK_SOFT = plotstyle.INK, plotstyle.INK_SOFT
except Exception:                                    # pragma: no cover
    C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    INK, INK_SOFT = "#1a1a1a", "#6b6b6b"

BANDS = [0.0, 1.0, 2.0, 3.0, 5.0, 10.0, np.inf]


def label_for(b: float) -> str:
    return "b=∞" if np.isinf(b) else f"b={b:g}"


def frontier() -> None:
    wpa = json.loads(open(os.path.join(OUT, "wpa_summary.json")).read())
    wpe = pd.read_csv(os.path.join(OUT, "wpe_bound.csv"))

    xs, ys, bs, bounds, xb = [], [], [], [], []
    for b in BANDS:
        key = "effectiveness" if np.isinf(b) else f"band{b:g}pp"
        cut = wpa[f"{key}_cut_MWh"]
        row = wpe[np.isinf(wpe.band_pp)] if np.isinf(b) else wpe[wpe.band_pp == b]
        if not len(row):
            continue
        xs.append(cut)
        ys.append(float(row.realised_max_divergence_pp.iloc[0]))
        bs.append(b)
        cb = float(row.claimed_bound_pp.iloc[0])
        if np.isfinite(cb):
            bounds.append(cb)
            xb.append(cut)

    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=160)

    # the frontier itself: one series, so the marks carry it
    ax.plot(xs, ys, "-o", color=C[0], lw=2, ms=8, zorder=3,
            markeredgecolor="white", markeredgewidth=1.5,
            label="realised max divergence")
    ax.plot(xb, bounds, "--s", color=C[3], lw=2, ms=8, zorder=3,
            markeredgecolor="white", markeredgewidth=1.5,
            label="guaranteed bound (b + δ)")

    # observed pro rata: the status quo, marked distinctly
    obs_x = wpa["observed_cut_MWh"]
    obs_y = json.loads(open(os.path.join(OUT, "wpe_summary.json")).read())[
        "observed_pro_rata_max_divergence_pp"]
    ax.plot([obs_x], [obs_y], "D", color=C[1], ms=10, zorder=4,
            markeredgecolor="white", markeredgewidth=1.5,
            label="observed pro rata (as dispatched)")

    for x, y, b in zip(xs, ys, bs):
        ax.annotate(label_for(b), (x, y), textcoords="offset points",
                    xytext=(6, 6), fontsize=8, color=INK_SOFT)
    ax.annotate("today", (obs_x, obs_y), textcoords="offset points",
                xytext=(-10, 8), fontsize=8, color=INK_SOFT, ha="right")

    ax.set_xlabel("dispatch-down over the window (MWh), less to the right")
    ax.set_ylabel("divergence from group mean (percentage points)")
    ax.set_title("Efficiency and equity on real 2026 data, North-West Group 3",
                 color=INK)
    ax.invert_xaxis()          # better is to the right
    ax.margins(x=0.09, y=0.12)  # keep the b=inf label inside the axes
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25, lw=0.6)
    fig.text(0.01, 0.01,
             f"{wpa['half_hours_with_relief']} half-hours, {wpa['units']} units, "
             f"{wpa['window'][0][:10]} to {wpa['window'][1][:10]}. "
             "Every rule delivers identical flow relief. "
             "Source: wpa_summary.json, wpe_bound.csv",
             fontsize=6.5, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "wpa_frontier_real.png"))
    plt.close(fig)
    print("wrote wpa_frontier_real.png")


def stations() -> None:
    st = pd.read_csv(os.path.join(OUT, "wpa_stations.csv"))
    st = st.sort_values("SF_eff", ascending=False)
    y = np.arange(len(st))

    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=160)
    h = 0.38
    ax.barh(y - h / 2, 100 * st.r_observed, height=h - 0.02, color=C[0],
            label="observed (pro rata)")
    ax.barh(y + h / 2, 100 * st.r_effectiveness, height=h - 0.02, color=C[2],
            label="effectiveness order")
    ax.set_yticks(y)
    # shift factor belongs in the tick label: as an in-bar annotation it
    # collided with the bar start and was unreadable on the short bars
    ax.set_yticklabels([f"{s.title()}  (SF {sf:.3f})"
                        for s, sf in zip(st.station, st.SF_eff)], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("constraint-only dispatch-down (% of available energy)")
    ax.set_title("Where the cut lands, by station (ordered by shift factor)",
                 color=INK)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(True, axis="x", alpha=0.25, lw=0.6)
    fig.text(0.01, 0.01,
             "Effectiveness ordering concentrates the cut on high shift-factor "
             "stations; the band limits that. Source: wpa_stations.csv",
             fontsize=6.5, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "wpa_station_real.png"))
    plt.close(fig)
    print("wrote wpa_station_real.png")


if __name__ == "__main__":
    frontier()
    stations()
