"""Usage: python n1_test_anynet.py <hour step> pst <year file prefix> <network.nc> <flows.pkl>
Run from research/n1_gonogo/. Year prefix e.g. ../../data/synth_out_extra/TYTFS2024_WP2024_V35_synthetic_2030_seed42_ (gunzip the csvs first).

Go/no-go test: do the real WDT monitored elements bind (intact or N-1) in the
WP2033 network with the synthetic year, under an unconstrained dispatch?

Unconstrained dispatch = what the wind fleet would do before the WDT acts.
Flows come from the LOPF's own network equations with ratings lifted x100.
N-1 flows via LODF from the kit PTDF.
"""
import warnings, logging, sys, time
warnings.filterwarnings("ignore")
logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("linopy").setLevel(logging.ERROR)
import numpy as np, pandas as pd, pypsa
sys.path.insert(0, "../../participant-kit")
import flowmath

STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PST = len(sys.argv) > 2 and sys.argv[2] == "pst"
UP = sys.argv[3] if len(sys.argv) > 3 else "/mnt/user-data/uploads/tfi_hackathon/data/synth_out/TYTFS2024_WP2033_V35_synthetic_2030_seed42_"

n = pypsa.Network(sys.argv[4] if len(sys.argv) > 4 else "networks/WP2033_all-island.nc")
pmax = pd.read_csv(UP + "p_max_pu.csv", index_col=0, parse_dates=True)
load = pd.read_csv(UP + "loads_p_set.csv", index_col=0, parse_dates=True)
snaps = pmax.index[::STEP]
print("year cols matching generators:", len(set(pmax.columns) & set(n.generators.index)), "of", len(pmax.columns), "; generators with a profile in kit week:", n.generators_t.p_max_pu.shape[1])
print("load cols matching:", len(set(load.columns) & set(n.loads.index)), "of", len(n.loads))

n.set_snapshots(snaps)
gp = pmax.loc[snaps, [c for c in pmax.columns if c in n.generators.index]]
n.generators_t.p_max_pu = gp
lp = load.loc[snaps, [c for c in load.columns if c in n.loads.index]]
n.loads_t.p_set = lp

# thermal availability in the synthetic year can drop below the static p_min_pu -> infeasible.
g = n.generators
pm = g.index[(g.p_min_pu > 0) & g.index.isin(gp.columns)]
n.generators_t.p_min_pu = pd.DataFrame({c: np.minimum(g.at[c, "p_min_pu"], gp[c].to_numpy()) for c in pm}, index=snaps)
print("p_min_pu clipped for", len(pm), "units")

# renewable bids -1 with deterministic jitter, as in problem_3_1/common.py
names = sorted(g.index[g.carrier.isin(["wind", "solar"])])
for i, nm in enumerate(names):
    g.at[nm, "marginal_cost"] = -1.0 - 1e-4 * i / len(names)

if PST:
    # model the Letterkenny-Strabane PST as a controllable link capped at the tie rating
    r = n.lines.at["3581-89516-1", "s_nom"]
    n.remove("Line", "3581-89516-1")
    n.add("Link", "LKY-STRABANE-PST", bus0="3581", bus1="89516", p_nom=r, p_min_pu=-1, efficiency=1.0, marginal_cost=0)
    print("PST link added, p_nom", r)
# lift ratings
n.lines["s_nom"] *= 100
n.transformers["s_nom"] *= 100

t0 = time.time()
flows = []
for k in range(0, len(snaps), 168):
    sub = snaps[k:k + 168]
    n.optimize(sub, solver_name="highs", assign_all_duals=False, log_fn=None)
    f = pd.concat([n.lines_t.p0.loc[sub], n.transformers_t.p0.loc[sub]], axis=1)
    flows.append(f)
    print(f"  chunk {k//168+1}/{(len(snaps)+167)//168} done, {time.time()-t0:.0f}s", flush=True)
F = pd.concat(flows)
n.lines["s_nom"] /= 100
n.transformers["s_nom"] /= 100
rating = pd.concat([n.lines.s_nom, n.transformers.s_nom])

# PTDF and LODF
br = flowmath.branches(n)
P = flowmath.ptdf(n, br)
def lodf(e, k):
    pk = P.loc[k, br.loc[k, "bus0"]] - P.loc[k, br.loc[k, "bus1"]]
    pe = P.loc[e, br.loc[k, "bus0"]] - P.loc[e, br.loc[k, "bus1"]]
    return pe / (1 - pk)

cases = {
    # monitored, contingency, label
    "CG3 Flagford-Sligo 110 | loss Flagford-Srananagh 220": ("2521-4981-1", "2522-5042-1"),
    "CG3 Flagford T2102 220/110 w1 | loss Flagford-Srananagh 220": ("T2522-2521-25221-1-w1", "2522-5042-1"),
    "CG3 Flagford T 220/110 w1 (2nd) | loss Flagford-Srananagh 220": ("T2522-2521-25222-2-w1", "2522-5042-1"),
    "CG1 Letterkenny-Lenalea 110 | loss Binbane-CathFall 110": ("3581-3591-1", "1341-1701-1"),
    "CG1 Letterkenny-Trillick 110 | loss Binbane-CathFall 110": ("3581-5361-1", "1341-1701-1"),
    "CG1 Drumkeen-Letterkenny 110 | loss Binbane-CathFall 110": ("2321-3581-1", "1341-1701-1"),
        "Srananagh 220/110 T w1 | loss Flagford-Srananagh 220": ("T5042-5041-50421-1-w1", "2522-5042-1"),
    "Corderry-Srananagh 110 | loss Flagford-Srananagh 220": ("1631-5041-1", "2522-5042-1"),
    "CathFall-Srananagh 110 | loss Flagford-Srananagh 220": ("1701-5041-1", "2522-5042-1"),
}
rows = []
for label, (e, k) in cases.items():
    fe, fk = F[e], F[k]
    post = fe + lodf(e, k) * fk
    r = rating[e]
    rows.append(dict(case=label, rating=r, lodf=round(lodf(e, k), 3),
                     intact_hours_over=int((fe.abs() > r).sum()),
                     intact_max=round(fe.abs().max(), 1),
                     n1_hours_over=int((post.abs() > r).sum()),
                     n1_share=round((post.abs() > r).mean(), 3),
                     n1_max=round(post.abs().max(), 1),
                     n1_overload_MWh=round((post.abs() - r).clip(lower=0).sum() * STEP, 0)))
out = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(out.to_string(index=False))

# intact binding survey in the NW
nw_keys = ["BINBANE","ARDNAG","CORDERRY","CATH","CUNGHILL","DRUMKEEN","CLOGHER","LETTERKENNY","LENALEA","MEENTYCAT","SLIGO","SORNE","SRANANAGH","TIEVEBRACK","TRILLICK","CROAGH","FLAGFORD","MOY","GLENREE","STRA","GOLAGH"]
def nm(b): return str(n.buses.loc[str(b), "psse_name"]) if str(b) in n.buses.index else str(b)
surv = []
for e in F.columns:
    if e not in br.index: continue
    s0, s1 = nm(br.loc[e, "bus0"]), nm(br.loc[e, "bus1"])
    if any(k in (s0 + s1).upper() for k in nw_keys):
        over = (F[e].abs() > rating[e]).mean()
        if over > 0:
            surv.append((e, s0, s1, rating[e], round(over, 3), round(F[e].abs().max(), 1)))
print("\nNW branches overloaded intact under unconstrained dispatch (share of hours):")
print(pd.DataFrame(surv, columns=["branch","from","to","rating","share_over","max_flow"]).sort_values("share_over", ascending=False).to_string(index=False))
F.to_pickle(sys.argv[5] if len(sys.argv) > 5 else ("flows_unconstrained_pst.pkl" if PST else "flows_unconstrained.pkl"))
