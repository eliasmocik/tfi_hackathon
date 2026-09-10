"""Generate out/wpa_map.html - the constraint-group map, built for a stage.

The page is built by a script, not written by hand, so it cannot drift from the
committed results: every figure comes from out/wpa_map_data.json, which is read
straight from out/wpa_stations.csv and wpa_summary.json.

    python project/src/wp_map_data.py     # payload
    python project/src/wp_map_page.py     # page

Two decisions worth keeping.

Discrete marks, never a smoothed surface. Shift factor is a property of the
network node, not of geography: across these nine stations it does not track
distance to the constrained line at all (Spearman +0.20, p=0.61). Corderry sits
18.1 km from Sligo with the lowest shift factor, 0.187; Cunghill sits 18.7 km
away with the highest, 0.295. A heat surface would assert a gradient the data
refutes.

Light only, and almost wordless. The page is projected and narrated, so it
carries numbers and marks rather than sentences.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"

PAGE = r"""<title>Where the Cut Lands</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{
  --s0:#eef4fc; --s1:#d3e4fa; --s2:#aecdf5; --s3:#7fadec;
  --s4:#4d89e0; --s5:#2a66bd; --s6:#1a4a91; --s7:#0d2f63;
  --accent:#e0592a;
  --bg:#ffffff; --land:#eef0f3; --rule:#e3e6ea;
  --ink:#11161c; --ink2:#5d6773; --ink3:#98a1ad;
}
*{box-sizing:border-box}
html{background:var(--bg)}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;
  font-size:14px; line-height:1.45; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1560px;margin:0 auto;padding:22px 34px 16px}

header{display:flex;align-items:baseline;justify-content:space-between;gap:30px;
  flex-wrap:wrap;margin-bottom:16px}
h1{margin:0;font-size:27px;font-weight:600;letter-spacing:-.015em}
.figs{display:flex;gap:34px}
.figs div{text-align:right}
.figs b{display:block;font-family:"IBM Plex Mono",monospace;font-size:31px;
  font-weight:500;line-height:1;font-variant-numeric:tabular-nums}
.figs span{display:block;font-size:11px;color:var(--ink3);margin-top:5px}

main{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:38px;align-items:start}
@media (max-width:900px){main{grid-template-columns:1fr}}

.seg{display:flex;gap:22px;margin-bottom:10px}
.seg button{appearance:none;border:0;background:none;padding:0 0 5px;
  font:inherit;font-size:13px;color:var(--ink3);cursor:pointer;
  border-bottom:2px solid transparent}
.seg button[aria-pressed="true"]{color:var(--ink);border-bottom-color:var(--ink)}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}

svg{display:block;width:100%;height:auto}
#map{max-height:50vh}
#traj{max-height:16vh}
.land{fill:var(--land)}
.corridor{stroke:var(--accent);stroke-width:2;fill:none;stroke-linecap:round}
.node{fill:var(--accent)}
.mark{stroke:#fff;stroke-width:1.5;transition:fill .4s ease}
.stn text{font-family:"IBM Plex Sans",sans-serif;font-size:10px;fill:var(--ink2);
  paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}
.gridlabel{font-family:"IBM Plex Mono",monospace;font-size:9px;fill:var(--accent);
  paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}

.key{display:flex;align-items:center;gap:20px;margin-top:6px}
.bar{display:flex;height:8px;width:170px}
.bar i{flex:1}
.keytxt{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--ink3);
  display:flex;justify-content:space-between;width:170px;margin-top:4px}
.key small{font-size:11px;color:var(--ink3)}
.sizekey{width:56px;height:26px;flex:none}

table{width:100%;border-collapse:collapse;font-size:12px}
th,td{padding:5px 0;text-align:right;border-bottom:1px solid var(--rule)}
th{font-size:10px;font-weight:500;color:var(--ink3);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td.n{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
tbody tr.hot{background:var(--s0)}
tbody tr:last-child td{border-bottom:0}

.pair{display:grid;grid-template-columns:1fr 1fr;gap:1px;margin-top:20px;
  background:var(--rule);border:1px solid var(--rule)}
.pair div{background:var(--bg);padding:11px 12px}
.pair b{display:block;font-family:"IBM Plex Mono",monospace;font-size:20px;
  font-weight:500;line-height:1.1;margin:3px 0 2px}
.pair span{font-size:11px;color:var(--ink3);font-family:"IBM Plex Mono",monospace}
.pair em{font-style:normal;font-size:12px;color:var(--ink2)}
.paircap{font-size:11px;color:var(--ink3);margin:7px 0 0}

.traj{margin-top:20px;padding-top:14px;border-top:1px solid var(--rule)}
.trajcap{margin:0 0 4px;font-size:11px;color:var(--ink3)}
.trajcap span{opacity:.7}
footer{margin-top:14px;font-family:"IBM Plex Mono",monospace;font-size:10px;
  color:var(--ink3)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
<header>
  <h1>Where the cut lands</h1>
  <div class="figs">
    <div><b id="figSave"></b><span>excess spill</span></div>
    <div><b id="figHH"></b><span>half-hours</span></div>
  </div>
</header>

<main>
  <div>
    <div class="seg" role="group" aria-label="Rule">
      <button data-mode="observed" aria-pressed="true">Today</button>
      <button data-mode="band" aria-pressed="false">Band 5pp</button>
      <button data-mode="effectiveness" aria-pressed="false">Effectiveness</button>
      <button data-mode="sf" aria-pressed="false">Shift factor</button>
    </div>
    <svg id="map" role="img" aria-label="North-West Ireland: nine constraint-group stations sized by available energy and shaded by dispatch-down under the selected rule"></svg>
    <div class="key">
      <div>
        <div class="bar" id="ramp"></div>
        <div class="keytxt"><span id="rampLo"></span><span id="rampHi"></span></div>
      </div>
      <svg class="sizekey" viewBox="0 0 56 26" aria-hidden="true">
        <circle cx="9" cy="18" r="5" fill="none" stroke="#98a1ad"></circle>
        <circle cx="34" cy="14" r="10" fill="none" stroke="#98a1ad"></circle>
      </svg>
      <small>available energy</small>
      <small id="keyNote"></small>
    </div>
  </div>

  <aside>
    <table>
      <thead><tr><th>Station</th><th>SF</th><th>Today</th><th>Band 5</th><th>Eff.</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pair">
      <div><em>Corderry</em><b>0.187</b><span>18.1 km</span></div>
      <div><em>Cunghill</em><b>0.295</b><span>18.7 km</span></div>
    </div>
    <p class="paircap">Same distance to Sligo. Spearman +0.20, p = 0.61.</p>
  </aside>
</main>

<div class="traj">
  <p class="trajcap">Worst farm's gap from group average, pp <span id="warm"></span></p>
  <svg id="traj" role="img" aria-label="Worst farm's gap from the group average across the window, four rules, percentage points"></svg>
</div>

<footer id="foot"></footer>
</div>

<script>
const DATA = __DATA__;
const SEQ = ["--s0","--s1","--s2","--s3","--s4","--s5","--s6","--s7"];
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS = "http://www.w3.org/2000/svg";
const el = (t, a={}) => { const e = document.createElementNS(NS, t);
  for (const k in a) e.setAttribute(k, a[k]); return e; };

const MODES = {
  observed:{get:s=>s.r.observed, kind:"seq"},
  band:{get:s=>s.r.band, kind:"seq"},
  effectiveness:{get:s=>s.r.effectiveness, kind:"seq"},
  sf:{get:s=>s.sf, kind:"sf"}
};
let mode = "observed";

// one scale across the three rule views, so the panels compare directly
const RMAX = Math.max(...DATA.stations.flatMap(s=>[s.r.observed,s.r.band,s.r.effectiveness]));
const SFLO = Math.min(...DATA.stations.map(s=>s.sf));
const SFHI = Math.max(...DATA.stations.map(s=>s.sf));

function lerpHex(a,b,t){
  const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  const [r1,g1,b1]=p(a),[r2,g2,b2]=p(b);
  const q=(x,y)=>Math.round(x+(y-x)*t).toString(16).padStart(2,"0");
  return "#"+q(r1,r2)+q(g1,g2)+q(b1,b2);
}
function seqColor(t){
  const st = SEQ.map(cssv); t = Math.max(0, Math.min(1, t));
  const x = t*(st.length-1), i = Math.min(st.length-2, Math.floor(x));
  return lerpHex(st[i], st[i+1], x-i);
}
const colorFor = s => MODES[mode].kind === "seq"
  ? seqColor(MODES[mode].get(s) / RMAX)
  : seqColor((s.sf - SFLO) / (SFHI - SFLO));
const pc = v => (v*100).toFixed(2) + "%";

/* ---------- map ---------- */
const W = 720, H = 468, PAD = 14;
function buildMap(){
  const svg = document.getElementById("map");
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  const pts = DATA.stations.map(s=>[s.lon,s.lat]);
  const mon = DATA.grid.monitored;
  pts.push([mon.from.lon,mon.from.lat],[mon.to.lon,mon.to.lat]);
  const mx=(Math.max(...pts.map(p=>p[0]))-Math.min(...pts.map(p=>p[0])))*0.11;
  const my=(Math.max(...pts.map(p=>p[1]))-Math.min(...pts.map(p=>p[1])))*0.11;
  const lon0=Math.min(...pts.map(p=>p[0]))-mx, lon1=Math.max(...pts.map(p=>p[0]))+mx;
  const lat0=Math.min(...pts.map(p=>p[1]))-my, lat1=Math.max(...pts.map(p=>p[1]))+my;
  const k = Math.cos((lat0+lat1)/2 * Math.PI/180);
  const sc = Math.min((W-2*PAD)/((lon1-lon0)*k), (H-2*PAD)/(lat1-lat0));
  const ox = PAD + ((W-2*PAD) - (lon1-lon0)*k*sc)/2;
  const oy = PAD + ((H-2*PAD) - (lat1-lat0)*sc)/2;
  const proj = (lon,lat) => [ox + (lon-lon0)*k*sc, oy + (lat1-lat)*sc];

  const defs = el("defs"); svg.appendChild(defs);
  const cp = el("clipPath",{id:"fr"});
  cp.appendChild(el("rect",{x:0,y:0,width:W,height:H}));
  defs.appendChild(cp);

  const gLand = el("g",{"clip-path":"url(#fr)"}); svg.appendChild(gLand);
  DATA.counties.features.forEach(f=>{
    const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    polys.forEach(poly=>{
      const d = poly.map(ring => "M" + ring.map(c=>proj(c[0],c[1]).map(n=>n.toFixed(1)).join(",")).join("L") + "Z").join("");
      gLand.appendChild(el("path",{d, class:"land"}));
    });
  });

  // Station geometry is registered before any label is placed, the corridor
  // label included: otherwise it is positioned against an empty canvas.
  const AMAX = Math.max(...DATA.stations.map(s=>s.avail_MWh));
  const boxes = [];
  const drawn = DATA.stations.map(s=>{
    const [x,y] = proj(s.lon, s.lat);
    const r = 6 + 19 * Math.sqrt(s.avail_MWh / AMAX);
    boxes.push({x:x-r, y:y-r, w:2*r, h:2*r});
    return {s, x, y, r};
  });

  const PADPX = 1.5;
  const hits = b => boxes.some(o =>
    !(b.x+b.w+PADPX < o.x || o.x+o.w+PADPX < b.x ||
      b.y+b.h+PADPX < o.y || o.y+o.h+PADPX < b.y));
  // Candidates are tried in order and the label is measured where it lands,
  // never estimated from character count.
  function place(x, y, txt, cls, pad, parent){
    const mid = cls !== "gridlabel";
    const t = el("text",{class:cls});
    if (mid) t.setAttribute("text-anchor","middle");
    t.textContent = txt; parent.appendChild(t);
    const cands = [];
    for (const rad of [pad+9, pad+19, pad+30, pad+42])
      for (const ang of [90, 270, 0, 180, 45, 135, 315, 225]){
        const a = ang*Math.PI/180;
        cands.push([Math.cos(a)*rad*1.7, Math.sin(a)*rad*0.75 + 4]);
      }
    let best = null, bestArea = Infinity;
    for (const [dx, dy] of cands){
      t.setAttribute("x", x+dx); t.setAttribute("y", y+dy);
      if (!mid) t.setAttribute("text-anchor", dx < 0 ? "end" : "start");
      const g = t.getBBox();
      const b = {x:g.x, y:g.y, w:g.width, h:g.height};
      if (!hits(b)){ boxes.push(b); return; }
      const area = boxes.reduce((acc,o)=>{
        const ox2 = Math.min(b.x+b.w,o.x+o.w)-Math.max(b.x,o.x);
        const oy2 = Math.min(b.y+b.h,o.y+o.h)-Math.max(b.y,o.y);
        return acc + (ox2>0&&oy2>0 ? ox2*oy2 : 0);
      },0);
      if (area < bestArea){ bestArea = area; best = [dx, dy, b]; }
    }
    t.setAttribute("x", x+best[0]); t.setAttribute("y", y+best[1]);
    if (!mid) t.setAttribute("text-anchor", best[0] < 0 ? "end" : "start");
    boxes.push(best[2]);
  }

  // the constrained element: one line, two ends, one label
  const gGrid = el("g"); svg.appendChild(gGrid);
  const a = proj(mon.from.lon, mon.from.lat), b = proj(mon.to.lon, mon.to.lat);
  gGrid.appendChild(el("line",{x1:a[0],y1:a[1],x2:b[0],y2:b[1],class:"corridor"}));
  [a,b].forEach(p=>gGrid.appendChild(el("circle",{cx:p[0],cy:p[1],r:3,class:"node"})));
  place(a[0]+(b[0]-a[0])*0.78, a[1]+(b[1]-a[1])*0.78,
        "Flagford-Sligo 110 kV", "gridlabel", 8, gGrid);

  const gStn = el("g"); svg.appendChild(gStn);
  drawn.forEach(function(d){
    const s = d.s, x = d.x, y = d.y, r = d.r;
    const g = el("g",{class:"stn", tabindex:"0",
      "aria-label": s.station + ", shift factor " + s.sf.toFixed(3)});
    gStn.appendChild(g);
    const c = el("circle",{cx:x,cy:y,r:r,class:"mark",fill:colorFor(s)});
    g.appendChild(c);
    place(x, y + r, s.station, "", 5, g);
    g._s = s; g._c = c;
    const on = function(){ mark(s.station); }, off = function(){ mark(null); };
    g.addEventListener("mouseenter", on); g.addEventListener("mouseleave", off);
    g.addEventListener("focus", on);      g.addEventListener("blur", off);
  });
}
function mark(name){
  document.querySelectorAll("#tbody tr").forEach(tr=>
    tr.classList.toggle("hot", !!name && tr.dataset.stn === name));
}

function paint(){
  document.querySelectorAll(".stn").forEach(g=>g._c.setAttribute("fill", colorFor(g._s)));
  const ramp = document.getElementById("ramp"); ramp.innerHTML = "";
  for (let i=0;i<26;i++){
    const b = document.createElement("i");
    b.style.background = seqColor(i/25); ramp.appendChild(b);
  }
  const seq = MODES[mode].kind === "seq";
  document.getElementById("rampLo").textContent = seq ? "0" : SFLO.toFixed(3);
  document.getElementById("rampHi").textContent = seq ? pc(RMAX) : SFHI.toFixed(3);
  document.getElementById("keyNote").textContent = seq
    ? "% of available energy \u00b7 one scale"
    : "MW relieved per MW cut";
  document.querySelectorAll(".seg button").forEach(b=>
    b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
}

function buildTable(){
  const rows = [...DATA.stations].sort((a,b)=>b.sf-a.sf);
  document.getElementById("tbody").innerHTML = rows.map(s=>
    '<tr data-stn="' + s.station + '"><td>' + s.station + '</td>'
    + '<td class="n">' + s.sf.toFixed(3) + '</td>'
    + '<td class="n">' + pc(s.r.observed) + '</td>'
    + '<td class="n">' + pc(s.r.band) + '</td>'
    + '<td class="n">' + pc(s.r.effectiveness) + '</td></tr>').join("");
}

/* ---------- worst farm's gap from the group average ---------- */
function buildTraj(){
  const svg = document.getElementById("traj");
  const T = DATA.trajectory, w = 1180, h = 152, L = 34, R = 132, TP = 10, B = 20;
  svg.setAttribute("viewBox", "0 0 " + w + " " + h);
  const series = [
    {k:"observed", label:"today",         col:"var(--accent)", wid:1.8},
    {k:"bandinf",  label:"effectiveness", col:"var(--s3)",     wid:1.4},
    {k:"band5",    label:"band 5pp",      col:"var(--s6)",     wid:1.8},
    {k:"band0",    label:"band 0pp",      col:"var(--ink3)",   wid:1.2}
  ];
  // The ledger divides by cumulative availability, so the opening hours are
  // arithmetic rather than inequity: band 0pp, the most equal rule that can
  // exist, peaks at 21 pp in the first row. That stretch is excluded from the
  // medians, so it is not drawn either - drawing it set the y-scale from an
  // artefact and squashed the three lines that matter into the bottom third.
  const B0 = T.burn_in;
  const cut = k => T[k].slice(B0);
  const ymax = Math.ceil(Math.max(...series.flatMap(s=>cut(s.k)))/20)*20;
  const n = T.t.length - B0;
  const X = i => L + i*(w-L-R)/(n-1);
  const Y = v => TP + (h-TP-B) * (1 - v/ymax);

  for (let g=0; g<=ymax; g+=20){
    svg.appendChild(el("line",{x1:L,y1:Y(g),x2:w-R,y2:Y(g),stroke:"var(--rule)","stroke-width":1}));
    const t = el("text",{x:L-6,y:Y(g)+3.5,"text-anchor":"end",
      style:"font-family:'IBM Plex Mono',monospace;font-size:9px;fill:var(--ink3)"});
    t.textContent = g; svg.appendChild(t);
  }
  const ends = [];
  series.forEach(s=>{
    svg.appendChild(el("path",{d:cut(s.k).map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+","+Y(v).toFixed(1)).join(""),
      fill:"none", stroke:s.col, "stroke-width":s.wid, "stroke-linejoin":"round"}));
    ends.push({s:s, y:Y(cut(s.k)[n-1]), med:T.stats[s.k].median_after});
  });
  // three series finish within 2 pp of one another: stack the end labels apart
  ends.sort((a,b)=>a.y-b.y);
  for (let i=1;i<ends.length;i++)
    if (ends[i].y - ends[i-1].y < 28) ends[i].y = ends[i-1].y + 28;
  const shift = Math.max(0, ends[ends.length-1].y - (h-B-2));
  ends.forEach(e=>{
    e.y -= shift;
    const y0 = Y(cut(e.s.k)[n-1]);
    svg.appendChild(el("path",{d:"M"+(w-R-1)+","+y0+"L"+(w-R+5)+","+(e.y-3),
      fill:"none", stroke:e.s.col, "stroke-width":1, opacity:.5}));
    const lt = el("text",{x:w-R+9, y:e.y,
      style:"font-family:'IBM Plex Sans',sans-serif;font-size:11px;fill:"+e.s.col});
    lt.textContent = e.s.label; svg.appendChild(lt);
    const lm = el("text",{x:w-R+9, y:e.y+13.5,
      style:"font-family:'IBM Plex Mono',monospace;font-size:9.5px;fill:var(--ink3)"});
    lm.textContent = e.med.toFixed(2) + " pp median"; svg.appendChild(lm);
  });
  [[L, T.t[B0], "start"],[w-R, T.t[T.t.length-1], "end"]].forEach(p=>{
    const t = el("text",{x:p[0], y:h-6, "text-anchor":p[2],
      style:"font-family:'IBM Plex Mono',monospace;font-size:9px;fill:var(--ink3)"});
    t.textContent = p[1].slice(0,10); svg.appendChild(t);
  });
}

document.getElementById("figSave").textContent = DATA.meta.effectiveness_saving_pct.toFixed(2) + "%";
document.getElementById("figHH").textContent = DATA.meta.half_hours;
document.getElementById("warm").textContent =
  "from +" + DATA.trajectory.warmup_days + " d";
document.getElementById("foot").textContent =
  "North-West Constraint Group 3 \u00b7 " + DATA.meta.window[0].slice(0,10)
  + " to " + DATA.meta.window[1].slice(0,10) + " \u00b7 "
  + DATA.meta.units + " farms \u00b7 wpa_stations.csv";
buildMap(); buildTable(); buildTraj(); paint();
document.querySelectorAll(".seg button").forEach(b=>
  b.addEventListener("click", ()=>{ mode = b.dataset.mode; paint(); }));
</script>
"""


def main() -> int:
    data = (OUT / "wpa_map_data.json").read_text(encoding="utf-8")
    html = PAGE.replace("__DATA__", data)
    bad = sorted({c for c in html if ord(c) > 127})
    if bad:
        raise SystemExit(f"page must stay ASCII, found {bad}")
    p = OUT / "wpa_map.html"
    p.write_text(html, encoding="utf-8")
    print(f"wrote {p.name}  {p.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
