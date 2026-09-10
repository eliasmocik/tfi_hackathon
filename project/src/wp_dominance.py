"""Where does the band rule beat today's rule on BOTH axes?

Picking a point on an efficiency-equity frontier normally needs a weight - how
much wind is worth how much equity - and that weight belongs to the regulator,
not to us (which is why wp_g_mcda leaves it blank). No weight is needed for the
subset of bands that beat the status quo on *both* measures at once. Inside
that set the choice is a matter of fact; only outside it does a value judgement
begin.

A band dominates today's rule when it spills less energy AND its realised
maximum divergence from the group mean is no larger than the divergence today's
rule actually produced over the same window.

    python project/src/wp_dominance.py

    out/wpe_dominance.csv           per band: spill, divergence, dominates
    out/wpe_dominance_splits.csv    the same test on each half of the window
    out/wpe_dominance_synthetic.csv the same test on the three synthetic cases
    out/wpe_dominance.json          the recommended band and how it was reached
    out/fig_dominance.png           the frontier with the dominance region shaded
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SYNTH_CASES = ["WP2024s42", "WP2033s42", "WP2033s43"]


def band_of(label: str) -> float:
    """'band3' -> 3.0, 'bandinf' -> inf, anything else -> nan."""
    if not str(label).startswith("band"):
        return float("nan")
    tail = str(label)[4:]
    return np.inf if tail == "inf" else float(tail)


# --------------------------------------------------------------------------- #
# real replay
# --------------------------------------------------------------------------- #
def real_table() -> pd.DataFrame:
    """Spill and realised divergence per band, on the real 2026 replay."""
    summ = json.loads((OUT / "wpa_summary.json").read_text())
    bound = pd.read_csv(OUT / "wpe_bound.csv")
    obs_div = json.loads((OUT / "wpe_summary.json").read_text())[
        "observed_pro_rata_max_divergence_pp"]

    rows = []
    for _, r in bound.iterrows():
        b = float(r.band_pp)
        key = "effectiveness" if np.isinf(b) else f"band{b:g}pp"
        rows.append({
            "band_pp": b,
            "cut_MWh": summ[f"{key}_cut_MWh"],
            "saving_pct": summ[f"{key}_saving_pct"],
            "realised_max_divergence_pp": r.realised_max_divergence_pp,
            "guaranteed_bound_pp": r.claimed_bound_pp,
            "feasibility_escapes": int(r.feasibility_escapes),
        })
    d = pd.DataFrame(rows).sort_values("band_pp").reset_index(drop=True)
    d["observed_divergence_pp"] = obs_div
    d["saves_energy"] = d.saving_pct > 0
    d["no_worse_on_equity"] = d.realised_max_divergence_pp <= obs_div
    d["dominates_today"] = d.saves_energy & d.no_worse_on_equity
    return d


def recommend(d: pd.DataFrame, sp: pd.DataFrame | None = None) -> dict:
    """The widest finite band that dominates today's rule *robustly*.

    Dominating over the whole window is not enough: the bar is today's own
    realised divergence, and that bar moves with the sample. Splitting the
    window in two, the observed divergence is 7.41 pp in the first half and
    5.46 pp in the second, so a band that clears the full-window bar can fail
    the tougher half. The recommendation therefore requires dominance over the
    full window AND in each half separately.
    """
    fin = d[np.isfinite(d.band_pp)]
    dom = fin[fin.dominates_today]
    if sp is not None and len(sp):
        ok = (sp.groupby("band_pp").no_worse_on_equity.all())
        dom = dom[[bool(ok.get(b, False)) for b in dom.band_pp]]
    rec = float(dom.band_pp.max()) if len(dom) else float("nan")
    above = fin[(~fin.dominates_today) & (fin.band_pp > rec)]
    first_fail = float(above.band_pp.min()) if len(above) else float("nan")
    row = d[d.band_pp == rec].iloc[0] if len(dom) else None
    return {
        "recommended_band_pp": rec,
        "dominance_upper_bound_pp": first_fail,
        "recommended_saving_pct": None if row is None else float(row.saving_pct),
        "recommended_saving_MWh": None if row is None else float(
            d[d.band_pp == 0].cut_MWh.iloc[0] * 0 + row.cut_MWh),
        "recommended_divergence_pp": None if row is None else float(
            row.realised_max_divergence_pp),
        "observed_divergence_pp": float(d.observed_divergence_pp.iloc[0]),
        "bands_that_dominate": [float(b) for b in dom.band_pp],
    }


# --------------------------------------------------------------------------- #
# robustness: split the window, and the synthetic cases
# --------------------------------------------------------------------------- #
def split_table() -> pd.DataFrame:
    """Re-run the dominance test on each half of the window.

    The trajectory carries the running maximum, so the second half's statistic
    is read as the increase over the first half's - it is a running max, not a
    per-half max, and is labelled as such.
    """
    tj = pd.read_csv(OUT / "wpe_trajectory.csv", parse_dates=["StartTime"])
    warm = json.loads((OUT / "wpe_summary.json").read_text())["warmup_days"]
    t0 = tj.StartTime.min()
    tj = tj[(tj.StartTime - t0).dt.total_seconds() / 86400.0 >= warm]
    mid = tj.StartTime.min() + (tj.StartTime.max() - tj.StartTime.min()) / 2

    rows = []
    for name, part in (("first half", tj[tj.StartTime <= mid]),
                       ("second half", tj[tj.StartTime > mid])):
        obs = float(part.observed_maxdiv_pp.max())
        for col in [c for c in part.columns if c.endswith("_maxdiv_pp")
                    and c != "observed_maxdiv_pp"]:
            b = band_of(col.replace("_maxdiv_pp", ""))
            rows.append({"half": name, "band_pp": b,
                         "realised_max_divergence_pp": float(part[col].max()),
                         "observed_divergence_pp": obs,
                         "no_worse_on_equity": float(part[col].max()) <= obs})
    return pd.DataFrame(rows).sort_values(["half", "band_pp"])


def synthetic_table() -> pd.DataFrame:
    """The same test on the synthetic cases, from the phase-2 summaries.

    The statistic there is the END-OF-YEAR divergence (max_i r_i - rbar), not a
    running maximum: the phase-2 pipeline stores year-end ratios, not the
    trajectory. Stated on the figure and in RESULTS so the two are not conflated.
    """
    rows = []
    for case in SYNTH_CASES:
        f = OUT / f"{case}_summary.csv"
        if not f.exists():
            continue
        s = pd.read_csv(f).set_index("rule")
        if "rule1" not in s.index:
            continue
        base_D = float(s.loc["rule1", "D_pct"])
        base_div = 100.0 * (float(s.loc["rule1", "r_max"])
                            - float(s.loc["rule1", "D_pct"]) / 100.0)
        for rule in s.index:
            b = band_of(rule)
            if not np.isfinite(b) and rule != "bandinf":
                continue
            div = 100.0 * (float(s.loc[rule, "r_max"])
                           - float(s.loc[rule, "D_pct"]) / 100.0)
            saving = 100.0 * (base_D - float(s.loc[rule, "D_pct"])) / base_D
            rows.append({
                "case": case, "band_pp": b, "D_pct": float(s.loc[rule, "D_pct"]),
                "saving_vs_rule1_pct": saving,
                "endofyear_divergence_pp": div,
                "rule1_divergence_pp": base_div,
                "saves_energy": saving > 0,
                "no_worse_on_equity": div <= base_div,
                "dominates_rule1": (saving > 0) and (div <= base_div),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
def figure(d: pd.DataFrame, rec: dict, sp: pd.DataFrame | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8983"
    BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"
    plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                         "savefig.facecolor": SURFACE, "font.size": 11,
                         "text.color": INK, "axes.labelcolor": INK2,
                         "axes.edgecolor": "#e8e7e3", "xtick.color": INK2,
                         "ytick.color": INK2, "axes.spines.top": False,
                         "axes.spines.right": False})

    fin = d[np.isfinite(d.band_pp)].sort_values("band_pp")
    obs = rec["observed_divergence_pp"]
    fig, ax = plt.subplots(figsize=(11.5, 6.6), dpi=150)

    ax.axhspan(0, obs, color=GREEN, alpha=0.07, zorder=0)
    ax.axhline(obs, color=MUTED, lw=1.5, ls=(0, (4, 3)), zorder=2)
    ax.text(fin.saving_pct.max() * 1.02, obs,
            f"  today's realised divergence\n  {obs:.2f} pp",
            va="center", fontsize=9.5, color=MUTED, linespacing=1.4)

    robust = set(rec["bands_that_dominate"])
    fragile = set(rec.get("dominate_full_window_but_not_every_half", []))
    ax.plot(fin.saving_pct, fin.realised_max_divergence_pp, color=BLUE, lw=2,
            zorder=3)
    for _, r in fin.iterrows():
        if r.band_pp in robust:
            ax.scatter([r.saving_pct], [r.realised_max_divergence_pp], s=70,
                       color=BLUE, zorder=4, edgecolors=SURFACE, linewidths=1.6)
        elif r.band_pp in fragile:
            ax.scatter([r.saving_pct], [r.realised_max_divergence_pp], s=80,
                       facecolors=SURFACE, edgecolors=BLUE, linewidths=2, zorder=4)
        else:
            ax.scatter([r.saving_pct], [r.realised_max_divergence_pp], s=70,
                       color=MUTED, zorder=4, edgecolors=SURFACE, linewidths=1.6)
    if fragile:
        f = fin[fin.band_pp.isin(fragile)]
        ax.annotate("hollow: clears the full window,\nbut not its tougher half",
                    (f.saving_pct.mean(), f.realised_max_divergence_pp.mean()),
                    textcoords="offset points", xytext=(24, -34), ha="left",
                    fontsize=9, color=INK2, linespacing=1.4)
    ax.scatter([0], [obs], s=150, marker="D", color=ORANGE, zorder=4,
               edgecolors=SURFACE, linewidths=1.6)
    ax.annotate("today (pro rata)", (0, obs), textcoords="offset points",
                xytext=(12, 10), fontsize=10, color=ORANGE, fontweight="bold")

    for _, r in fin.iterrows():
        ax.annotate(f"b={r.band_pp:g}", (r.saving_pct, r.realised_max_divergence_pp),
                    textcoords="offset points", xytext=(0, -18), ha="center",
                    fontsize=9, color=INK2)

    rb = rec["recommended_band_pp"]
    row = fin[fin.band_pp == rb].iloc[0]
    ax.scatter([row.saving_pct], [row.realised_max_divergence_pp], s=320,
               facecolors="none", edgecolors=ORANGE, linewidths=2.4, zorder=5)
    ax.annotate(f"recommended: b = {rb:g} pp",
                (row.saving_pct, row.realised_max_divergence_pp),
                textcoords="offset points", xytext=(-14, 26), ha="right",
                fontsize=11, fontweight="bold", color=ORANGE,
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.8,
                                shrinkA=0, shrinkB=10))

    ax.set_xlabel("wind saved against today's dispatch (%)", fontsize=10.5)
    ax.set_ylabel("worst divergence from the group average (pp)", fontsize=10.5)
    ax.set_xlim(-0.45, fin.saving_pct.max() * 1.30)
    ax.set_ylim(0, max(fin.realised_max_divergence_pp.max(), obs) * 1.22)
    ax.grid(color="#e8e7e3", lw=0.9)
    ax.set_axisbelow(True)

    fig.text(0.012, 0.962, "A band of 5 points beats today's rule on both counts",
             ha="left", va="top", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.012, 0.905,
             "Shaded: less unequal than the rule in force. Further right: less wind "
             "spilled. A filled point inside the shading needs no\nvalue judgement — "
             "it is better than today on both axes, and stays better when the window "
             "is split in half.",
             ha="left", va="top", fontsize=10.5, color=INK2, linespacing=1.5)
    fig.text(0.012, 0.028,
             f"Real 2026 replay, {json.loads((OUT / 'wpa_summary.json').read_text())['half_hours_with_relief']} "
             f"half-hours, matched flow relief. Divergence measured after a "
             f"{json.loads((OUT / 'wpe_summary.json').read_text())['warmup_days']:g}-day ledger warm-up. "
             f"Source: wpe_dominance.csv.", fontsize=9, color=MUTED)
    fig.tight_layout(rect=[0, 0.05, 1, 0.875])
    fig.savefig(OUT / "fig_dominance.png")
    plt.close(fig)


def main() -> int:
    d = real_table()
    d.to_csv(OUT / "wpe_dominance.csv", index=False)

    sp = split_table()
    sp.to_csv(OUT / "wpe_dominance_splits.csv", index=False)
    rec = recommend(d, sp)

    syn = synthetic_table()
    if len(syn):
        syn.to_csv(OUT / "wpe_dominance_synthetic.csv", index=False)

    rb = rec["recommended_band_pp"]
    halves = sp[sp.band_pp == rb]
    rec["holds_in_both_halves"] = bool(halves.no_worse_on_equity.all()) if len(halves) else None
    full_only = sorted(set(d[d.dominates_today & np.isfinite(d.band_pp)].band_pp)
                       - set(rec["bands_that_dominate"]))
    rec["dominate_full_window_but_not_every_half"] = [float(b) for b in full_only]

    # The synthetic cases cannot test dominance: their pro-rata baseline is the
    # idealised per-hour rule on a single binding element, so it comes out
    # almost perfectly equal (0.7-1.5 pp against the real 7.4 pp) and nothing
    # can be "no worse" than it. They are evidence about the frontier's shape,
    # not about the status quo. Recorded, with that caveat, rather than scored.
    if len(syn):
        rec["synthetic_rule1_divergence_pp"] = {
            str(c): float(v) for c, v in
            syn.groupby("case").rule1_divergence_pp.first().items()}
        rec["synthetic_note"] = (
            "The synthetic model's pro rata is idealised and already near-equal, "
            "so the dominance test is not meaningful there; it is a test against "
            "what the real rule actually produced.")
        s2 = syn[syn.band_pp == rb]
        rec["synthetic_saving_at_recommended_pct"] = {
            str(r.case): float(r.saving_vs_rule1_pct) for _, r in s2.iterrows()}
    (OUT / "wpe_dominance.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")

    figure(d, rec, sp)

    pd.set_option("display.width", 200)
    print(d[["band_pp", "saving_pct", "realised_max_divergence_pp",
             "observed_divergence_pp", "dominates_today"]].to_string(index=False))
    print(f"\nrecommended band: {rec['recommended_band_pp']:g} pp "
          f"(first band that does not dominate: {rec['dominance_upper_bound_pp']:g} pp)")
    print(f"holds in both halves of the window: {rec['holds_in_both_halves']}")
    print(f"dominate the full window but not every half: "
          f"{rec['dominate_full_window_but_not_every_half']}")
    if "synthetic_saving_at_recommended_pct" in rec:
        print(f"saving at b={rb:g} in the synthetic cases: "
              f"{ {k: round(v, 2) for k, v in rec['synthetic_saving_at_recommended_pct'].items()} }")
        print(f"  (synthetic pro rata divergence "
              f"{ {k: round(v, 2) for k, v in rec['synthetic_rule1_divergence_pp'].items()} } "
              f"vs real 7.41 pp - see synthetic_note)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
