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
import os

import numpy as np
import pandas as pd

import wp_a_replay as W

OUT = W.OUT

#: Days at the start of the window during which the ledger accumulates but the
#: divergence and delta statistics are NOT recorded.
#:
#: r_i = cumulative cut / cumulative availability divides by a denominator that
#: starts at zero, so in the opening hours a single instruction moves a unit's
#: ratio by tens of percentage points and the "largest single-event increment"
#: is a property of the empty ledger, not of the rule. Measured here: with no
#: warm-up delta is 22.1 pp and every band shows the same 21.2 pp realised
#: divergence; after one week they separate and track b (see
#: wpe_warmup_sensitivity.csv, which reports the whole range so the choice is
#: visible rather than tuned). A real annual scheme would either seed the
#: ledger from the previous year or state the same warm-up in its licence text.
WARMUP_DAYS = float(os.environ.get("WARMUP_DAYS", 7.0))


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
    t0 = meas.StartTime.min()
    # sensitivity: the same statistics under a range of warm-ups
    SENS = [0.0, 3.0, 7.0, 14.0]
    sens_div = {(w, b): 0.0 for w in SENS for b in bands}
    sens_delta = {(w, b): 0.0 for w in SENS for b in bands}
    sens_obs = {w: 0.0 for w in SENS}

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
        age_days = (t - t0).total_seconds() / 86400.0
        counted = age_days >= WARMUP_DAYS
        obs_div_now = float((r_obs - rbar_obs).max())
        if counted:
            obs_max_div = max(obs_max_div, obs_div_now)
        for w in SENS:
            if age_days >= w:
                sens_obs[w] = max(sens_obs[w], obs_div_now)

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
            step = float((cum_cut[b][idx] / av_i - r_before).max())
            if counted:
                max_div[b] = max(max_div[b], div)
                delta[b] = max(delta[b], step)
            for w in SENS:
                if age_days >= w:
                    sens_div[(w, b)] = max(sens_div[(w, b)], div)
                    sens_delta[(w, b)] = max(sens_delta[(w, b)], step)
            row[f"band{W.band_key(b)}_maxdiv_pp"] = 100.0 * div
        row["observed_maxdiv_pp"] = 100.0 * float((r_obs - rbar_obs).max())
        traj.append(row)

    tj = pd.DataFrame(traj)
    tj.to_csv(OUT / "wpe_trajectory.csv", index=False)

    sens_rows = []
    for w in SENS:
        for b in bands:
            sens_rows.append({
                "warmup_days": w, "band_pp": b,
                "realised_max_divergence_pp": 100.0 * sens_div[(w, b)],
                "delta_pp": 100.0 * sens_delta[(w, b)],
                "observed_pro_rata_max_divergence_pp": 100.0 * sens_obs[w],
            })
    pd.DataFrame(sens_rows).to_csv(OUT / "wpe_warmup_sensitivity.csv", index=False)

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
        "warmup_days": WARMUP_DAYS,
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
    print(f"half-hours: {n_hh}   warm-up: {WARMUP_DAYS:g} days "
          f"(statistics recorded after it; the ledger accumulates throughout)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
