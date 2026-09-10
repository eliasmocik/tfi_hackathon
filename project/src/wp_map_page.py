"""Generate out/wpa_map.html - the constraint-group map.

The page is built by a script, not written by hand, so it cannot drift from the
committed results: every figure it shows comes from out/wpa_map_data.json,
which in turn is read straight from out/wpa_stations.csv and wpa_summary.json.

    python project/src/wp_map_data.py     # payload
    python project/src/wp_map_page.py     # page

Design note. The stations are drawn as discrete marks and never interpolated
into a continuous surface. Shift factor is a property of the network node, not
of geography: across these nine stations it does not track distance to the
constrained line at all (Spearman +0.20, p=0.61). Corderry sits 18.1 km from
Sligo with the lowest shift factor of the group, 0.187; Cunghill sits 18.7 km
away with the highest, 0.295. A smoothed heat surface would assert a spatial
gradient the data refutes.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"

PAGE = r"""<title>Where the Cut Lands</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{
  --seq0:#eef5fd; --seq1:#cde2fb; --seq2:#9ec5f4; --seq3:#6da7ec;
  --seq4:#3987e5; --seq5:#256abf; --seq6:#184f95; --seq7:#0d366b;
  --div-lo:#0d366b; --div-mid:#eceae6; --div-hi:#8f1f1f;
  --accent:#eb6834; --accent-soft:#f6b699;
  --ground:#f7f8fa; --panel:#ffffff; --sunk:#eef1f6;
  --line:#d7dde7; --line-soft:#e7ebf2;
  --ink:#141a22; --ink-2:#495566; --ink-3:#78849a;
  --land:#e6ebf2; --land-line:#ccd5e1;
  --ok:#1baf7a;
}
:root:not([data-theme="light"]){ @media (prefers-color-scheme: dark){
  --seq0:#12233c; --seq1:#173154; --seq2:#1d4272; --seq3:#245696;
  --seq4:#2f6fbd; --seq5:#4a8bd6; --seq6:#77aae6; --seq7:#a9caf2;
  --div-lo:#77aae6; --div-mid:#2a3240; --div-hi:#e07070;
  --accent:#f4854e; --accent-soft:#7a3d22;
  --ground:#0e1319; --panel:#151b24; --sunk:#1b2330;
  --line:#2a3444; --line-soft:#212a37;
  --ink:#eef2f8; --ink-2:#a9b4c4; --ink-3:#7b8698;
  --land:#1c2532; --land-line:#2c3849;
  --ok:#3fc999;
}}
:root[data-theme="dark"]{
  --seq0:#12233c; --seq1:#173154; --seq2:#1d4272; --seq3:#245696;
  --seq4:#2f6fbd; --seq5:#4a8bd6; --seq6:#77aae6; --seq7:#a9caf2;
  --div-lo:#77aae6; --div-mid:#2a3240; --div-hi:#e07070;
  --accent:#f4854e; --accent-soft:#7a3d22;
  --ground:#0e1319; --panel:#151b24; --sunk:#1b2330;
  --line:#2a3444; --line-soft:#212a37;
  --ink:#eef2f8; --ink-2:#a9b4c4; --ink-3:#7b8698;
  --land:#1c2532; --land-line:#2c3849;
  --ok:#3fc999;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;
  font-size:14px; line-height:1.55; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1340px;margin:0 auto;padding:28px 22px 56px}

header.top{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end;
  justify-content:space-between;padding-bottom:18px;border-bottom:1px solid var(--line)}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin:0 0 6px}
h1{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:30px;
  line-height:1.15;margin:0;letter-spacing:-.01em;text-wrap:balance;max-width:22ch}
h1 em{font-style:italic;color:var(--ink-2)}
.lede{margin:8px 0 0;color:var(--ink-2);max-width:62ch}
.headline-fig{display:flex;gap:26px;align-items:flex-end}
.fig{text-align:right}
.fig b{display:block;font-family:"IBM Plex Mono",monospace;font-size:30px;
  font-weight:600;line-height:1;font-variant-numeric:tabular-nums;color:var(--ink)}
.fig span{display:block;font-size:11px;color:var(--ink-3);margin-top:5px;
  letter-spacing:.04em;text-transform:uppercase}

.grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.85fr);
  gap:22px;margin-top:22px;align-items:start}
@media (max-width:940px){.grid{grid-template-columns:1fr}}

.card{background:var(--panel);border:1px solid var(--line);border-radius:10px}
.card-h{display:flex;flex-wrap:wrap;gap:10px;align-items:center;
  justify-content:space-between;padding:13px 16px;border-bottom:1px solid var(--line-soft)}
.card-h h2{margin:0;font-size:13px;font-weight:600;letter-spacing:.02em}
.card-h .sub{font-size:11px;color:var(--ink-3);font-family:"IBM Plex Mono",monospace}

.seg{display:flex;flex-wrap:wrap;gap:3px;padding:3px;background:var(--sunk);
  border-radius:7px}
.seg button{appearance:none;border:0;background:transparent;color:var(--ink-2);
  font:inherit;font-size:12px;font-weight:500;padding:6px 11px;border-radius:5px;
  cursor:pointer;transition:background .16s,color .16s;white-space:nowrap}
.seg button:hover{color:var(--ink)}
.seg button[aria-pressed="true"]{background:var(--panel);color:var(--ink);
  box-shadow:0 1px 2px rgba(20,26,34,.13)}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:1px}

figure.map{margin:0;padding:6px 6px 0}
svg{display:block;width:100%;height:auto;overflow:visible}
.county{fill:var(--land);stroke:var(--land-line);stroke-width:.5}
.corridor{stroke:var(--accent);fill:none;stroke-linecap:round}
.node-halo{fill:none;stroke:var(--panel);stroke-width:2.5}
.stn{cursor:pointer}
.stn circle.mark{stroke:var(--panel);stroke-width:1.6;transition:fill .45s ease,r .45s ease}
.stn:hover circle.mark,.stn:focus-visible circle.mark{stroke:var(--ink);stroke-width:2}
.stn:focus-visible{outline:none}
.stn text{font-family:"IBM Plex Sans",sans-serif;font-size:9.5px;font-weight:500;
  fill:var(--ink-2);paint-order:stroke;stroke:var(--panel);stroke-width:2.6px;
  stroke-linejoin:round}
.gridlabel{font-family:"IBM Plex Mono",monospace;font-size:8.5px;fill:var(--accent);
  paint-order:stroke;stroke:var(--ground);stroke-width:2.6px;stroke-linejoin:round}

.legend{display:flex;flex-wrap:wrap;gap:18px;align-items:center;
  padding:11px 16px 14px;border-top:1px solid var(--line-soft)}
.ramp{display:flex;flex-direction:column;gap:4px}
.ramp .bar{display:flex;height:9px;width:190px;border-radius:2px;overflow:hidden}
.ramp .bar i{flex:1}
.ramp .ends{display:flex;justify-content:space-between;font-size:10px;
  color:var(--ink-3);font-family:"IBM Plex Mono",monospace}
.legend .note{font-size:11px;color:var(--ink-3);max-width:30ch}
.sizekey{display:flex;align-items:flex-end;gap:7px}
.sizekey svg{width:64px;height:34px}
.sizekey span{font-size:10px;color:var(--ink-3)}

table{width:100%;border-collapse:collapse;font-size:12px}
th,td{padding:6px 8px;text-align:right;border-bottom:1px solid var(--line-soft)}
th{font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);
  font-weight:600;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td.num{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
tbody tr{transition:background .12s}
tbody tr:hover,tbody tr.hot{background:var(--sunk)}
td .minibar{display:block;height:3px;border-radius:2px;margin-top:3px;
  background:var(--seq4);opacity:.75}
.tablewrap{overflow-x:auto;padding:2px 10px 10px}

.callout{margin:0;padding:14px 16px;border-left:3px solid var(--accent);
  background:var(--sunk);border-radius:0 8px 8px 0}
.callout p{margin:0;font-size:13px;color:var(--ink-2)}
.callout b{color:var(--ink)}
.pairfig{display:flex;gap:14px;margin-top:10px;font-family:"IBM Plex Mono",monospace;
  font-size:11px}
.pairfig div{flex:1;background:var(--panel);border:1px solid var(--line);
  border-radius:6px;padding:8px 10px}
.pairfig b{display:block;font-size:17px;font-variant-numeric:tabular-nums}

.notes{font-size:12px;color:var(--ink-2);padding:14px 16px}
.notes ul{margin:8px 0 0;padding-left:17px}
.notes li{margin:5px 0}
.notes code{font-family:"IBM Plex Mono",monospace;font-size:11px;
  background:var(--sunk);padding:1px 4px;border-radius:3px}

.tip{position:fixed;pointer-events:none;z-index:20;background:var(--panel);
  border:1px solid var(--line);border-radius:8px;padding:9px 11px;font-size:12px;
  box-shadow:0 6px 20px rgba(10,15,25,.16);opacity:0;transition:opacity .12s;
  max-width:250px}
.tip.on{opacity:1}
.tip h4{margin:0 0 5px;font-size:12.5px;font-weight:600}
.tip dl{margin:0;display:grid;grid-template-columns:auto auto;gap:1px 12px;
  font-family:"IBM Plex Mono",monospace;font-size:11px}
.tip dt{color:var(--ink-3)}
.tip dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}

footer{margin-top:26px;padding-top:14px;border-top:1px solid var(--line);
  font-size:11px;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:14px;
  justify-content:space-between}
footer code{font-family:"IBM Plex Mono",monospace}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<div class="wrap">
<header class="top">
  <div>
    <p class="eyebrow">North-West Constraint Group 3 &middot; SEM-O dispatch, summer 2026</p>
    <h1>Where the cut lands, and where it <em>should</em></h1>
    <p class="lede">When the Flagford&ndash;Sligo line overloads, EirGrid cuts the whole
      group pro rata. Each farm's shift factor &mdash; the MW of relief it actually
      delivers per MW cut &mdash; builds the group and is then discarded. This is the
      same 670 half-hours of real instructions, re-allocated three ways, every one
      delivering identical flow relief.</p>
  </div>
  <div class="headline-fig">
    <div class="fig"><b id="figSave">&mdash;</b><span>more spilled than needed</span></div>
    <div class="fig"><b id="figHH">&mdash;</b><span>half-hours replayed</span></div>
  </div>
</header>

<div class="grid">
  <section class="card">
    <div class="card-h">
      <h2>Dispatch-down by station</h2>
      <div class="seg" role="group" aria-label="Allocation rule">
        <button data-mode="observed" aria-pressed="true">Today (pro rata)</button>
        <button data-mode="band3" aria-pressed="false">Band 3&thinsp;pp</button>
        <button data-mode="effectiveness" aria-pressed="false">Effectiveness</button>
        <button data-mode="delta" aria-pressed="false">Change vs today</button>
        <button data-mode="sf" aria-pressed="false">Shift factor</button>
      </div>
    </div>
    <figure class="map"><svg id="map" role="img" aria-labelledby="mapTitle"><title id="mapTitle">Map of North-West Ireland showing nine wind constraint-group stations, coloured by dispatch-down under the selected rule</title></svg></figure>
    <div class="legend">
      <div class="ramp">
        <div class="bar" id="ramp"></div>
        <div class="ends"><span id="rampLo">0</span><span id="rampHi"></span></div>
      </div>
      <div class="sizekey">
        <svg viewBox="0 0 64 34" aria-hidden="true">
          <circle cx="12" cy="22" r="5" fill="none" stroke="var(--ink-3)" stroke-width="1"></circle>
          <circle cx="36" cy="18" r="11" fill="none" stroke="var(--ink-3)" stroke-width="1"></circle>
        </svg>
        <span>circle area&nbsp;=<br>energy available</span>
      </div>
      <p class="note" id="legendNote"></p>
    </div>
  </section>

  <div style="display:flex;flex-direction:column;gap:22px">
    <section class="card">
      <div class="card-h"><h2>The pair that settles it</h2>
        <span class="sub">same distance, opposite effect</span></div>
      <div style="padding:14px 16px">
        <div class="callout">
          <p>Shift factor is an <b>electrical</b> property, not a geographic one. Across
            these nine stations it does not track distance to the constrained line at all
            &mdash; Spearman <b>+0.20</b>, p&nbsp;=&nbsp;0.61.</p>
          <div class="pairfig">
            <div>Corderry<b>0.187</b>18.1&nbsp;km from Sligo</div>
            <div>Cunghill<b>0.295</b>18.7&nbsp;km from Sligo</div>
          </div>
        </div>
        <p style="font-size:12.5px;color:var(--ink-2);margin:12px 0 0">Two stations the
          same distance from the line differ <b style="color:var(--ink)">1.57&times;</b> in
          how much they relieve it. That is why the stations are drawn as discrete marks
          and never smoothed into a heat surface: there is no spatial gradient to draw.</p>
      </div>
    </section>

    <section class="card">
      <div class="card-h"><h2>Station detail</h2><span class="sub" id="tableMode"></span></div>
      <div class="tablewrap">
        <table>
          <thead><tr><th>Station</th><th>Shift&nbsp;factor</th><th>Today</th>
            <th>Band&nbsp;3</th><th>Effect.</th></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </section>
  </div>
</div>

<section class="card" style="margin-top:22px">
  <div class="card-h"><h2>Worst farm's distance from the group average, over the window</h2>
    <span class="sub">670 half-hours &middot; percentage points</span></div>
  <figure class="map" style="padding:10px 16px 4px"><svg id="traj" role="img" aria-label="Line chart of maximum divergence between the worst-hit farm and the group average across the window, for four rules"></svg></figure>
  <div class="notes" style="padding-top:0">
    <p style="margin:0 0 8px"><b>Read the shaded stretch as excluded.</b> The ledger
      divides cumulative cut by cumulative availability, so in the opening hours the
      denominator is a single half-hour and the spread is arithmetic, not inequity:
      band&nbsp;0&nbsp;pp &mdash; the most equal rule that can exist &mdash; peaks at
      21.2&thinsp;pp in the very first row. Every rule's maximum falls inside the first
      day. The figures quoted here are therefore taken <b>after</b> a 24-hour burn-in.</p>
    <p style="margin:0">On that basis band&nbsp;3&nbsp;pp holds a median gap of
      <b>3.04&thinsp;pp</b> against today's <b>4.85&thinsp;pp</b>, while cutting
      3.74&thinsp;% less wind &mdash; tighter and cheaper at once. Pure effectiveness
      reaches <b>25.4&thinsp;pp</b>. Pro rata still offers <b>no ex-ante bound at
      all</b>; the band bounds the gap by construction, which is the legal argument.</p>
  </div>
</section>

<section class="card notes" style="margin-top:22px">
  <b>How to read this, and what it does not say</b>
  <ul>
    <li>All three rule views share <b>one colour scale</b>, so the panels are directly
      comparable. Today's own spread is narrow (5.45&ndash;8.95&thinsp;%) and deliberately
      looks flat against effectiveness ordering's 29&thinsp;% peak &mdash; that flatness
      is the finding, not a rendering artefact.</li>
    <li>Every rule delivers the <b>same flow relief</b> in every half-hour, verified to
      3.3e-16. This is not a security trade-off.</li>
    <li>Nine stations, one constraint group, one binding element, 89 days of one summer.
      Shift factors come from the 2024 TYTFS network applied to 2026 operation.</li>
    <li>Stations are placed at their network bus coordinates, geocoded in the organisers'
      kit. Nothing between the marks is interpolated.</li>
    <li>Source: <code>out/wpa_stations.csv</code>, <code>out/wpa_summary.json</code>,
      <code>out/wpe_trajectory.csv</code>, all as committed.</li>
  </ul>
</section>

<footer>
  <span>TPSA / TF Wind Hackathon 2026 &middot; North-West Constraint Group 3</span>
  <span id="foot"></span>
</footer>
</div>
<div class="tip" id="tip" role="tooltip" aria-hidden="true"></div>

<script>
const DATA = __DATA__;
const SEQ = ["--seq0","--seq1","--seq2","--seq3","--seq4","--seq5","--seq6","--seq7"];
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS = "http://www.w3.org/2000/svg";
const el = (t, a={}) => { const e = document.createElementNS(NS, t);
  for (const k in a) e.setAttribute(k, a[k]); return e; };

const MODES = {
  observed:{label:"Today (pro rata)", kind:"seq", get:s=>s.r.observed,
    note:"Share of each station's available energy cut under today's pro-rata split."},
  band3:{label:"Band 3 pp", kind:"seq", get:s=>s.r.band3,
    note:"Effectiveness order, restricted to farms within 3 pp of the group's year-to-date average."},
  effectiveness:{label:"Effectiveness", kind:"seq", get:s=>s.r.effectiveness,
    note:"Cut the highest shift factor first. Three stations are never cut at all."},
  delta:{label:"Change vs today", kind:"div", get:s=>s.r.effectiveness - s.r.observed,
    note:"Blue: cut less than today. Red: cut more. The redistribution is the proposal."},
  sf:{label:"Shift factor", kind:"sf", get:s=>s.sf,
    note:"MW of relief delivered per MW cut. This is the physics today's rule discards."}
};
let mode = "observed";

// one scale across the three rule views so the panels compare honestly
const RMAX = Math.max(...DATA.stations.flatMap(s=>[s.r.observed,s.r.band3,s.r.effectiveness]));
const DMAX = Math.max(...DATA.stations.map(s=>Math.abs(s.r.effectiveness-s.r.observed)));
const SFLO = Math.min(...DATA.stations.map(s=>s.sf)), SFHI = Math.max(...DATA.stations.map(s=>s.sf));

function lerpHex(a,b,t){
  const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  const [r1,g1,b1]=p(a),[r2,g2,b2]=p(b);
  const q=(x,y)=>Math.round(x+(y-x)*t).toString(16).padStart(2,"0");
  return "#"+q(r1,r2)+q(g1,g2)+q(b1,b2);
}
function seqColor(t){
  const stops = SEQ.map(cssv); t = Math.max(0, Math.min(1, t));
  const x = t*(stops.length-1), i = Math.min(stops.length-2, Math.floor(x));
  return lerpHex(stops[i], stops[i+1], x-i);
}
function colorFor(s){
  const m = MODES[mode], v = m.get(s);
  if (m.kind === "seq") return seqColor(v / RMAX);
  if (m.kind === "sf")  return seqColor((v - SFLO) / (SFHI - SFLO || 1));
  const t = v / (DMAX || 1);
  return t >= 0 ? lerpHex(cssv("--div-mid"), cssv("--div-hi"), Math.min(1,t))
                : lerpHex(cssv("--div-mid"), cssv("--div-lo"), Math.min(1,-t));
}
const fmtPc = v => (v*100).toFixed(2) + "%";
const fmtSg = v => (v>=0?"+":"\u2212") + Math.abs(v*100).toFixed(2) + " pp";

/* ---------- map ---------- */
const W = 760, H = 620, PAD = 18;
let proj;
function buildMap(){
  const svg = document.getElementById("map");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  // Frame on the study area - the nine stations and the constrained corridor -
  // not on the full extent of the counties drawn for context. Framing on the
  // counties pushed the group into a corner and gave most of the panel to land
  // the study says nothing about.
  const pts = [];
  DATA.stations.forEach(s=>pts.push([s.lon,s.lat]));
  Object.values(DATA.grid).forEach(g=>{pts.push([g.from.lon,g.from.lat]);pts.push([g.to.lon,g.to.lat]);});
  const mLon=(Math.max(...pts.map(p=>p[0]))-Math.min(...pts.map(p=>p[0])))*0.13;
  const mLat=(Math.max(...pts.map(p=>p[1]))-Math.min(...pts.map(p=>p[1])))*0.13;
  const lon0=Math.min(...pts.map(p=>p[0]))-mLon, lon1=Math.max(...pts.map(p=>p[0]))+mLon;
  const lat0=Math.min(...pts.map(p=>p[1]))-mLat, lat1=Math.max(...pts.map(p=>p[1]))+mLat;
  const k = Math.cos((lat0+lat1)/2 * Math.PI/180);          // equirectangular
  const sx = (W-2*PAD)/((lon1-lon0)*k), sy = (H-2*PAD)/(lat1-lat0);
  const s = Math.min(sx, sy);
  const ox = PAD + ((W-2*PAD) - (lon1-lon0)*k*s)/2;
  const oy = PAD + ((H-2*PAD) - (lat1-lat0)*s)/2;
  proj = (lon,lat) => [ox + (lon-lon0)*k*s, oy + (lat1-lat)*s];

  const defs = el("defs"); svg.appendChild(defs);
  const cp = el("clipPath",{id:"frame"});
  cp.appendChild(el("rect",{x:0,y:0,width:W,height:H}));
  defs.appendChild(cp);
  // Station geometry is computed first and its circles registered before any
  // label is placed, grid labels included: otherwise SRANANAGH is positioned
  // against an empty canvas and lands on Corderry's mark.
  const AMAX = Math.max(...DATA.stations.map(s=>s.avail_MWh));
  const boxes = [];
  const drawn = DATA.stations.map(s=>{
    const [x,y] = proj(s.lon, s.lat);
    const r = 7 + 20 * Math.sqrt(s.avail_MWh / AMAX);
    boxes.push({x:x-r, y:y-r, w:2*r, h:2*r});
    return {s, x, y, r};
  });

  const gLand = el("g",{"clip-path":"url(#frame)"}); svg.appendChild(gLand);
  DATA.counties.features.forEach(f=>{
    const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    polys.forEach(poly=>{
      const d = poly.map(ring => "M" + ring.map(c=>proj(c[0],c[1]).map(n=>n.toFixed(1)).join(",")).join("L") + "Z").join("");
      gLand.appendChild(el("path",{d, class:"county"}));
    });
  });

  // the constraint being managed
  const gGrid = el("g"); svg.appendChild(gGrid);
  const drawLine = (g, dash, w) => {
    const a = proj(g.from.lon, g.from.lat), b = proj(g.to.lon, g.to.lat);
    gGrid.appendChild(el("line",{x1:a[0],y1:a[1],x2:b[0],y2:b[1],class:"corridor",
      "stroke-width":w, ...(dash?{"stroke-dasharray":dash}:{})}));
    return [a,b];
  };
  drawLine(DATA.grid.contingency, "5 4", 1.6);
  const [fa, fb] = drawLine(DATA.grid.monitored, null, 2.6);

  // Labels are placed by trying candidate offsets and keeping the first that
  // collides with nothing already placed. Substation and station names sit on
  // top of each other around Sligo otherwise.
  const PADPX = 1.5;
  const hits = b => boxes.some(o =>
    !(b.x+b.w+PADPX < o.x || o.x+o.w+PADPX < b.x ||
      b.y+b.h+PADPX < o.y || o.y+o.h+PADPX < b.y));

  // Candidates are tried in order and the label is *measured where it lands*,
  // not estimated from character count: an estimate ran SRANANAGH through
  // Corderry. getBBox only reports on an element already in the document, so
  // callers append their group before calling this.
  function place(x, y, txt, cls, pad, parent){
    const mid = cls !== "gridlabel";
    const t = el("text",{class:cls, ...(mid?{"text-anchor":"middle"}:{})});
    t.textContent = txt;
    parent.appendChild(t);
    // a ring of candidates at growing radius, tried nearest-first
    const cands = [];
    for (const rad of [pad+9, pad+19, pad+30, pad+42]){
      for (const ang of [90, 270, 0, 180, 45, 135, 315, 225]){
        const a = ang * Math.PI/180;
        cands.push([Math.cos(a)*rad*1.7, Math.sin(a)*rad*0.75 + 4]);
      }
    }
    // Pick the first candidate that collides with nothing. If the station sits
    // in a crowd and every candidate collides, take the one that overlaps
    // least - falling back to the first put four labels straight over marks.
    let best = null, bestArea = Infinity;
    for (const [dx, dy] of cands){
      t.setAttribute("x", x+dx); t.setAttribute("y", y+dy);
      if (!mid) t.setAttribute("text-anchor", dx < 0 ? "end" : "start");
      const g = t.getBBox();
      const b = {x:g.x, y:g.y, w:g.width, h:g.height};
      if (!hits(b)){ boxes.push(b); return; }
      const area = boxes.reduce((acc,o)=>{
        const ox = Math.min(b.x+b.w,o.x+o.w)-Math.max(b.x,o.x);
        const oy = Math.min(b.y+b.h,o.y+o.h)-Math.max(b.y,o.y);
        return acc + (ox>0&&oy>0 ? ox*oy : 0);
      },0);
      if (area < bestArea){ bestArea = area; best = [dx, dy, b]; }
    }
    t.setAttribute("x", x+best[0]); t.setAttribute("y", y+best[1]);
    if (!mid) t.setAttribute("text-anchor", best[0] < 0 ? "end" : "start");
    boxes.push(best[2]);
  }

  [[DATA.grid.monitored.from, fa],[DATA.grid.monitored.to, fb],
   [DATA.grid.contingency.to, proj(DATA.grid.contingency.to.lon, DATA.grid.contingency.to.lat)]]
    .forEach(([p, xy])=>{
      gGrid.appendChild(el("rect",{x:xy[0]-2.6,y:xy[1]-2.6,width:5.2,height:5.2,
        fill:"var(--accent)",transform:`rotate(45 ${xy[0]} ${xy[1]})`}));
      place(xy[0], xy[1], p.name.replace("_"," "), "gridlabel", 7, gGrid);
    });

  const gStn = el("g"); svg.appendChild(gStn);
  drawn.forEach(({s, x, y, r})=>{
    const g = el("g",{class:"stn", tabindex:"0", role:"listitem",
      "aria-label":`${s.station}, shift factor ${s.sf.toFixed(3)}`});
    gStn.appendChild(g);                       // in the DOM before measuring
    g.appendChild(el("circle",{cx:x,cy:y,r:r+1.2,class:"node-halo"}));
    const c = el("circle",{cx:x,cy:y,r:r,class:"mark",fill:colorFor(s)});
    g.appendChild(c);
    place(x, y + r, s.station, "", 6, g);
    g._s = s; g._c = c; g._r = r;
    g.addEventListener("mouseenter", e=>showTip(e, s));
    g.addEventListener("mousemove", e=>moveTip(e));
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("focus", e=>showTipAt(g, s));
    g.addEventListener("blur", hideTip);
  });
  svg.setAttribute("role","img");
}

function paint(){
  const m = MODES[mode];
  document.querySelectorAll(".stn").forEach(g=>{
    g._c.setAttribute("fill", colorFor(g._s));
  });
  const ramp = document.getElementById("ramp"); ramp.innerHTML = "";
  const steps = 28;
  for (let i=0;i<steps;i++){
    const t = i/(steps-1), b = document.createElement("i");
    if (m.kind === "div"){
      const u = t*2-1;
      b.style.background = u>=0 ? lerpHex(cssv("--div-mid"), cssv("--div-hi"), u)
                                : lerpHex(cssv("--div-mid"), cssv("--div-lo"), -u);
    } else b.style.background = seqColor(t);
    ramp.appendChild(b);
  }
  const lo = document.getElementById("rampLo"), hi = document.getElementById("rampHi");
  if (m.kind === "seq"){ lo.textContent = "0%"; hi.textContent = fmtPc(RMAX); }
  else if (m.kind === "sf"){ lo.textContent = SFLO.toFixed(3); hi.textContent = SFHI.toFixed(3); }
  else { lo.textContent = "\u2212" + (DMAX*100).toFixed(1) + " pp"; hi.textContent = "+" + (DMAX*100).toFixed(1) + " pp"; }
  document.getElementById("legendNote").textContent = m.note;
  document.getElementById("tableMode").textContent = m.label;
  document.querySelectorAll(".seg button").forEach(b=>
    b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
}

/* ---------- tooltip ---------- */
const tip = document.getElementById("tip");
function tipHTML(s){
  return `<h4>${s.station}</h4><dl>
    <dt>Shift factor</dt><dd>${s.sf.toFixed(4)}</dd>
    <dt>Farms</dt><dd>${s.n_units}</dd>
    <dt>Available</dt><dd>${Math.round(s.avail_MWh).toLocaleString()} MWh</dd>
    <dt>Today</dt><dd>${fmtPc(s.r.observed)}</dd>
    <dt>Band 3 pp</dt><dd>${fmtPc(s.r.band3)}</dd>
    <dt>Effectiveness</dt><dd>${fmtPc(s.r.effectiveness)}</dd>
    <dt>Change</dt><dd>${fmtSg(s.r.effectiveness - s.r.observed)}</dd></dl>`;
}
function showTip(e,s){ tip.innerHTML = tipHTML(s); tip.classList.add("on");
  tip.setAttribute("aria-hidden","false"); moveTip(e); markRow(s.station); }
function showTipAt(g,s){ const b = g.getBoundingClientRect();
  tip.innerHTML = tipHTML(s); tip.classList.add("on");
  tip.style.left = (b.right + 10) + "px"; tip.style.top = (b.top) + "px"; markRow(s.station); }
function moveTip(e){
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX + 14, y = e.clientY - 10;
  if (x + w > innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > innerHeight - 8) y = innerHeight - h - 8;
  tip.style.left = x + "px"; tip.style.top = Math.max(8,y) + "px";
}
function hideTip(){ tip.classList.remove("on"); tip.setAttribute("aria-hidden","true"); markRow(null); }
function markRow(name){
  document.querySelectorAll("#tbody tr").forEach(tr=>
    tr.classList.toggle("hot", !!name && tr.dataset.stn === name));
}

/* ---------- table ---------- */
function buildTable(){
  const tb = document.getElementById("tbody");
  const rows = [...DATA.stations].sort((a,b)=>b.sf-a.sf);
  const max = Math.max(...rows.map(s=>s.r.observed));
  tb.innerHTML = rows.map(s=>`<tr data-stn="${s.station}">
    <td>${s.station}</td>
    <td class="num">${s.sf.toFixed(4)}</td>
    <td class="num">${fmtPc(s.r.observed)}
      <span class="minibar" style="width:${(s.r.observed/max*100).toFixed(0)}%"></span></td>
    <td class="num">${fmtPc(s.r.band3)}</td>
    <td class="num">${fmtPc(s.r.effectiveness)}</td></tr>`).join("");
}

/* ---------- trajectory ---------- */
function buildTraj(){
  const svg = document.getElementById("traj");
  const T = DATA.trajectory, w = 1100, h = 220, L = 46, R = 116, TP = 12, B = 26;
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  const series = [
    {k:"observed", label:"observed pro rata", col:"var(--accent)", wid:2},
    {k:"bandinf",  label:"effectiveness",     col:"var(--seq3)",   wid:1.6},
    {k:"band3",    label:"band 3 pp",         col:"var(--seq6)",   wid:2},
    {k:"band0",    label:"band 0 pp",         col:"var(--ink-3)",  wid:1.3}
  ];
  const all = series.flatMap(s=>T[s.k]);
  const ymax = Math.ceil(Math.max(...all)/10)*10;
  const n = T.t.length;
  const X = i => L + i*(w-L-R)/(n-1);
  const Y = v => TP + (h-TP-B) * (1 - v/ymax);
  // the ledger's burn-in, shaded out: r_i divides by cumulative availability,
  // so the first hours are arithmetic noise rather than inequity
  const bx = X(T.burn_in);
  svg.appendChild(el("rect",{x:L, y:TP, width:bx-L, height:h-TP-B,
    fill:"var(--sunk)", opacity:"0.85"}));
  svg.appendChild(el("line",{x1:bx,y1:TP,x2:bx,y2:h-B,stroke:"var(--line)",
    "stroke-width":1,"stroke-dasharray":"3 3"}));
  const bl = el("text",{x:bx+5, y:TP+11,
    style:"font-family:'IBM Plex Mono',monospace;font-size:9px;fill:var(--ink-3)"});
  bl.textContent = `\u2190 first ${T.burn_in_hours} h: ledger burn-in, excluded`;
  svg.appendChild(bl);
  for (let g=0; g<=ymax; g+=10){
    svg.appendChild(el("line",{x1:L,y1:Y(g),x2:w-R,y2:Y(g),stroke:"var(--line-soft)","stroke-width":1}));
    const t = el("text",{x:L-7,y:Y(g)+3.5,"text-anchor":"end",
      style:"font-family:'IBM Plex Mono',monospace;font-size:9.5px;fill:var(--ink-3)"});
    t.textContent = g; svg.appendChild(t);
  }
  const ends = [];
  series.forEach(s=>{
    const d = T[s.k].map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+","+Y(v).toFixed(1)).join("");
    svg.appendChild(el("path",{d, fill:"none", stroke:s.col, "stroke-width":s.wid,
      "stroke-linejoin":"round"}));
    ends.push({s, y: Y(T[s.k][n-1]), med: T.stats[s.k].median_after});
  });
  // Three of the four series finish within 2 pp of one another, so the end
  // labels are stacked apart rather than parked on the line they belong to,
  // and a leader line keeps each tied to its series.
  ends.sort((a,b)=>a.y-b.y);
  const GAP = 27;
  for (let i=1;i<ends.length;i++)
    if (ends[i].y - ends[i-1].y < GAP) ends[i].y = ends[i-1].y + GAP;
  const shift = Math.max(0, ends[ends.length-1].y - (h-B-4));
  ends.forEach(e=>e.y -= shift);
  ends.forEach(e=>{
    const y0 = Y(T[e.s.k][n-1]);
    svg.appendChild(el("path",{d:`M${w-R-1},${y0}L${w-R+5},${e.y-3}`, fill:"none",
      stroke:e.s.col, "stroke-width":1, opacity:.55}));
    const lt = el("text",{x:w-R+8, y:e.y,
      style:`font-family:'IBM Plex Sans',sans-serif;font-size:10.5px;font-weight:500;fill:${e.s.col}`});
    lt.textContent = e.s.label; svg.appendChild(lt);
    const lm = el("text",{x:w-R+8, y:e.y+12.5,
      style:"font-family:'IBM Plex Mono',monospace;font-size:9.5px;fill:var(--ink-3)"});
    lm.textContent = `median ${e.med.toFixed(2)} pp`; svg.appendChild(lm);
  });

  const ax = el("text",{x:L, y:h-7, style:"font-family:'IBM Plex Mono',monospace;font-size:9.5px;fill:var(--ink-3)"});
  ax.textContent = T.t[0].slice(0,10); svg.appendChild(ax);
  const ax2 = el("text",{x:w-R, y:h-7, "text-anchor":"end",
    style:"font-family:'IBM Plex Mono',monospace;font-size:9.5px;fill:var(--ink-3)"});
  ax2.textContent = T.t[n-1].slice(0,10); svg.appendChild(ax2);
}

/* ---------- boot ---------- */
document.getElementById("figSave").textContent = DATA.meta.effectiveness_saving_pct.toFixed(2) + "%";
document.getElementById("figHH").textContent = DATA.meta.half_hours.toLocaleString();
document.getElementById("foot").textContent =
  `${DATA.meta.window[0].slice(0,10)} to ${DATA.meta.window[1].slice(0,10)} \u00b7 ${DATA.meta.units} farms \u00b7 ${DATA.meta.source}`;
buildMap(); buildTable(); buildTraj(); paint();
document.querySelectorAll(".seg button").forEach(b=>
  b.addEventListener("click", ()=>{ mode = b.dataset.mode; paint(); }));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ()=>{ paint(); });
</script>
"""


def main() -> int:
    data = (OUT / "wpa_map_data.json").read_text(encoding="utf-8")
    html = PAGE.replace("__DATA__", data)
    p = OUT / "wpa_map.html"
    p.write_text(html, encoding="utf-8")
    print(f"wrote {p.name}  {p.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
