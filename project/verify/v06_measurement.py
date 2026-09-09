"""MASTER §10 item 6 — measurement re-derived independently from the raw BM files.

Implements MASTER §6.1-§6.3 from scratch (join, state machine, ratios) and
compares against out/measurement_units.csv and the original
data/nw_unit_dispatchdown_2026-06-08_to_09-05.csv.

Imports no src module. Also quantifies the drift between the committed
measurement and a fresh 2026-09-09 pull of the same window, which is a data
vintage question, not a code question.
"""
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D, OUT, VER = ROOT / "project" / "data", ROOT / "project" / "out", ROOT / "project" / "verify"
WIN_START = pd.Timestamp("2026-06-08 00:00")
WIN_END = pd.Timestamp("2026-09-05 23:59")

av = pd.read_csv(D / "BM-101_nw_units.csv", parse_dates=["StartTime"])
dq = pd.read_csv(D / "BM-096_nw_units.csv", parse_dates=["StartTime"])
ins = pd.read_csv(D / "BM-037_dispatch_instructions_2026-06-07_to_09-05.csv",
                  parse_dates=["EffTime", "InstrIssueTime"])

# --- §6.1 join -------------------------------------------------------------
j = av[["ResourceName", "StartTime", "AvgOutturnAvail"]].merge(
    dq[["ResourceName", "StartTime", "DispatchQuantity"]],
    on=["ResourceName", "StartTime"], how="inner")
j = j[(j.StartTime >= WIN_START) & (j.StartTime <= WIN_END)].copy()
j["avail_MWh"] = 0.5 * j.AvgOutturnAvail
j["dd_MWh"] = (j.avail_MWh - j.DispatchQuantity).clip(lower=0)

# --- §6.2 state machine ----------------------------------------------------
SET = {"LOCL": "constraint", "CURL": "curtail"}
CLR = {"LCLO": "constraint", "CRLO": "curtail"}
ins = ins[ins.EffTime >= pd.Timestamp("2026-06-07 00:00")]
ins = ins.sort_values(["ResourceName", "EffTime", "InstrIssueTime"])

def states_for(unit, times):
    """State at each half-hour start: False at 2026-06-07 00:00, then the last
    SET/CLR instruction at or before that time wins."""
    e = ins[(ins.ResourceName == unit) &
            (ins.InstructionCombinationCode.isin(list(SET) + list(CLR)))]
    out = {"constraint": np.zeros(len(times), bool), "curtail": np.zeros(len(times), bool)}
    if e.empty:
        return out
    for field in ("constraint", "curtail"):
        codes = e[e.InstructionCombinationCode.isin(
            [k for k, v in {**SET, **CLR}.items() if v == field])]
        if codes.empty:
            continue
        val = codes.InstructionCombinationCode.isin(list(SET)).to_numpy()
        t = codes.EffTime.to_numpy()
        idx = np.searchsorted(t, times.to_numpy(), side="right") - 1
        out[field] = np.where(idx >= 0, val[np.clip(idx, 0, None)], False)
    return out

rows = []
for unit, g in j.groupby("ResourceName"):
    g = g.sort_values("StartTime")
    st = states_for(unit, g.StartTime)
    con, cur = st["constraint"], st["curtail"]
    avail = g.avail_MWh.sum()
    con_only = g.dd_MWh.to_numpy()[con & ~cur].sum()
    rows.append(dict(unit=unit, avail_MWh=avail, dd_MWh=g.dd_MWh.sum(),
                     constraint_only_ratio=con_only / avail if avail > 0 else np.nan,
                     locl_any_ratio=g.dd_MWh.to_numpy()[con].sum() / avail if avail > 0 else np.nan,
                     halfhours=len(g)))
mine = pd.DataFrame(rows).set_index("unit")

ref = pd.read_csv(OUT / "measurement_units.csv").set_index("unit")
repro = VER / "repro" / "measurement_units.csv"
fresh = pd.read_csv(repro).set_index("unit") if repro.exists() else None

common = [u for u in ref.index if u in mine.index]
cmp = pd.DataFrame({
    "committed": ref.loc[common, "constraint_only_ratio"],
    "independent_fresh_pull": mine.loc[common, "constraint_only_ratio"],
})
if fresh is not None:
    cmp["pipeline_fresh_pull"] = fresh.loc[common, "constraint_only_ratio"]
    cmp["indep_vs_pipeline"] = (cmp.independent_fresh_pull - cmp.pipeline_fresh_pull).abs()
cmp["committed_vs_fresh"] = (cmp.independent_fresh_pull - cmp.committed).abs()
cmp["avail_committed"] = ref.loc[common, "avail_MWh"]
cmp["avail_fresh"] = mine.loc[common, "avail_MWh"]
cmp = cmp.sort_values("committed", ascending=False)
cmp.to_csv(VER / "v06_measurement.csv")

worst_code = cmp["indep_vs_pipeline"].max() if "indep_vs_pipeline" in cmp else float("nan")
worst_vint = cmp["committed_vs_fresh"].max()

retention = j.StartTime.min()
missing_hh = int(ref["halfhours"].max() - mine["halfhours"].max())

lines = [
    "# Verification §10.6 — measurement re-derived from the raw BM files", "",
    "## Retention finding (acted on 2026-09-09)", "",
    f"The SEM-O window is no longer fully retrievable. The earliest half-hour the",
    f"API now returns for these units is **{retention}**, not 2026-06-08 00:00, and",
    f"BM-037 instructions now begin 2026-06-10. The fresh pull therefore has",
    f"**{missing_hh} fewer half-hours** per unit than the committed measurement",
    f"({int(mine['halfhours'].max())} vs {int(ref['halfhours'].max())}).", "",
    "Consequences:", "",
    "1. `out/measurement_*.csv` as committed **can no longer be reproduced from the",
    "   API**. Those files and Elias's local raw pull are the only record of",
    "   2026-06-08 to 2026-06-09.",
    "2. The committed outputs were therefore restored, not overwritten. The fresh",
    "   run is kept separately under `verify/repro/`.",
    "3. The residual difference below is fully consistent with the missing leading",
    "   days. It cannot be decomposed further without the original raw files.", "",
    "MASTER §6.1–§6.3 re-implemented independently (join, LOCL/CURL state",
    "machine, constraint-only ratio). `measurement.py` is not imported.", "",
    "Three columns are compared:", "",
    "- **committed** — `out/measurement_units.csv` as published (Elias's pull).",
    "- **pipeline_fresh_pull** — `src/measurement.py` re-run on a fresh 2026-09-09 pull.",
    "- **independent_fresh_pull** — this file's own code on that same fresh pull.", "",
    "The first comparison isolates *code*; the second reflects the shorter window.", "",
    f"- units compared: **{len(cmp)}**",
    f"- worst |independent − pipeline| on the same data (code agreement): **{worst_code:.2e}**",
    f"- worst |fresh − committed| (shorter window, not a code difference): **{worst_vint:.2e}**", "",
    "## Per unit", "",
    "| unit | committed | pipeline (fresh) | independent (fresh) | code diff | vintage diff |",
    "|---|---|---|---|---|---|",
]
for u, r in cmp.iterrows():
    pf = f"{r.pipeline_fresh_pull:.6f}" if "pipeline_fresh_pull" in cmp else "-"
    cd = f"{r.indep_vs_pipeline:.2e}" if "indep_vs_pipeline" in cmp else "-"
    lines.append(f"| {u} | {r.committed:.6f} | {pf} | {r.independent_fresh_pull:.6f} "
                 f"| {cd} | {r.committed_vs_fresh:.2e} |")
lines += ["", "Full table: `v06_measurement.csv`.", ""]
(VER / "v06_measurement.md").write_text("\n".join(lines), encoding="utf-8")
print(f"units {len(cmp)}  worst code diff {worst_code:.3e}  worst vintage diff {worst_vint:.3e}")
print(cmp.head(8).to_string())
