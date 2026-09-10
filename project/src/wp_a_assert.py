"""WP-A assertions - the replay is only usable if the counterfactual really is
security-equivalent (design brief v2 section 3, WP-B).

Re-reads the replay's own inputs and re-checks, per half-hour and per rule:

  A1  relief delivered equals the observed relief R      (identical security)
  A2  no unit is cut beyond its declared availability
  A3  no cut is negative
  A4  band 0 tracks the observed pro-rata cut closely    (today's rule is modelled)
  A5  annual cut is monotone non-increasing as the band widens
  A6  every half-hour is feasible (the fleet, fully cut, can reach R)

Writes out/wpa_assertions.csv and prints a pass/fail line per assertion.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import wp_a_replay as W

OUT = W.OUT
TOL_REL = 1e-6


def main() -> int:
    meas = W.load_measured()
    sfw = W.station_shift_factors()

    umap = pd.read_csv(W.DATA / "semo_unit_map_IE.csv")
    umap["st"] = umap.station.map(W.canon_station)
    meas["st"] = meas.ResourceName.map(dict(zip(umap.unit, umap.st)))
    meas = meas[meas.st.isin(W.CG3_STATIONS)].copy()
    meas["SF_eff"] = meas.st.map(sfw)
    meas = meas[meas.SF_eff.notna()].copy()
    meas["active"] = meas.constraint & ~meas.curtail

    units = sorted(meas.ResourceName.unique())
    uidx = {u: i for i, u in enumerate(units)}
    cum_cut = {b: np.zeros(len(units)) for b in W.BANDS}
    cum_avail = np.zeros(len(units))

    worst_relief = 0.0
    worst_cap = 0.0
    n_negative = 0
    n_infeasible = 0
    n_halfhours = 0
    obs_tot = 0.0
    band0_tot = 0.0
    monotone_breaks = 0

    for _t, g in meas.groupby("StartTime", sort=True):
        idx = np.array([uidx[u] for u in g.ResourceName])
        cap = g.avail_MW.to_numpy(float)
        obs = np.where(g.active.to_numpy(), g.cut_MW.to_numpy(float), 0.0)
        sfh = g.SF_eff.to_numpy(float)
        cum_avail[idx] += cap * 0.5
        R = float((sfh * obs).sum())
        if R <= 1e-9:
            continue
        n_halfhours += 1
        obs_tot += obs.sum() * 0.5

        # Can the whole fleet, fully cut, deliver R at all?
        if float((sfh * cap).sum()) + 1e-9 < R:
            n_infeasible += 1

        totals = []
        for b in W.BANDS:
            if np.isinf(b):
                elig = np.ones(len(idx), bool)
            else:
                av_i = np.maximum(cum_avail[idx], 1e-9)
                r = cum_cut[b][idx] / av_i
                tot_av = cum_avail[idx].sum()
                rbar = (cum_cut[b][idx].sum() / tot_av) if tot_av > 0 else 0.0
                elig = r <= rbar + b / 100.0
                if not elig.any():
                    elig = np.ones(len(idx), bool)
            c = W.greedy_to_relief(sfh, cap, R, elig)

            delivered = float((sfh * c).sum())
            worst_relief = max(worst_relief, abs(delivered - R) / max(R, 1e-9))
            worst_cap = max(worst_cap, float(np.max(c - cap)) if len(c) else 0.0)
            n_negative += int((c < -1e-12).sum())

            cum_cut[b][idx] += c * 0.5
            totals.append(float(c.sum()))
            if b == 0.0:
                band0_tot += c.sum() * 0.5

        del totals  # per-half-hour totals are not comparable across bands: each
        # band carries its own year-to-date ledger, so the eligible sets differ
        # by history as well as by width. Monotonicity is a claim about the
        # annual total, checked below.

    band0_gap = abs(band0_tot - obs_tot) / obs_tot if obs_tot else float("nan")
    annual = np.array([cum_cut[b].sum() for b in W.BANDS])
    monotone_breaks = int((np.diff(annual) > 1e-6).sum())

    # A7: the replay's own observed-cut bookkeeping against the separate
    # measurement pipeline, which reaches the same quantity by a different route
    a7_worst, a7_n = float("nan"), 0
    # Prefer the re-run in verify/repro when it exists (it is the measurement
    # pipeline on the *same* BM window as this replay). Fall back to the
    # committed out/measurement_units.csv, which is the right target whenever
    # data/ and out/ are on the same window.
    mu = OUT.parent / "verify" / "repro" / "measurement_units.csv"
    if not mu.exists():
        mu = OUT / "measurement_units.csv"
    wu = OUT / "wpa_units.csv"
    if mu.exists() and wu.exists():
        m = pd.read_csv(mu).set_index("unit")
        w = pd.read_csv(wu).set_index("unit")
        common = [u for u in w.index if u in m.index]
        if common:
            a7_n = len(common)
            a7_worst = float((w.loc[common, "r_observed"]
                              - m.loc[common, "constraint_only_ratio"]).abs().max())

    rows = [
        ("A1 relief delivered == observed relief R", f"worst rel dev {worst_relief:.3e}",
         worst_relief <= TOL_REL),
        ("A2 cut <= declared availability", f"worst excess {worst_cap:.3e} MW",
         worst_cap <= 1e-9),
        ("A3 no negative cut", f"{n_negative} negative entries", n_negative == 0),
        ("A4 band 0 tracks observed pro-rata", f"gap {100 * band0_gap:.3f} %",
         band0_gap < 0.02),
        ("A5 annual cut monotone non-increasing in b", f"{monotone_breaks} breaks; totals " + " > ".join(f"{v:.0f}" for v in annual),
         monotone_breaks == 0),
        ("A6 every half-hour feasible", f"{n_infeasible} infeasible of {n_halfhours}",
         n_infeasible == 0),
        ("A7 observed r matches the measurement pipeline",
         f"{a7_n} units, worst abs diff {a7_worst:.3e}",
         bool(a7_n) and a7_worst < 1e-12),
    ]
    df = pd.DataFrame(rows, columns=["assertion", "detail", "passed"])
    df.to_csv(OUT / "wpa_assertions.csv", index=False)
    for a, d_, p in rows:
        print(f"{'PASS' if p else 'FAIL'}  {a:45s}  {d_}")
    print(f"\nhalf-hours checked: {n_halfhours}")
    return 0 if bool(df.passed.all()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
