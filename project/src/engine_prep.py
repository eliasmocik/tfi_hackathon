"""MASTER.md §2 (group definition, classification) and §3 (network preparation,
baseline dispatch, PTDF/LODF/shift factors, overload series).

Public functions
    prepare(case)            -> (network, rating Series, info dict)
    classify_group(case, n)  -> DataFrame (also written to out/<case>_group_units.csv)
    run_baseline(case)       -> dict of sanity numbers (writes the three parquet files)
    compute_ptdf_lodf(case)  -> dict (writes shift_factors.csv, node table, lodf csv)
    overload_series(case)    -> dict (writes out/<case>_overloads.csv)

Every number that ends up in ENGINE_NOTES.md is printed by this code.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import sys
import time
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, "kit")
OUT = os.path.join(ROOT, "out")
YEARS = os.path.join(ROOT, "years")
DATA = os.path.join(ROOT, "data")
if KIT not in sys.path:
    sys.path.insert(0, KIT)

warnings.filterwarnings("ignore")
import logging  # noqa: E402

for _name in ("pypsa", "linopy", "pypsa.consistency", "pypsa.optimization", "pypsa.io"):
    logging.getLogger(_name).setLevel(logging.ERROR)

import pypsa  # noqa: E402
import flowmath  # noqa: E402
import gridkit  # noqa: E402

# --------------------------------------------------------------------------- #
# Fixed decisions (MASTER §0, §1)
# --------------------------------------------------------------------------- #
CASES = {
    "WP2024s42": dict(network="WP2024_all-island_windin.nc",
                      year="TYTFS2024_WP2024_V35_synthetic_2030_seed42_",
                      sites="TYTFS2024_WP2024_V35_synthetic_2030_seed42_sites.csv",
                      step=1),
    "WP2033s42": dict(network="WP2033_all-island.nc",
                      year="TYTFS2024_WP2033_V35_synthetic_2030_seed42_",
                      sites="TYTFS2024_WP2033_V35_synthetic_2030_seed43_sites.csv",
                      step=2),
    "WP2033s43": dict(network="WP2033_all-island.nc",
                      year="TYTFS2024_WP2033_V35_synthetic_2030_seed43_",
                      sites="TYTFS2024_WP2033_V35_synthetic_2030_seed43_sites.csv",
                      step=2),
}
TIE_LINE = "3581-89516-1"
TIE_LINK = "LKY-STRABANE-PST"
CONTINGENCY = "2522-5042-1"
MONITORED = {  # row label -> (element, post-contingency?)
    "FLG_SLIGO_N1": ("2521-4981-1", True),
    "T25221_N1": ("T2522-2521-25221-1-w1", True),
    "T25222_N1": ("T2522-2521-25222-2-w1", True),
    "FLG_SLIGO_N0": ("2521-4981-1", False),
}
CHUNK = 168
SF_FLOOR = 0.02

# WDT §3.3 stations -> model psse_name(s) (MASTER §2)
STATION_BUSNAMES = {
    "Ardnagappary": ["ARDNAGAPPARY"], "Binbane": ["BINBANE"],
    "Cathaleen's Fall": ["CATH_FALL", "CATH FALL"], "Corderry": ["CORDERRY"],
    "Cunghill": ["CUNGHILL"], "Garvagh": ["GARVAGH"], "Glenree": ["GLENREE"],
    "Lenalea": ["LENALEA"], "Meentycat": ["MEENTYCAT"], "Moy": ["MOY"],
    "Mulreavy": ["MULREAVY"], "Sligo": ["SLIGO"], "Sorne Hill": ["SORNE HILL"],
    "Tawnaghmore": ["TAWNAGHMORE"], "Trillick": ["TRILLICK"],
}
EXPECTED_BUS = {  # WP2024 wind-in bus numbers from MASTER §2, for the re-match report
    "ARDNAGAPPARY": "1571", "BINBANE": "1341", "CATH_FALL": "1701", "CATH FALL": "17010",
    "CORDERRY": "1631", "CUNGHILL": "1931", "GARVAGH": "2671", "GLENREE": "4371",
    "LENALEA": "3591", "MEENTYCAT": "4071", "MOY": "4041", "MULREAVY": "4091",
    "SLIGO": "4981", "SORNE HILL": "4991", "TAWNAGHMORE": "5241", "TRILLICK": "5361",
}
NW_KEYS = ["ARDNAGAPPARY", "BINBANE", "CATH_FALL", "CATH FALL", "CORDERRY", "CUNGHILL",
           "GARVAGH", "GLENREE", "LENALEA", "MEENTYCAT", "MOY", "MULREAVY", "SLIGO",
           "SORNE HILL", "TAWNAGHMORE", "TRILLICK", "FLAGFORD", "SRANANAGH", "LETTERKENNY",
           "CLOGHER", "DRUMKEEN", "CROAGHONAGH", "TIEVEBRACK"]


def log(*a):
    print(*a, flush=True)


def decision(text: str):
    """Append an unspecified decision to out/DECISIONS_LOG.md (MASTER preamble)."""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "DECISIONS_LOG.md")
    line = f"[engine] {text}"
    if os.path.exists(path):
        with open(path) as f:
            if line in f.read():
                return
    with open(path, "a") as f:
        f.write(line + "\n")
    log("DECISION:", text)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_network(case: str):
    c = CASES[case]
    n = pypsa.Network(os.path.join(KIT, c["network"]))
    n.meta = {"case": case}
    return n


def load_year(case: str):
    c = CASES[case]
    pmax = pd.read_csv(os.path.join(YEARS, c["year"] + "p_max_pu.csv"), index_col=0, parse_dates=True)
    load = pd.read_csv(os.path.join(YEARS, c["year"] + "loads_p_set.csv"), index_col=0, parse_dates=True)
    pmax.index = pd.DatetimeIndex(pmax.index.astype("datetime64[ns]"), name="snapshot")
    load.index = pd.DatetimeIndex(load.index.astype("datetime64[ns]"), name="snapshot")
    assert pmax.index.equals(load.index), "year files disagree on the index"
    assert len(pmax) == 8760, len(pmax)
    return pmax, load


def snapshots_for(case: str, index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    step = CASES[case]["step"]
    return index[::step]


def cg3_buses(n) -> pd.DataFrame:
    """Bus -> station for the CG3 stations, matched on buses.psse_name (§2)."""
    rows = []
    names = n.buses["psse_name"].astype(str).str.strip()
    for station, psse in STATION_BUSNAMES.items():
        for p in psse:
            hit = names.index[names == p]
            if len(hit) == 0:
                raise KeyError(f"no bus with psse_name {p!r} for station {station}")
            for b in hit:
                rows.append(dict(bus=str(b), psse_name=p, station=station,
                                 expected_bus=EXPECTED_BUS[p], bus_differs=str(b) != EXPECTED_BUS[p]))
    return pd.DataFrame(rows).set_index("bus")


# --------------------------------------------------------------------------- #
# §2.1 classification
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    s = str(s).upper()
    s = re.sub(r"^W_|^S_", "", s)
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return s.strip()


def _name_score(gen_name: str, row_name: str) -> float:
    a, b = _norm(gen_name), _norm(row_name)
    if not a:
        return 0.0
    # token prefix overlap, then sequence ratio
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    toks_a = [t for t in a.split() if len(t) >= 4]
    bonus = sum(1 for t in toks_a if t in b or any(w.startswith(t[:6]) for w in b.split())) * 0.25
    return ratio + bonus


def classify_group(case: str, n=None) -> pd.DataFrame:
    """§2.1: match generators at CG3 buses to eirgrid_gss1_res_units.csv."""
    if n is None:
        n = load_network(case)
    buses = cg3_buses(n)
    g = n.generators
    gg = g[g.bus.astype(str).isin(buses.index) & g.carrier.isin(["wind", "solar"])].copy()
    gg["bus"] = gg["bus"].astype(str)
    # psse_bus_name: the wind-in network carries none for the switched-in records -> take from sites.csv
    sites = pd.read_csv(os.path.join(YEARS, CASES[case]["sites"])).set_index("generator")
    pname = gg["psse_bus_name"].astype(str).replace("nan", "")
    missing = pname.str.strip() == ""
    if missing.any():
        fill = sites["psse_bus_name"].reindex(gg.index[missing]).fillna("")
        pname.loc[missing] = fill.values
        decision(f"{case}: psse_bus_name empty in the network for {int(missing.sum())} CG3 generators; "
                 f"taken from years/{CASES[case]['sites']} ({int((fill != '').sum())} filled).")
    gg["psse_bus_name"] = pname

    res = pd.read_csv(os.path.join(DATA, "eirgrid_gss1_res_units.csv"))
    res["node_l"] = res["node"].astype(str).str.strip().str.lower()
    res["prio_l"] = res["priority"].astype(str).str.strip().str.lower()
    res["gt_l"] = res["gen_type"].astype(str).str.strip().str.lower()

    decision("§2.1 matching: candidate rows of eirgrid_gss1_res_units.csv are restricted to gen_type containing the "
             "generator's carrier (wind/solar); battery rows are never matched (e.g. Killala Battery Phase 2, 10.8 MW at "
             "Tawnaghmore, has the same mec as model unit 67059-2 which the network carries as wind). Priority strings are "
             "read by substring: 'uncontrolled' -> U, 'not priority' -> N, otherwise 'priority' -> P.")
    decision("§2.1 unmatched units stay class P as specified even where an aggregate or near match exists "
             "(e.g. 68269-1 20.0 MW = Clogheravaddy Ph1+Ph2 9.2+10.8, both 'wind not priority'; 35971-1 Lenalea 30.5 MW vs "
             "30.1 MW 'not priority'; 15771-1+15772-1 Cronalaght 1.98+3.0 = Cronalaght (1) 4.98 'uncontrolled'). These are "
             "listed per case in ENGINE_NOTES for the RESULTS caveat.")
    rows = []
    for gen, r in gg.iterrows():
        station = buses.at[r.bus, "station"]
        cand = res[(res.node_l == station.lower()) & res.gt_l.str.contains(r.carrier)
                   & ((res.mec_mw - r.p_nom).abs() <= 0.05 + 1e-9)]
        if len(cand) == 0:
            cls, mname, mmec, status = "P", "", np.nan, "unmatched"
        else:
            if len(cand) > 1:
                scores = cand["name"].map(lambda s: _name_score(r.psse_bus_name, s))
                best = cand.loc[scores.idxmax()]
                status = "matched_multi"
            else:
                best = cand.iloc[0]
                status = "matched"
            p = best.prio_l
            if "uncontrolled" in p:
                cls = "U"
            elif "not priority" in p:
                cls = "N"
            elif "priority" in p:
                cls = "P"
            else:
                cls, status = "P", "matched_unknown_priority"
            mname, mmec = best["name"], float(best.mec_mw)
        rows.append(dict(generator=gen, bus=r.bus, station=station, carrier=r.carrier, p_nom=float(r.p_nom),
                         psse_bus_name=r.psse_bus_name, **{"class": cls}, matched_name=mname,
                         matched_mec=mmec, match_status=status))
    out = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    out.to_csv(os.path.join(OUT, f"{case}_group_units.csv"), index=False)
    inG = out["class"] != "U"
    stats = dict(n_units=len(out), n_matched=int(out.match_status.str.startswith("matched").sum()),
                 match_rate=float(out.match_status.str.startswith("matched").mean()),
                 mw_total=float(out.p_nom.sum()), mw_G=float(out.p_nom[inG].sum()),
                 mw_excluded_U=float(out.p_nom[~inG].sum()), n_G=int(inG.sum()), n_U=int((~inG).sum()),
                 n_P=int((out["class"] == "P").sum()), n_N=int((out["class"] == "N").sum()),
                 mw_P=float(out.p_nom[out["class"] == "P"].sum()), mw_N=float(out.p_nom[out["class"] == "N"].sum()),
                 n_unmatched=int((out.match_status == "unmatched").sum()),
                 n_multi=int((out.match_status == "matched_multi").sum()))
    log(f"[{case}] group_units: {json.dumps(stats)}")
    diff = buses[buses.bus_differs]
    log(f"[{case}] CG3 buses whose number differs from MASTER §2: {diff.index.tolist() if len(diff) else 'none'}")
    with open(os.path.join(OUT, f"{case}_group_stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    return out


# --------------------------------------------------------------------------- #
# §3.1 prepare
# --------------------------------------------------------------------------- #
def _great_circle(x0, y0, x1, y1):
    d = np.pi / 180.0
    dlat = (y1 - y0) * d
    dlon = (x1 - x0) * d
    h = np.sin(dlat / 2) ** 2 + np.cos(y0 * d) * np.cos(y1 * d) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def prepare(case: str, with_year: bool = True):
    """§3.1 steps 1-7. Returns (n, rating, info)."""
    n = load_network(case)
    info = {"case": case}
    # 1. tie replacement
    r = float(n.lines.at[TIE_LINE, "s_nom"])
    n.remove("Line", TIE_LINE)
    n.add("Link", TIE_LINK, bus0="3581", bus1="89516", p_nom=r, p_min_pu=-1, efficiency=1.0, marginal_cost=0)
    info["tie_p_nom"] = r
    log(f"[{case}] tie {TIE_LINE} -> Link {TIE_LINK} p_nom {r}")

    if with_year:
        pmax, load = load_year(case)
        snaps = snapshots_for(case, pmax.index)
        # 2. snapshots
        n.set_snapshots(snaps)
        info["n_snapshots"] = len(snaps)
        g = n.generators
        # 3. p_max_pu
        have = [c for c in pmax.columns if c in g.index]
        gp = pmax.loc[snaps, have].copy()
        info["year_cols_matching"] = len(have)
        info["year_cols_total"] = pmax.shape[1]
        ws = g.index[g.carrier.isin(["wind", "solar"])]
        no_col = [c for c in ws if c not in have]
        placed = gridkit.placed_buses(n)
        borrow_rows = []
        for gen in no_col:
            carrier = g.at[gen, "carrier"]
            bus = str(g.at[gen, "bus"])
            donors = [d for d in have if g.at[d, "carrier"] == carrier]
            same_bus = [d for d in donors if str(g.at[d, "bus"]) == bus]
            if same_bus:
                donor, how, dist = same_bus[0], "same_bus", 0.0
            else:
                if bus in placed.index:
                    x0, y0 = float(placed.at[bus, "x"]), float(placed.at[bus, "y"])
                    dbus = g.loc[donors, "bus"].astype(str)
                    ok = dbus.isin(placed.index)
                    dd = pd.Series({d: _great_circle(x0, y0, float(placed.at[b, "x"]), float(placed.at[b, "y"]))
                                    for d, b in dbus[ok].items()})
                    donor = dd.idxmin(); dist = float(dd.min()); how = "nearest_km"
                else:
                    # bus without coordinates: nearest cannot be defined; use the largest same-carrier donor
                    donor = g.loc[donors, "p_nom"].idxmax(); dist = np.nan; how = "unplaced_bus_largest_donor"
            gp[gen] = pmax.loc[snaps, donor].to_numpy()
            borrow_rows.append(dict(generator=gen, bus=bus, psse_name=str(n.buses.at[bus, "psse_name"]) if bus in n.buses.index else "",
                                    carrier=carrier, p_nom=float(g.at[gen, "p_nom"]), donor=donor,
                                    donor_bus=str(g.at[donor, "bus"]), method=how, distance_km=dist))
        borrow = pd.DataFrame(borrow_rows)
        os.makedirs(OUT, exist_ok=True)
        borrow.to_csv(os.path.join(OUT, f"{case}_profile_borrowing.csv"), index=False)
        if len(borrow) and (borrow.method == "unplaced_bus_largest_donor").any():
            decision(f"{case}: {(borrow.method == 'unplaced_bus_largest_donor').sum()} wind/solar generators "
                     "without a year column sit at a bus without coordinates; they borrow the largest same-carrier "
                     "generator's profile because 'nearest' is undefined (see profile_borrowing.csv).")
        info["borrowed"] = len(borrow)
        info["borrowed_mw"] = float(borrow.p_nom.sum()) if len(borrow) else 0.0
        info["borrowed_same_bus"] = int((borrow.method == "same_bus").sum()) if len(borrow) else 0
        log(f"[{case}] year columns matching {len(have)}/{pmax.shape[1]}; wind/solar without column: {len(no_col)} "
            f"({info['borrowed_mw']:.1f} MW) borrowed, {info['borrowed_same_bus']} from the same bus")
        thermal_no_col = [c for c in g.index if c not in have and c not in ws and g.at[c, "carrier"] != "load shedding"]
        info["thermal_without_column"] = len(thermal_no_col)
        log(f"[{case}] non-renewable generators without a column (keep p_max_pu=1): {len(thermal_no_col)}")
        n.generators_t.p_max_pu = gp
        # 4. loads
        missing_loads = [c for c in n.loads.index if c not in load.columns]
        assert not missing_loads, f"loads without a year column: {missing_loads}"
        n.loads_t.p_set = load.loc[snaps, n.loads.index]
        # 5. p_min_pu clip
        pm = g.index[(g.p_min_pu > 0) & g.index.isin(have)]
        n.generators_t.p_min_pu = pd.DataFrame(
            {c: np.minimum(float(g.at[c, "p_min_pu"]), gp[c].to_numpy()) for c in pm}, index=snaps)
        info["p_min_pu_clipped"] = len(pm)
        log(f"[{case}] p_min_pu clipped for {len(pm)} generators")
    # 6. renewable bids
    g = n.generators
    names = sorted(g.index[g.carrier.isin(["wind", "solar"])])
    N = len(names)
    for i, nm in enumerate(names):
        g.at[nm, "marginal_cost"] = -1.0 - 1e-4 * i / N
    # 7. lift ratings: keep the originals; lift via s_max_pu so transformer impedances are untouched
    rating = pd.concat([n.lines["s_nom"], n.transformers["s_nom"]]).astype(float)
    rating.name = "rating"
    n.lines["s_max_pu"] = 100.0
    n.transformers["s_max_pu"] = 100.0
    decision("§3.1 step 7 implemented as s_max_pu = 100 on every line and transformer instead of s_nom x 100: "
             "in PyPSA a transformer's x is per-unit on its own s_nom (x_pu = x / s_nom), so scaling s_nom would "
             "divide every transformer impedance by 100 inside the LOPF and make the solved flows inconsistent "
             "with the PTDF. The effective limit is the same (100 x rating); `rating` holds the unchanged s_nom.")
    info["n_lines"] = len(n.lines); info["n_transformers"] = len(n.transformers)
    return n, rating, info


# --------------------------------------------------------------------------- #
# §3.2 solve
# --------------------------------------------------------------------------- #
def run_baseline(case: str, resume: bool = True) -> dict:
    t0 = time.time()
    n, rating, info = prepare(case)
    units = classify_group(case, n)
    G = units.loc[units["class"] != "U", "generator"].tolist()
    snaps = n.snapshots
    ckdir = os.path.join(OUT, f"_chunks_{case}")
    os.makedirs(ckdir, exist_ok=True)
    nchunks = (len(snaps) + CHUNK - 1) // CHUNK
    statuses = []
    for k in range(nchunks):
        sub = snaps[k * CHUNK:(k + 1) * CHUNK]
        fp = os.path.join(ckdir, f"p_{k:03d}.parquet")
        ff = os.path.join(ckdir, f"f_{k:03d}.parquet")
        fs = os.path.join(ckdir, f"s_{k:03d}.json")
        if resume and os.path.exists(fp) and os.path.exists(ff) and os.path.exists(fs):
            with open(fs) as f:
                statuses.append(json.load(f))
            continue
        status, cond = n.optimize(sub, solver_name="highs", assign_all_duals=False, log_fn=None,
                                  solver_options={"output_flag": False}, progress=False)
        st = dict(chunk=k, start=str(sub[0]), end=str(sub[-1]), n=len(sub), status=str(status), condition=str(cond),
                  objective=float(n.objective) if hasattr(n, "objective") else np.nan)
        assert status == "ok" and cond == "optimal", f"chunk {k} not optimal: {status} {cond}"
        p = n.generators_t.p.loc[sub]
        f = pd.concat([n.lines_t.p0.loc[sub], n.transformers_t.p0.loc[sub], n.links_t.p0.loc[sub]], axis=1)
        p.to_parquet(fp); f.to_parquet(ff)
        with open(fs, "w") as fh:
            json.dump(st, fh)
        statuses.append(st)
        log(f"[{case}] chunk {k + 1}/{nchunks} {st['condition']} obj {st['objective']:.1f} {time.time() - t0:.0f}s")
    P = pd.concat([pd.read_parquet(os.path.join(ckdir, f"p_{k:03d}.parquet")) for k in range(nchunks)])
    F = pd.concat([pd.read_parquet(os.path.join(ckdir, f"f_{k:03d}.parquet")) for k in range(nchunks)])
    assert P.index.equals(snaps) and F.index.equals(snaps)
    stat = pd.DataFrame(statuses)
    stat.to_csv(os.path.join(OUT, f"{case}_chunk_status.csv"), index=False)
    all_opt = bool((stat.condition == "optimal").all() and (stat.status == "ok").all())
    log(f"[{case}] chunks: {len(stat)}, all optimal: {all_opt}")
    assert all_opt
    P.to_parquet(os.path.join(OUT, f"{case}_baseline_p.parquet"))
    F.to_parquet(os.path.join(OUT, f"{case}_flows.parquet"))
    g = n.generators
    avail = n.generators_t.p_max_pu[G] * g.loc[G, "p_nom"]
    avail.to_parquet(os.path.join(OUT, f"{case}_avail.parquet"))
    rating.to_csv(os.path.join(OUT, f"{case}_rating.csv"), header=True)
    # sanity
    ws = g.index[g.carrier.isin(["wind", "solar"])]
    wind = g.index[g.carrier == "wind"]
    av_all = n.generators_t.p_max_pu[ws] * g.loc[ws, "p_nom"]
    step = CASES[case]["step"]
    san = dict(case=case, hours=len(snaps), step=step, all_chunks_optimal=all_opt,
               wind_energy_MWh=float(P[wind].sum().sum() * step),
               wind_avail_MWh=float(av_all[wind].sum().sum() * step),
               ws_energy_MWh=float(P[ws].clip(lower=0).sum().sum() * step),
               ws_avail_MWh=float(av_all.sum().sum() * step))
    san["wind_surplus_share"] = 1.0 - san["wind_energy_MWh"] / san["wind_avail_MWh"]
    san["ws_surplus_share"] = 1.0 - san["ws_energy_MWh"] / san["ws_avail_MWh"]
    shed = g.index[g.carrier == "load shedding"]
    shed_h = P[shed].sum(axis=1)
    san["load_shedding_hours"] = int((shed_h > 1e-3).sum())
    san["load_shedding_MWh"] = float(shed_h.clip(lower=0).sum() * step)
    tie = F[TIE_LINK]
    san["tie_p_nom"] = info["tie_p_nom"]
    san["tie_at_cap_share"] = float((tie.abs() >= info["tie_p_nom"] - 1e-3).mean())
    san["tie_at_cap_hours"] = int((tie.abs() >= info["tie_p_nom"] - 1e-3).sum())
    san["tie_mean_flow_MW"] = float(tie.mean())
    san["G_energy_MWh"] = float(P[G].clip(lower=0).sum().sum() * step)
    san["G_avail_MWh"] = float(avail.sum().sum() * step)
    san["G_surplus_share"] = 1.0 - san["G_energy_MWh"] / san["G_avail_MWh"]
    san["solve_seconds"] = time.time() - t0
    san.update({k: v for k, v in info.items() if k != "case"})
    with open(os.path.join(OUT, f"{case}_baseline_sanity.json"), "w") as f:
        json.dump(san, f, indent=1)
    log(f"[{case}] sanity: {json.dumps(san)}")
    return san


# --------------------------------------------------------------------------- #
# §3.3 PTDF, LODF, shift factors
# --------------------------------------------------------------------------- #
def reference_bus(n, P: pd.DataFrame, elements) -> tuple[str, list]:
    g = n.generators
    gas = g[g.carrier == "gas"].sort_values("p_nom", ascending=False)
    tried = []
    for gen, r in gas.iterrows():
        bus = str(r.bus)
        vals = {e: float(P.at[e, bus]) for e in elements}
        ok = all(abs(v) < 0.02 for v in vals.values())
        tried.append(dict(generator=gen, bus=bus, psse_name=str(n.buses.at[bus, "psse_name"]), p_nom=float(r.p_nom),
                          accepted=ok, **{f"P_{e}": v for e, v in vals.items()}))
        if ok:
            return bus, tried
    raise RuntimeError("no gas bus satisfies |P[e,ref]| < 0.02")


def compute_ptdf_lodf(case: str, n=None) -> dict:
    if n is None:
        n, rating, info = prepare(case, with_year=False)
    units = pd.read_csv(os.path.join(OUT, f"{case}_group_units.csv")) if os.path.exists(
        os.path.join(OUT, f"{case}_group_units.csv")) else classify_group(case, n)
    br = flowmath.branches(n)
    P = flowmath.ptdf(n, br)
    k = CONTINGENCY
    elements = sorted({e for e, _ in MONITORED.values()})
    ref, tried = reference_bus(n, P, elements)
    ref_name = str(n.buses.at[ref, "psse_name"])
    pd.DataFrame(tried).to_csv(os.path.join(OUT, f"{case}_reference_bus.csv"), index=False)
    log(f"[{case}] reference bus {ref} ({ref_name}); |P[e,ref]|: " +
        ", ".join(f"{e}={abs(P.at[e, ref]):.5f}" for e in elements))
    # LODF
    b0k, b1k = br.at[k, "bus0"], br.at[k, "bus1"]
    denom = 1.0 - (P.at[k, b0k] - P.at[k, b1k])
    assert abs(denom) > 1e-6, denom
    lodf = {e: float((P.at[e, b0k] - P.at[e, b1k]) / denom) for e in elements}
    # PyPSA check: sub-network BODF
    n.determine_network_topology()
    n.calculate_dependent_values()
    sn_name = n.lines.at[k, "sub_network"]
    sn = n.sub_networks.at[sn_name, "obj"] if "obj" in n.sub_networks.columns else n.c.sub_networks.static.at[sn_name, "obj"]
    sn.calculate_BODF()
    sbr = sn.branches()
    kind = {e: ("Line" if e in n.lines.index else "Transformer") for e in elements}
    ki = sbr.index.get_loc(("Line", k))
    bodf = {e: float(sn.BODF[sbr.index.get_loc((kind[e], e)), ki]) for e in elements}
    lodf_rows = []
    for e in elements:
        lodf_rows.append(dict(element=e, contingency=k, lodf_kit=lodf[e], bodf_pypsa=bodf[e],
                              abs_diff=abs(lodf[e] - bodf[e]), agree_1e6=abs(lodf[e] - bodf[e]) < 1e-6,
                              denom=float(denom), P_e_ref=float(P.at[e, ref])))
    lodf_df = pd.DataFrame(lodf_rows)
    lodf_df.to_csv(os.path.join(OUT, f"{case}_lodf.csv"), index=False)
    log(f"[{case}] LODF check:\n{lodf_df.to_string(index=False)}")
    assert lodf_df.agree_1e6.all(), "LODF disagrees with PyPSA BODF"
    # PTDF rows per monitored row
    rows = {}
    for m, (e, post) in MONITORED.items():
        rows[m] = P.loc[e] + lodf[e] * P.loc[k] if post else P.loc[e].copy()
    Pk = pd.DataFrame(rows).T  # rows x buses
    Pk.to_parquet(os.path.join(OUT, f"{case}_ptdf_rows.parquet"))
    P.to_parquet(os.path.join(OUT, f"{case}_ptdf_full.parquet"))
    post_ref = {m: float(Pk.at[m, ref]) for m in MONITORED}
    log(f"[{case}] |Pk[m,ref]| on the four rows: " + ", ".join(f"{m}={abs(v):.5f}" for m, v in post_ref.items()))
    # SF_raw per generator in the group
    sf = units.copy()
    sf["bus"] = sf["bus"].astype(str)
    for m in MONITORED:
        sf[f"SF_{m}"] = [float(Pk.at[m, b] - Pk.at[m, ref]) for b in sf.bus]
    sf.to_csv(os.path.join(OUT, f"{case}_shift_factors.csv"), index=False)
    # WDT-style node table: every bus hosting wind/solar on the island, SF on the Flagford-Sligo N-1 row.
    # Orientation: the raw row is signed by PyPSA's p0 convention (bus0 -> bus1). The WDT table ranks nodes by
    # their effectiveness in relieving the constraint, so each row is oriented such that the availability-weighted
    # mean SF of the CG3 nodes is positive (the group's export direction); the sign used is recorded.
    g = n.generators
    ws = g[g.carrier.isin(["wind", "solar"])]
    cg3 = cg3_buses(n)
    names = n.buses["psse_name"].astype(str).str.upper()
    nw_set = set(n.buses.index[names.apply(lambda s: any(kk in s for kk in NW_KEYS))].astype(str)) | set(cg3.index)
    nodes = sorted(set(ws.bus.astype(str)))
    wsp = ws.groupby(ws.bus.astype(str))["p_nom"].sum()
    orient = {}
    for m in MONITORED:
        raw = np.array([Pk.at[m, b] - Pk.at[m, ref] for b in cg3.index])
        w = np.array([wsp.get(b, 0.0) for b in cg3.index])
        orient[m] = 1.0 if float((raw * w).sum()) >= 0 else -1.0
    decision("WDT-style node table: shift-factor rows are oriented so that the availability-weighted (p_nom) mean "
             "SF of the CG3 nodes is positive, i.e. positive = the node loads the element in the group's export "
             "direction; the orientation sign per row is stored in <case>_ptdf_summary.json (orientation). Raw signed "
             "values (PyPSA p0 convention) remain in <case>_shift_factors.csv.")
    m1 = "FLG_SLIGO_N1"
    tab = pd.DataFrame({
        "bus": nodes,
        "psse_name": [str(n.buses.at[b, "psse_name"]) for b in nodes],
        "station": [cg3.at[b, "station"] if b in cg3.index else "" for b in nodes],
        "in_CG3": [b in cg3.index for b in nodes],
        "in_NW": [b in nw_set for b in nodes],
        "ws_p_nom": [float(wsp.get(b, 0.0)) for b in nodes],
    })
    for m in MONITORED:
        tab[f"SF_{m}"] = [orient[m] * float(Pk.at[m, b] - Pk.at[m, ref]) for b in nodes]
    tab = tab.sort_values(f"SF_{m1}", ascending=False).reset_index(drop=True)
    v = tab[f"SF_{m1}"].to_numpy()
    ratio = np.full(len(v), np.nan)
    for i in range(len(v) - 1):
        if v[i] > 0 and v[i + 1] >= SF_FLOOR:
            ratio[i] = v[i] / v[i + 1]
    decision(f"Step change in the node table is searched only among consecutive nodes whose lower value is >= "
             f"{SF_FLOOR} (same 0.02 threshold as the reference-bus test); ratios between near-zero shift factors "
             "far from the North-West are numerically meaningless.")
    tab["ratio_to_next"] = ratio
    tab["step_change"] = False
    if np.isfinite(ratio).any():
        j = int(np.nanargmax(ratio))
        tab.loc[j, "step_change"] = True
    tab.to_csv(os.path.join(OUT, f"{case}_node_table.csv"), index=False)
    log(f"[{case}] node table (SF on Flagford-Sligo N-1, ref {ref_name}, orientation {orient}); top 30 of {len(tab)}:\n"
        f"{tab.head(30).to_string(index=False)}")
    step_row = tab[tab.step_change]
    res = dict(case=case, ref_bus=ref, ref_name=ref_name, lodf=lodf, bodf=bodf, P_e_ref={e: float(P.at[e, ref]) for e in elements},
               Pk_m_ref=post_ref, n_nodes=len(tab), orientation=orient,
               cg3_SF_min=float(tab.loc[tab.in_CG3, f"SF_{m1}"].min()), cg3_SF_max=float(tab.loc[tab.in_CG3, f"SF_{m1}"].max()),
               cg3_rank_range=[int(tab.index[tab.in_CG3].min()) + 1, int(tab.index[tab.in_CG3].max()) + 1],
               step_after_bus=str(step_row.bus.iloc[0]) if len(step_row) else None,
               step_after_name=str(step_row.psse_name.iloc[0]) if len(step_row) else None,
               step_ratio=float(step_row.ratio_to_next.iloc[0]) if len(step_row) else None,
               step_value_above=float(step_row.SF_FLG_SLIGO_N1.iloc[0]) if len(step_row) else None,
               step_value_below=float(tab.SF_FLG_SLIGO_N1.iloc[step_row.index[0] + 1]) if len(step_row) else None,
               step_rank=int(step_row.index[0]) + 1 if len(step_row) else None,
               cg3_nodes_below_step=tab.loc[step_row.index[0] + 1:, :].query("in_CG3").psse_name.tolist() if len(step_row) else None,
               non_cg3_nodes_above_step=tab.loc[:step_row.index[0], :].query("~in_CG3").psse_name.tolist() if len(step_row) else None)
    with open(os.path.join(OUT, f"{case}_ptdf_summary.json"), "w") as f:
        json.dump(res, f, indent=1)
    log(f"[{case}] ptdf summary: {json.dumps(res)}")
    return res


# --------------------------------------------------------------------------- #
# §3.4 overload series
# --------------------------------------------------------------------------- #
def overload_series(case: str) -> dict:
    F = pd.read_parquet(os.path.join(OUT, f"{case}_flows.parquet"))
    rating = pd.read_csv(os.path.join(OUT, f"{case}_rating.csv"), index_col=0)["rating"]
    lodf = pd.read_csv(os.path.join(OUT, f"{case}_lodf.csv")).set_index("element")["lodf_kit"]
    k = CONTINGENCY
    step = CASES[case]["step"]
    out = pd.DataFrame(index=F.index)
    out.index.name = "hour"
    stats = dict(case=case, hours=len(F), step=step)
    for m, (e, post) in MONITORED.items():
        Fm = F[e] + lodf[e] * F[k] if post else F[e].copy()
        Om = (Fm.abs() - rating[e]).clip(lower=0.0)
        out[f"F_{m}"] = Fm
        out[f"O_{m}"] = Om
        stats[f"hours_over_{m}"] = int((Om > 0).sum())
        stats[f"overload_MWh_{m}"] = float(Om.sum() * step)
        stats[f"max_over_{m}"] = float(Om.max())
        stats[f"max_abs_flow_{m}"] = float(Fm.abs().max())
        stats[f"rating_{m}"] = float(rating[e])
        stats[f"share_pos_flow_over_{m}"] = float((Fm[Om > 0] > 0).mean()) if (Om > 0).any() else np.nan
    Ocols = [c for c in out.columns if c.startswith("O_")]
    nover = (out[Ocols] > 0).sum(axis=1)
    out["n_rows_over"] = nover
    stats["hours_any_overload"] = int((nover > 0).sum())
    stats["share_hours_any_overload"] = float((nover > 0).mean())
    stats["total_overload_MWh_all_rows"] = float(out[Ocols].sum().sum() * step)
    stats["max_overload_MW"] = float(out[Ocols].max().max())
    stats["max_overload_row"] = str(out[Ocols].max().idxmax())
    stats["share_overload_hours_multi_row"] = float((nover[nover > 0] > 1).mean()) if (nover > 0).any() else np.nan
    stats["hours_multi_row"] = int((nover > 1).sum())
    stats["hours_all_three_N1_rows"] = int((out[["O_FLG_SLIGO_N1", "O_T25221_N1", "O_T25222_N1"]] > 0).all(axis=1).sum())
    out.to_csv(os.path.join(OUT, f"{case}_overloads.csv"))
    with open(os.path.join(OUT, f"{case}_overload_stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    log(f"[{case}] overload stats: {json.dumps(stats)}")
    return stats


# --------------------------------------------------------------------------- #
# Extra verification: post-contingency DC power flow with frozen dispatch
# --------------------------------------------------------------------------- #
def verify_lodf_dcpf(case: str, n_hours: int = 3) -> pd.DataFrame:
    """Remove the contingency line, rebuild the DC flows from the frozen baseline injections
    (flowmath.flows), and compare with f_e + LODF[e,k] f_k on the three monitored elements.
    Also checks that the intact rebuild reproduces the LOPF flows."""
    P = pd.read_parquet(os.path.join(OUT, f"{case}_baseline_p.parquet"))
    F = pd.read_parquet(os.path.join(OUT, f"{case}_flows.parquet"))
    lodf = pd.read_csv(os.path.join(OUT, f"{case}_lodf.csv")).set_index("element")["lodf_kit"]
    k = CONTINGENCY
    # pick the hours with the largest |post-contingency flow| on Flagford-Sligo plus a random one
    e0 = MONITORED["FLG_SLIGO_N1"][0]
    post = (F[e0] + lodf[e0] * F[k]).abs().sort_values(ascending=False)
    hours = list(post.index[:n_hours - 1]) + [F.index[len(F) // 2]]
    n, rating, info = prepare(case, with_year=False)
    pmax, load = load_year(case)
    n.set_snapshots(pd.DatetimeIndex(hours))
    n.loads_t.p_set = load.loc[hours, n.loads.index]
    n.generators_t.p = P.loc[hours]
    links = [c for c in F.columns if c in n.links.index]
    n.links_t.p0 = F.loc[hours, links]
    rows = []
    br = flowmath.branches(n)
    for h in hours:
        f_intact = flowmath.flows(n, h, br)
        n2 = n.copy()
        n2.remove("Line", k)
        br2 = flowmath.branches(n2)
        f_post = flowmath.flows(n2, h, br2)
        for e in lodf.index:
            rows.append(dict(hour=str(h), element=e, lopf_intact=float(F.at[h, e]), dc_intact=float(f_intact[e]),
                             lodf_post=float(F.at[h, e] + lodf[e] * F.at[h, k]), dc_post=float(f_post[e]),
                             intact_diff=float(F.at[h, e] - f_intact[e]),
                             post_diff=float(F.at[h, e] + lodf[e] * F.at[h, k] - f_post[e])))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, f"{case}_lodf_dcpf_check.csv"), index=False)
    log(f"[{case}] LODF vs post-contingency DC power flow, frozen dispatch:\n{out.to_string(index=False)}")
    log(f"[{case}] max |intact_diff| {out.intact_diff.abs().max():.4f} MW, max |post_diff| {out.post_diff.abs().max():.4f} MW")
    return out
