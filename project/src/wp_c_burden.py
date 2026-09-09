"""WP-C - operational burden and implementability (design brief v2, WP-C / C5).

Merriman's objection: dispatching individual wind farms inside a constraint
group is time-consuming unless automated. So the rule must not need per-hour
per-farm eligibility. This tests the implementable version:

  * the group is pre-split into k sub-groups, two ways: contiguous bands of
    shift factor, and a round-robin interleave that gives every sub-group a
    similar spread. The choice turns out to matter more than k does;
  * which sub-group is "on duty" is refreshed on a slow cadence (hour, day,
    week, month) by picking the sub-group with the lowest year-to-date cut
    ratio, so the ledger still drives rotation;
  * within the on-duty sub-group units are cut in effectiveness order, and if
    that sub-group cannot deliver the relief the next one is drawn in.

The operator still issues one instruction per event: the eligible list is
precomputed, not solved in the control room.

C5 is falsified if the retained gain at k <= 3 on a daily cadence falls below
about 50 %.

    python project/src/wp_c_burden.py

Outputs out/wpc_burden.csv and out/wpc_summary.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import wp_a_replay as W

OUT = W.OUT
KS = [2, 3, 4]
CADENCES = {"hour": "h", "day": "D", "week": "W", "month": "MS"}


def period_key(ts: pd.Timestamp, cadence: str):
    if cadence == "hour":
        return ts.floor("h")
    if cadence == "day":
        return ts.normalize()
    if cadence == "week":
        return ts.normalize() - pd.Timedelta(days=int(ts.dayofweek))
    return pd.Timestamp(ts.year, ts.month, 1)


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
    first = meas.groupby("ResourceName").first()
    sf_u = first.loc[units, "SF_eff"].to_numpy(float)

    # Two ways to pre-split the group, because the choice turns out to matter:
    #  "tiers"       contiguous bands of descending shift factor. The lowest-
    #                burden tier is then almost always the low-SF one, so
    #                equity-driven rotation actively selects the least
    #                effective units.
    #  "interleaved" round-robin over the SF ranking, so every sub-group holds
    #                a similar spread of shift factors and whichever is on duty
    #                can still cut effectively.
    order = np.argsort(-sf_u)
    PARTITIONS = {
        "tiers": {k: np.array_split(order, k) for k in KS},
        "interleaved": {k: [order[i::k] for i in range(k)] for k in KS},
    }

    # reference points from the full replay
    wpa = json.loads((OUT / "wpa_summary.json").read_text(encoding="utf-8"))
    obs_MWh = wpa["observed_cut_MWh"]
    ideal_MWh = wpa["effectiveness_cut_MWh"]
    ideal_gain = obs_MWh - ideal_MWh

    rows = []
    for part_name, tiers in PARTITIONS.items():
     for k in KS:
      for cad in CADENCES:
            cum_cut = np.zeros(n)
            cum_avail = np.zeros(n)
            on_duty = 0
            cur_period = None
            switches = 0
            escapes = 0
            hh = 0

            for t, g in meas.groupby("StartTime", sort=True):
                idx = np.array([uidx[u] for u in g.ResourceName])
                cap = g.avail_MW.to_numpy(float)
                obs = np.where(g.active.to_numpy(), g.cut_MW.to_numpy(float), 0.0)
                sfh = g.SF_eff.to_numpy(float)
                cum_avail[idx] += cap * 0.5
                R = float((sfh * obs).sum())
                if R <= 1e-9:
                    continue
                hh += 1

                p = period_key(pd.Timestamp(t), cad)
                if p != cur_period:
                    cur_period = p
                    # rotate to the sub-group carrying the least burden so far
                    r = cum_cut / np.maximum(cum_avail, 1e-9)
                    means = [float(r[tier].mean()) if len(tier) else np.inf
                             for tier in tiers[k]]
                    new_duty = int(np.argmin(means))
                    if new_duty != on_duty:
                        switches += 1
                    on_duty = new_duty

                # eligible = the on-duty tier, restricted to units present this hh
                duty_units = set(tiers[k][on_duty].tolist())
                elig = np.array([i in duty_units for i in idx])
                if not elig.any():
                    elig = np.ones(len(idx), bool)
                if float((sfh[elig] * cap[elig]).sum()) + 1e-9 < R:
                    escapes += 1
                c = W.greedy_to_relief(sfh, cap, R, elig)
                cum_cut[idx] += c * 0.5

            tot = float(cum_cut.sum())
            gain = obs_MWh - tot
            rows.append({
                "partition": part_name, "k": k, "cadence": cad,
                "cut_MWh": tot,
                "gain_MWh": gain,
                "gain_retained_pct": 100.0 * gain / ideal_gain if ideal_gain else np.nan,
                "saving_vs_observed_pct": 100.0 * gain / obs_MWh if obs_MWh else np.nan,
                "eligibility_switches": switches,
                "feasibility_escapes": escapes,
                "half_hours": hh,
                "operator_actions_per_event": 1,
                "precomputed_subgroups": k,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "wpc_burden.csv", index=False)

    best = df[df.partition == "interleaved"]
    daily_small = best[(best.k <= 3) & (best.cadence == "day")]
    c5_holds = bool((daily_small.gain_retained_pct >= 50.0).all())
    summary = {
        "observed_cut_MWh": obs_MWh,
        "ideal_effectiveness_cut_MWh": ideal_MWh,
        "ideal_gain_MWh": ideal_gain,
        "C5_test": "retained gain at k<=3 on a daily cadence stays at or above 50 %",
        "C5_holds": c5_holds,
        "C5_partition": "interleaved",
        "C5_values_pct": daily_small.set_index("k").gain_retained_pct.round(2).to_dict(),
        "contiguous_tier_values_pct": df[(df.partition == "tiers") & (df.k <= 3) &
            (df.cadence == "day")].set_index("k").gain_retained_pct.round(2).to_dict(),
        "operator_actions_per_event": 1,
        "groups_in_scope": 1,
    }
    (OUT / "wpc_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    for pn in PARTITIONS:
        print(f"--- {pn} (gain retained, %)")
        print(df[df.partition == pn].pivot(index="k", columns="cadence",
              values="gain_retained_pct").round(1).to_string())
    print()
    print(f"C5 (k<=3, daily, >=50 % retained): {'HOLDS' if c5_holds else 'FALSIFIED'}"
          f"  values {summary['C5_values_pct']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
