"""Proof of the SPEC's Tier-1 / Tier-2 / LODF computations on the kit.

    TFI_KIT=<path to participant-kit> python proof_siting.py [SCENARIO] [SCOPE]

Everything is timed.  Nothing is written into the project folder.
"""
import os, sys, time
import numpy as np
import pandas as pd

KIT = os.environ.get("TFI_KIT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "participant-kit"))
sys.path.insert(0, KIT)
import gridkit, flowmath  # noqa: E402

gridkit.quiet()
pd.set_option("display.width", 200)
SCENARIO = sys.argv[1] if len(sys.argv) > 1 else "WP2033"
SCOPE = sys.argv[2] if len(sys.argv) > 2 else "north-west"
NEW_MW = 50.0
EXISTING_RE_COST = -1.0          # spec section 5: existing wind bids -1 ("kit default")
T0 = time.time()
TIMES = {}


def tick(label):
    TIMES[label] = time.time() - T0
    print(f"   [t={TIMES[label]:6.1f}s] {label}")


def great_circle(a, b):
    R, d = 6371.0088, np.pi / 180
    dlat, dlon = (b[1] - a[1]) * d, (b[0] - a[0]) * d
    h = np.sin(dlat / 2) ** 2 + np.cos(a[1] * d) * np.cos(b[1] * d) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def nearest_wind_profile(n, bus):
    """Profile of the nearest (great-circle) existing wind unit that has a p_max_pu series."""
    wind = n.generators[(n.generators.carrier == "wind")
                        & n.generators.index.isin(n.generators_t.p_max_pu.columns)]
    xy = n.buses[["x", "y"]]
    here = xy.loc[bus].to_numpy()
    dist = pd.Series({g: great_circle(here, xy.loc[b].to_numpy()) for g, b in wind["bus"].items()})
    g = dist.idxmin()
    return n.generators_t.p_max_pu[g].copy(), g, float(dist.min())


def load_baseline():
    n = gridkit.load(SCENARIO, SCOPE)
    re = n.generators.carrier.isin(["wind", "solar"])
    n.generators.loc[re, "marginal_cost"] = EXISTING_RE_COST
    return n


def re_delivered(n, names):
    return float(n.generators_t.p[names].clip(lower=0).sum().sum())


# ------------------------------------------------------------------ B1 baseline
print(f"\n=== B1 baseline  {SCENARIO} {SCOPE} ===")
n = load_baseline()
print(gridkit.summary(n).to_string())
print("kit-shipped wind marginal_cost values:",
      gridkit.load(SCENARIO, SCOPE).generators.query("carrier=='wind'").marginal_cost.unique())
status = gridkit.solve(n, assign_all_duals=True)   # <- without this, mu_upper/mu_lower stay empty in PyPSA 1.3
tick("baseline solve")
print("status:", status, " objective:", round(n.objective, 1))
print("populated dual attrs on lines_t:", [k for k in n.lines_t.keys() if len(n.lines_t[k].columns)])
print("populated on buses_t:", [k for k in n.buses_t.keys() if len(n.buses_t[k].columns)])
if len(n.transformers):
    print("populated on transformers_t:", [k for k in n.transformers_t.keys() if len(n.transformers_t[k].columns)])
mu_up, mu_lo = n.lines_t.mu_upper, n.lines_t.mu_lower
lam = n.buses_t.marginal_price
print("\nbinding circuits (hours at rating):\n", gridkit.binding(n).to_string())
print("\nmu_upper: min/max", mu_up.min().min(), mu_up.max().max(),
      "| mu_lower: min/max", mu_lo.min().min(), mu_lo.max().max())
print("hours with any nonzero mu:", int(((mu_up.abs() + mu_lo.abs()).sum(axis=1) > 1e-9).sum()))
print("sum |mu_upper| per line (EUR/MW over week):\n", mu_up.abs().sum()[mu_up.abs().sum() > 1e-9].round(2).to_string())
print("sum |mu_lower| per line:\n", mu_lo.abs().sum()[mu_lo.abs().sum() > 1e-9].round(2).to_string())
print("\nnodal price (EUR/MWh): mean per bus\n", lam.mean().round(2).to_string())
print("nodal price min/max:", lam.min().min(), lam.max().max())
print("\ndispatch-down:\n", gridkit.dispatch_down(n).round(1).to_string())
print("unserved:", gridkit.unserved(n).to_dict())
base_names = n.generators.index[n.generators.carrier.isin(["wind", "solar"])].tolist()
base_re_mwh = re_delivered(n, base_names)
print("baseline RE delivered MWh:", round(base_re_mwh, 1))

# Check the sign/consistency: lambda_b - mean_b(lambda) == sum_e PTDF_unif(e,b) * (mu_up - mu_lo)_e ?
frame = flowmath.branches(n)
P = flowmath.ptdf(n, frame)                          # branches x buses, uniform reference
# PyPSA 1.3 keeps the RAW solver sign: mu_upper <= 0 (dual of s <= s_nom), mu_lower >= 0 (dual of s >= -s_nom).
# Standard non-negative multipliers: mu+ = -mu_upper, mu- = mu_lower.  Congestion penalty of injecting at b:
#     pen(b,h) = sum_e PTDF(e,b) * (mu+ - mu-)_e,h = -sum_e PTDF(e,b) * (mu_upper + mu_lower)_e,h
# and the exact identity  lambda_b,h = mean_b(lambda_h) - pen(b,h)   (uniform-reference PTDF, per sub-network).
mu_net = -(mu_up + mu_lo).reindex(columns=P.index).fillna(0.0)
if len(n.transformers):
    mu_net = mu_net.add(-(n.transformers_t.mu_upper + n.transformers_t.mu_lower)
                        .reindex(columns=P.index), fill_value=0.0).fillna(0.0)
rhs = mu_net.to_numpy() @ P.to_numpy()               # hours x buses = pen(b,h)
rhs = pd.DataFrame(rhs, index=n.snapshots, columns=P.columns)
lhs = lam.sub(lam.mean(axis=1), axis=0)
for sign in (+1, -1):
    err = (lhs - sign * rhs).abs().max().max()
    print(f"sign {sign:+d}: max|lambda_b - mean(lambda) - ({sign:+d}) * sum_e PTDF(e,b) mu_e| = {err:.4g}")
# note: Moy is an island in NW (no line touches it) so its own mean is separate; check per sub-network
n.determine_network_topology()
for sn, buses in n.buses.groupby("sub_network").groups.items():
    buses = list(buses)
    lhs_s = lam[buses].sub(lam[buses].mean(axis=1), axis=0)
    rhs_s = rhs[buses].sub(rhs[buses].mean(axis=1), axis=0)
    for sign in (+1, -1):
        err = (lhs_s - sign * rhs_s).abs().max().max()
        print(f"  sub_network {sn} ({len(buses)} buses) sign {sign:+d}: max err {err:.4g}")
tick("dual consistency check")

# ------------------------------------------------------------------ B2 Tier 1
print("\n=== B2 Tier 1 screen ===")
# (i) one common profile for every bus -> LMP ranking must equal PTDF-sum ranking exactly
common = n.generators_t.p_max_pu[[c for c in n.generators_t.p_max_pu.columns
                                  if n.generators.at[c, "carrier"] == "wind"]].mean(axis=1)
expo_lmp_common = lam.mul(common, axis=0).sum()                  # sum_h lambda_b,h * w_h  (EUR/MW over week; HIGH = good for the farm)
expo_ptdf_common = rhs.mul(common, axis=0).sum()                 # spec Tier-1: sum_h sum_e mu_e,h * PTDF(e,b) * w_h  (HIGH = loads congested circuits = BAD)
# (ii) per-bus nearest wind profile (what the spec asks for)
profiles = {}
for b in n.buses.index:
    prof, g, d = nearest_wind_profile(n, b)
    profiles[b] = prof
profiles = pd.DataFrame(profiles)
expo_lmp = (lam * profiles).sum()
expo_ptdf = (rhs * profiles).sum()
tier1 = pd.DataFrame({
    "lmp_common": expo_lmp_common, "ptdfsum_common": expo_ptdf_common,
    "lmp_nearest": expo_lmp, "ptdfsum_nearest": expo_ptdf,
    "mean_lmp": lam.mean(), "hosts_wind_MW": n.generators[n.generators.carrier == "wind"].groupby("bus").p_nom.sum().reindex(n.buses.index).fillna(0),
}).sort_values("lmp_nearest", ascending=False)
print((tier1 if len(tier1) <= 40 else pd.concat([tier1.head(15), tier1.tail(15)])).round(2).to_string())
def spearman(a, b):
    return a.rank().corr(b.rank(), method="spearman") if a.nunique() > 1 and b.nunique() > 1 else float("nan")
r_common = spearman(tier1["lmp_common"], -tier1["ptdfsum_common"])
r_near = spearman(tier1["lmp_nearest"], -tier1["ptdfsum_nearest"])
print(f"\nSpearman(LMP rank, -PTDF-sum rank): common profile {r_common:.4f}, nearest profile {r_near:.4f}")
print("(exact identity per hour: lambda_b = mean(lambda) - sum_e PTDF(e,b)*(mu_up-mu_lo)_e, so with ONE common profile the two"
      "\n rankings are identical; with per-bus profiles they differ only via the profile-weighted mean-price term)")
print("NB: Tier-1 'exposure' = revenue-like weight (EUR/MW over week) - HIGH = market pays most to inject here."
      "\n    For the developer (least dispatch-down) the relevant sign is: high nodal price = NOT congested-behind.")
main_sn = n.buses.sub_network.value_counts().idxmax()
cand = tier1.index[(n.buses.loc[tier1.index, "sub_network"] == main_sn)
                   & ~tier1.index.str.startswith("star:")
                   & (n.buses.loc[tier1.index, "has_coordinates"].astype(str) != "False"
                      if "has_coordinates" in n.buses.columns else True)]
tier1["offered_mwh_per_mw"] = profiles.sum()
tier1["pen_per_mwh"] = tier1["ptdfsum_nearest"] / tier1["offered_mwh_per_mw"]   # grid effect with the weather divided out
ranked = tier1.loc[cand].sort_values("ptdfsum_nearest")            # spec Tier-1 metric: LOW penalty = good site
best_bus, worst_bus = ranked.index[0], ranked.index[-1]
print(f"candidates: {len(cand)} of {len(tier1)} buses (main AC sub-network, no star points, placed)")
print(f"best Tier-1 bus (min penalty): {best_bus}   worst (max penalty): {worst_bus}")
print(f"  by LMP-weighted instead: best {ranked['lmp_nearest'].idxmax()}  worst {ranked['lmp_nearest'].idxmin()}")
print(f"  by penalty per offered MWh: best {ranked['pen_per_mwh'].idxmin()}  worst {ranked['pen_per_mwh'].idxmax()}")
print("top/bottom 8 by spec penalty:\n", pd.concat([ranked.head(8), ranked.tail(8)])[["ptdfsum_nearest","pen_per_mwh","lmp_nearest","mean_lmp","offered_mwh_per_mw","hosts_wind_MW"]].round(2).to_string())
tick("tier 1")

# ------------------------------------------------------------------ B3 Tier 2
print("\n=== B3 Tier 2 confirm ===")


def tier2(bus, cost, label):
    m = load_baseline()
    prof, g, d = nearest_wind_profile(m, bus)
    m.add("Generator", f"NEW {bus}", bus=bus, carrier="wind", p_nom=NEW_MW,
          p_max_pu=prof, marginal_cost=cost)
    st = gridkit.solve(m, assign_all_duals=True)
    new = float(m.generators_t.p[f"NEW {bus}"].clip(lower=0).sum())
    offered = float((prof * NEW_MW).sum())
    ext = re_delivered(m, base_names)
    e_own = new / NEW_MW
    de_ext = (ext - base_re_mwh) / NEW_MW
    print(f"{label:28s} bus={bus:18s} cost={cost:+.0f}  profile from '{g}' ({d:.1f} km)  "
          f"status={st[1]}  delivered={new:8.1f} of {offered:8.1f} MWh  "
          f"E_own={e_own:6.2f} MWh/MW  dE_ext={de_ext:+7.2f} MWh/MW  system={e_own + de_ext:6.2f}")
    return e_own, de_ext


res = {}
for bus in (best_bus, worst_bus):
    res[(bus, -1)] = tier2(bus, -1.0, "class A (-1)")
tick("tier 2 best/worst")

# ------------------------------------------------------------------ B4 farm classes
print("\n=== B4 farm classes at the worst bus ===")
for cost, label in ([(-1.0, "class A (-1, tie w/ existing)")] if SCOPE == "north-west" else []) + [
                    (-0.5, "class A' (-0.5, cut first)"), (-2.0, "class B (-2)"), (-3.0, "class C (-3)")]:
    res[(worst_bus, cost)] = tier2(worst_bus, cost, label)
if SCOPE == "north-west":
    print("... and at the best bus:")
    for cost, label in ((-0.5, "class A' (-0.5)"), (-3.0, "class C (-3)")):
        res[(best_bus, cost)] = tier2(best_bus, cost, label)
tick("farm classes")

# ------------------------------------------------------------------ B5 LODF
print("\n=== B5 LODF ===")
# (a) from the kit PTDF (uniform reference; LODF is reference-independent)
K, buses, edges = flowmath.incidence(n, frame)
Pm = P.to_numpy()
branch_ptdf = Pm @ K                     # flow on k when 1 MW goes bus0(l) -> bus1(l)
diag = np.diag(branch_ptdf)
with np.errstate(divide="ignore", invalid="ignore"):
    lodf = branch_ptdf / (1.0 - diag)[None, :]
radial = np.isclose(diag, 1.0, atol=1e-8)
lodf[:, radial] = np.nan             # outage of a radial branch islands a bus: undefined
np.fill_diagonal(lodf, -1.0)
LODF = pd.DataFrame(lodf, index=edges, columns=edges)
print("radial branches (LODF undefined, outage islands a bus):", list(edges[radial]))
# (b) PyPSA's own BODF
n.determine_network_topology()
sn = n.sub_networks.obj[main_sn]
sn.calculate_BODF()
bodf = pd.DataFrame(sn.BODF, index=sn.branches_i(), columns=sn.branches_i())
bodf.index = bodf.index.get_level_values(1); bodf.columns = bodf.columns.get_level_values(1)
common_e = [e for e in bodf.index if e in LODF.index]
diff = (LODF.loc[common_e, common_e] - bodf.loc[common_e, common_e])
print(f"max |kit LODF - pypsa BODF| over non-radial outages: {np.nanmax(diff.abs().to_numpy()):.3g}")
# (c) brute force: remove the branch and lpf at the peak hour
gridkit.freeze_dispatch(n)
n.lpf(n.snapshots)
loading = gridkit.line_loading(n)
monitored = gridkit.binding(n).index[0] if len(gridkit.binding(n)) else loading.max().idxmax()
peak = loading[monitored].idxmax()
f0 = flowmath.flows(n, peak, frame)           # lines AND transformers, same sign as p0
print(f"flowmath.flows vs n.lines_t.p0 at peak: max diff {np.abs(f0.reindex(n.lines.index) - n.lines_t.p0.loc[peak]).max():.3g} MW")
worst_l, worst_val = None, -1
for l in LODF.columns:
    if l == monitored or np.isnan(LODF.at[monitored, l]):
        continue
    post = f0[monitored] + LODF.at[monitored, l] * f0[l]
    if abs(post) > worst_val:
        worst_l, worst_val = l, abs(post)
pred = f0[monitored] + LODF.at[monitored, worst_l] * f0[worst_l]
print(f"monitored={monitored}  peak={peak}  base flow={f0[monitored]:+.2f} MW (rating {frame.at[monitored,'s_nom']:.0f})  "
      f"worst outage={worst_l} ({frame.at[worst_l,'kind']})  LODF={LODF.at[monitored, worst_l]:+.4f}  predicted post-outage flow={pred:+.2f} MW")
m = load_baseline()
m.generators_t.p = n.generators_t.p.copy()
if len(m.links):
    m.links_t.p0 = n.links_t.p0.copy()
gridkit.freeze_dispatch(m)
gridkit.remove_line(m, worst_l)
m.lpf(peak)
bf = m.lines_t.p0.at[peak, monitored] if monitored in m.lines.index else m.transformers_t.p0.at[peak, monitored]
print(f"brute-force lpf after removing {worst_l}: flow on {monitored} = {bf:+.2f} MW  (LODF prediction {pred:+.2f}, diff {bf-pred:.2e})")
# n.lpf_contingency: crashes if any sub-network has no branches (NW: Moy is a 1-bus island)
try:
    pc = n.lpf_contingency(peak, branch_outages=[(frame.at[worst_l, "kind"], worst_l)])
    print(f"n.lpf_contingency says: {pc[(frame.at[worst_l,'kind'], worst_l)].loc[(frame.at[monitored,'kind'], monitored)]:+.2f}")
except ValueError as e:
    print(f"n.lpf_contingency FAILED: {e!r}")
    k = load_baseline()
    k.generators_t.p = n.generators_t.p.copy(); gridkit.freeze_dispatch(k)
    k.determine_network_topology()
    lonely = k.buses.index[k.buses.sub_network.map(lambda s: len(k.sub_networks.obj[s].branches_i()) == 0)]
    for c in ("Generator", "Load"):
        k.remove(c, getattr(k, c.lower() + "s").index[getattr(k, c.lower() + "s").bus.isin(lonely)])
    k.remove("Bus", lonely)
    pc = k.lpf_contingency(peak, branch_outages=[(frame.at[worst_l, "kind"], worst_l)])
    print(f"  workaround (drop branchless island buses {list(lonely)}): lpf_contingency says "
          f"{pc[(frame.at[worst_l,'kind'], worst_l)].loc[(frame.at[monitored,'kind'], monitored)]:+.2f}")
# outage-adjusted shift factor for monitored circuit, load reference
sf_base = flowmath.shift_factors(n, monitored, reference="load", branch_frame=frame)
sf_l = flowmath.shift_factors(n, worst_l, reference="load", branch_frame=frame)
adj = sf_base["shift_factor"] + LODF.at[monitored, worst_l] * sf_l["shift_factor"]
out = pd.DataFrame({"bus": sf_base["bus"], "SF_N0": sf_base["shift_factor"], f"SF_N-1({worst_l})": adj})
out = out[n.generators.loc[out.index, "carrier"] == "wind"]
out = out.reindex(out["SF_N0"].abs().sort_values(ascending=False).index).head(15)
print(f"\nshift factors on {monitored}, N-0 vs worst single outage (top 15 wind units by |SF|):\n", out.round(4).to_string())
tick("LODF")

print("\n=== timings (s since start) ===")
for k, v in TIMES.items():
    print(f"{v:7.1f}  {k}")
