"""Assemble project/verify/VERIFICATION.md from the individual check reports.

MASTER section 10 lists ten checks. Each has its own script and its own
markdown output in this directory; this collects them into the single document
section 10 asks for, including item 10 - the list of every discrepancy with
its size and which numbers in RESULTS.md it touches.

A check with no report file is reported as not run, with the reason, rather
than quietly omitted.

    python project/verify/build_verification.py
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

VER = Path(__file__).resolve().parent
ROOT = VER.parents[1]

# item -> (short title, report file, one-line verdict source)
CHECKS = {
    1: ("LODF for the monitored rows, re-derived and checked against "
        "pypsa calculate_BODF", "v01_lodf.md"),
    2: ("F and O recomputed from raw flows for 50 random hours", "v02_flows.md"),
    3: ("Sum SF*c >= O and c <= p0 for each rule over 200 random overload hours",
        "v03_relief.md"),
    4: ("Per-hour ordering of total cut, and band-inf == rule 2", "v04_ordering.md"),
    5: ("Jain, Gini, D and the ratios recomputed from farm_r.csv", "v05_metrics.md"),
    6: ("Measurement recomputed from the raw BM files with independent code",
        "v06_measurement.md"),
    7: ("Every WDT quotation found verbatim; group station lists checked",
        "v07_quotes.md"),
    8: ("Priority classification checked against eirgrid_gss1_res_units.csv",
        "v08_priority.md"),
    9: ("Sanity: cut MWh vs overload MWh, tie link at cap, load shedding",
        "v09_sanity.md"),
    10: ("Every discrepancy with its size, and which RESULTS.md numbers it affects",
         None),
    11: ("The band rule re-implemented from MASTER section 4 and compared with "
         "cuts_band3.parquet (the HANDOFF's most valuable check)", "v11_band_rule.md"),
}


def first_summary(text: str, n: int = 6) -> list[str]:
    """The report's own bullet summary, if it has one."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- ") or s.startswith("**"):
            out.append(s)
        if len(out) >= n:
            break
    return out


def main() -> int:
    L = [
        "# VERIFICATION - independent checks of the pro-rata project",
        "",
        f"Assembled by `verify/build_verification.py` on "
        f"{dt.date.today().isoformat()}.",
        "",
        "MASTER section 10 requires these checks to be done by an agent that does",
        "**not** import `src/rules.py`, `src/metrics.py`, `src/measurement.py`,",
        "`src/compare.py` or `src/robustness.py`. No script in this directory imports",
        "any of them; each re-derives its quantity from the saved data files and the",
        "raw inputs. `kit/flowmath.py`, `pypsa` and `engine_prep.prepare()` are",
        "permitted and are used where the network itself is needed.",
        "",
        "## Status of the ten checks",
        "",
        "| # | check | status |",
        "|---|---|---|",
    ]

    present = {}
    for i, (title, fname) in CHECKS.items():
        if fname is None:
            present[i] = None
            L.append(f"| {i} | {title} | see section below |")
            continue
        p = VER / fname
        if p.exists():
            present[i] = p.read_text(encoding="utf-8")
            L.append(f"| {i} | {title} | done - `{fname}` |")
        else:
            present[i] = None
            L.append(f"| {i} | {title} | **not run** |")

    L += ["", "## Findings by check", ""]
    for i, (title, fname) in CHECKS.items():
        if fname is None or present[i] is None:
            continue
        L += [f"### {i}. {title}", ""]
        L += first_summary(present[i])
        L += ["", f"Full report: [`{fname}`]({fname}).", ""]

    missing = [i for i, (t, f) in CHECKS.items() if f and present[i] is None]
    if missing:
        L += [
            "## Checks not run", "",
            "These require the large parquet tables, which are git-ignored and were",
            "regenerated locally; if the engine run did not complete they are absent.",
            "",
        ]
        for i in missing:
            L.append(f"- **{i}. {CHECKS[i][0]}**")
        L.append("")

    L += [
        "## 10. Discrepancies, with size and effect",
        "",
        "Every difference found, whether or not it changes a reported number.",
        "",
        "| # | where | size | affects RESULTS.md? | resolution |",
        "|---|---|---|---|---|",
        "| D1 | MASTER section 5 defines `worst_over_mean` as `max r_i / r-bar` "
        "without defining `r-bar` | the two readings differ by up to 37 % "
        "(rule 2, WP2024s42: 6.551 unweighted vs 5.447 availability-weighted) | "
        "No - `summary.csv` is internally consistent | `r-bar` is the "
        "availability-weighted group mean (= D/100), confirmed against "
        "`summary.csv` to 15 significant figures. MASTER should say so. |",
        "| D2 | MASTER section 2.1 states the priority mapping as the exact "
        "strings `wind priority` / `solar priority` / `not priority` / "
        "`uncontrolled` | the gss1 labels are compound (`wind not priority`, "
        "`solar uncontrolled`), so an exact-match reading misclassifies 73 of "
        "210 units | No - the implementation matches on the status suffix and is "
        "correct | MASTER section 2.1 should quote the real label forms. |",
        "| D3 | A 10.8 MW battery row at Tawnaghmore matches a wind generator's "
        "MEC exactly | 1 unit of 210 | No | The pipeline correctly declines the "
        "cross-carrier match; a verifier must filter candidates by `gen_type`. |",
        "| D4 | SEM-O retention has trimmed the measurement window | 48 "
        "half-hours per unit (4226 now retrievable vs 4274 committed); "
        "constraint-only ratios move by up to 3.8e-3 | **Yes, potentially** - the "
        "committed measurement can no longer be regenerated from the API | "
        "`out/measurement_*.csv` restored, not overwritten; the fresh pull is kept "
        "in `verify/repro/`. Elias's local raw files are the only complete copy. |",
        "| D5 | HANDOFF section 2 describes the repository as private and says "
        "only Elias can push | n/a | No | The repository is public "
        "(`\"private\": false`) and DarraghE has write access. |",
        "| D6 | HANDOFF section 3 cites \"section 10 item 5's second half\" for "
        "the band-rule re-derivation | n/a | No | Item 5 is only the Jain/Gini/D "
        "recompute; the band-rule re-derivation is not in the numbered list. |",
        "| D7 | `src/measurement.py` and `src/engine_prep.py` write text with "
        "`Path.write_text()` and `print()` without an encoding | crashes on "
        "Windows (cp1252) partway through, after some outputs are written | No - "
        "output values are unaffected | Run with `PYTHONUTF8=1`. A one-word "
        "`encoding=\"utf-8\"` would make it portable. |",
        "| D8 | `node_table.csv` sorts nodes by shift factor and flags the "
        "\"significant step change\" by comparing each node with the next. Buses "
        "1401 and 14016 have effectively equal shift factors | the sort is "
        "unstable between runs, so the flagged step moved from bus 1401 to bus "
        "14016 and `step_after_name` from BELLACORICK to CROAGHAUN; the shift "
        "factors themselves agree to 1.7e-12 | **Only the node table.** Group "
        "membership is fixed by MASTER section 0, not derived from the step, so "
        "no headline number moves | Break the tie deterministically (bus id as "
        "secondary sort key). Relevant to hackathon problem 3.2, which proposes "
        "generating groups from this threshold. |",
        "| D9 | The band rule is **path-dependent**: r_i feeds the next hour's "
        "eligible set | an independent re-implementation reproduces the total cut "
        "to 4.9e-4 and the year-end ratio spread to 0.13 pp (13.74 vs 13.87 pp), "
        "with per-farm cumulative cut correlating 0.9993, but 1634 of 25500 "
        "per-hour-per-farm entries differ, the largest by a whole 73.8 MW farm "
        "alternating between adjacent hours | No - every reported quantity is an "
        "aggregate and those agree | Not a bug in either implementation. But if "
        "the rule is ever codified, the tie-break and float tolerance must be "
        "specified: two conforming implementations will otherwise issue different "
        "per-farm instructions. |",
        "",
        "### Reproduction on different hardware",
        "",
        "The whole pipeline was re-run from scratch on Windows with different",
        "package versions (pandas 3.0.5, numpy 2.4.6, pypsa from the current",
        "release) against Elias's macOS run:",
        "",
        "| stage | worst difference from the committed output |",
        "|---|---|",
        "| synthetic year (`sites`, `fleet`, `anchors`) | byte-identical |",
        "| shift factors | 1.7e-12 |",
        "| LODF | 6.9e-13 |",
        "| overload series | 1.7e-10 |",
        "| overload energy totals | 1.6e-7 MWh on 34,817 MWh |",
        "| post-cut violations, sign-convention check | 9.4e-10 |",
        "| `rules_summary.json` | wall-clock `seconds` only |",
        "",
        "Every regenerated file was compared and then **restored** from git, so",
        "the committed outputs are untouched. The two files that differ beyond",
        "float noise are `node_table.csv` (D8) and `lodf_dcpf_check.csv`, the",
        "latter because it samples random hours without a fixed seed and so drew",
        "a different sample - not a discrepancy, but it does mean that file",
        "cannot be diffed between runs.",
        "",
        "### What this does not cover",
        "",
        "- The measurement's own window is one summer, and the first two days of it",
        "  are now unrecoverable from the API.",
        "- Checks 2, 3 and 4 depend on the regenerated parquet tables; they verify",
        "  the saved cut vectors, not the LOPF solve that produced the baseline.",
        "- Nothing here verifies the *choice* of decisions in MASTER section 0, only",
        "  that the code implements them.",
        "",
    ]

    (VER / "VERIFICATION.md").write_text("\n".join(L), encoding="utf-8")
    done = sum(1 for i, (t, f) in CHECKS.items() if f and present[i] is not None)
    total = sum(1 for i, (t, f) in CHECKS.items() if f)
    print(f"wrote verify/VERIFICATION.md - {done} of {total} scripted checks present"
          f"{'; missing ' + ', '.join(map(str, missing)) if missing else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
