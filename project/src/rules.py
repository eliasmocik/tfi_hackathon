"""MASTER §4 — the five rules and the band sweep, per case, from the engine's saved files.

    python src/rules.py <case> [rule ...]     rules: rule1 rule2 rule3 rule1N band  (default: all)

Inputs (out/<case>_*): group_units.csv, shift_factors.csv (RAW signed SF, PyPSA p0 convention), overloads.csv
(signed F_<row>, O_<row> >= 0), avail.parquet (a_i,h for G), baseline_p.parquet (p0), flows.parquet, ptdf_full.parquet,
reference_bus.csv, rating.csv.

Convention (MASTER §3.4, checked numerically by src/check_sf_convention.py -> out/<case>_sf_convention_check.csv):
    SF[m,i,h] = sign(F_m,h) * SF_raw[m,i];   a cut c_i changes |F_m| by -SF[m,i,h] * c_i.
Feasible: sum_i SF[m,i,h] c_i >= O_m,h on every row m with O_m,h > 0, 0 <= c_i <= p0_i,h.

Outputs per case and rule: out/<case>_cuts_<rule>.parquet (hour x generator, MW), out/<case>_<rule>_residual.csv,
out/<case>_rule3_status.csv, out/<case>_rule_hourly.csv (sum of cuts per hour per rule),
out/<case>_postcut_violations.csv (§4.6), out/<case>_nw_branches.csv (the §4.6 branch list).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import linprog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402

OUT = ep.OUT
ROWS = list(ep.MONITORED)                # FLG_SLIGO_N1, T25221_N1, T25222_N1, FLG_SLIGO_N0
BANDS = [0, 1, 2, 3, 5, 10, np.inf]
BAND_NAMES = {0: "band0", 1: "band1", 2: "band2", 3: "band3", 5: "band5", 10: "band10", np.inf: "bandinf"}
RULES = ["rule1", "rule2", "rule3", "rule1N"] + list(BAND_NAMES.values())
TOL_MW = 1e-6           # bisection tolerance on the total cut (MASTER §4.1) and residual-hour threshold
EPS = 1e-12
LP_OPTS = {"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9}


def log(*a):
    print(*a, flush=True)


def decision(text: str):
    """Append an unspecified decision to out/DECISIONS_LOG.md, prefixed [rules]."""
    path = os.path.join(OUT, "DECISIONS_LOG.md")
    line = f"[rules] {text}"
    if os.path.exists(path):
        with open(path) as f:
            if line in f.read():
                return
    with open(path, "a") as f:
        f.write(line + "\n")
    log("DECISION:", text)


# --------------------------------------------------------------------------- #
# Case data
# --------------------------------------------------------------------------- #
class CaseData:
    def __init__(self, case: str):
        self.case = case
        self.step = ep.CASES[case]["step"]
        units = pd.read_csv(os.path.join(OUT, f"{case}_group_units.csv"), dtype={"bus": str})
        self.units_all = units
        inG = units["class"] != "U"
        u = units[inG].reset_index(drop=True)
        self.units = u
        self.G = u.generator.tolist()
        self.bus = u.bus.astype(str).to_numpy()
        self.station = u.station.to_numpy()
        self.cls = u["class"].to_numpy()
        sf = pd.read_csv(os.path.join(OUT, f"{case}_shift_factors.csv"), dtype={"bus": str}).set_index("generator")
        self.SF_raw = sf.loc[self.G, [f"SF_{m}" for m in ROWS]].to_numpy().T      # rows x G
        ov = pd.read_csv(os.path.join(OUT, f"{case}_overloads.csv"), index_col=0, parse_dates=True)
        self.hours = ov.index
        self.F = ov[[f"F_{m}" for m in ROWS]].to_numpy()                             # H x rows
        self.O = ov[[f"O_{m}" for m in ROWS]].to_numpy()
        a = pd.read_parquet(os.path.join(OUT, f"{case}_avail.parquet"))
        assert list(a.columns) == self.G, "avail.parquet columns must be G in group_units order"
        assert a.index.equals(self.hours)
        self.a = a.to_numpy().clip(min=0.0)
        p0 = pd.read_parquet(os.path.join(OUT, f"{case}_baseline_p.parquet"))
        assert p0.index.equals(self.hours)
        self.p0 = np.minimum(p0[self.G].to_numpy().clip(min=0.0), self.a)   # -0.0 -> 0; p0 <= a by construction
        self.over_hours = np.where((self.O > 0).any(axis=1))[0]
        # nodes = buses
        self.nodes = sorted(set(self.bus))
        self.node_of = np.array([self.nodes.index(b) for b in self.bus])
        self.node_members = [np.where(self.node_of == k)[0] for k in range(len(self.nodes))]
        log(f"[{case}] H={len(self.hours)} step={self.step} |G|={len(self.G)} nodes={len(self.nodes)} "
            f"overload hours={len(self.over_hours)} classes={dict(zip(*np.unique(self.cls, return_counts=True)))}")

    def hour(self, t: int):
        """Effective SF (rows x G), O (rows), p0 (G), a (G) and the set of rows over at hour t."""
        sgn = np.sign(self.F[t])
        SF = sgn[:, None] * self.SF_raw
        return SF, self.O[t], self.p0[t], self.a[t], self.O[t] > 0


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def residuals(SF, O, c, active):
    """Residual overload per row after cut c; rows not over contribute 0."""
    r = O - SF @ c
    r = np.where(active, r, 0.0)
    return np.maximum(r, 0.0)


def prorata_capped(a, cap, X):
    """Vector min(psi * a, cap) whose sum equals X exactly (X <= sum(cap)); psi found on the breakpoints.
    a >= 0, cap >= 0. Farms with a = 0 get 0 (their cap is 0 whenever p0 <= a)."""
    a = np.asarray(a, float); cap = np.asarray(cap, float)
    total = cap.sum()
    if X >= total - EPS:
        return cap.copy()
    if X <= 0:
        return np.zeros_like(cap)
    pos = a > 0
    out = np.zeros_like(cap)
    if not pos.any():
        return out
    ratio = np.full(len(a), np.inf)
    ratio[pos] = cap[pos] / a[pos]
    order = np.argsort(ratio)
    # walk the breakpoints: below ratio r, farm i gives psi*a_i; above, cap_i
    remaining = X
    capped_sum = 0.0
    slope = a[pos].sum()      # sum of a over farms not yet capped
    prev = 0.0
    for idx in order:
        if not pos[idx]:
            break
        r = ratio[idx]
        # can psi reach r without exceeding X?
        need = capped_sum + slope * r
        if need >= X - EPS:
            psi = (X - capped_sum) / slope
            out = np.minimum(psi * a, cap)
            return out
        capped_sum += cap[idx]
        slope -= a[idx]
        prev = r
    # numerical fallthrough: everything capped
    return cap.copy()


# --------------------------------------------------------------------------- #
# Rule 1 — pro rata on availability, bisection on phi
# --------------------------------------------------------------------------- #
def rule1_hour(SF, O, p0, a, active, subset=None, c_fixed=None):
    """c_i = min(phi a_i, p0_i) for i in subset; c_fixed (other farms) is added to the relief.
    Returns (c_subset_full_vector, phi, feasible)."""
    n = len(p0)
    sub = np.ones(n, bool) if subset is None else subset
    base = np.zeros(n) if c_fixed is None else c_fixed
    SFa, Oa = SF[active], O[active]
    relief_base = SFa @ base if active.any() else np.zeros(0)

    def cut(phi):
        c = np.zeros(n)
        c[sub] = np.minimum(phi * a[sub], p0[sub])
        return c

    def feasible(phi):
        if not active.any():
            return True
        return bool(np.all(SFa @ cut(phi) + relief_base >= Oa))

    if not active.any():
        return np.zeros(n), 0.0, True
    if feasible(0.0):
        return np.zeros(n), 0.0, True
    if not feasible(1.0):
        return cut(1.0), 1.0, False
    lo, hi = 0.0, 1.0
    span = a[sub].sum()
    # stop when the total cut between lo and hi can differ by < TOL_MW
    while (hi - lo) * span > TOL_MW and hi - lo > 1e-15:
        mid = 0.5 * (lo + hi)
        if feasible(mid):
            hi = mid
        else:
            lo = mid
    return cut(hi), hi, True


# --------------------------------------------------------------------------- #
# Rule 2 — effectiveness order by node, pro rata on availability inside a node
# --------------------------------------------------------------------------- #
def rule2_core(cd: CaseData, SF, O, p0, a, active, allowed, c=None, max_iter=None):
    """Greedy on the row with the largest residual. allowed: bool mask of farms that may be cut.
    c: starting cut vector (continued). Returns (c, residual vector, n_iter, exhausted_flag)."""
    n = len(p0)
    c = np.zeros(n) if c is None else c.copy()
    max_iter = max_iter or 50 * (len(cd.nodes) + 1)
    it = 0
    exhausted = False
    while True:
        res = residuals(SF, O, c, active)
        if res.max() <= EPS:
            break
        if it >= max_iter:
            exhausted = True
            break
        it += 1
        m = int(np.argmax(res))
        rem = np.where(allowed, p0 - c, 0.0)
        # node SF on m* and remaining capacity per node
        best, best_sf = -1, 0.0
        for k, mem in enumerate(cd.node_members):
            if rem[mem].sum() <= EPS:
                continue
            s = float(SF[m, mem[0]])         # all farms of a node share the bus, hence the SF
            if s > 0 and (s > best_sf or (s == best_sf and best >= 0 and cd.nodes[k] < cd.nodes[best])):
                best, best_sf = k, s
        if best < 0:
            exhausted = True
            break
        mem = cd.node_members[best]
        cap = rem[mem]
        need = res[m] / best_sf
        X = min(need, cap.sum())
        add = prorata_capped(a[mem], cap, X)
        c[mem] += add
    res = residuals(SF, O, c, active)
    return c, res, it, exhausted


def rule2_hour(cd, SF, O, p0, a, active):
    allowed = np.ones(len(p0), bool)
    c, res, it, exhausted = rule2_core(cd, SF, O, p0, a, active, allowed)
    feasible = res.max() <= TOL_MW
    if not feasible:
        c = p0.copy()                      # §4: cut everything in G
        res = residuals(SF, O, c, active)
    return c, res, feasible, it


# --------------------------------------------------------------------------- #
# Rule 3 — nodal optimum (LP)
# --------------------------------------------------------------------------- #
def rule3_hour(SF, O, p0, a, active):
    n = len(p0)
    if not active.any():
        return np.zeros(n), "no_overload", True, 0
    A = -SF[active]
    b = -O[active]
    r = linprog(c=np.ones(n), A_ub=A, b_ub=b, bounds=list(zip(np.zeros(n), p0)), method="highs", options=LP_OPTS)
    if r.status == 0:
        c = np.clip(r.x, 0.0, p0)
        return c, r.message, True, int(r.nit)
    return p0.copy(), r.message, False, int(getattr(r, "nit", 0) or 0)


# --------------------------------------------------------------------------- #
# Rule 1N — non-priority first
# --------------------------------------------------------------------------- #
def rule1N_hour(SF, O, p0, a, active, cls):
    n = len(p0)
    isN = cls == "N"; isP = cls == "P"
    if not active.any():
        return np.zeros(n), 0.0, 0.0, True, "none"
    if isN.any():
        cN, phiN, feasN = rule1_hour(SF, O, p0, a, active, subset=isN)
    else:
        cN, phiN, feasN = np.zeros(n), 1.0, False
    if feasN:
        return cN, phiN, 0.0, True, "N_only"
    # tier 1 fully cut leaves a residual -> tier 2 pro rata among P with N cut
    cP, phiP, feasP = rule1_hour(SF, O, p0, a, active, subset=isP, c_fixed=cN)
    c = cN + cP
    return c, phiN, phiP, feasP, ("N_then_P" if feasP else "infeasible")


# --------------------------------------------------------------------------- #
# Rule 4 — band
# --------------------------------------------------------------------------- #
def band_run(cd: CaseData, b: float, on_hour=None):
    """Chronological sweep with the year-to-date tally. b in percentage points (np.inf = rule 2 exactly)."""
    H, n = cd.p0.shape
    C = np.zeros((H, n))
    cum_cut = np.zeros(n); cum_avail = np.zeros(n)
    resid_rows = []
    widen_log = []
    bfrac = b / 100.0
    for t in range(H):
        if cd.O[t].max() > 0:
            SF, O, p0, a, active = cd.hour(t)
            r = np.where(cum_avail > 0, cum_cut / np.where(cum_avail > 0, cum_avail, 1.0), 0.0)
            rbar = cum_cut.sum() / cum_avail.sum() if cum_avail.sum() > 0 else 0.0
            allowed = r <= rbar + bfrac + 1e-15 if np.isfinite(b) else np.ones(n, bool)
            c, res, it, exhausted = rule2_core(cd, SF, O, p0, a, active, allowed)
            n_widen = 0
            while res.max() > TOL_MW and (~allowed).any():
                outside = np.where(~allowed)[0]
                j = outside[np.argmin(r[outside])]      # lowest r_i outside E; ties -> first in G order
                allowed[j] = True
                n_widen += 1
                c, res, it, exhausted = rule2_core(cd, SF, O, p0, a, active, allowed, c=c)
            if res.max() > TOL_MW:
                c = p0.copy(); res = residuals(SF, O, c, active)
                resid_rows.append(dict(hour=cd.hours[t], **{f"residual_{m}": res[k] for k, m in enumerate(ROWS)},
                                       n_widen=n_widen, flag="infeasible_all_cut"))
            C[t] = c
            widen_log.append(dict(hour=cd.hours[t], eligible=int(allowed.sum()) - n_widen, n_widen=n_widen,
                                  rbar=rbar, cut_MW=c.sum()))
        cum_cut += C[t] * cd.step
        cum_avail += cd.a[t] * cd.step
    return C, resid_rows, pd.DataFrame(widen_log)


# --------------------------------------------------------------------------- #
# §4.6 post-cut check
# --------------------------------------------------------------------------- #
def nw_branches(case: str) -> pd.DataFrame:
    """All intact lines/transformers with an end at a North-West bus (MASTER §4.6 list), with rating and flows."""
    path = os.path.join(OUT, f"{case}_nw_branches.csv")
    if os.path.exists(path):
        return pd.read_csv(path, dtype={"bus0": str, "bus1": str}).set_index("branch")
    n, rating, info = ep.prepare(case, with_year=False)
    names = n.buses["psse_name"].astype(str).str.upper().str.strip()

    def is_nw(b):
        s = names[b]
        if " NI" in s:
            return False
        return any(s == k or s.startswith(k + " ") or s.startswith(k + "_") for k in ep.NW_KEYS)
    rows = []
    for kind, frame in (("Line", n.lines), ("Transformer", n.transformers)):
        for e, r in frame.iterrows():
            if is_nw(r.bus0) or is_nw(r.bus1):
                rows.append(dict(branch=e, kind=kind, bus0=str(r.bus0), bus1=str(r.bus1), name0=names[r.bus0],
                                 name1=names[r.bus1], rating=float(rating[e])))
    df = pd.DataFrame(rows).set_index("branch")
    df.to_csv(path)
    return df


def postcut_check(cd: CaseData, C: np.ndarray, nw: pd.DataFrame, P: pd.DataFrame, flows: pd.DataFrame, ref: str):
    """Count hour-branch pairs where |f + df| > rating and |f| <= rating; df = -sum_i (P[e,bus_i] - P[e,ref]) c_i."""
    Hm = (P.loc[nw.index, cd.bus].to_numpy() - P.loc[nw.index, [ref]].to_numpy())   # branches x G
    df = -(C @ Hm.T)                                                                   # hours x branches
    f = flows[nw.index].to_numpy()
    rating = nw.rating.to_numpy()[None, :]
    cut_hours = C.sum(axis=1) > EPS
    before = np.abs(f) <= rating + TOL_MW
    after = np.abs(f + df) > rating + TOL_MW
    new = before & after & cut_hours[:, None]
    per_branch = pd.Series(new.sum(axis=0), index=nw.index)
    # extra: monitored rows (post-contingency and intact) newly over after the cut
    SF_eff_all = np.sign(cd.F)[:, :, None] * cd.SF_raw[None, :, :]     # H x rows x G
    dabs = -np.einsum("hmg,hg->hm", SF_eff_all, C)
    absF = np.abs(cd.F)
    rat = np.array([cd_rating(cd, m) for m in ROWS])[None, :]
    mon_new = ((absF <= rat + TOL_MW) & (absF + dabs > rat + TOL_MW) & cut_hours[:, None]).sum()
    return int(new.sum()), int(cut_hours.sum()), per_branch, int(mon_new), float(np.abs(df).max())


def cd_rating(cd, m):
    rt = pd.read_csv(os.path.join(OUT, f"{cd.case}_rating.csv"), index_col=0)["rating"]
    return float(rt[ep.MONITORED[m][0]])


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def save_cuts(cd, name, C):
    pd.DataFrame(C, index=cd.hours, columns=cd.G).to_parquet(os.path.join(OUT, f"{cd.case}_cuts_{name}.parquet"))


def save_residual(cd, name, rows):
    cols = ["hour"] + [f"residual_{m}" for m in ROWS] + ["flag"]
    df = pd.DataFrame(rows)
    if len(df) == 0:
        df = pd.DataFrame(columns=cols)
    df.to_csv(os.path.join(OUT, f"{cd.case}_{name}_residual.csv"), index=False)
    return len(df)


def run_case(case: str, which=None):
    t0 = time.time()
    cd = CaseData(case)
    which = which or RULES
    H, n = cd.p0.shape
    summary = {}
    # ---------------- rule 1
    if "rule1" in which:
        C = np.zeros((H, n)); rows = []; phis = []
        for t in cd.over_hours:
            SF, O, p0, a, active = cd.hour(t)
            c, phi, feas = rule1_hour(SF, O, p0, a, active)
            C[t] = c; phis.append(phi)
            if not feas:
                res = residuals(SF, O, c, active)
                rows.append(dict(hour=cd.hours[t], **{f"residual_{m}": res[k] for k, m in enumerate(ROWS)}, flag="infeasible_all_cut"))
        save_cuts(cd, "rule1", C); nres = save_residual(cd, "rule1", rows)
        summary["rule1"] = dict(residual_hours=nres, phi_max=float(np.max(phis)) if phis else 0.0,
                                phi_mean=float(np.mean(phis)) if phis else 0.0, hours_phi_eq_1=int(sum(1 for p in phis if p >= 1.0)))
        log(f"[{case}] rule1 done {time.time()-t0:.0f}s: total cut {C.sum()*cd.step:.1f} MWh, residual hours {nres}, "
            f"phi max {summary['rule1']['phi_max']:.4f}")
    # ---------------- rule 2
    if "rule2" in which:
        C = np.zeros((H, n)); rows = []; its = []
        for t in cd.over_hours:
            SF, O, p0, a, active = cd.hour(t)
            c, res, feas, it = rule2_hour(cd, SF, O, p0, a, active)
            C[t] = c; its.append(it)
            if not feas:
                rows.append(dict(hour=cd.hours[t], **{f"residual_{m}": res[k] for k, m in enumerate(ROWS)}, flag="infeasible_all_cut"))
        save_cuts(cd, "rule2", C); nres = save_residual(cd, "rule2", rows)
        summary["rule2"] = dict(residual_hours=nres, iter_max=int(max(its)) if its else 0)
        log(f"[{case}] rule2 done {time.time()-t0:.0f}s: total cut {C.sum()*cd.step:.1f} MWh, residual hours {nres}, max node steps {summary['rule2']['iter_max']}")
    # ---------------- rule 3
    if "rule3" in which:
        C = np.zeros((H, n)); rows = []; stat = []
        for t in cd.over_hours:
            SF, O, p0, a, active = cd.hour(t)
            c, msg, ok, nit = rule3_hour(SF, O, p0, a, active)
            C[t] = c
            res = residuals(SF, O, c, active)
            stat.append(dict(hour=cd.hours[t], success=ok, status=msg, nit=nit, cut_MW=c.sum(), max_residual=res.max()))
            if not ok:
                rows.append(dict(hour=cd.hours[t], **{f"residual_{m}": res[k] for k, m in enumerate(ROWS)}, flag="infeasible_all_cut"))
        save_cuts(cd, "rule3", C); nres = save_residual(cd, "rule3", rows)
        st = pd.DataFrame(stat); st.to_csv(os.path.join(OUT, f"{case}_rule3_status.csv"), index=False)
        summary["rule3"] = dict(residual_hours=nres, lp_success=int(st.success.sum()) if len(st) else 0, lp_total=len(st),
                                max_residual_after_lp=float(st.max_residual.max()) if len(st) else 0.0,
                                statuses=st.status.value_counts().to_dict() if len(st) else {})
        log(f"[{case}] rule3 done {time.time()-t0:.0f}s: total cut {C.sum()*cd.step:.1f} MWh, LPs {len(st)}, success {summary['rule3']['lp_success']}, "
            f"max residual {summary['rule3']['max_residual_after_lp']:.2e}")
    # ---------------- rule 1N
    if "rule1N" in which:
        C = np.zeros((H, n)); rows = []; tiers = []
        for t in cd.over_hours:
            SF, O, p0, a, active = cd.hour(t)
            c, phiN, phiP, feas, tier = rule1N_hour(SF, O, p0, a, active, cd.cls)
            C[t] = c; tiers.append(dict(hour=cd.hours[t], phi_N=phiN, phi_P=phiP, tier=tier))
            if not feas:
                res = residuals(SF, O, c, active)
                rows.append(dict(hour=cd.hours[t], **{f"residual_{m}": res[k] for k, m in enumerate(ROWS)}, flag="infeasible_all_cut"))
        save_cuts(cd, "rule1N", C); nres = save_residual(cd, "rule1N", rows)
        tdf = pd.DataFrame(tiers); tdf.to_csv(os.path.join(OUT, f"{case}_rule1N_tiers.csv"), index=False)
        summary["rule1N"] = dict(residual_hours=nres, tiers=tdf.tier.value_counts().to_dict() if len(tdf) else {},
                                 cut_MWh_N=float(C[:, cd.cls == "N"].sum() * cd.step), cut_MWh_P=float(C[:, cd.cls == "P"].sum() * cd.step))
        log(f"[{case}] rule1N done {time.time()-t0:.0f}s: total cut {C.sum()*cd.step:.1f} MWh, tiers {summary['rule1N']['tiers']}, residual hours {nres}")
    # ---------------- bands
    if "band" in which or any(b in which for b in BAND_NAMES.values()):
        for b, name in BAND_NAMES.items():
            if "band" not in which and name not in which:
                continue
            C, rows, wl = band_run(cd, b)
            save_cuts(cd, name, C); nres = save_residual(cd, name, rows)
            wl.to_csv(os.path.join(OUT, f"{case}_{name}_widen.csv"), index=False)
            summary[name] = dict(residual_hours=nres, hours_widened=int((wl.n_widen > 0).sum()) if len(wl) else 0,
                                 max_widen=int(wl.n_widen.max()) if len(wl) else 0)
            log(f"[{case}] {name} done {time.time()-t0:.0f}s: total cut {C.sum()*cd.step:.1f} MWh, hours widened {summary[name]['hours_widened']}, residual hours {nres}")
    # ---------------- hourly totals and post-cut check for every rule that exists on disk
    hourly = pd.DataFrame(index=cd.hours)
    ref = str(pd.read_csv(os.path.join(OUT, f"{case}_reference_bus.csv"), dtype={"bus": str}).query("accepted").bus.iloc[0])
    nw = nw_branches(case)
    P = pd.read_parquet(os.path.join(OUT, f"{case}_ptdf_full.parquet"))
    flows = pd.read_parquet(os.path.join(OUT, f"{case}_flows.parquet"))
    pc_rows = []
    per_branch_all = {}
    for name in RULES:
        fp = os.path.join(OUT, f"{case}_cuts_{name}.parquet")
        if not os.path.exists(fp):
            continue
        C = pd.read_parquet(fp).to_numpy()
        hourly[name] = C.sum(axis=1)
        npairs, nhours, per_branch, mon_new, dfmax = postcut_check(cd, C, nw, P, flows, ref)
        per_branch_all[name] = per_branch
        pc_rows.append(dict(rule=name, postcut_violations=npairs, hours_with_cut=nhours, nw_branches=len(nw),
                            monitored_rows_newly_over=mon_new, max_abs_df_MW=dfmax,
                            residual_hours=len(pd.read_csv(os.path.join(OUT, f"{case}_{name}_residual.csv")))))
    hourly.to_csv(os.path.join(OUT, f"{case}_rule_hourly.csv"))
    pc = pd.DataFrame(pc_rows)
    pc.to_csv(os.path.join(OUT, f"{case}_postcut_violations.csv"), index=False)
    pd.DataFrame(per_branch_all).to_csv(os.path.join(OUT, f"{case}_postcut_by_branch.csv"))
    log(f"[{case}] post-cut check (§4.6):\n{pc.to_string(index=False)}")
    with open(os.path.join(OUT, f"{case}_rules_summary.json"), "w") as f:
        json.dump(dict(case=case, seconds=time.time() - t0, **summary), f, indent=1, default=str)
    log(f"[{case}] rules done in {time.time()-t0:.0f}s")
    return summary


if __name__ == "__main__":
    case = sys.argv[1]
    which = sys.argv[2:] or None
    decision("Feasibility is enforced on the rows that are over at the hour (O_m,h > 0) using the full signed effective "
             "shift factor; rows with O = 0 have nothing to relieve and are not constrained (a cut may load them, which "
             "the §4.6-style count 'monitored_rows_newly_over' in <case>_postcut_violations.csv reports). In all three "
             "cases every farm in G has SF_eff > 0 on every row that is ever over, so the 'ignore SF <= 0' and "
             "'signed' readings of §4 coincide (checked in src/rules.py preamble, printed by src/results_md.py).")
    decision("§4.6 NW branch list: a bus is North-West when its psse_name equals one of the §4.6 keywords or starts with "
             "the keyword followed by a space or underscore, excluding names containing ' NI' (GARVAGH NI is in Northern "
             "Ireland; MOYL_DUM is the Moyle dummy). A branch is in the list when either end is North-West. The list is "
             "saved as <case>_nw_branches.csv.")
    decision("Rule 2 tie-break: nodes with exactly equal SF on m* are taken in ascending bus-number order; the row m* is "
             "the argmax of the residual vector (first row in the order FLG_SLIGO_N1, T25221_N1, T25222_N1, FLG_SLIGO_N0 "
             "on exact ties). Rule 4 tie-break: among farms outside E with the same lowest r_i, the first in group_units "
             "order is added.")
    decision("Rule 1 bisection stops when (phi_hi - phi_lo) x sum(a) < 1e-6 MW and returns phi_hi (the feasible side). "
             "'Residual hours' are hours whose largest residual exceeds 1e-6 MW after the rule; rule 3 uses HiGHS with "
             "primal/dual feasibility tolerances 1e-9.")
    decision("Cumulative tallies (cum_cut, cum_avail) and all MWh totals are MW x step (step = 2 h for the WP2033 cases); "
             "ratios are unaffected. Rule 3's LP is solved with c bounded by p0 (not a): p0 <= a in every hour.")
    run_case(case, which)
