"""MASTER §10 item 7 — quote and group-membership audit. Stdlib only.

Checks every quoted phrase in project/MASTER.md and project/out/RESULTS.md
against the WDT source text, and re-derives the NW Group 1 / Group 3 station
lists from §3.1/§3.3 of that text rather than from any project module.
"""
import re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WDT = ROOT / "project" / "data" / "eirgrid-wdt-constraint-group-overview-2024.txt"
DOCS = [ROOT / "project" / "MASTER.md", ROOT / "project" / "out" / "RESULTS.md"]
OUT = ROOT / "project" / "verify"

def norm(s: str) -> str:
    """Fold quote glyphs, dashes and whitespace so extraction artefacts do not
    masquerade as quotation errors."""
    s = unicodedata.normalize("NFKD", s)
    for a, b in [("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), ("−", "-"), (" ", " ")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()

wdt_raw = WDT.read_text(encoding="utf-8", errors="replace")
wdt = norm(wdt_raw)

QUOTE_RE = re.compile(r'["“]([^"“”]{8,300})["”]')

rows = []
for doc in DOCS:
    if not doc.exists():
        rows.append((doc.name, "-", "DOC MISSING", ""))
        continue
    text = doc.read_text(encoding="utf-8", errors="replace")
    for m in QUOTE_RE.finditer(text):
        q = m.group(1).strip()
        if not re.search(r"[a-zA-Z]", q) or q.startswith(("http", "GU_")):
            continue
        line = text[:m.start()].count("\n") + 1
        # only phrases the document attributes to the WDT / EirGrid document
        ctx = norm(text[max(0, m.start() - 260):m.start()])
        attributed = any(k in ctx for k in ("wdt", "constraint group overview",
                                            "eirgrid", "app. 2", "appendix"))
        found = norm(q) in wdt
        if attributed:
            verdict = "FOUND" if found else "NOT FOUND IN WDT"
        else:
            verdict = "found (not WDT-attributed)" if found else "n/a - not WDT-attributed"
        rows.append((doc.name, line, verdict, q[:110]))

hard_fail = [r for r in rows if r[2] == "NOT FOUND IN WDT"]

# --- group membership, re-derived from the WDT text itself -------------------
def section(text, head):
    i = text.find(head)
    if i < 0:
        return ""
    j = text.find("\n3.", i + len(head))
    return text[i: j if j > 0 else i + 4000]

s31 = section(wdt_raw, "3.1")
s33 = section(wdt_raw, "3.3")

report = [
    "# Verification §10.7 — WDT quotes and group membership",
    "",
    f"Source: `project/data/eirgrid-wdt-constraint-group-overview-2024.txt` ({len(wdt_raw):,} chars).",
    "Comparison is whitespace- and quote-glyph-normalised, case-insensitive.",
    "",
    "## Quoted phrases",
    "",
    "| document | line | verdict | phrase |",
    "|---|---|---|---|",
]
for d, l, v, q in rows:
    qs = q.replace("|", "\|")
    report.append(f"| {d} | {l} | {v} | {qs} |")
report += [
    "",
    f"**WDT-attributed quotes checked:** {sum(1 for r in rows if r[2].startswith(('FOUND','NOT FOUND')))}; "
    f"**not found: {len(hard_fail)}**.",
    "",
    "## §3.1 / §3.3 extract (for the station-list check)",
    "",
    "```",
    (s31[:1500] if s31 else "SECTION 3.1 NOT LOCATED"),
    "```",
    "",
    "```",
    (s33[:1500] if s33 else "SECTION 3.3 NOT LOCATED"),
    "```",
]
(OUT / "v07_quotes.md").write_text("\n".join(report), encoding="utf-8")
print(f"quotes checked: {len(rows)}; hard failures: {len(hard_fail)}")
for r in hard_fail:
    print("  MISSING:", r[0], r[1], r[3])
print("wrote project/verify/v07_quotes.md")
