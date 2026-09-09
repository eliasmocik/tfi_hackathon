"""MASTER §10 item 8 — priority classification, re-derived independently.

Implements MASTER §2.1 from scratch against data/eirgrid_gss1_res_units.csv and
compares with out/<case>_group_units.csv. Stdlib only; imports no src module.
"""
import csv, difflib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GSS1 = ROOT / "project" / "data" / "eirgrid_gss1_res_units.csv"
OUT = ROOT / "project" / "out"
VER = ROOT / "project" / "verify"
CASES = ["WP2024s42", "WP2033s42", "WP2033s43"]
TOL = 0.05

def priority_to_class(raw):
    """MASTER §2.1 maps priority -> class. The gss1 labels are compound
    ("wind not priority", "solar uncontrolled", ...), so match on the status
    suffix rather than the whole string."""
    p = (raw or "").strip().lower()
    if "uncontrolled" in p:
        return "U"
    if "not priority" in p:
        return "N"
    if "priority" in p:
        return "P"
    if "battery" in p:
        return "B"
    return "P"

def read_csv(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

gss1 = read_csv(GSS1)

def canon(s):
    return (s or "").strip().lower().replace("'", "").replace("`", "").replace("’", "")

# index gss1 by canonical node name
by_node = {}
for r in gss1:
    by_node.setdefault(canon(r["node"]), []).append(r)

def classify(station, p_nom, psse_name, carrier=""):
    """MASTER §2.1, re-implemented. Candidate rows are restricted to the
    generator's own carrier: a wind unit must not match a battery row that
    happens to share its MEC (see Tawnaghmore 10.8 MW)."""
    cands = by_node.get(canon(station), [])
    car = canon(carrier)
    if car:
        cands = [r for r in cands if canon(r.get("gen_type", "")) == car]
    hits = []
    for r in cands:
        try:
            mec = float(r["mec_mw"])
        except (TypeError, ValueError):
            continue
        if abs(mec - p_nom) <= TOL:
            hits.append(r)
    if not hits:
        return "P", "", "", "unmatched"
    if len(hits) == 1:
        r = hits[0]
        return (priority_to_class(r["priority"]),
                r["name"], r["mec_mw"], "matched")
    names = [h["name"] for h in hits]
    best = difflib.get_close_matches(psse_name or "", names, n=1, cutoff=0.0)
    r = next(h for h in hits if h["name"] == (best[0] if best else names[0]))
    return (priority_to_class(r["priority"]),
            r["name"], r["mec_mw"], "matched_multi")

lines = ["# Verification §10.8 — priority classification re-derived", "",
         "MASTER §2.1 re-implemented from `data/eirgrid_gss1_res_units.csv` with no",
         "src module imported. Every unit is checked, not a sample of 15.", ""]
grand = {"n": 0, "class_agree": 0, "status_agree": 0}
disagreements = []

for case in CASES:
    f = OUT / f"{case}_group_units.csv"
    if not f.exists():
        lines += [f"## {case}", "", "`group_units.csv` missing.", ""]
        continue
    rows = read_csv(f)
    n = cls_ok = st_ok = 0
    for r in rows:
        n += 1
        p_nom = float(r["p_nom"])
        got_cls, got_name, got_mec, got_st = classify(
            r["station"], p_nom, r.get("psse_bus_name", ""), r.get("carrier", ""))
        if got_cls == r["class"]:
            cls_ok += 1
        else:
            disagreements.append((case, r["generator"], r["station"], r["p_nom"],
                                  r["class"], got_cls, r["match_status"], got_st))
        if got_st == r["match_status"]:
            st_ok += 1
    grand["n"] += n; grand["class_agree"] += cls_ok; grand["status_agree"] += st_ok
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    matched = sum(1 for r in rows if r["match_status"] != "unmatched")
    lines += [
        f"## {case}", "",
        f"- units: **{n}**; class agreement **{cls_ok}/{n}**; match-status agreement {st_ok}/{n}",
        f"- classes in file: {counts}",
        f"- matched (file): {matched}/{n} = {100*matched/n:.1f} %",
        "",
    ]

lines += ["## Disagreements", ""]
if disagreements:
    lines += ["| case | generator | station | p_nom | file class | rederived | file status | rederived status |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} | {e} | {f_} | {g} | {h} |"
              for a, b, c, d, e, f_, g, h in disagreements]
else:
    lines.append("None. Every unit's class reproduces exactly.")

lines += ["", "## Totals", "",
          f"- units checked: **{grand['n']}**",
          f"- class agreement: **{grand['class_agree']}/{grand['n']}**",
          f"- match-status agreement: {grand['status_agree']}/{grand['n']}", ""]

(VER / "v08_priority.md").write_text("\n".join(lines), encoding="utf-8")
print(f"units {grand['n']}  class agree {grand['class_agree']}  "
      f"status agree {grand['status_agree']}  disagreements {len(disagreements)}")
for d in disagreements[:15]:
    print("  ", d)
