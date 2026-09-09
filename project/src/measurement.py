#!/usr/bin/env python3
"""MASTER §6 — Measurement (2026 SEM-O data).

Reproduces and extends data/nw_unit_dispatchdown_2026-06-08_to_09-05.csv from the
raw BM-101 / BM-096 / BM-037 files, assigns units to WDT constraint groups by
station, computes the group fairness table, the co-instruction batch table and
the bar chart. Re-runnable; every number that reaches a document is printed here
and written to out/.

Run:  python3 src/measurement.py   (from /home/claude/project)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

F_AVAIL = DATA / "BM-101_nw_units.csv"
F_DQ = DATA / "BM-096_nw_units.csv"
F_INSTR = DATA / "BM-037_dispatch_instructions_2026-06-07_to_09-05.csv"
F_OLD = DATA / "nw_unit_dispatchdown_2026-06-08_to_09-05.csv"
F_MAP = DATA / "semo_unit_map_IE.csv"

# ---- fixed by MASTER §6 -------------------------------------------------------
STATE_INIT_TIME = pd.Timestamp("2026-06-07T00:00:00")   # state = False here
MIN_AVAIL_MWH = 250.0                                    # filter (§6.6)
# station names exactly as spelled in semo_unit_map_IE.csv (checked: Cathaleen's
# Fall is "CATH_FALL"; ARDNAGAPPARY, MOY and SLIGO have no unit in the IE map)
CG1_STATIONS = {"ARDNAGAPPARY", "BINBANE", "LENALEA", "TRILLICK"}
CG3_EXTRA = {"CATH_FALL", "CORDERRY", "CUNGHILL", "GARVAGH", "GLENREE",
             "MEENTYCAT", "MOY", "MULREAVY", "SLIGO", "TAWNAGHMORE"}
CG3_STATIONS = CG1_STATIONS | CG3_EXTRA
BOOLTIAGH = {"BOOLTIAGH"}
STATE_CODES = {"LOCL": ("constraint", True), "LCLO": ("constraint", False),
               "CURL": ("curtail", True), "CRLO": ("curtail", False)}

LINES: list[str] = []          # everything printed also goes to the notes


def say(*args):
    s = " ".join(str(a) for a in args)
    print(s)
    LINES.append(s)


def jain(r: np.ndarray) -> float:
    r = np.asarray(r, float)
    n = len(r)
    if n == 0 or (r ** 2).sum() == 0:
        return float("nan")
    return float(r.sum() ** 2 / (n * (r ** 2).sum()))


def gini(r: np.ndarray) -> float:
    """MASTER §5: ascending sort, G = Σ (2i − N − 1) r_i / (N Σ r_i); unweighted,
    no small-sample correction."""
    r = np.sort(np.asarray(r, float))
    n = len(r)
    if n == 0 or r.sum() == 0:
        return float("nan")
    i = np.arange(1, n + 1)
    return float(((2 * i - n - 1) * r).sum() / (n * r.sum()))


# ==============================================================================
# 1. Join BM-101 and BM-096
# ==============================================================================
say("=" * 78)
say("§6.1  Join BM-101 (AvgOutturnAvail, MW) and BM-096 (DispatchQuantity, MWh/30min)")
av = pd.read_csv(F_AVAIL, parse_dates=["StartTime"])
dq = pd.read_csv(F_DQ, parse_dates=["StartTime"])
say(f"BM-101 rows {len(av)}, units {av.ResourceName.nunique()}, "
    f"window {av.StartTime.min()} .. {av.StartTime.max()}")
say(f"BM-096 rows {len(dq)}, units {dq.ResourceName.nunique()}, "
    f"window {dq.StartTime.min()} .. {dq.StartTime.max()}")
assert not av.duplicated(["ResourceName", "StartTime"]).any()
assert not dq.duplicated(["ResourceName", "StartTime"]).any()
units_101 = set(av.ResourceName)
units_096 = set(dq.ResourceName)
say(f"units in BM-101 but not BM-096: {sorted(units_101 - units_096)}")
say(f"units in BM-096 but not BM-101 (0 rows in BM-101 -> no availability, dropped): "
    f"{sorted(units_096 - units_101)}")

hh = av.merge(dq[["ResourceName", "StartTime", "DispatchQuantity"]],
              on=["ResourceName", "StartTime"], how="inner")
say(f"inner join rows {len(hh)}, units {hh.ResourceName.nunique()}")
hh["avail_MWh"] = 0.5 * hh["AvgOutturnAvail"]
hh["dd_MWh"] = np.maximum(0.0, hh["avail_MWh"] - hh["DispatchQuantity"])
say(f"half-hours per unit: min {hh.groupby('ResourceName').size().min()}, "
    f"max {hh.groupby('ResourceName').size().max()}")
window_start = hh.StartTime.min()
window_end = hh.StartTime.max()
say(f"measurement window (StartTime): {window_start} .. {window_end}, "
    f"{(window_end - window_start) / pd.Timedelta(days=1):.4f} days between first and last StartTime")

# ==============================================================================
# 2. State machine from BM-037
# ==============================================================================
say("=" * 78)
say("§6.2  State machine from BM-037")
ins = pd.read_csv(F_INSTR, parse_dates=["EffTime", "InstrIssueTime"])
say(f"BM-037 rows {len(ins)}; EffTime {ins.EffTime.min()} .. {ins.EffTime.max()}")
n_stray = int((ins.EffTime < STATE_INIT_TIME).sum())
say(f"rows with EffTime before state initialisation {STATE_INIT_TIME} "
    f"(stray 2020-04 rows, dropped): {n_stray}")
ins = ins[ins.EffTime >= STATE_INIT_TIME].copy()
wind = ins[ins.InstructionCode.eq("WIND")
           & ins.InstructionCombinationCode.isin(STATE_CODES)].copy()
say("WIND rows by combination code: "
    + ", ".join(f"{k}={v}" for k, v in wind.InstructionCombinationCode.value_counts().items()))
wind = wind.sort_values(["ResourceName", "EffTime", "InstrIssueTime"], kind="stable")
wind["var"] = wind.InstructionCombinationCode.map(lambda c: STATE_CODES[c][0])
wind["val"] = wind.InstructionCombinationCode.map(lambda c: STATE_CODES[c][1])

units = sorted(hh.ResourceName.unique())


def state_at(times: pd.Series, unit: str, var: str, inclusive: bool) -> np.ndarray:
    """State of `var` for `unit` at each time. State is False at STATE_INIT_TIME
    and follows the LOCL/LCLO (or CURL/CRLO) instructions sorted by EffTime.
    inclusive=True: an instruction with EffTime == StartTime counts for that
    half-hour (EffTime <= StartTime); False: strictly before."""
    ev = wind[(wind.ResourceName == unit) & (wind["var"] == var)]
    if ev.empty:
        return np.zeros(len(times), bool)
    t_ev = ev.EffTime.to_numpy(dtype="datetime64[ns]")
    v_ev = ev.val.to_numpy(bool)
    t = times.to_numpy(dtype="datetime64[ns]")
    side = "right" if inclusive else "left"
    idx = np.searchsorted(t_ev, t, side=side)   # number of events applied
    out = np.zeros(len(t), bool)
    m = idx > 0
    out[m] = v_ev[idx[m] - 1]
    return out


def first_event_info(unit: str, var: str):
    ev = wind[(wind.ResourceName == unit) & (wind["var"] == var)]
    if ev.empty:
        return None, None
    return ev.iloc[0].InstructionCombinationCode, ev.iloc[0].EffTime


# state at window start (from the 06-07 instructions) and first-event codes
init_rows = []
for u in units:
    rec = {"unit": u}
    for var in ("constraint", "curtail"):
        s = state_at(pd.Series([window_start]), u, var, inclusive=True)[0]
        code, t = first_event_info(u, var)
        rec[f"{var}_state_at_window_start"] = bool(s)
        rec[f"{var}_first_code"] = code
        rec[f"{var}_first_efftime"] = t
    init_rows.append(rec)
init = pd.DataFrame(init_rows)
n_c_start = int(init.constraint_state_at_window_start.sum())
n_k_start = int(init.curtail_state_at_window_start.sum())
n_c_release_first = int(init.constraint_first_code.eq("LCLO").sum())
n_k_release_first = int(init.curtail_first_code.eq("CRLO").sum())
say(f"state initialised False for every unit at {STATE_INIT_TIME}; instructions from "
    f"{STATE_INIT_TIME.date()} onward are replayed before the window opens at {window_start}")
say(f"units under LOCL constraint at window start {window_start}: {n_c_start} "
    f"{sorted(init.unit[init.constraint_state_at_window_start].tolist())}")
say(f"units under CURL curtailment at window start: {n_k_start} "
    f"{sorted(init.unit[init.curtail_state_at_window_start].tolist())}")
say(f"units whose FIRST constraint instruction in BM-037 is a release (LCLO), i.e. "
    f"they entered the file mid-instruction and the state machine misses that first "
    f"spell: {n_c_release_first} "
    f"{sorted(init.unit[init.constraint_first_code.eq('LCLO')].tolist())}")
say(f"units whose FIRST curtailment instruction is a release (CRLO): {n_k_release_first} "
    f"{sorted(init.unit[init.curtail_first_code.eq('CRLO')].tolist())}")
say(f"units with no LOCL/LCLO instruction at all in BM-037: "
    f"{sorted(init.unit[init.constraint_first_code.isna()].tolist())}")


def unit_table(inclusive: bool) -> pd.DataFrame:
    rows = []
    for u, g in hh.groupby("ResourceName", sort=True):
        c = state_at(g.StartTime, u, "constraint", inclusive)
        k = state_at(g.StartTime, u, "curtail", inclusive)
        avail = g.avail_MWh.sum()
        dd = g.dd_MWh.sum()
        rows.append({
            "unit": u,
            "avail_MWh": avail,
            "dd_MWh": dd,
            "dd_ratio": dd / avail if avail > 0 else np.nan,
            "constraint_only_ratio": g.dd_MWh[c & ~k].sum() / avail if avail > 0 else np.nan,
            "locl_any_ratio": g.dd_MWh[c].sum() / avail if avail > 0 else np.nan,
            "curl_only_ratio": g.dd_MWh[k & ~c].sum() / avail if avail > 0 else np.nan,
            "h_locl": 0.5 * c.sum(),
            "h_curl": 0.5 * k.sum(),
            "halfhours": len(g),
            "hh_constraint_only": int((c & ~k).sum()),
            "hh_both": int((c & k).sum()),
        })
    return pd.DataFrame(rows)


# ==============================================================================
# 3/4. Per-unit table and reproduction check
# ==============================================================================
say("=" * 78)
say("§6.3/6.4  Per-unit table and reproduction of the existing CSV")
old = pd.read_csv(F_OLD)
CMP_COLS = ["avail_MWh", "dd_MWh", "dd_ratio", "constraint_only_ratio",
            "locl_any_ratio", "curl_only_ratio", "h_locl", "h_curl", "halfhours"]


def compare(new: pd.DataFrame, label: str) -> pd.DataFrame:
    m = old.merge(new, on="unit", suffixes=("_old", "_new"), how="left")
    say(f"-- comparison [{label}]: old rows {len(old)}, matched {m.avail_MWh_new.notna().sum()}")
    recs = []
    for c in CMP_COLS:
        d = (m[f"{c}_new"] - m[f"{c}_old"]).abs()
        d_round = (m[f"{c}_new"].round(0) - m[f"{c}_old"]).abs() if c in ("avail_MWh", "dd_MWh") else d
        recs.append({"column": c, "max_abs_diff": d.max(),
                     "max_abs_diff_after_rounding_new_to_int": d_round.max(),
                     "unit_at_max": m.unit[d.idxmax()]})
        say(f"   {c:24s} max|new-old| = {d.max():.6g}  (unit {m.unit[d.idxmax()]})"
            + (f"; after rounding new to integer: {d_round.max():.6g}" if c in ("avail_MWh", "dd_MWh") else ""))
    return pd.DataFrame(recs)


tab_incl = unit_table(inclusive=True)
tab_excl = unit_table(inclusive=False)
cmp_incl = compare(tab_incl, "EffTime <= StartTime")
cmp_excl = compare(tab_excl, "EffTime <  StartTime")
say(f"half-hours whose StartTime equals an instruction EffTime exactly (where the two "
    f"conventions differ): "
    f"{int(hh.StartTime.isin(wind.EffTime).sum())}")
ratio_cols = ["dd_ratio", "constraint_only_ratio", "locl_any_ratio", "curl_only_ratio", "h_locl", "h_curl"]
ok_incl = cmp_incl.set_index("column").loc[ratio_cols, "max_abs_diff"].max()
ok_excl = cmp_excl.set_index("column").loc[ratio_cols, "max_abs_diff"].max()
say(f"max abs diff over ratio/hour columns: inclusive {ok_incl:.3g}, exclusive {ok_excl:.3g}")
use_inclusive = ok_incl <= ok_excl
tab = tab_incl if use_inclusive else tab_excl
cmp = cmp_incl if use_inclusive else cmp_excl
say(f"convention used from here on: EffTime {'<=' if use_inclusive else '<'} StartTime")
repro_ok = cmp.set_index("column").loc[ratio_cols, "max_abs_diff"].max() < 5e-4
say(f"reproduction to 3 decimals on ratio and hour columns: {'PASS' if repro_ok else 'FAIL'}")
old_int = old[["avail_MWh", "dd_MWh"]].eq(old[["avail_MWh", "dd_MWh"]].round(0)).all().all()
say(f"old CSV avail_MWh/dd_MWh are whole numbers: {old_int} (old file rounded MWh to integers; "
    f"ratios in the old file were computed from unrounded values, see dd_ratio diff above)")
say(f"units in the raw data but absent from the old CSV: {sorted(set(tab.unit) - set(old.unit))}")

# ==============================================================================
# 5. Map to stations, assign groups
# ==============================================================================
say("=" * 78)
say("§6.5  Stations and groups")
umap = pd.read_csv(F_MAP)
tab = tab.merge(umap[["unit", "name", "station", "tso_id"]], on="unit", how="left")
say(f"units without a station in the map: {sorted(tab.unit[tab.station.isna()].tolist())}")
map_stations = set(umap.station)
for s in sorted(CG3_STATIONS):
    say(f"   station {s:12s} in map: {s in map_stations}; units in map: "
        f"{umap.unit[umap.station == s].tolist()}")
say("Sorne Hill Generator Unit (GU_400550) sits at TRILLICK in the map; the WDT document lists "
    "Sorne Hill and Trillick as separate stations. Both are CG1, so nothing changes.")
say("TIEVEBRACK (Cronalaght 2, GU_403840) is in neither CG1 nor CG3 in the Feb 2024 document.")
say("Cathaleen's Fall is spelled CATH_FALL in the map; ARDNAGAPPARY, MOY and SLIGO have no "
    "unit in the IE map, so no measured unit can be assigned to them.")


def group_of(st):
    if st in CG1_STATIONS:
        return "CG1"
    if st in CG3_STATIONS:
        return "CG3-only"
    if st in BOOLTIAGH:
        return "Booltiagh"
    return "other"


tab["group"] = tab.station.map(group_of)
tab["in_CG1"] = tab.station.isin(CG1_STATIONS)
tab["in_CG3"] = tab.station.isin(CG3_STATIONS)
tab["in_Booltiagh"] = tab.station.isin(BOOLTIAGH)
say("units per group label: " + ", ".join(f"{k}={v}" for k, v in tab.group.value_counts().items()))

# units at CG3 stations in the map that have no BM-101 rows (absent from the data)
absent = umap[umap.station.isin(CG3_STATIONS) & ~umap.unit.isin(units_101)]
say("map units at CG1/CG3 stations with 0 rows in BM-101 (absent from the measurement):")
for _, r in absent.iterrows():
    say(f"   {r.unit} {r['name']} ({r.station})"
        + ("  [has BM-096 rows only]" if r.unit in units_096 else ""))

# ==============================================================================
# 6. Filter and group table
# ==============================================================================
say("=" * 78)
say(f"§6.6  Filter avail_MWh > {MIN_AVAIL_MWH} and h_locl > 0")
tab["passes_filter"] = (tab.avail_MWh > MIN_AVAIL_MWH) & (tab.h_locl > 0)
say(f"units passing: {int(tab.passes_filter.sum())} of {len(tab)}; excluded: "
    + "; ".join(f"{r.unit} {r['name']} (avail {r.avail_MWh:.1f} MWh, h_locl {r.h_locl})"
                for _, r in tab[~tab.passes_filter].iterrows()))
sel = tab[tab.passes_filter].copy()


def group_stats(df: pd.DataFrame, group: str, level: str) -> dict:
    if level == "unit":
        r = df.constraint_only_ratio.to_numpy()
        names = df.unit.tolist()
    else:
        st = df.groupby("station").agg(dd_c=("dd_constraint_only_MWh", "sum"),
                                       avail=("avail_MWh", "sum"))
        r = (st.dd_c / st.avail).to_numpy()
        names = st.index.tolist()
    r = np.asarray(r, float)
    i_min, i_max = int(np.argmin(r)), int(np.argmax(r))
    return {"group": group, "level": level, "N": len(r),
            "min": r.min(), "max": r.max(),
            "max_over_min": r.max() / r.min() if r.min() > 0 else np.inf,
            "jain": jain(r), "gini": gini(r),
            "min_member": names[i_min], "max_member": names[i_max],
            "members": ";".join(names)}


sel["dd_constraint_only_MWh"] = sel.constraint_only_ratio * sel.avail_MWh
groups = {"CG1": sel[sel.in_CG1], "CG3": sel[sel.in_CG3],
          "Booltiagh": sel[sel.in_Booltiagh], "all_filtered": sel}
grows = []
for gname, gdf in groups.items():
    for level in ("unit", "station"):
        grows.append(group_stats(gdf, gname, level))
gtab = pd.DataFrame(grows)
say("group table (constraint_only_ratio; station = Σdd_constraint_only / Σavail):")
say(gtab.drop(columns="members").to_string(index=False, float_format=lambda x: f"{x:.6f}"))
say("station-level members and ratios:")
for gname, gdf in groups.items():
    st = gdf.groupby("station").agg(dd_c=("dd_constraint_only_MWh", "sum"),
                                    avail=("avail_MWh", "sum"), n=("unit", "size")).astype({"n": int})
    st["r_s"] = st.dd_c / st.avail
    say(f"  [{gname}] " + "; ".join(f"{s}: {row.r_s:.6f} (n={int(row.n)})" for s, row in st.iterrows()))

# ==============================================================================
# 7. Co-instruction batches
# ==============================================================================
say("=" * 78)
say("§6.7  LOCL co-instruction batches (same InstrIssueTime to the second)")
locl = wind[wind.InstructionCombinationCode.eq("LOCL")].copy()
locl = locl.merge(umap[["unit", "station"]].rename(columns={"unit": "ResourceName"}),
                  on="ResourceName", how="left")
locl["station_f"] = locl.station.fillna("UNMAPPED:" + locl.ResourceName)
locl["is_cg3"] = locl.station.isin(CG3_STATIONS)
locl["is_cg1"] = locl.station.isin(CG1_STATIONS)
b = locl.groupby("InstrIssueTime").agg(
    n_units=("ResourceName", "size"),
    n_cg3=("is_cg3", "sum"),
    n_cg1=("is_cg1", "sum"),
    all_cg3=("is_cg3", "all"),
    all_cg1=("is_cg1", "all"),
    stations=("station_f", lambda s: "+".join(sorted(set(s)))),
    units=("ResourceName", lambda s: ";".join(sorted(s))),
)
say(f"LOCL rows {len(locl)}, of which at CG3 stations {int(locl.is_cg3.sum())}; "
    f"LOCL rows with no station in the IE map (NI or unmapped units): {int(locl.station.isna().sum())}")
say(f"batches (distinct InstrIssueTime): {len(b)}; batches with >= 2 units: {int((b.n_units >= 2).sum())}")
say(f"batches containing any CG3 unit: {int((b.n_cg3 > 0).sum())}; "
    f"batches whose units are ALL at CG3 stations: {int(b.all_cg3.sum())}; "
    f"of those, ALL at CG1 stations: {int((b.all_cg3 & b.all_cg1).sum())}")
say(f"all-CG3 batches with >= 2 units: {int((b.all_cg3 & (b.n_units >= 2)).sum())}; "
    f"single-unit all-CG3 batches: {int((b.all_cg3 & (b.n_units == 1)).sum())}")
say(f"batches mixing CG3 and non-CG3 units: {int(((b.n_cg3 > 0) & ~b.all_cg3).sum())}")
comp = (b[b.all_cg3].groupby("stations")
        .agg(batches=("n_units", "size"), units_per_batch_min=("n_units", "min"),
             units_per_batch_max=("n_units", "max"), example_units=("units", "first"))
        .sort_values("batches", ascending=False).reset_index())
comp["all_CG1"] = comp.stations.map(lambda s: set(s.split("+")) <= CG1_STATIONS)
say("10 most frequent station compositions among all-CG3 batches:")
say(comp.head(10).drop(columns="example_units").to_string(index=False))
mixed = b[(b.n_cg3 > 0) & ~b.all_cg3]
n_mixed_unmapped = int(mixed.stations.str.contains("UNMAPPED").sum())
say(f"of the {len(mixed)} mixed batches, {n_mixed_unmapped} include an unmapped (NI or non-CLAF) unit "
    f"and {len(mixed) - n_mixed_unmapped} mix CG3 with other mapped IE stations")
comp_all = (b.groupby("stations").agg(batches=("n_units", "size"), units_per_batch=("n_units", "max"),
                                      all_cg3=("all_cg3", "first"), all_cg1=("all_cg1", "first"))
            .sort_values("batches", ascending=False).reset_index())
say("for context, the 10 most frequent compositions among ALL LOCL batches (any station):")
say(comp_all.head(10).to_string(index=False))
# batches by size among all-CG3 batches
say("all-CG3 batches by number of units: "
    + ", ".join(f"{k}={v}" for k, v in b[b.all_cg3].n_units.value_counts().sort_index().items()))

# ==============================================================================
# 8. Outputs
# ==============================================================================
say("=" * 78)
say("§6.8  Outputs")
unit_cols = ["unit", "name", "tso_id", "station", "group", "in_CG1", "in_CG3", "in_Booltiagh",
             "avail_MWh", "dd_MWh", "dd_ratio", "constraint_only_ratio", "locl_any_ratio",
             "curl_only_ratio", "h_locl", "h_curl", "halfhours", "hh_constraint_only", "hh_both",
             "passes_filter"]
tab_out = tab[unit_cols].merge(init, on="unit", how="left")
tab_out = tab_out.sort_values("constraint_only_ratio", ascending=False)
tab_out.to_csv(OUT / "measurement_units.csv", index=False)
gtab.to_csv(OUT / "measurement_groups.csv", index=False)
comp_out = comp.copy()
comp_out.insert(0, "rank", np.arange(1, len(comp_out) + 1))
comp_out.to_csv(OUT / "measurement_batches.csv", index=False)
cmp.to_csv(OUT / "measurement_reproduction_check.csv", index=False)

# chart: constraint-only ratio per unit, coloured by group
try:
    from kit import plotstyle
    plotstyle.use()
    PAL = plotstyle.CATEGORICAL
    INK = plotstyle.INK_SOFT
except Exception as e:  # noqa: BLE001
    say(f"plotstyle not usable ({e}); matplotlib defaults")
    PAL = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
    INK = "#52514e"
colour = {"CG1": PAL[0], "CG3-only": PAL[1], "Booltiagh": PAL[2], "other": PAL[3]}
plot_df = tab_out[tab_out.passes_filter].sort_values("constraint_only_ratio")
fig, ax = plt.subplots(figsize=(9, 0.34 * len(plot_df) + 1.8))
y = np.arange(len(plot_df))
ax.barh(y, 100 * plot_df.constraint_only_ratio,
        color=[colour[g] for g in plot_df.group], height=0.72)
ax.set_yticks(y)
ax.set_yticklabels([f"{n} ({s})" for n, s in zip(plot_df.name, plot_df.station)], fontsize=8)
ax.set_xlabel("constraint-only dispatch-down, % of available energy")
ax.set_title("Constraint-only ratio by WDT group, 2026-06-08 to 09-05", loc="left", fontsize=11)
for yi, v in zip(y, plot_df.constraint_only_ratio):
    ax.text(100 * v + 0.1, yi, f"{100 * v:.1f}", va="center", fontsize=7, color=INK)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=colour[g], label=lab) for g, lab in
                   [("CG1", "CG1 (also in CG3)"), ("CG3-only", "CG3 only"),
                    ("Booltiagh", "Booltiagh (same-shift-factor example)"), ("other", "neither")]],
          loc="lower right", fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(0, 100 * plot_df.constraint_only_ratio.max() * 1.15)
fig.tight_layout()
fig.savefig(OUT / "measurement_bars.png", dpi=150)
plt.close(fig)
say("written: " + ", ".join(str(OUT / f) for f in
    ["measurement_units.csv", "measurement_groups.csv", "measurement_batches.csv",
     "measurement_bars.png", "measurement_reproduction_check.csv"]))

# ==============================================================================
# Notes
# ==============================================================================
caveats = [
    "90 days, one summer (2026-06-08 to 2026-09-05); no seasonal coverage.",
    "Group membership is inferred from station names in semo_unit_map_IE.csv and the Feb 2024 WDT "
    "Constraint Group Overview; groups may have changed since (Tievebrack receives LOCL but is in "
    "neither CG1 nor CG3 in the document).",
    "The LOCL/CURL state machine cannot tell which constraint group fired; a unit at a CG1 station "
    "may be constrained by CG1, CG3 or an outage variant.",
    "constraint-only is a lower bound: half-hours that are under both a LOCL and a CURL instruction "
    "are excluded from the numerator, and the state machine misses spells that began before "
    "2026-06-07 (a unit whose first instruction is a release would be under-counted; the count of such units is in the run log).",
    "Rebalancing (live since 26 Nov 2025) is in force for the whole window, so the measured spread "
    "is the with-rebalancing regime.",
    "Availability (BM-101) is the TSO's outturn availability estimate; dd = max(0, avail − dispatch "
    "quantity) treats every shortfall of dispatch quantity below availability as dispatch-down.",
    "Units with 0 rows in BM-101 are absent (listed in the run log); ARDNAGAPPARY, MOY and SLIGO have no "
    "unit in the IE map, so CG3 is measured on the stations that do.",
]

notes = ["# MEASUREMENT_NOTES — MASTER §6, run of src/measurement.py", "",
         "Every number below is printed by `src/measurement.py`; the file is the log of one run.", "",
         "## Method", "",
         "1. Inner join BM-101 (AvgOutturnAvail, MW average over the half hour) and BM-096 "
         "(DispatchQuantity, MWh per half hour) on (ResourceName, StartTime); "
         "`avail_MWh = 0.5 × AvgOutturnAvail`, `dd_MWh = max(0, avail_MWh − DispatchQuantity)`.",
         "2. State machine per unit from BM-037 WIND rows sorted by EffTime (ties by InstrIssueTime): "
         "LOCL → constraint=True, LCLO → False; CURL → curtail=True, CRLO → False. State False for all "
         f"units at {STATE_INIT_TIME}; rows with EffTime before that (stray 2020-04 rows) dropped. "
         "A half-hour is under a state if the state at its StartTime is True (convention chosen by the "
         "reproduction check below).",
         "3. Per unit: avail, dd, dd_ratio, constraint_only_ratio (dd in half-hours constrained and not "
         "curtailed ÷ avail over all half-hours), locl_any_ratio, curl_only_ratio, h_locl, h_curl.",
         "4. Reproduction against data/nw_unit_dispatchdown_2026-06-08_to_09-05.csv.",
         "5. Stations from semo_unit_map_IE.csv; CG1 = {" + ", ".join(sorted(CG1_STATIONS)) + "}; CG3 = CG1 ∪ {"
         + ", ".join(sorted(CG3_EXTRA)) + "} (map spellings).",
         f"6. Filter avail > {MIN_AVAIL_MWH:.0f} MWh and h_locl > 0; N, min, max, max/min, Jain, Gini on "
         "constraint_only_ratio at unit and station level; Jain = (Σr)²/(N Σr²); Gini = Σ(2i−N−1) r_i / (N Σ r_i) "
         "on the ascending sort, unweighted, no small-sample correction.",
         "7. LOCL batches = rows sharing InstrIssueTime to the second; a batch is 'all-CG3' if every unit "
         "in it maps to a CG3 station (NI / unmapped units count as non-CG3).", "",
         "## Headline numbers (from this run)", "",
         f"- Reproduction of the earlier CSV: {'PASS' if repro_ok else 'FAIL'}; convention EffTime "
         f"{'<=' if use_inclusive else '<'} StartTime; max abs diff on ratio/hour columns "
         f"{cmp.set_index('column').loc[ratio_cols, 'max_abs_diff'].max():.3g}; avail_MWh/dd_MWh differ by at most "
         f"{cmp.set_index('column').loc['avail_MWh', 'max_abs_diff']:.4f} / "
         f"{cmp.set_index('column').loc['dd_MWh', 'max_abs_diff']:.4f} MWh because the earlier file stored them "
         f"rounded to integers (difference after rounding: "
         f"{cmp.set_index('column').loc['avail_MWh', 'max_abs_diff_after_rounding_new_to_int']:.0f}).",
         f"- State machine: False at {STATE_INIT_TIME}; units under LOCL at window start {window_start}: "
         f"{n_c_start}; under CURL: {n_k_start}; units whose first LOCL/LCLO instruction is a release: "
         f"{n_c_release_first}; first CURL/CRLO a release: {n_k_release_first}.",
         f"- Units with 0 rows in BM-101 (absent): {sorted(units_096 - units_101)} (BM-096 only); see the run log "
         f"for map units at CG1/CG3 stations with no BM-101 rows.",
         f"- Filter avail > {MIN_AVAIL_MWH:.0f} MWh and h_locl > 0 keeps {int(tab.passes_filter.sum())} of {len(tab)} units.",
         "", "Group table (constraint_only_ratio):", "",
         "| group | level | N | min | max | max/min | Jain | Gini | min member | max member |",
         "|---|---|---|---|---|---|---|---|---|---|"]
notes += [f"| {r.group} | {r.level} | {r.N} | {r['min']:.6f} | {r['max']:.6f} | {r.max_over_min:.4f} | "
         f"{r.jain:.4f} | {r.gini:.4f} | {r.min_member} | {r.max_member} |" for _, r in gtab.iterrows()]
notes += ["", f"LOCL batches: {len(b)} distinct InstrIssueTime; all-CG3 batches {int(b.all_cg3.sum())} "
         f"(of which >= 2 units {int((b.all_cg3 & (b.n_units >= 2)).sum())}, all-CG1 {int((b.all_cg3 & b.all_cg1).sum())}); "
         f"batches mixing CG3 and non-CG3 units {int(((b.n_cg3 > 0) & ~b.all_cg3).sum())}.", "",
         "Top-10 all-CG3 station compositions:", "",
         "| rank | stations | batches | units/batch |", "|---|---|---|---|"]
notes += [f"| {i + 1} | {r.stations} | {r.batches} | {r.units_per_batch_min}"
         f"{'' if r.units_per_batch_min == r.units_per_batch_max else '-' + str(r.units_per_batch_max)} |"
         for i, r in comp.head(10).reset_index(drop=True).iterrows()]
notes += ["", "## Caveats", ""] + [f"- {c}" for c in caveats] + ["", "## Run log", "", "```"] + LINES + ["```", ""]
(OUT / "MEASUREMENT_NOTES.md").write_text("\n".join(notes))

decisions = [
    f"[measurement] BM-037 rows with EffTime before 2026-06-07 00:00 ({n_stray} stray 2020-04 rows) are dropped before the state machine; state is False for every unit at 2026-06-07 00:00.",
    f"[measurement] A half-hour is 'under' a state if the state after all instructions with EffTime {'<=' if use_inclusive else '<'} StartTime is True (the convention that reproduces the earlier CSV; the two conventions differ only when an EffTime equals a StartTime to the second).",
    "[measurement] Instructions with equal EffTime for one unit are ordered by InstrIssueTime (stable sort).",
    "[measurement] Units with rows in BM-096 but none in BM-101 (GU_401190) are dropped: no availability, no ratio.",
    "[measurement] Group station names use the map spellings: Cathaleen's Fall = CATH_FALL. ARDNAGAPPARY, MOY, SLIGO have no unit in semo_unit_map_IE.csv and so contribute no measured unit.",
    "[measurement] Station-level ratio for the group table = Σ(constraint-only dd) / Σ(avail) over the station's filtered units (MASTER §6.6 'Σdd/Σavail' read as the constraint-only numerator, consistent with the unit-level metric).",
    "[measurement] Batch 'station composition' = the sorted set of distinct stations in the batch; batches of one unit are counted as batches. Unmapped (NI) units make a batch non-CG3.",
    "[measurement] Chart uses kit/plotstyle CATEGORICAL colours; only units passing the §6.6 filter are drawn.",
    "[measurement] An extra file out/measurement_reproduction_check.csv holds the per-column max-abs-diff table.",
]
dl = OUT / "DECISIONS_LOG.md"
existing = dl.read_text() if dl.exists() else "# DECISIONS_LOG\n\n"
existing = "\n".join(l for l in existing.splitlines() if not l.startswith("[measurement]")).rstrip("\n") + "\n"
dl.write_text(existing + "\n".join(decisions) + "\n")
say("notes and decisions written")
