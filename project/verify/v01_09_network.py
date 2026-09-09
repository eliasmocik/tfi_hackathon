"""MASTER section 10, items 1 and 9 - network-level checks.

  1  re-derive the LODF for the monitored rows from the bus PTDF and compare
     with the kit's own value and with pypsa's BODF, both of which the saved
     table already carries
  9  sanity: total cut MWh under rule 1 against total overload MWh (the ratio
     should be of order 1 / mean shift factor), and the tie link's share of
     hours at its cap

Imports no src module: both quantities are formed from the saved parquet and
CSV tables.

    python project/verify/v01_09_network.py [case]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "project"
OUT, VER = PROJ / "out", PROJ / "verify"

CASE = sys.argv[1] if len(sys.argv) > 1 else "WP2024s42"
CONTINGENCY = "2522-5042-1"          # Flagford-Srananagh 220 kV (MASTER section 0)
BUS_A, BUS_B = "2522", "5042"        # its end buses

ROW_FOR_ELEMENT = {
    "2521-4981-1": "FLG_SLIGO_N1",
    "T2522-2521-25221-1-w1": "T25221_N1",
    "T2522-2521-25222-2-w1": "T25222_N1",
}


def lodf_report() -> str:
    """LODF re-derived from the bus PTDF, independently of the kit and of pypsa.

    For an outage of branch k with end buses (a, b) and a monitored row l,

        LODF[l, k] = (H[l, a] - H[l, b]) / (1 - (H[k, a] - H[k, b]))

    where H is the bus PTDF. Both H tables are read from the regenerated
    parquet, so no project function forms the quantity.
    """
    L = ["# Verification section 10.1 - LODF re-derived from the PTDF", "",
         f"Case `{CASE}`. Contingency `{CONTINGENCY}`, end buses "
         f"{BUS_A} and {BUS_B}.", "",
         "LODF[l,k] = (H[l,a] - H[l,b]) / (1 - (H[k,a] - H[k,b])), H the bus PTDF.",
         ""]

    fp, rp = OUT / f"{CASE}_ptdf_full.parquet", OUT / f"{CASE}_ptdf_rows.parquet"
    if not (fp.exists() and rp.exists()):
        L.append("PTDF parquet tables absent; run `src/run_engine.py` first.")
        return "\n".join(L)

    H = pd.read_parquet(fp)
    Hr = pd.read_parquet(rp)
    if CONTINGENCY not in H.index:
        L.append(f"Contingency `{CONTINGENCY}` is not in the PTDF index.")
        return "\n".join(L)

    denom = 1.0 - (float(H.at[CONTINGENCY, BUS_A]) - float(H.at[CONTINGENCY, BUS_B]))
    saved = pd.read_csv(OUT / f"{CASE}_lodf.csv")
    saved_denom = float(saved.denom.iloc[0])

    L += [
        f"- re-derived denominator: **{denom:.15f}**",
        f"- denominator in `{CASE}_lodf.csv`: **{saved_denom:.15f}** "
        f"(difference {abs(denom - saved_denom):.3e})",
        "",
        "| monitored row | re-derived | lodf_kit | bodf_pypsa | max abs diff |",
        "|---|---|---|---|---|",
    ]
    # Use the intact bus PTDF (ptdf_full) keyed by the branch's own name.
    # ptdf_rows is NOT the intact sensitivity: it is already the
    # post-contingency row sensitivity, so its bus difference equals the LODF
    # and dividing it again would double-count the outage.
    worst = 0.0
    for elem, key in ROW_FOR_ELEMENT.items():
        if elem not in H.index:
            L.append(f"| {elem} | absent from the intact PTDF | - | - | - |")
            continue
        mine = (float(H.at[elem, BUS_A]) - float(H.at[elem, BUS_B])) / denom
        hit = saved[saved.element == elem]
        kit = float(hit.lodf_kit.iloc[0]) if len(hit) else float("nan")
        pyp = float(hit.bodf_pypsa.iloc[0]) if len(hit) else float("nan")
        d = float(np.nanmax([abs(mine - kit), abs(mine - pyp)]))
        worst = max(worst, d)
        L.append(f"| {elem} | {mine:.15f} | {kit:.15f} | {pyp:.15f} | {d:.3e} |")

    L += ["", f"- worst |re-derived - saved|: **{worst:.3e}**", "",
          "The saved table already carries the kit's own LODF and pypsa's BODF and",
          "reports them agreeing to 4e-13. This is a third, independent route to the",
          "same three numbers.", "",
          "Note for a future verifier: `ptdf_rows.parquet` is the post-contingency",
          "row sensitivity, so its bus difference already equals the LODF. The",
          "intact bus PTDF for this derivation is `ptdf_full.parquet`, keyed by the",
          "branch name.", ""]
    return "\n".join(L)


def sanity_report() -> str:
    L = ["# Verification section 10.9 - sanity", "", f"Case `{CASE}`.", ""]
    stats = json.loads((OUT / f"{CASE}_overload_stats.json").read_text(encoding="utf-8"))
    ov_MWh = stats.get("total_overload_MWh_all_rows", float("nan"))

    # rules_summary.json carries solver diagnostics, not energies; the cut
    # totals live in summary.csv
    cut1 = float("nan")
    sm = OUT / f"{CASE}_summary.csv"
    if sm.exists():
        d = pd.read_csv(sm).set_index("rule")
        if "rule1" in d.index and "cut_MWh" in d.columns:
            cut1 = float(d.loc["rule1", "cut_MWh"])

    sf = pd.read_csv(OUT / f"{CASE}_shift_factors.csv")
    sfe = (-sf["SF_FLG_SLIGO_N1"]).to_numpy(float)
    mean_sf = float(np.average(sfe, weights=sf.p_nom.clip(lower=1e-9)))
    ratio = cut1 / ov_MWh if ov_MWh else float("nan")

    L += [
        f"- total overload energy, all rows: **{ov_MWh:,.1f} MWh** "
        f"(`{CASE}_overload_stats.json`)",
        f"- total cut under rule 1: **{cut1:,.1f} MWh**",
        f"- ratio cut / overload: **{ratio:.3f}**",
        f"- capacity-weighted mean effective shift factor: **{mean_sf:.4f}**, "
        f"so 1 / mean SF = **{1 / mean_sf:.3f}**",
        "",
        "MASTER section 10.9 expects the ratio to be of order 1 / mean SF: cutting "
        "1 MW of wind removes only SF MW of flow, so relieving 1 MWh of overload "
        "costs about 1/SF MWh of spill.",
        f"- agreement: ratio / (1/mean SF) = **{ratio * mean_sf:.3f}** "
        f"(1.0 would be exact)",
        "",
    ]

    fp = OUT / f"{CASE}_flows.parquet"
    if fp.exists():
        fl = pd.read_parquet(fp)
        tie = [c for c in fl.columns
               if "STRABANE" in str(c).upper() or "PST" in str(c).upper()]
        if tie:
            v = fl[tie[0]].abs()
            cap = v.max()
            share = float((v >= cap - 1e-6).mean())
            L.append(f"- tie link `{tie[0]}`: |flow| max {cap:.2f} MW, at cap in "
                     f"**{100 * share:.1f} %** of hours")
        else:
            L.append("- tie link column not found in flows.parquet")
    else:
        L.append("- `flows.parquet` absent, so the tie-link cap share is not checked "
                 "here; ENGINE_NOTES.md reports it at 100 % of hours in every case")
    L.append("")
    return "\n".join(L)


def main() -> int:
    (VER / "v09_sanity.md").write_text(sanity_report(), encoding="utf-8")
    (VER / "v01_lodf.md").write_text(lodf_report(), encoding="utf-8")
    for f in ("v09_sanity.md", "v01_lodf.md"):
        print("---", f)
        print("\n".join(l for l in (VER / f).read_text(encoding="utf-8").splitlines()
                        if l.startswith("- ") or l.startswith("|")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
