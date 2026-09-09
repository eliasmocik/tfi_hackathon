"""WP-G - multi-criteria decision analysis (design brief v2 section 3, WP-G).

Tuohy's point was that the team does not get to choose the weights: the
contribution is the transfer function from a policy dial to outcomes, and the
SEM Committee, CRU or DECC picks the operating point. So this builds the
options-by-criteria table with the **weights left blank**, and reports which
weight vectors would select each option.

Every number is read from a file written by another script. Nothing is typed
in. Inputs that the design brief's verification queue has not cleared are
carried as explicit UNVERIFIED parameters and swept, never as point claims.

    python project/src/wp_g_mcda.py

Outputs out/wpg_mcda.csv, out/wpg_weight_sensitivity.csv, out/wpg_mcda.md.
"""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"

# --- UNVERIFIED inputs (design brief v2 section 8, verification queue) -------
# A euro figure is admissible only as a published unit rate times a measured
# MWh difference, with the rate visible and swept. The denominator needed to
# turn the EUR 34.92 m 2025/26 constrained wind and solar provision into an
# implied EUR/MWh has not been sourced, so the rate is swept over a stated
# range instead of being asserted.
EUR_PER_MWH_SWEEP = [40.0, 60.0, 80.0, 100.0, 120.0]
# Marginal emissions factor of displaced generation: queue item 1, unsourced.
TCO2_PER_MWH = None
# Community Benefit Fund: EUR 2/MWh, verified, but it attaches only to
# RESS-supported projects and that subset has not been identified for the
# North-West fleet (queue item 3), so the community column stays qualitative.
CBF_EUR_PER_MWH = 2.0
CBF_SUBSET_KNOWN = False


def load() -> tuple[dict, pd.DataFrame]:
    wpa = json.loads((OUT / "wpa_summary.json").read_text(encoding="utf-8"))
    wpe = pd.read_csv(OUT / "wpe_bound.csv")
    return wpa, wpe


def main() -> int:
    wpa, wpe = load()
    obs = wpa["observed_cut_MWh"]
    w0, w1 = pd.Timestamp(wpa["window"][0]), pd.Timestamp(wpa["window"][1])
    days = (w1 - w0).total_seconds() / 86400.0
    scale = 365.0 / days  # window -> annualised, stated as an assumption

    options = [
        ("a", "Today (pro rata)", "band0pp"),
        ("b", "Band 2 pp", "band2pp"),
        ("c", "Band 3 pp", "band3pp"),
        ("d", "Band 5 pp", "band5pp"),
        ("e", "Pure effectiveness", "effectiveness"),
    ]

    rows = []
    for tag, label, key in options:
        cut = wpa[f"{key}_cut_MWh"]
        saving = wpa[f"{key}_saving_MWh"]
        b = 0.0 if key == "band0pp" else (
            np.inf if key == "effectiveness" else float(key.replace("band", "").replace("pp", "")))
        e = wpe[wpe.band_pp == b]
        bound = float(e.claimed_bound_pp.iloc[0]) if len(e) else np.nan
        realised = float(e.realised_max_divergence_pp.iloc[0]) if len(e) else np.nan
        escapes = int(e.feasibility_escapes.iloc[0]) if len(e) else -1
        rows.append({
            "option": tag,
            "label": label,
            "spill_MWh_window": cut,
            "spill_saving_MWh_window": saving,
            "spill_saving_MWh_annualised": saving * scale,
            "spill_saving_pct": wpa[f"{key}_saving_pct"],
            "equity_guaranteed_bound_pp": bound,
            "equity_realised_divergence_pp": realised,
            "feasibility_escapes": escapes,
            "operator_actions_per_event": 1,      # WP-C: one instruction, as today
            "security": "invariant",              # verified: wpa_assertions A1
            "community_EUR_window": (saving * CBF_EUR_PER_MWH) if CBF_SUBSET_KNOWN else np.nan,
            "carbon_tCO2_window": (saving * TCO2_PER_MWH) if TCO2_PER_MWH else np.nan,
        })
    mcda = pd.DataFrame(rows)

    for rate in EUR_PER_MWH_SWEEP:
        mcda[f"consumer_EUR_window_at_{rate:g}"] = mcda.spill_saving_MWh_window * rate

    mcda.to_csv(OUT / "wpg_mcda.csv", index=False)

    # --- weight sensitivity ------------------------------------------------
    # Two criteria are genuinely in tension: spill (lower is better) and
    # realised equity divergence (lower is better). Everything else is either
    # invariant across options (security, operator actions) or a monotone
    # transform of spill (consumer euro, carbon, community euro). So the
    # sensitivity is over the weight placed on spill versus equity.
    def norm(x, lower_better=True):
        """Min-max to [0, 1], best = 1. An infinite criterion value (a rule with
        no ex-ante bound at all) scores worst, not undefined."""
        x = np.asarray(x, float)
        finite = np.isfinite(x)
        if not finite.any():
            return np.zeros_like(x)
        lo, hi = np.nanmin(x[finite]), np.nanmax(x[finite])
        z = np.where(finite, (x - lo) / (hi - lo) if hi - lo > 1e-12 else 0.0, 1.0)
        out = 1.0 - z if lower_better else z
        return np.where(np.isnan(out), 0.0, out)

    s_spill = norm(mcda.spill_MWh_window)
    s_equity = norm(mcda.equity_realised_divergence_pp)
    s_bound = norm(mcda.equity_guaranteed_bound_pp)

    sens = []
    for w in np.round(np.arange(0.0, 1.0001, 0.05), 3):
        score_realised = w * s_spill + (1 - w) * s_equity
        score_bound = w * s_spill + (1 - w) * s_bound
        sens.append({
            "weight_on_spill": w,
            "weight_on_equity": round(1 - w, 3),
            "winner_by_realised_equity": mcda.label.iloc[int(np.argmax(score_realised))],
            "winner_by_guaranteed_bound": mcda.label.iloc[int(np.argmax(score_bound))],
        })
    sens = pd.DataFrame(sens)
    sens.to_csv(OUT / "wpg_weight_sensitivity.csv", index=False)

    # --- markdown artefact -------------------------------------------------
    md = [
        "# WP-G - options and criteria, weights blank", "",
        "The team does not select the weights. The SEM Committee, CRU or DECC does.",
        "This table is the transfer function; the weights are the policy choice.", "",
        f"Window: {wpa['window'][0]} to {wpa['window'][1]} ({days:.1f} days, "
        f"{wpa['half_hours_with_relief']} half-hours with relief, {wpa['units']} units).",
        "Annualised columns scale the window linearly, which assumes the summer",
        "constraint pattern is representative. It is one summer; state that.", "",
        "| criterion | serves | " + " | ".join(r.label for r in mcda.itertuples()) + " | weight |",
        "|---|---|" + "---|" * (len(mcda) + 1),
    ]

    def line(name, serves, vals, fmt="{:.1f}"):
        cells = " | ".join("-" if (isinstance(v, float) and np.isnan(v)) else
                           (fmt.format(v) if isinstance(v, (int, float)) else str(v))
                           for v in vals)
        md.append(f"| {name} | {serves} | {cells} |  |")

    line("Spill, MWh (window)", "Generators, carbon, consumers", mcda.spill_MWh_window)
    line("Spill saved vs today, MWh", "All", mcda.spill_saving_MWh_window)
    line("Spill saved, %", "All", mcda.spill_saving_pct, "{:.2f}")
    line("Spill saved, MWh/yr (scaled)", "All", mcda.spill_saving_MWh_annualised, "{:.0f}")
    for rate in EUR_PER_MWH_SWEEP:
        line(f"Consumer EUR at {rate:g}/MWh (UNVERIFIED rate)", "Consumers, taxpayers",
             mcda[f"consumer_EUR_window_at_{rate:g}"], "{:.0f}")
    line("Equity: guaranteed bound, pp", "Generators", mcda.equity_guaranteed_bound_pp, "{:.2f}")
    line("Equity: realised divergence, pp", "Generators", mcda.equity_realised_divergence_pp, "{:.2f}")
    line("Feasibility escapes (of 638 hh)", "Generators, TSO", mcda.feasibility_escapes, "{:.0f}")
    line("Operator actions per event", "TSO", mcda.operator_actions_per_event, "{:.0f}")
    line("Security", "All", mcda.security)
    line("Carbon, tCO2 (UNVERIFIED factor)", "Third parties, State", mcda.carbon_tCO2_window)
    line("Community CBF EUR (RESS subset unidentified)", "Host communities",
         mcda.community_EUR_window)

    md += [
        "", "Cells marked `-` are criteria whose input the verification queue has",
        "not cleared (design brief v2 section 8). They are deliberately left",
        "empty rather than filled with a plausible number.", "",
        "## Which weight vector selects which option", "",
        "Spill and realised equity divergence are the only two criteria in real",
        "tension; the euro, carbon and community columns are monotone transforms",
        "of spill, and security and operator burden are invariant across options.",
        "So the sensitivity reduces to one dial.", "",
        "| weight on spill | weight on equity | winner (realised equity) | winner (guaranteed bound) |",
        "|---|---|---|---|",
    ]
    for r in sens.itertuples():
        md.append(f"| {r.weight_on_spill:.2f} | {r.weight_on_equity:.2f} | "
                  f"{r.winner_by_realised_equity} | {r.winner_by_guaranteed_bound} |")
    md += ["", "Full tables: `wpg_mcda.csv`, `wpg_weight_sensitivity.csv`.", ""]

    (OUT / "wpg_mcda.md").write_text("\n".join(md), encoding="utf-8")

    print(mcda[["label", "spill_MWh_window", "spill_saving_pct",
                "equity_guaranteed_bound_pp", "equity_realised_divergence_pp",
                "feasibility_escapes"]].to_string(index=False))
    print()
    print(sens.drop_duplicates(subset=["winner_by_realised_equity",
                                       "winner_by_guaranteed_bound"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
