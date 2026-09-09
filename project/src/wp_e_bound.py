"""WP-E - the equity guarantee (design brief v2 section 3, WP-E).

Merriman's requirement is an *ex-ante* bound that would stand up in court, not
an ex-post average. The claim under test:

    under the band rule of width b, for every half-hour t and every unit i in
    the group,   r_i(t) - rbar_G(t)  <=  b + delta

where r_i is the unit's year-to-date cut ratio, rbar_G the availability-
weighted group mean, and delta the largest single-event ratio increment (the
overshoot a single instruction can add to one unit before the ledger can
react). The bound is claimed only while no feasibility escape fires.

This measures, on the real 2026 replay:

  * realised max_i (r_i - rbar) per band, against the claimed bound b + delta
  * delta itself, measured rather than assumed
  * how often the eligible set could not deliver R and had to be widened
  * the same divergence statistic for the observed pro-rata dispatch, which
    has no bound at all - that asymmetry is the legal argument

    python project/src/wp_e_bound.py

Outputs out/wpe_bound.csv, out/wpe_trajectory.csv and out/wpe_summary.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import wp_a_replay as W

OUT = W.OUT


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
    n = len(units)

    # the infinite band (pure effectiveness) is included so the table can say
    # what it costs in equity; it has no ex-ante bound by construction
    bands = list(W.BANDS)
    cum_cut = {b: np.zeros(n) for b in bands}
    cum_avail = np.zeros(n)
    obs_cut = np.zeros(n)

    max_div = {b: 0.0 for b in bands}      # realised max_i (r_i - rbar)
    delta = {b: 0.0 for b in bands}        # largest single-event ratio increment
    escapes = {b: 0 for b in bands}        # eligible set could not deliver R
    obs_max_div = 0.0
    traj = []
    n_hh = 0

    for t, g in meas.groupby("StartTime", sort=True):
        idx = np.array([uidx[u] for u in g.ResourceName])
        cap = g.avail_MW.to_numpy(float)
        obs = np.where(g.active.to_numpy(), g.cut_MW.to_numpy(float), 0.0)
        sfh = g.SF_eff.to_numpy(float)
        cum_avail[idx] += cap * 0.5
        obs_cut[idx] += obs * 0.5
        R = float((sfh * obs).sum())
        if R <= 1e-9:
            continue
        n_hh += 1

        # observed pro-rata divergence, for the contrast
        av_all = np.maximum(cum_avail, 1e-9)
        r_obs = obs_cut / av_all
        rbar_obs = obs_cut.sum() / cum_avail.sum() if cum_avail.sum() > 0 else 0.0
        obs_max_div = max(obs_max_div, float((r_obs - rbar_obs).max()))

        row = {"StartTime": t}
        for b in bands:
            av_i = np.maximum(cum_avail[idx], 1e-9)
            r_before = cum_cut[b][idx] / av_i
            tot_av = cum_avail[idx].sum()
            rbar = (cum_cut[b][idx].sum() / tot_av) if tot_av > 0 else 0.0
            elig = (np.ones(len(idx), bool) if np.isinf(b)
                    else r_before <= rbar + b / 100.0)
            if not elig.any():
                elig = np.ones(len(idx), bool)
            # a feasibility escape is a half-hour where the eligible set alone
            # cannot deliver R, so ineligible units must be drawn in
            if float((sfh[elig] * cap[elig]).sum()) + 1e-9 < R:
                escapes[b] += 1

            c = W.greedy_to_relief(sfh, cap, R, elig)
            cum_cut[b][idx] += c * 0.5

            r_after = cum_cut[b] / np.maximum(cum_avail, 1e-9)
            rbar_all = cum_cut[b].sum() / cum_avail.sum() if cum_avail.sum() > 0 else 0.0
            div = float((r_after - rbar_all).max())
            max_div[b] = max(max_div[b], div)
            step = float((cum_cut[b][idx] / av_i - r_before).max())
            delta[b] = max(delta[b], step)
            row[f"band{W.band_key(b)}_maxdiv_pp"] = 100.0 * div
        row["observed_maxdiv_pp"] = 100.0 * float((r_obs - rbar_obs).max())
        traj.append(row)

    tj = pd.DataFrame(traj)
    tj.to_csv(OUT / "wpe_trajectory.csv", index=False)

    rows = []
    for b in bands:
        realised = 100.0 * max_div[b]
        d_pp = 100.0 * delta[b]
        rows.append({
            "band_pp": b,
            "claimed_bound_pp": (np.inf if np.isinf(b) else b + d_pp),
            "realised_max_divergence_pp": realised,
            "delta_pp": d_pp,
            "bound_holds": (True if np.isinf(b) else bool(realised <= b + d_pp + 1e-9)),
            "slack_pp": (np.inf if np.isinf(b) else (b + d_pp) - realised),
            "feasibility_escapes": escapes[b],
            "escape_share": escapes[b] / n_hh if n_hh else np.nan,
        })
    bd = pd.DataFrame(rows)
    bd.to_csv(OUT / "wpe_bound.csv", index=False)

    summary = {
        "half_hours": n_hh,
        "units": n,
        "observed_pro_rata_max_divergence_pp": 100.0 * obs_max_div,
        "observed_has_ex_ante_bound": False,
        "all_bounds_hold": bool(bd.bound_holds.all()),
        "bands": rows,
    }
    (OUT / "wpe_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    print(bd.to_string(index=False))
    print(f"\nobserved pro-rata max divergence: {100 * obs_max_div:.3f} pp "
          f"(no ex-ante bound exists for it)")
    print(f"half-hours: {n_hh}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
