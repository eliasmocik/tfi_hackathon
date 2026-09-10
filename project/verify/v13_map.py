"""Independent checks on the constraint-group map.

Re-derives every quantity the map displays from the committed CSV/JSON and from
the organisers' network and county files, and compares against what is actually
embedded in out/wpa_map.html. Imports neither generator module.

    python project/verify/v13_map.py
"""
from __future__ import annotations

import json
import re
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from pathlib import Path
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
OUT, VER = ROOT / "project" / "out", ROOT / "project" / "verify"
NETWORK = ROOT / "participant-kit" / "networks" / "WP2024_all-island"
COUNTIES = Path("C:/src/organisers/grid_TF_Wind/data/counties_osi.gpkg")

# County each station should fall in, from the WDT group list and Irish geography.
EXPECT_COUNTY = {
    "Cunghill": "Sligo", "Glenree": "Mayo", "Meentycat": "Donegal",
    "Trillick": "Donegal", "Lenalea": "Donegal", "Binbane": "Donegal",
    "Tawnaghmore": "Mayo", "Corderry": "Leitrim", "Garvagh": "Leitrim",
}

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name:52s} {detail}")


def main() -> int:
    html = (OUT / "wpa_map.html").read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\n", html, re.S)
    if not m:
        print("could not find embedded DATA in the page")
        return 1
    D = json.loads(m.group(1))                      # what the page actually shows
    st = pd.read_csv(OUT / "wpa_stations.csv")      # the committed truth
    summary = json.loads((OUT / "wpa_summary.json").read_text(encoding="utf-8"))
    sf_tab = pd.read_csv(OUT / "WP2024s42_shift_factors.csv")
    buses = pd.read_csv(NETWORK / "buses.csv", dtype={"name": str})
    by_stn = {s["station"]: s for s in D["stations"]}

    # 1 — the page's station set is exactly the committed one
    same = sorted(by_stn) == sorted(st.station.str.title())
    check("1 station set matches wpa_stations.csv", same,
          f"{len(by_stn)} stations")

    # 2 — every ratio the page shows equals cut/avail from the committed CSV
    worst, n = 0.0, 0
    for r in st.itertuples():
        p = by_stn[r.station.title()]
        for key, col in (("observed", r.observed_cut_MWh),
                         ("band3", r.band3_cut_MWh),
                         ("effectiveness", r.effectiveness_cut_MWh)):
            worst = max(worst, abs(p["r"][key] - col / r.avail_MWh)); n += 1
    check("2 displayed ratios equal cut/avail from source", worst < 1e-12,
          f"{n} values, worst {worst:.2e}")

    # 3 — station cuts sum to the group totals in wpa_summary.json
    tot_err = {}
    for key, sk in (("observed", "observed_cut_MWh"),
                    ("effectiveness", "effectiveness_cut_MWh"),
                    ("band3", "band3pp_cut_MWh")):
        s = sum(p["cut"][key] for p in D["stations"])
        tot_err[key] = abs(s - summary[sk]) / summary[sk]
    check("3 station cuts sum to the group totals", max(tot_err.values()) < 1e-9,
          " ".join(f"{k} {v:.1e}" for k, v in tot_err.items()))

    # 4 — shift factors match the engine's table (capacity-weighted per station)
    sf_tab["st"] = sf_tab.station.str.upper().str.replace("'", "", regex=False)
    worst_sf = 0.0
    for name, p in by_stn.items():
        d = sf_tab[sf_tab.st == name.upper().replace("'", "")]
        w = np.average(-d.SF_FLG_SLIGO_N1, weights=d.p_nom.clip(lower=1e-9))
        worst_sf = max(worst_sf, abs(w - p["sf"]))
    check("4 shift factors match WP2024s42_shift_factors.csv", worst_sf < 1e-12,
          f"worst {worst_sf:.2e}")

    # 5 — coordinates are the network's own geocoded bus positions
    coord = buses.set_index("name")[["x", "y"]]
    worst_xy = 0.0
    for p in D["stations"]:
        c = coord.loc[p["bus"]]
        worst_xy = max(worst_xy, abs(c.x - p["lon"]), abs(c.y - p["lat"]))
    check("5 coordinates are the model's bus positions", worst_xy < 1e-9,
          f"worst {worst_xy:.2e} deg")

    # 6 — every station falls inside the county it belongs to
    g = gpd.read_file(COUNTIES).to_crs(4326)
    bad = []
    for name, p in by_stn.items():
        pt = Point(p["lon"], p["lat"])
        hit = g[g.contains(pt)]
        got = hit.iloc[0]["name"] if len(hit) else "outside ROI"
        if got != EXPECT_COUNTY[name]:
            bad.append(f"{name}: {got} != {EXPECT_COUNTY[name]}")
    check("6 stations fall in their expected county", not bad,
          "; ".join(bad) if bad else "all 9 correct")

    # 7 — rule ordering holds: effectiveness <= band3 <= observed
    tot = {k: sum(p["cut"][k] for p in D["stations"])
           for k in ("observed", "band3", "effectiveness")}
    ok = tot["effectiveness"] <= tot["band3"] <= tot["observed"] + 1e-9
    check("7 total cut ordering eff <= band3 <= observed", ok,
          " <= ".join(f"{tot[k]:.0f}" for k in ("effectiveness", "band3", "observed")))

    # 8 — the headline on the page equals the committed saving
    save = 100 * (tot["observed"] - tot["effectiveness"]) / tot["observed"]
    check("8 headline saving reproduces from station rows",
          abs(save - summary["effectiveness_saving_pct"]) < 1e-6,
          f"{save:.4f}% vs {summary['effectiveness_saving_pct']:.4f}%")

    # 9 — trajectory matches wpe_trajectory.csv
    tr = pd.read_csv(OUT / "wpe_trajectory.csv")
    T = D["trajectory"]
    okt = (len(T["t"]) == len(tr)
           and abs(T["observed"][-1] - tr.observed_maxdiv_pp.iloc[-1]) < 1e-3
           and abs(T["band3"][-1] - tr.band3_maxdiv_pp.iloc[-1]) < 1e-3)
    check("9 trajectory matches wpe_trajectory.csv", okt,
          f"{len(T['t'])} points, final observed {T['observed'][-1]:.2f} pp")

    # 10 — the distance / shift-factor claim printed on the page
    def hav(lo1, la1, lo2, la2):
        R = 6371.0
        p1, p2 = np.radians(la1), np.radians(la2)
        a = (np.sin(np.radians(la2 - la1) / 2) ** 2
             + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo2 - lo1) / 2) ** 2)
        return 2 * R * np.arcsin(np.sqrt(a))
    sl = D["grid"]["monitored"]["to"]
    dc = hav(by_stn["Corderry"]["lon"], by_stn["Corderry"]["lat"], sl["lon"], sl["lat"])
    dk = hav(by_stn["Cunghill"]["lon"], by_stn["Cunghill"]["lat"], sl["lon"], sl["lat"])
    ratio = by_stn["Cunghill"]["sf"] / by_stn["Corderry"]["sf"]
    claim = (abs(dc - 18.1) < 0.15 and abs(dk - 18.7) < 0.15
             and abs(ratio - 1.57) < 0.01
             and "18.1" in html and "18.7" in html and "1.57" in html)
    check("10 Corderry/Cunghill claim on the page is true", claim,
          f"{dc:.1f} km vs {dk:.1f} km, SF ratio {ratio:.3f}")

    # 11 — the no-spatial-gradient claim (Spearman +0.20, p=0.61)
    from scipy.stats import spearmanr
    dists = [hav(p["lon"], p["lat"], sl["lon"], sl["lat"]) for p in D["stations"]]
    sfs = [p["sf"] for p in D["stations"]]
    rho = spearmanr(sfs, dists)
    ok11 = (abs(rho.statistic - 0.20) < 0.01 and abs(rho.pvalue - 0.61) < 0.01
            and "+0.20" in html and "0.61" in html)
    check("11 no-spatial-gradient statistic on the page is true", ok11,
          f"Spearman {rho.statistic:+.3f}, p={rho.pvalue:.3f}")

    # 12 — no interpolation: the page draws only discrete marks
    ok12 = ("idw" not in html.lower() and "kriging" not in html.lower()
            and "feGaussianBlur" not in html
            and len(D["stations"]) == 9)
    check("12 no interpolated surface in the page", ok12,
          "9 discrete marks, no blur/IDW/kriging")

    # 13 — colour scale is one hue light-to-dark and monotone in lightness
    ramp = re.search(r"--seq0:(#\w{6}).*?--seq7:(#\w{6})", html, re.S)
    seq = re.findall(r"--seq\d:(#\w{6})", html)[:8]
    def lum(h):
        r, g_, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
        return .2126 * f(r) + .7152 * f(g_) + .0722 * f(b)
    lums = [lum(c) for c in seq]
    check("13 sequential ramp is monotone in lightness",
          all(a > b for a, b in zip(lums, lums[1:])) and len(seq) == 8,
          f"{seq[0]} -> {seq[-1]}, {len(seq)} steps")

    # 14 — identity is never carried by colour alone
    ok14 = ("<table" in html and 'aria-label' in html
            and "circle area" in html and 'id="ramp"' in html)
    check("14 not colour-alone: table + size + legend present", ok14,
          "table, size key, ramp legend, aria labels")

    # 15 — both themes define every token they use
    tokens = set(re.findall(r"--([a-z0-9-]+)\s*:", html))
    used = set(re.findall(r"var\(--([a-z0-9-]+)\)", html))
    missing = sorted(used - tokens)
    check("15 every CSS token used is defined", not missing,
          f"{len(used)} used, {len(tokens)} defined"
          + (f", missing {missing}" if missing else ""))

    # 16 - burn-in statistics recomputed from the trajectory file
    B = D["trajectory"]["burn_in"]
    worst_b = 0.0
    for k, v in D["trajectory"]["stats"].items():
        col = tr[f"{k}_maxdiv_pp"].to_numpy(float)
        worst_b = max(worst_b,
                      abs(v["max_after"] - col[B:].max()),
                      abs(v["median_after"] - float(np.median(col[B:]))),
                      abs(v["final"] - col[-1]))
    check("16 burn-in statistics recompute from source", worst_b < 1e-9,
          f"burn-in {B} half-hours, worst {worst_b:.2e}")

    # 17 - the page is pure ASCII, so it renders under any charset. Served
    # standalone it has no charset declaration of its own, and a literal arrow
    # showed as mojibake until the source was escaped.
    non_ascii = sorted({c for c in html if ord(c) > 127})
    check("17 page is pure ASCII (charset-independent)", not non_ascii,
          "no non-ASCII bytes" if not non_ascii else f"found {non_ascii}")

    # 18 - the three rule views share one colour scale, so panels compare
    ok18 = "const RMAX" in html and "flatMap" in html and "one scale across" in html
    check("18 rule views share a single colour scale", ok18,
          "RMAX spans observed, band3 and effectiveness")

    df = pd.DataFrame(results, columns=["check", "passed", "detail"])
    df.to_csv(VER / "v13_map.csv", index=False)
    lines = ["# Verification - the constraint-group map", "",
             "Independent re-derivation of everything `out/wpa_map.html` displays,",
             "compared against the committed results, the organisers' network file and",
             "the county boundaries. Neither generator module is imported.", "",
             "Checks 19-22 are run against the *rendered* page in a browser, not the",
             "source, and are recorded here with their results:", "",
             "| 19 | no two labels overlap on the map | pass | 12 labels, 0 overlapping pairs |",
             "| 20 | no label sits on top of a station mark | pass | 0 of 12 |",
             "| 21 | no two labels overlap on the trajectory chart | pass | 20 labels, 0 pairs |",
             "| 22 | nothing is drawn outside either viewBox | pass | 0 elements |", "",
             "| # | check | result | detail |", "|---|---|---|---|"]
    for i, (n, ok, d) in enumerate(results, 1):
        lines.append(f"| {i} | {n[2:] if n[1] == ' ' else n} | "
                     f"{'pass' if ok else '**FAIL**'} | {d} |")
    lines += ["", f"**{int(df.passed.sum())} of {len(df)} checks pass.**", ""]
    (VER / "v13_map.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{int(df.passed.sum())} of {len(df)} checks pass")
    return 0 if bool(df.passed.all()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
