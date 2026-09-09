"""Sign/orientation check of the shift-factor convention used by the rules (MASTER §3.4).

For two hours h, h' the post-contingency flow difference on each monitored row must equal
Pk[m,:] @ (p_h - p_h') where p is the net bus injection (generators + link bus1 - link bus0 - loads);
the phase-shifter offset cancels in the difference. Then, for the overload hour with the largest
|F| on FLG_SLIGO_N1, removing 1 MW at each CG3 bus (and adding it at the reference bus) must change
|F| by -sign(F)*SF_raw, i.e. SF_eff = sign(F)*SF_raw > 0 means the cut relieves the row.
Writes out/<case>_sf_convention_check.csv and prints every number.
"""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep

def main(case="WP2024s42"):
    OUT = ep.OUT
    n, rating, info = ep.prepare(case, with_year=False)
    pmax, load = ep.load_year(case)
    P0 = pd.read_parquet(os.path.join(OUT, f"{case}_baseline_p.parquet"))
    F = pd.read_parquet(os.path.join(OUT, f"{case}_flows.parquet"))
    Pk = pd.read_parquet(os.path.join(OUT, f"{case}_ptdf_rows.parquet"))
    ov = pd.read_csv(os.path.join(OUT, f"{case}_overloads.csv"), index_col=0, parse_dates=True)
    sf = pd.read_csv(os.path.join(OUT, f"{case}_shift_factors.csv"))
    ref = str(pd.read_csv(os.path.join(OUT, f"{case}_reference_bus.csv")).query("accepted").bus.iloc[0])
    lodf = pd.read_csv(os.path.join(OUT, f"{case}_lodf.csv")).set_index("element")["lodf_kit"]
    buses = Pk.columns
    def inj(h):
        p = pd.Series(0.0, index=buses)
        g = n.generators
        gp = P0.loc[h]
        sign = g["sign"].reindex(gp.index).fillna(1.0)
        p = p.add((gp * sign).groupby(g.loc[gp.index, "bus"].astype(str)).sum(), fill_value=0.0)
        ld = load.loc[h, n.loads.index]
        p = p.sub(ld.groupby(n.loads["bus"].astype(str)).sum(), fill_value=0.0)
        for lk in n.links.index:
            v = float(F.at[h, lk])
            p[str(n.links.at[lk, "bus0"])] -= v
            p[str(n.links.at[lk, "bus1"])] += v * float(n.links.at[lk, "efficiency"])
        return p.reindex(buses).fillna(0.0)
    # hour with the largest |F| on the N-1 line, and a mid-year hour
    h1 = ov["F_FLG_SLIGO_N1"].abs().idxmax(); h2 = ov.index[len(ov) // 2]
    d = inj(h1) - inj(h2)
    rows = []
    for m, (e, post) in ep.MONITORED.items():
        dF_ptdf = float(Pk.loc[m].to_numpy() @ d.to_numpy())
        dF_lopf = float(ov.at[h1, f"F_{m}"] - ov.at[h2, f"F_{m}"])
        rows.append(dict(check="finite_difference", row=m, hour1=str(h1), hour2=str(h2), dF_from_PTDF=dF_ptdf,
                         dF_from_flows=dF_lopf, abs_diff=abs(dF_ptdf - dF_lopf)))
    # cut check at h1 on every CG3 bus: 1 MW removed at bus, added at ref
    m = "FLG_SLIGO_N1"
    Fh = float(ov.at[h1, f"F_{m}"])
    for b in sorted(sf.bus.astype(str).unique()):
        sfr = float(sf.loc[sf.bus.astype(str) == b, f"SF_{m}"].iloc[0])
        dp = pd.Series(0.0, index=buses); dp[b] -= 1.0; dp[ref] += 1.0
        dF = float(Pk.loc[m].to_numpy() @ dp.to_numpy())
        new_abs = abs(Fh + dF)
        rows.append(dict(check="unit_cut", row=m, hour1=str(h1), bus=b, F=Fh, sign_F=np.sign(Fh), SF_raw=sfr,
                         SF_eff=np.sign(Fh) * sfr, dF_for_1MW_cut=dF, d_absF=new_abs - abs(Fh),
                         relieves=(new_abs < abs(Fh)), consistent=bool(((new_abs - abs(Fh)) < 0) == (np.sign(Fh) * sfr > 0)),
                         d_absF_plus_SF_eff=(new_abs - abs(Fh)) + np.sign(Fh) * sfr))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, f"{case}_sf_convention_check.csv"), index=False)
    print(out.to_string())
    fd = out[out.check == "finite_difference"]
    uc = out[out.check == "unit_cut"]
    print(f"max |dF_PTDF - dF_flows| over the 4 rows: {fd.abs_diff.max():.3e} MW")
    print(f"unit-cut check: all consistent = {bool(uc.consistent.all())}; max |d|F| + SF_eff| = {uc.d_absF_plus_SF_eff.abs().max():.3e}")
    assert fd.abs_diff.max() < 1e-3 and uc.consistent.all()

if __name__ == "__main__":
    main(*(sys.argv[1:] or ["WP2024s42"]))
