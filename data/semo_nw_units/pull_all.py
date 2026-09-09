"""Pull BM-101 (availability), BM-096 (dispatch quantity) and BM-037 (dispatch
instructions) for the North-West wind units, into project/data/ under the exact
filenames project/src/measurement.py expects.

Additive companion to pull.py (which pulls BM-096 only). Windows:
  BM-101, BM-096 : StartTime 2026-06-08 .. 2026-09-05  (the documented window)
  BM-037         : EffTime is the time field and the API ignores a StartTime
                   filter on this report, so the full per-unit history is
                   pulled; measurement.py drops the stray pre-2026-06-07 rows.
"""
import json, time, urllib.request, urllib.parse, csv, sys, os

UNITS = ["GU_400021","GU_403990","GU_403750","GU_406560","GU_405130","GU_403760","GU_403880","GU_401280",
         "GU_403400","GU_400950","GU_402160","GU_402200","GU_400550","GU_404630","GU_400070","GU_405870",
         "GU_401730","GU_401720","GU_405930","GU_404480","GU_400940","GU_403840","GU_403800","GU_404560",
         "GU_403900","GU_400030","GU_401190","GU_404930","GU_400020","GU_407660"]
BASE = "https://reports.sem-o.com/api/v1/dynamic/"
T0, T1 = "2026-06-08T00:00:00", "2026-09-05T23:59:00"
OUT = os.path.join("project", "data")

def fetch(query):
    url = BASE + urllib.parse.quote(query, safe="=&?<>:")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {attempt+1}: {type(e).__name__}", file=sys.stderr, flush=True)
            time.sleep(5 * (attempt + 1))
    return None

def pull(report, unit, timefilter):
    rows, page = [], 1
    while True:
        q = (f"{report}?{timefilter}ResourceName={unit}"
             f"&sort_by={'EffTime' if report=='BM-037' else 'StartTime'}&order_by=ASC"
             f"&page={page}&page_size=5000")
        j = fetch(q)
        if not j or "items" not in j:
            print("FAIL", report, unit, page, file=sys.stderr, flush=True)
            break
        rows += j["items"]
        pg = j.get("pagination", {})
        tp = pg.get("totalPages") or -(-int(pg.get("totalItems", 0)) // 5000)
        if page >= tp or len(j["items"]) < 5000:
            break
        page += 1
    return rows

JOBS = [
    ("BM-101", f"StartTime=>={T0}<={T1}&", os.path.join(OUT, "BM-101_nw_units.csv")),
    ("BM-096", f"StartTime=>={T0}<={T1}&", os.path.join(OUT, "BM-096_nw_units.csv")),
    ("BM-037", "", os.path.join(OUT, "BM-037_dispatch_instructions_2026-06-07_to_09-05.csv")),
]

for report, tf, path in JOBS:
    total, w = 0, None
    with open(path, "w", newline="", encoding="utf-8") as out:
        for u in UNITS:
            rows = pull(report, u, tf)
            total += len(rows)
            print(f"{report} {u} {len(rows)}", flush=True)
            for r in rows:
                if w is None:
                    w = csv.DictWriter(out, fieldnames=list(r.keys())); w.writeheader()
                w.writerow(r)
    print(f"WROTE {path} rows={total}", flush=True)
print("done")
