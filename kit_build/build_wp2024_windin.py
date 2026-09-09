"""WP2024 all-island kit network + the wind and solar records the TYTFS case
flags out of service.

The shipped WP2024 kit network carries 10 MW of wind: the TYTFS winter-peak
2024 case flags 374 wind and 36 solar machine records STAT = 0 (renewables
switched out as a security assumption for the peak) and the kit's converter
keeps only STAT = 1.  This script converts the case once more with those
records kept, takes the resulting wind/solar generators (name, bus, p_nom),
and adds them to the ORGANISERS' shipped WP2024 network, so everything else
(shed generators, links, ratings) is exactly the kit's.  p_min_pu = 0 for the
added units.  Thermal STAT = 0 records stay out.

Deviation from the kit; say so on any slide that uses it.
Run from grid_TF_Wind/:  python build_wp2024_windin.py <kit WP2024_all-island.nc> <out.nc>
"""
import sys, warnings, logging
warnings.filterwarnings("ignore")
logging.getLogger("pypsa").setLevel(logging.ERROR)
import pandas as pd, pypsa
import psse, pypsa_net

RAW = "data/TYTFS2024_studyfiles/TYTFS2024_WP2024_V35.raw"
KIT = sys.argv[1] if len(sys.argv) > 1 else "participant-kit/networks/WP2024_all-island.nc"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out/WP2024_all-island_windin.nc"

case = psse.read_raw(RAW)
bus_name = dict(zip(case.bus["I"], case.bus["NAME"]))
df = case.generator
carrier = pd.Series([pypsa_net.carrier_of(str(bus_name.get(i, ""))) for i in df["I"]], index=df.index)
keep = ((df["STAT"] == 1) | carrier.isin(["wind", "solar"])).values
_orig = psse.generators
psse.generators = lambda c, in_service=True: _orig(c, in_service=False)[keep]
model = pypsa_net.build(case, min_kv=pypsa_net.TRANSMISSION_KV)
full = model.network if hasattr(model, "network") else model

n = pypsa.Network(KIT)
extra = full.generators[full.generators.carrier.isin(["wind", "solar"]) & ~full.generators.index.isin(n.generators.index)]
extra = extra[extra.bus.astype(str).isin(n.buses.index.astype(str))]
n.add("Generator", extra.index, bus=extra.bus.astype(str).values, carrier=extra.carrier.values,
      p_nom=extra.p_nom.values, p_min_pu=0.0, p_max_pu=1.0,
      marginal_cost=[pypsa_net.PLACEHOLDER_COST[c] for c in extra.carrier])
n.generators.loc[extra.index, "switched_in"] = True
n.generators["switched_in"] = n.generators["switched_in"].fillna(False).astype(bool)

g = n.generators[n.generators.carrier != "load shedding"]
print("p_nom by carrier:", g.groupby("carrier").p_nom.sum().round(0).to_dict())
print("added:", len(extra), "of", int((full.generators.carrier.isin(["wind", "solar"])).sum()), "wind/solar records in the case")
nw = ["1341", "1571", "3591", "4991", "5361", "4071", "5191", "51911", "1701", "17010", "4981", "1931", "1631", "3581"]
print("NW wind MW by bus:", g[g.bus.isin(nw) & (g.carrier == "wind")].groupby("bus").p_nom.sum().round(1).to_dict())
n.export_to_netcdf(OUT)
print("saved", OUT, len(n.buses), "buses", len(n.generators), "generators")
