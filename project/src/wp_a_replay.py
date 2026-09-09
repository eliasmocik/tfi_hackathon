"""WP-A - equal-relief replay on real 2026 SEM-O data (design brief v2 section 3).

For every half-hour in which North-West units are under constraint (LOCL, not
CURL), this replays the observed dispatch-down against counterfactual rules
that deliver *identical flow relief* on the binding element. Because the
relief R is matched by construction, security is invariant and the comparison
is purely on MWh.

No synthetic weather is used. Shift factors come from the WP2024 wind-in
network (out/WP2024s42_shift_factors.csv); everything else is measured.

    python project/src/wp_a_replay.py

Outputs into out/:
    wpa_halfhourly.csv   per half-hour totals per rule
    wpa_units.csv        per unit: observed vs counterfactual cut
    wpa_summary.json     headline savings
    wpa_stations.csv     saving by station with the station's shift factor
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "out"

# The only row that ever binds in the main case (out/WP2024s42_overload_stats.json:
# hours_over_FLG_SLIGO_N1 = 1308, both transformer windings 0). Flow on it is
# negative whenever it is over (share_pos_flow_over = 0.0), so the effective
# shift factor - MW of relief per MW cut - is the negated raw PTDF difference.
SF_COL, SF_SIGN = "SF_FLG_SLIGO_N1", -1.0

CG1_STATIONS = {"ARDNAGAPPARY", "BINBANE", "LENALEA", "TRILLICK"}
CG3_STATIONS = CG1_STATIONS | {
    "CATHALEENS FALL", "CORDERRY", "CUNGHILL", "GARVAGH", "GLENREE",
    "MEENTYCAT", "MOY", "MULREAVY", "SLIGO", "TAWNAGHMORE"}
BANDS = [0.0, 1.0, 2.0, 3.0, 5.0, 10.0, np.inf]
WIN_START, WIN_END = pd.Timestamp("2026-06-08 00:00"), pd.Timestamp("2026-09-05 23:59")

SET_CODES = {"LOCL": "constraint", "CURL": "curtail"}
CLR_CODES = {"LCLO": "constraint", "CRLO": "curtail"}
ALL_CODES = {**SET_CODES, **CLR_CODES}


#: The SEM-O unit map and the model spell some stations differently. Without
#: this, Cathaleen's Fall units are silently dropped from the group: the map
#: says CATH_FALL and the model says "Cathaleen's Fall". Today those units have
#: no BM-101 rows so nothing is lost, but that is luck, not correctness.
STATION_ALIASES = {
    "CATH FALL": "CATHALEENS FALL",
    "CATHALEENS FALL": "CATHALEENS FALL",
}


def canon_station(s) -> str:
    c = str(s).upper().replace("'", "").replace("_", " ").strip()
    return STATION_ALIASES.get(c, c)


def band_key(b: float) -> str:
    return "inf" if np.isinf(b) else f"{b:g}"


def load_measured() -> pd.DataFrame:
    """Half-hourly availability, dispatch quantity and LOCL/CURL state per unit."""
    av = pd.read_csv(DATA / "BM-101_nw_units.csv", parse_dates=["StartTime"])
    dq = pd.read_csv(DATA / "BM-096_nw_units.csv", parse_dates=["StartTime"])
    ins = pd.read_csv(DATA / "BM-037_dispatch_instructions_2026-06-07_to_09-05.csv",
                      parse_dates=["EffTime", "InstrIssueTime"])

    j = av[["ResourceName", "StartTime", "AvgOutturnAvail"]].merge(
        dq[["ResourceName", "StartTime", "DispatchQuantity"]],
        on=["ResourceName", "StartTime"], how="inner")
    j = j[(j.StartTime >= WIN_START) & (j.StartTime <= WIN_END)].copy()
    # MW, not MWh: DispatchQuantity is energy over the half hour, so twice it is
    # the average rate, directly comparable with AvgOutturnAvail.
    j["avail_MW"] = j.AvgOutturnAvail
    j["cut_MW"] = (j.avail_MW - 2.0 * j.DispatchQuantity).clip(lower=0)

    ins = ins[ins.InstructionCombinationCode.isin(ALL_CODES)]
    ins = ins.sort_values(["ResourceName", "EffTime", "InstrIssueTime"])

    j = j.sort_values(["ResourceName", "StartTime"]).reset_index(drop=True)
    con = np.zeros(len(j), bool)
    cur = np.zeros(len(j), bool)
    for unit, g in j.groupby("ResourceName", sort=False):
        e = ins[ins.ResourceName == unit]
        if e.empty:
            continue
        times = g.StartTime.to_numpy()
        for field, sink in (("constraint", con), ("curtail", cur)):
            codes = e[e.InstructionCombinationCode.isin(
                [k for k, v in ALL_CODES.items() if v == field])]
            if codes.empty:
                continue
            on = codes.InstructionCombinationCode.isin(SET_CODES).to_numpy()
            t = codes.EffTime.to_numpy()
            pos = np.searchsorted(t, times, side="right") - 1
            sink[g.index.to_numpy()] = np.where(pos >= 0, on[np.clip(pos, 0, None)], False)
    j["constraint"], j["curtail"] = con, cur
    return j


def station_shift_factors() -> pd.Series:
    """Effective shift factor per station, from the model's per-bus values.

    Shift factor is a property of the bus, so every unit at a station shares it.
    Where a station has more than one bus (Cathaleen's Fall) the capacity-
    weighted mean is used.
    """
    sf = pd.read_csv(OUT / "WP2024s42_shift_factors.csv")
    sf["SF_eff"] = SF_SIGN * sf[SF_COL]
    sf["st"] = sf.station.map(canon_station)
    out = {}
    for st, d in sf.groupby("st"):
        w = d.p_nom.to_numpy(float).clip(min=1e-9)
        out[st] = float(np.average(d.SF_eff.to_numpy(float), weights=w))
    return pd.Series(out, name="SF_eff")


def greedy_to_relief(sf, cap, R, eligible=None):
    """Cut in descending shift factor until the relief R is delivered.

    Eligible units are taken first; if they cannot reach R the remaining units
    follow in the same descending-effectiveness order (the feasibility escape
    of design brief v2 section 3, WP-E). Returns the cut vector in MW.
    """
    c = np.zeros_like(cap)
    if R <= 0:
        return c
    order = np.argsort(-sf)
    if eligible is not None:
        order = np.concatenate([order[eligible[order]], order[~eligible[order]]])
    remaining = R
    for i in order:
        if remaining <= 1e-9 or sf[i] <= 0 or cap[i] <= 0:
            continue
        take = min(cap[i], remaining / sf[i])
        c[i] = take
        remaining -= take * sf[i]
    return c


def main() -> int:
    meas = load_measured()
    sfw = station_shift_factors()

    umap = pd.read_csv(DATA / "semo_unit_map_IE.csv")
    umap["st"] = umap.station.map(canon_station)
    u2s = dict(zip(umap.unit, umap.st))

    meas["st"] = meas.ResourceName.map(u2s)
    meas = meas[meas.st.isin(CG3_STATIONS)].copy()
    meas["SF_eff"] = meas.st.map(sfw)
    meas = meas[meas.SF_eff.notna()].copy()
    if meas.empty:
        raise SystemExit("no CG3 units matched a station shift factor")
    # constraint-only: LOCL active and CURL not, so curtailment is excluded
    meas["active"] = meas.constraint & ~meas.curtail

    units = sorted(meas.ResourceName.unique())
    uidx = {u: i for i, u in enumerate(units)}
    first = meas.groupby("ResourceName").first()
    sf_u = first.loc[units, "SF_eff"].to_numpy(float)
    st_u = first.loc[units, "st"].tolist()

    cum_cut = {b: np.zeros(len(units)) for b in BANDS}
    cum_cut_obs = np.zeros(len(units))
    cum_avail = np.zeros(len(units))
    rows = []

    for t, g in meas.groupby("StartTime", sort=True):
        idx = np.array([uidx[u] for u in g.ResourceName])
        cap = g.avail_MW.to_numpy(float)
        obs = np.where(g.active.to_numpy(), g.cut_MW.to_numpy(float), 0.0)
        sfh = g.SF_eff.to_numpy(float)
        cum_avail[idx] += cap * 0.5
        cum_cut_obs[idx] += obs * 0.5
        R = float((sfh * obs).sum())
        if R <= 1e-9:
            continue
        rec = {"StartTime": t, "R_MW": R, "observed_MW": float(obs.sum()),
               "n_units_cut": int((obs > 0).sum()), "n_units_available": int((cap > 0).sum())}
        for b in BANDS:
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
            c = greedy_to_relief(sfh, cap, R, elig)
            cum_cut[b][idx] += c * 0.5
            rec[f"band{band_key(b)}_MW"] = float(c.sum())
        rows.append(rec)

    hh = pd.DataFrame(rows)
    hh.to_csv(OUT / "wpa_halfhourly.csv", index=False)

    obs_MWh = float(cum_cut_obs.sum())
    summary = {
        "half_hours_with_relief": int(len(hh)),
        "units": len(units),
        "window": [str(meas.StartTime.min()), str(meas.StartTime.max())],
        "binding_row": SF_COL,
        "observed_cut_MWh": obs_MWh,
        "observed_avail_MWh": float(cum_avail.sum()),
        "SF_min": float(np.nanmin(sf_u)),
        "SF_max": float(np.nanmax(sf_u)),
    }
    for b in BANDS:
        key = "effectiveness" if np.isinf(b) else f"band{band_key(b)}pp"
        tot = float(cum_cut[b].sum())
        summary[f"{key}_cut_MWh"] = tot
        summary[f"{key}_saving_MWh"] = obs_MWh - tot
        summary[f"{key}_saving_pct"] = (100.0 * (obs_MWh - tot) / obs_MWh) if obs_MWh else float("nan")

    ut = pd.DataFrame({"unit": units, "station": st_u, "SF_eff": sf_u,
                       "cum_avail_MWh": cum_avail, "observed_cut_MWh": cum_cut_obs})
    for b in BANDS:
        ut[f"cut_MWh_band{band_key(b)}"] = cum_cut[b]
    ut["r_observed"] = ut.observed_cut_MWh / ut.cum_avail_MWh.replace(0, np.nan)
    ut["r_effectiveness"] = ut["cut_MWh_bandinf"] / ut.cum_avail_MWh.replace(0, np.nan)
    ut.to_csv(OUT / "wpa_units.csv", index=False)

    st = ut.groupby("station").agg(
        n_units=("unit", "count"),
        SF_eff=("SF_eff", "first"),
        avail_MWh=("cum_avail_MWh", "sum"),
        observed_cut_MWh=("observed_cut_MWh", "sum"),
        effectiveness_cut_MWh=("cut_MWh_bandinf", "sum"),
        band3_cut_MWh=("cut_MWh_band3", "sum"))
    st["r_observed"] = st.observed_cut_MWh / st.avail_MWh
    st["r_effectiveness"] = st.effectiveness_cut_MWh / st.avail_MWh
    st.sort_values("SF_eff", ascending=False).to_csv(OUT / "wpa_stations.csv")

    (OUT / "wpa_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
