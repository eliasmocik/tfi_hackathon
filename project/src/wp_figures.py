"""Three presentation figures the analysis was missing.

    python project/src/wp_figures.py

    out/fig_headline_saving.png   the headline: wind saved per rule, real 2026 data
    out/fig_nw_map.png            North-West map: shift factor is geographic
    out/fig_band_schematic.png    how the band rule works (mechanism, not data)

Every number in figures 1 and 2 is read from a file in out/; figure 3 is a
labelled schematic with no data in it. Palette and mark specs follow the
data-visualisation reference palette (categorical slots 1-3, sequential blue).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"

SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8983"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRID = "#e8e7e3"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 11,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
})


def _bar(ax, y, w, color, h=0.6):
    """A bar with a 4px-equivalent rounded data-end, anchored at zero."""
    ax.barh(y, w, height=h, color=color, zorder=3,
            edgecolor=SURFACE, linewidth=1.4)


# --------------------------------------------------------------------------- #
# 1. The headline
# --------------------------------------------------------------------------- #
def headline() -> None:
    d = json.loads((OUT / "wpa_summary.json").read_text())
    rows = [("As dispatched\n(pro rata, today)", 0.0, 0.0, MUTED)]
    for b in ["0", "1", "2", "3", "5", "10"]:
        rows.append((f"Band {b} pp", d[f"band{b}pp_saving_MWh"],
                     d[f"band{b}pp_saving_pct"], BLUE))
    rows.append(("Pure effectiveness\n(the ceiling)",
                 d["effectiveness_saving_MWh"], d["effectiveness_saving_pct"], ORANGE))

    labels = [r[0] for r in rows]
    vals = np.array([r[1] for r in rows])
    pcts = [r[2] for r in rows]
    colors = [r[3] for r in rows]

    fig, ax = plt.subplots(figsize=(11.5, 6.4), dpi=150)
    y = np.arange(len(rows))[::-1]
    for yi, v, c in zip(y, vals, colors):
        _bar(ax, yi, v, c)

    for yi, v, p in zip(y, vals, pcts):
        if v == 0:
            ax.text(12, yi, "reference", va="center", ha="left",
                    color=MUTED, fontsize=10.5, zorder=4)
        else:
            ax.text(v + 12, yi, f"{v:,.0f} MWh   ({p:.2f} %)", va="center",
                    ha="left", color=INK, fontsize=10.5, zorder=4)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5, color=INK)
    ax.set_xlim(0, vals.max() * 1.36)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.set_axisbelow(True)

    n_hh = d["half_hours_with_relief"]
    obs = d["observed_cut_MWh"]
    fig.text(0.012, 0.955, "Wind that need not have been spilled",
             ha="left", va="top", fontsize=18, fontweight="bold", color=INK)
    fig.text(0.012, 0.898,
             f"North-West Group 3, {n_hh} half-hours under local constraint, "
             f"8 June to 5 September 2026. Every alternative delivers the\nidentical "
             f"flow relief on the same line in the same half-hour, so security is "
             f"unchanged.",
             ha="left", va="top", fontsize=10.5, color=INK2, linespacing=1.5)
    fig.text(0.012, 0.028,
             f"Observed dispatch-down over the window: {obs:,.0f} MWh. "
             f"Source: out/wpa_summary.json.",
             fontsize=9.5, color=MUTED, ha="left")
    fig.tight_layout(rect=[0, 0.055, 1, 0.855])
    fig.savefig(OUT / "fig_headline_saving.png")
    plt.close(fig)
    print("wrote fig_headline_saving.png  "
          f"ceiling {d['effectiveness_saving_MWh']:.0f} MWh "
          f"({d['effectiveness_saving_pct']:.2f} %)")


# --------------------------------------------------------------------------- #
# 2. The map
# --------------------------------------------------------------------------- #
NODES = {
    "CUNGHILL": (-8.649199, 54.111152), "GLENREE": (-8.989324, 54.105345),
    "MEENTYCAT": (-7.842446, 54.867666), "TRILLICK": (-7.418642, 55.112776),
    "LENALEA": (-7.864283, 54.902881), "BINBANE": (-8.263429, 54.718937),
    "TAWNAGHMORE": (-9.217877, 54.191803), "CORDERRY": (-8.197639, 54.198868),
    "GARVAGH": (-8.192487, 54.150459),
}
CONTEXT = {
    "FLAGFORD": (-8.123836, 53.911679), "SRANANAGH": (-8.383984, 54.177760),
    "SLIGO": (-8.467222, 54.241225), "MOY": (-9.187904, 54.123261),
    "CATHALEEN'S FALL": (-8.176982, 54.498753), "LETTERKENNY": (-7.697755, 54.924129),
    "SORNE HILL": (-7.368423, 55.131355), "MULREAVY": (-7.969235, 54.664487),
    "TIEVEBRACK": (-8.235617, 54.810276), "ARDNAGAPPARY": (-8.268818, 55.056640),
}
#: label offsets in points, chosen by eye to stop collisions
LBL = {
    "TRILLICK": (0, 17, "center"), "LENALEA": (-8, 17, "right"),
    "MEENTYCAT": (10, -26, "left"), "BINBANE": (-11, 4, "right"),
    "CORDERRY": (10, 12, "left"), "GARVAGH": (10, -20, "left"),
    "CUNGHILL": (0, -22, "center"), "GLENREE": (0, -22, "center"),
    "TAWNAGHMORE": (0, 18, "center"),
}
CLBL = {
    "SLIGO": (-10, 4, "right"), "SRANANAGH": (-11, 6, "right"),
    "SORNE HILL": (10, 2, "left"), "LETTERKENNY": (11, -2, "left"),
    "CATHALEEN'S FALL": (-11, -3, "right"), "TIEVEBRACK": (-11, -4, "right"),
    "MULREAVY": (11, -3, "left"), "ARDNAGAPPARY": (0, 12, "center"),
    "MOY": (0, -16, "center"), "FLAGFORD": (0, -17, "center"),
}

GREY_LINES = [
    ("BINBANE", "CATHALEEN'S FALL"), ("BINBANE", "TIEVEBRACK"),
    ("ARDNAGAPPARY", "TIEVEBRACK"), ("LENALEA", "TIEVEBRACK"),
    ("CORDERRY", "GARVAGH"), ("CORDERRY", "SRANANAGH"),
    ("CATHALEEN'S FALL", "SRANANAGH"), ("CUNGHILL", "GLENREE"),
    ("CUNGHILL", "SLIGO"), ("LETTERKENNY", "LENALEA"),
    ("LETTERKENNY", "TRILLICK"), ("MOY", "GLENREE"), ("MOY", "TAWNAGHMORE"),
    ("SLIGO", "SRANANAGH"), ("SORNE HILL", "TRILLICK"),
    ("SRANANAGH", "CATHALEEN'S FALL"), ("MEENTYCAT", "LETTERKENNY"),
]


def nice(name: str) -> str:
    """Title-case a station name without capitalising after an apostrophe."""
    return name.title().replace("'S", "'s")


def nw_map() -> None:
    st = pd.read_csv(OUT / "wpa_stations.csv").set_index("station")
    pos = {**NODES, **CONTEXT}
    sf = st["SF_eff"]
    lo, hi = sf.min(), sf.max()

    def shade(v):
        # sequential: 7 steps, light = low magnitude
        i = int(round((v - lo) / (hi - lo) * (len(SEQ) - 3))) + 2
        return SEQ[min(i, len(SEQ) - 1)]

    fig, ax = plt.subplots(figsize=(11.5, 8.2), dpi=150)

    for a, b in GREY_LINES:
        if a in pos and b in pos:
            ax.plot(*zip(pos[a], pos[b]), color="#d6d5d0", lw=1.6, zorder=1)

    # The two circuits leave Flagford on nearly the same bearing, so the
    # contingency is nudged perpendicular to itself to keep both readable.
    (fx, fy), (sx, sy) = pos["FLAGFORD"], pos["SRANANAGH"]
    ux, uy = sx - fx, sy - fy
    nrm = (ux ** 2 + uy ** 2) ** 0.5
    ox, oy = -uy / nrm * 0.055, ux / nrm * 0.055
    ax.plot([fx + ox, sx + ox], [fy + oy, sy + oy], color="#d03b3b", lw=2.6,
            ls=(0, (5, 3)), zorder=2)
    ax.plot(*zip(pos["FLAGFORD"], pos["SLIGO"]), color=ORANGE, lw=3.4, zorder=2)

    for name, (x, y) in CONTEXT.items():
        ax.scatter([x], [y], s=42, c="#ffffff", edgecolors="#c9c8c2",
                   linewidths=1.4, zorder=4)
        cdx, cdy, cha = CLBL.get(name, (0, -15, "center"))
        ax.annotate(nice(name), (x, y), textcoords="offset points",
                    xytext=(cdx, cdy), ha=cha, fontsize=8.5, color=MUTED, zorder=6)

    sizes = 90 + 620 * (st["avail_MWh"] / st["avail_MWh"].max())
    for name, (x, y) in NODES.items():
        ax.scatter([x], [y], s=sizes[name], c=shade(sf[name]), edgecolors=SURFACE,
                   linewidths=2.0, zorder=5)
        dx, dy, ha = LBL.get(name, (0, 16, "center"))
        ax.annotate(f"{nice(name)}  {sf[name]:.2f}", (x, y),
                    textcoords="offset points", xytext=(dx, dy), ha=ha,
                    fontsize=9.5, color=INK, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.18", fc=SURFACE, ec="none",
                              alpha=0.85))

    handles = [
        Line2D([], [], color=ORANGE, lw=3.4,
               label="Flagford–Sligo 110 kV — the monitored circuit"),
        Line2D([], [], color="#d03b3b", lw=2.6, ls=(0, (5, 3)),
               label="Flagford–Srananagh 220 kV — the contingency"),
        Line2D([], [], color="#d6d5d0", lw=1.6, label="other 110 kV circuits"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9.5,
              labelcolor=INK2, handlelength=2.6, borderaxespad=0.8)

    grad = np.linspace(lo, hi, 60).reshape(1, -1)
    cax = fig.add_axes([0.70, 0.135, 0.20, 0.017])
    cax.imshow(grad, aspect="auto",
               cmap=matplotlib.colors.LinearSegmentedColormap.from_list("s", SEQ[2:]))
    cax.set_xticks([0, 59]); cax.set_xticklabels([f"{lo:.2f}", f"{hi:.2f}"], fontsize=8.5)
    cax.set_yticks([]); cax.tick_params(length=0, colors=INK2)
    for s in cax.spines.values():
        s.set_visible(False)
    cax.set_title("shift factor — MW of relief per MW cut", fontsize=8.5,
                  color=INK2, pad=5)
    fig.text(0.70, 0.085, "circle area = energy available over the window",
             fontsize=8.5, color=MUTED)

    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlim(-9.48, -7.05); ax.set_ylim(53.80, 55.30)
    ax.set_aspect(1.0 / np.cos(np.radians(54.5)))

    fig.text(0.012, 0.962, "Effectiveness is geography", ha="left", va="top",
             fontsize=18, fontweight="bold", color=INK)
    fig.text(0.012, 0.912,
             "When Flagford–Srananagh trips, the North-West's export squeezes onto "
             "Flagford–Sligo. A cut at Cunghill relieves\nthat circuit by 0.29 MW per "
             "MW; the same cut at Garvagh relieves 0.19. Pro rata ignores the difference.",
             ha="left", va="top", fontsize=10.5, color=INK2, linespacing=1.5)
    fig.text(0.012, 0.022,
             "Stations of North-West Constraint Group 3 with a metered unit. "
             "Shift factors from out/wpa_stations.csv (WP2024 network); "
             "coordinates from the participant kit.",
             fontsize=9, color=MUTED, ha="left")
    fig.tight_layout(rect=[0, 0.045, 1, 0.885])
    fig.savefig(OUT / "fig_nw_map.png")
    plt.close(fig)
    print(f"wrote fig_nw_map.png  shift factors {lo:.3f} to {hi:.3f}")


# --------------------------------------------------------------------------- #
# 3. The mechanism
# --------------------------------------------------------------------------- #
def schematic() -> None:
    """A labelled diagram of the rule. No measured data is plotted here."""
    farms = ["A", "B", "C", "D", "E", "F"]
    sf = [0.29, 0.26, 0.22, 0.21, 0.19, 0.18]
    before = [9.0, 5.1, 4.4, 4.0, 3.6, 3.1]
    after = [9.0, 8.8, 4.4, 4.0, 3.6, 3.1]
    b = 3.0

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.0), dpi=150, sharey=True)

    for ax, tally, title, cut_idx in (
        (axes[0], before, "An overload arrives", 1),
        (axes[1], after, "The next overload", 2),
    ):
        avg = float(np.mean(tally))
        line = avg + b
        x = np.arange(len(farms))
        colors, hatch = [], []
        for i, t in enumerate(tally):
            if t > line:
                colors.append("#dedcd6")
            elif i == cut_idx:
                colors.append(ORANGE)
            else:
                colors.append(BLUE)
        ax.bar(x, tally, width=0.62, color=colors, zorder=3,
               edgecolor=SURFACE, linewidth=1.6)

        ax.axhline(avg, color=MUTED, lw=1.4, ls=(0, (4, 3)), zorder=2)
        ax.axhline(line, color="#d03b3b", lw=1.8, zorder=2)
        ax.text(len(farms) - 0.42, avg, " group average", va="center", ha="left",
                fontsize=9, color=MUTED)
        ax.text(len(farms) - 0.42, line, f" average + b\n (b = {b:.0f} pp)",
                va="center", ha="left", fontsize=9, color="#d03b3b", linespacing=1.3)

        ax.annotate("cut goes here", (cut_idx, tally[cut_idx]),
                    textcoords="offset points", xytext=(0, 26), ha="center",
                    fontsize=9.5, color=ORANGE, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.8,
                                    shrinkA=0, shrinkB=4))
        for i, t in enumerate(tally):
            if t > line:
                ax.annotate("protected", (i, t), textcoords="offset points",
                            xytext=(0, 8), ha="center", fontsize=8.5, color=MUTED)

        ax.set_xticks(x)
        ax.set_xticklabels([f"{f}\n{s:.2f}" for f, s in zip(farms, sf)],
                           fontsize=9.5, linespacing=1.5)
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=26)
        ax.set_ylim(0, 12.6)
        ax.grid(axis="y", color=GRID, lw=0.9)
        ax.set_axisbelow(True)
        ax.spines["left"].set_color(GRID)
        ax.tick_params(length=0)

    axes[0].set_ylabel("share of the year's available energy already cut (pp)",
                       fontsize=9.5, color=INK2)
    fig.text(0.5, 0.115,
             "Farms are ordered by shift factor (the number under each letter). "
             "The most effective eligible farm is cut first.\nCutting raises that "
             "farm's ledger; once it passes the line it is protected and the next "
             "one takes over, so the burden rotates.",
             ha="center", fontsize=10, color=INK2, linespacing=1.6)

    handles = [
        Line2D([], [], marker="s", ls="", ms=11, color=ORANGE, label="cut this event"),
        Line2D([], [], marker="s", ls="", ms=11, color=BLUE, label="eligible"),
        Line2D([], [], marker="s", ls="", ms=11, color="#dedcd6",
               label="above the band — protected"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=10, labelcolor=INK2, bbox_to_anchor=(0.5, 0.015))

    fig.text(0.012, 0.962, "How the band rule decides who is cut", ha="left",
             va="top", fontsize=18, fontweight="bold", color=INK)
    fig.text(0.012, 0.905,
             "Schematic — six illustrative farms, no measured data. "
             "b is the dial: 0 reproduces today's rule, infinity is pure effectiveness.",
             fontsize=10.5, color=INK2, ha="left")
    fig.tight_layout(rect=[0, 0.20, 1, 0.865])
    fig.savefig(OUT / "fig_band_schematic.png")
    plt.close(fig)
    print("wrote fig_band_schematic.png  (schematic, no data)")


def main() -> int:
    headline()
    nw_map()
    schematic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
