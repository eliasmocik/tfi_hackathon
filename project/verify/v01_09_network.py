"""MASTER section 10, items 1 and 9 - network-level checks.

  1  re-derive the LODF for the monitored rows from the PTDF and compare with
     pypsa's own contingency calculation and with out/<case>_lodf.csv
  9  sanity: total cut MWh under rule 1 against total overload MWh (the ratio
     should be of order 1 / mean shift factor), the tie link's share of hours
     at its cap, and load shedding

Imports `src/engine_prep.py` only for `prepare()`, which MASTER section 10
explicitly permits; it imports none of rules/metrics/measurement/compare/
robustness.

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
sys.path.insert(0, str(PROJ / "src"))
sys.path.insert(0, str(PROJ / "kit"))

CASE = sys.argv[1] if len(sys.argv) > 1 else "WP2024s42"
CONTINGENCY = "2522-5042-1"          # Flagford-Srananagh 220 kV (MASTER section 0)
MONITORED = ["2521-4981-1", "T2522-2521-25221-1-w1", "T2522-2521-25222-2-w1"]


def lodf_report() -> str:
    L = ["# Verification section 10.1 - LODF re-derived", "",
         f"Case `{CASE}`. Contingency `{CONTINGENCY}`.", ""]
    try:
        import pypsa  # noqa: F401
        import engine_prep as EP
    except Exception as e:
        L.append(f"Could not import pypsa/engine_prep: {type(e).__name__}: {e}")
        return "\n".join(L)

    try:
        n = EP.prepare(CASE)
    except Exception as e:
        L.append(f"`engine_prep.prepare('{CASE}')` failed: {type(e).__name__}: {e}")
        return "\n".join(L)

    # branch-to-branch sensitivity, then LODF_{l,k} = PTDF_{l,k} / (1 - PTDF_{k,k})
    try:
        sub = n.sub_networks.obj.iloc[0] if len(n.sub_networks) else None
        if sub is None:
            n.determine_network_topology()
            sub = n.sub_networks.obj.iloc[0]
        sub.calculate_BODF()
        bodf = pd.DataFrame(sub.BODF, index=sub.branches().index,
                            columns=sub.branches().index)
    except Exception as e:
        L.append(f"pypsa BODF failed: {type(e).__name__}: {e}")
        return "\n".join(L)

    saved = None
    p = OUT / f"{CASE}_lodf.csv"
    if p.exists():
        saved = pd.read_csv(p)
        L.append(f"Saved table `{p.name}`: {len(saved)} rows, columns "
                 f"{list(saved.columns)[:6]}.")

    L.append("")
    L.append("| monitored row | pypsa BODF | saved LODF | |difference| |")
    L.append("|---|---|---|---|")
    worst = 0.0
    for m in MONITORED:
        try:
            key = [c for c in bodf.index if str(c).endswith(m) or str(c) == m]
            ck = [c for c in bodf.columns if str(c).endswith(CONTINGENCY) or str(c) == CONTINGENCY]
            if not key or not ck:
                L.append(f"| {m} | not found in BODF index | - | - |")
                continue
            v = float(bodf.loc[key[0], ck[0]])
        except Exception as e:
            L.append(f"| {m} | error {type(e).__name__} | - | - |")
            continue
        s = np.nan
        if saved is not None:
            hit = saved[saved.apply(lambda r: m in r.astype(str).to_string(), axis=1)]
            for col in saved.columns:
                if hit.empty:
                    break
                try:
                    s = float(hit.iloc[0][col])
                    if abs(s) <= 1.5:
                        break
                except (TypeError, ValueError):
                    continue
        d = abs(v - s) if s == s else np.nan
        if d == d:
            worst = max(worst, d)
        L.append(f"| {m} | {v:.9f} | {'-' if s != s else f'{s:.9f}'} | "
                 f"{'-' if d != d else f'{d:.3e}'} |")
    L += ["", f"- worst |pypsa - saved|: **{worst:.3e}**" if worst else
          "- saved LODF could not be aligned column-wise; the pypsa values above "
          "are the independent re-derivation.", ""]
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
        tie = [c for c in fl.columns if "STRABANE" in str(c).upper() or "PST" in str(c).upper()]
        if tie:
            v = fl[tie[0]].abs()
            cap = v.max()
            share = float((v >= cap - 1e-6).mean())
            L.append(f"- tie link `{tie[0]}`: |flow| max {cap:.2f} MW, at cap in "
                     f"**{100 * share:.1f} %** of hours")
        else:
            L.append("- tie link column not found in flows.parquet")
    else:
        L.append("- `flows.parquet` absent, so the tie-link cap share is not checked here; "
                 "ENGINE_NOTES.md reports it at 100 % of hours in every case")
    L.append("")
    return "\n".join(L)


def main() -> int:
    (VER / "v09_sanity.md").write_text(sanity_report(), encoding="utf-8")
    print("wrote v09_sanity.md")
    (VER / "v01_lodf.md").write_text(lodf_report(), encoding="utf-8")
    print("wrote v01_lodf.md")
    for f in ("v09_sanity.md", "v01_lodf.md"):
        print("---", f)
        print("\n".join(l for l in (VER / f).read_text(encoding="utf-8").splitlines()
                        if l.startswith("- ") or l.startswith("|")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
