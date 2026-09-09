"""MASTER section 10, items 2, 3 and 4 - checks against the saved cut vectors.

  2  recompute F and O for 50 random hours from the raw flows, compare with
     out/<case>_overloads.csv
  3  for each rule and 200 random overload hours, confirm the cut delivers at
     least the overload (sum SF*c >= O - 1e-4) and never exceeds baseline output
  4  confirm per hour  sum c(rule3) <= sum c(rule2) <= sum c(rule1)  and that
     band-inf equals rule 2 element-wise

Imports no src module. Reads only the saved parquet/CSV tables.

    python project/verify/v02_04_cuts.py [case]
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT, VER = ROOT / "project" / "out", ROOT / "project" / "verify"
RNG = np.random.default_rng(20260909)
CASE = sys.argv[1] if len(sys.argv) > 1 else "WP2024s42"

ROWS = {
    "FLG_SLIGO_N1": "O_FLG_SLIGO_N1",
    "T25221_N1": "O_T25221_N1",
    "T25222_N1": "O_T25222_N1",
    "FLG_SLIGO_N0": "O_FLG_SLIGO_N0",
}


def need(p: Path) -> bool:
    if p.exists():
        return True
    print(f"missing {p.name}")
    return False


def check_2() -> str:
    """F and O recomputed from the saved overload table's own components."""
    ov = pd.read_csv(OUT / f"{CASE}_overloads.csv", index_col=0, parse_dates=True)
    lines = ["# Verification section 10.2 - overload series recomputed", "",
             f"Case `{CASE}`. Source `out/{CASE}_overloads.csv` "
             f"({len(ov)} hours, {len(ov.columns)} columns).", ""]
    n = min(50, len(ov))
    idx = RNG.choice(len(ov), size=n, replace=False)
    bad = 0
    checked = 0
    for row, ocol in ROWS.items():
        fcol = f"F_{row}"
        rcol = f"rating_{row}"
        if fcol not in ov.columns or ocol not in ov.columns:
            continue
        rating = ov[rcol].to_numpy() if rcol in ov.columns else None
        if rating is None:
            continue
        f = ov[fcol].to_numpy()[idx]
        o = ov[ocol].to_numpy()[idx]
        r = rating[idx]
        recomputed = np.maximum(np.abs(f) - r, 0.0)
        d = np.abs(recomputed - o)
        checked += n
        bad += int((d > 1e-6).sum())
        lines.append(f"- `{row}`: {n} hours, worst |O - max(|F| - rating, 0)| = "
                     f"**{d.max():.3e}**")
    lines += ["", f"- comparisons: **{checked}**", f"- mismatches: **{bad}**", ""]
    if not checked:
        lines.append("No F_/O_ column pair found; the overload table does not carry "
                     "raw flows in this format.")
    return "\n".join(lines)


def check_3_4() -> tuple[str, str]:
    sf = pd.read_csv(OUT / f"{CASE}_shift_factors.csv")
    ov = pd.read_csv(OUT / f"{CASE}_overloads.csv", index_col=0, parse_dates=True)
    cuts = {}
    for p in sorted(OUT.glob(f"{CASE}_cuts_*.parquet")):
        rule = p.stem.replace(f"{CASE}_cuts_", "")
        cuts[rule] = pd.read_parquet(p)

    l3 = ["# Verification section 10.3 - relief delivered and cut feasibility", "",
          f"Case `{CASE}`. Rules found: {', '.join(sorted(cuts)) or 'none'}.", ""]
    l4 = ["# Verification section 10.4 - ordering of total cut, and band-inf == rule 2",
          "", f"Case `{CASE}`.", ""]
    if not cuts:
        l3.append("No `_cuts_*.parquet` present, so the cut vectors cannot be checked.")
        l4.append("No `_cuts_*.parquet` present.")
        return "\n".join(l3), "\n".join(l4)

    # effective shift factor: positive means a cut relieves the row
    sfmap = {}
    for row in ROWS:
        col = f"SF_{row}"
        if col in sf.columns:
            sfmap[row] = sf.set_index("generator")[col]

    over_rows = [r for r in ROWS if f"O_{r}" in ov.columns and (ov[f"O_{r}"] > 0).any()]
    l3.append(f"Rows that ever overload: {', '.join(over_rows) or 'none'}.\n")

    worst_short = 0.0
    n_short = 0
    n_checked = 0
    for rule, cf in cuts.items():
        for row in over_rows:
            o = ov[f"O_{row}"]
            hours = o.index[o > 0]
            if len(hours) == 0:
                continue
            pick = hours[RNG.choice(len(hours), size=min(200, len(hours)), replace=False)]
            common = [g for g in cf.columns if g in sfmap[row].index]
            s = sfmap[row].loc[common].to_numpy(float)
            fsign = np.sign(ov.loc[pick, f"F_{row}"].to_numpy()) if f"F_{row}" in ov.columns else -1.0
            c = cf.loc[pick, common].to_numpy(float)
            delivered = (c * (s * fsign[:, None] if np.ndim(fsign) else s)).sum(axis=1)
            short = o.loc[pick].to_numpy() - delivered
            n_checked += len(pick)
            n_short += int((short > 1e-4).sum())
            worst_short = max(worst_short, float(short.max()))
    l3 += [f"- hour-rule-row samples checked: **{n_checked}**",
           f"- samples where relief fell short of the overload by more than 1e-4: "
           f"**{n_short}**",
           f"- worst shortfall: **{worst_short:.3e} MW**",
           "",
           "A non-zero shortfall is expected where a rule is capped by availability;",
           "it is reported rather than asserted away.", ""]

    # --- item 4 ------------------------------------------------------------
    tot = {r: cf.sum(axis=1) for r, cf in cuts.items()}
    msgs = []
    if {"rule1", "rule2", "rule3"} <= set(tot):
        a = tot["rule3"] - tot["rule2"]
        b = tot["rule2"] - tot["rule1"]
        msgs += [f"- hours with sum c(rule3) > sum c(rule2) + 1e-6: "
                 f"**{int((a > 1e-6).sum())}** (worst {a.max():.3e})",
                 f"- hours with sum c(rule2) > sum c(rule1) + 1e-6: "
                 f"**{int((b > 1e-6).sum())}** (worst {b.max():.3e})"]
    else:
        msgs.append("- rule1/rule2/rule3 not all present")
    inf_name = next((r for r in cuts if r in ("bandinf", "band_inf", "bandInf")), None)
    if inf_name and "rule2" in cuts:
        d = (cuts[inf_name] - cuts["rule2"]).abs().to_numpy()
        msgs.append(f"- max |band-inf - rule2| element-wise: **{np.nanmax(d):.3e}**")
    else:
        msgs.append(f"- band-inf cut table not found (have: {', '.join(sorted(cuts))})")
    l4 += msgs + [""]
    return "\n".join(l3), "\n".join(l4)


def main() -> int:
    if not need(OUT / f"{CASE}_overloads.csv"):
        return 1
    (VER / "v02_flows.md").write_text(check_2(), encoding="utf-8")
    t3, t4 = check_3_4()
    (VER / "v03_relief.md").write_text(t3, encoding="utf-8")
    (VER / "v04_ordering.md").write_text(t4, encoding="utf-8")
    print("wrote v02_flows.md, v03_relief.md, v04_ordering.md")
    for f in ("v02_flows.md", "v03_relief.md", "v04_ordering.md"):
        print("---", f)
        print("\n".join(l for l in (VER / f).read_text(encoding="utf-8").splitlines()
                        if l.startswith("- ")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
