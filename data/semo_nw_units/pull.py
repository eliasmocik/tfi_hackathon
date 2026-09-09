"""Pull BM-101 (availability) and BM-086 (metered) for the North-West wind units, 2026-06-08 .. 2026-09-05."""
import json, time, urllib.request, urllib.parse, csv, sys
UNITS = ["GU_400021","GU_403990","GU_403750","GU_406560","GU_405130","GU_403760","GU_403880","GU_401280",
         "GU_403400","GU_400950","GU_402160","GU_402200","GU_400550","GU_404630","GU_400070","GU_405870",
         "GU_401730","GU_401720","GU_405930","GU_404480","GU_400940","GU_403840","GU_403800","GU_404560",
         "GU_403900","GU_400030","GU_401190","GU_404930","GU_400020","GU_407660"]
BASE = "https://reports.sem-o.com/api/v1/dynamic/"
def pull(report, unit, t0="2026-06-08T00:00:00", t1="2026-09-05T23:59:00"):
    rows, page = [], 1
    while True:
        q = f"{report}?StartTime=>={t0}<={t1}&ResourceName={unit}&sort_by=StartTime&order_by=ASC&page={page}&page_size=5000"
        url = BASE + urllib.parse.quote(q, safe="=&?<>:")
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    j = json.load(r); break
            except Exception as e:
                time.sleep(5 * (attempt + 1)); j = None
        if not j or "pagination" not in j or "items" not in j:
            print("FAIL", report, unit, page, str(j)[:200], file=sys.stderr); time.sleep(20); continue
        rows += j["items"]
        pg=j["pagination"]; tp=pg.get("totalPages") or -(-int(pg.get("totalItems",0))//5000)
        if page >= tp or len(j["items"])<5000: break
        page += 1
    return rows
for report, key in [("BM-096", "DispatchQuantity")]:
    out = open(f"data/semo_nw_units/{report}_nw_units.csv", "w", newline="")
    w = None
    for u in UNITS:
        rows = pull(report, u)
        print(report, u, len(rows), flush=True)
        for r in rows:
            if w is None:
                w = csv.DictWriter(out, fieldnames=list(r.keys())); w.writeheader()
            w.writerow(r)
    out.close()
print("done")
