"""Build the geographic payload for the constraint-group map.

Joins the committed WP-A station results to the model's own geocoded bus
coordinates, adds the constraint elements that make the map explicable
(the monitored line, its contingency), and writes one JSON the map page reads.

Nothing is recomputed here: every station number is read from
`out/wpa_stations.csv` as committed, so the map cannot drift from the
published result. Coordinates come from the organisers' network file.

    python project/src/wp_map_data.py   ->  out/wpa_map_data.json
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "out"
NETWORK = REPO / "participant-kit" / "networks" / "WP2024_all-island"
COUNTIES = Path("C:/src/organisers/grid_TF_Wind/data/counties_osi.gpkg")

# Counties drawn on the main map. The study is North-West Constraint Group 3,
# not the whole island, so the map is framed on the region rather than the
# country: a national frame would imply a national result.
NW_COUNTIES = ["Donegal", "Sligo", "Leitrim", "Mayo", "Roscommon",
               "Cavan", "Longford", "Galway", "Monaghan", "Westmeath"]

# The constraint being managed (MASTER section 0).
MONITORED = ("2522", "4981")     # Flagford - Sligo 110 kV, the row that binds
CONTINGENCY = ("2522", "5042")   # Flagford - Srananagh 220 kV, whose loss it is


def canon(s) -> str:
    return str(s).upper().replace("'", "").replace("_", " ").strip()


def main() -> int:
    st = pd.read_csv(OUT / "wpa_stations.csv")
    sf = pd.read_csv(OUT / "WP2024s42_shift_factors.csv")
    buses = pd.read_csv(NETWORK / "buses.csv", dtype={"name": str})
    summary = json.loads((OUT / "wpa_summary.json").read_text(encoding="utf-8"))

    # station -> bus, via the shift-factor table's own station labels
    sf["st"] = sf.station.map(canon)
    bus_of = {}
    for s, d in sf.groupby("st"):
        # a station may sit on more than one bus; take the largest by capacity
        b = d.groupby("bus").p_nom.sum().idxmax()
        bus_of[s] = str(b)

    buses["name"] = buses["name"].astype(str)
    coord = buses.set_index("name")[["x", "y", "psse_name"]]

    feats = []
    for r in st.itertuples():
        key = canon(r.station)
        bus = bus_of.get(key)
        if bus is None or bus not in coord.index:
            raise SystemExit(f"no bus/coordinate for station {r.station}")
        c = coord.loc[bus]
        avail = float(r.avail_MWh)
        feats.append({
            "station": r.station.title(),
            "bus": bus,
            "psse_name": str(c.psse_name),
            "lon": float(c.x), "lat": float(c.y),
            "n_units": int(r.n_units),
            "sf": float(r.SF_eff),
            "avail_MWh": avail,
            "cut": {
                "observed": float(r.observed_cut_MWh),
                "band3": float(r.band3_cut_MWh),
                "effectiveness": float(r.effectiveness_cut_MWh),
            },
            "r": {
                "observed": float(r.observed_cut_MWh) / avail,
                "band3": float(r.band3_cut_MWh) / avail,
                "effectiveness": float(r.effectiveness_cut_MWh) / avail,
            },
        })

    # constraint elements
    def pt(b):
        c = coord.loc[b]
        return {"bus": b, "name": str(c.psse_name), "lon": float(c.x), "lat": float(c.y)}

    grid = {
        "monitored": {"from": pt(MONITORED[0]), "to": pt(MONITORED[1]),
                      "label": "Flagford–Sligo 110 kV (the row that overloads)"},
        "contingency": {"from": pt(CONTINGENCY[0]), "to": pt(CONTINGENCY[1]),
                        "label": "Flagford–Srananagh 220 kV (the outage assumed)"},
    }

    # counties, simplified enough to inline
    g = gpd.read_file(COUNTIES).to_crs(4326)
    g = g[g.name.isin(NW_COUNTIES)].copy()
    # one county comes through as a GeometryCollection (a polygon plus stray
    # line/point artefacts); keep only its polygonal parts so every feature
    # serialises with a "coordinates" key
    from shapely.geometry import MultiPolygon

    def polygons_only(geom):
        if geom.geom_type in ("Polygon", "MultiPolygon"):
            return geom
        parts = [p for p in geom.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        return MultiPolygon([q for p in parts
                             for q in (p.geoms if p.geom_type == "MultiPolygon" else [p])])

    g["geometry"] = g.geometry.map(polygons_only)
    # simplify hard and round to ~11 m: this is a schematic of where the farms
    # are, not a survey, and the page has to stay small enough to load
    g["geometry"] = g.geometry.simplify(0.02, preserve_topology=True)
    counties = json.loads(g[["name", "geometry"]].to_json())

    def round_coords(o, nd=4):
        if isinstance(o, list):
            if o and isinstance(o[0], (int, float)):
                return [round(float(v), nd) for v in o]
            return [round_coords(v, nd) for v in o]
        return o

    for f in counties["features"]:
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
        f.pop("id", None)

    # temporal: divergence trajectory over the window (real, committed data)
    traj = pd.read_csv(OUT / "wpe_trajectory.csv", parse_dates=["StartTime"])
    keep = ["observed_maxdiv_pp", "band3_maxdiv_pp", "bandinf_maxdiv_pp",
            "band0_maxdiv_pp"]
    step = max(1, len(traj) // 400)          # thin for the browser, keep the shape
    t = traj.iloc[::step]
    # The ledger needs a burn-in. r_i = cumulative cut / cumulative availability,
    # so in the first hours the denominator is a single half-hour and the spread
    # is arithmetic noise, not inequity: band 0, the most equal rule that exists,
    # peaks at 21.2 pp in row 0. Every rule's maximum sits in the first day. The
    # honest statistics are therefore taken after 48 half-hours (24 h), and the
    # page shades that stretch so the reader can see what was excluded and why.
    BURN = 48
    stats = {}
    for k in keep:
        v = traj[k].to_numpy(float)
        stats[k.replace("_maxdiv_pp", "")] = {
            "max_all": float(v.max()),
            "max_after": float(v[BURN:].max()),
            "median_after": float(np.median(v[BURN:])),
            "final": float(v[-1]),
        }
    trajectory = {
        "t": [x.isoformat() for x in t.StartTime],
        "burn_in": BURN,
        "burn_in_hours": BURN // 2,
        "stats": stats,
        **{k.replace("_maxdiv_pp", ""): [round(float(v), 4) for v in t[k]] for k in keep},
    }

    payload = {
        "meta": {
            "window": summary["window"],
            "half_hours": summary["half_hours_with_relief"],
            "units": summary["units"],
            "observed_cut_MWh": summary["observed_cut_MWh"],
            "effectiveness_saving_pct": summary["effectiveness_saving_pct"],
            "band3_saving_pct": summary["band3pp_saving_pct"],
            "source": "out/wpa_stations.csv, out/wpa_summary.json, "
                      "out/wpe_trajectory.csv (all as committed)",
        },
        "stations": feats,
        "grid": grid,
        "counties": counties,
        "trajectory": trajectory,
    }
    p = OUT / "wpa_map_data.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {p.name}  {p.stat().st_size/1024:.0f} KB  "
          f"{len(feats)} stations, {len(counties['features'])} counties, "
          f"{len(trajectory['t'])} trajectory points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
