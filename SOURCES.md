# Data sources — verified 2026-09-07

Every URL below was fetched today. "Local" = copy already sitting in the session scratchpad
(`/private/tmp/claude-501/-Users-elias-Desktop-aiOS-tfi-hackathon/9d3f668f-18dd-4cf6-93d1-b7c2fc2f1ab2/scratchpad/`)
or in this folder's `data/`. Move what you need into `data/` before the session ends.

## A. Network model (have)

| Source | What | Where |
|---|---|---|
| Hackathon kit | 8 PyPSA networks (4 TYTFS scenarios × all-island / north-west), 168 h synthetic profiles, `gridkit.py`, `flowmath.py`, 6 examples, 22 self-checks (pass) | github.com/farrencc/Hackathons → `grid_TF_Wind/participant-kit` |
| TYTFS 2024 study files | the 4 PSS/E `.raw` cases the kit was built from (V35; parser refuses V33). **No 2025 edition exists** | in repo `data/TYTFS2024_studyfiles/`; source https://cms.eirgrid.ie/sites/default/files/publications/TYTFS2024_studyfiles.zip |
| Bus geocoding | bus → lat/lon per case, cross-checked to EirGrid station register (median 14 m) | repo `data/pypsa/geocoding/<case>.csv` |
| EirGrid transmission geometry | 26,559 line sections (110/220/400 kV, overhead/cable, length) + 161 stations, EPSG:2157 | repo `data/eirgrid_transmission.gpkg` — real line geometry for the map backdrop |
| County polygons | 26 ROI counties | repo `data/counties_osi.gpkg` |
| Leaflet map scaffold | self-contained HTML map template + builder | repo `web/map_template.html`, `build_web_map.py` — reuse for the heatmap product |

## B. Weather / time series

| Source | What | Status |
|---|---|---|
| Kit synthetic week | 168 h, seed 42, the exact slice of the synthetic year | have |
| **Synthetic full year** | `synthetic.py build --case data/TYTFS2024_studyfiles/TYTFS2024_WP2033_V35.raw --year 2030 --seed 42 --out <dir>` → 8760 h p_max_pu for 710 units + loads. Runs in 5 s. `--seed N` = different weather year (the seed-sensitivity lever) | **done for WP2033**, local `synth_out/` |
| **ERA5 via Open-Meteo** | `profiles.py fetch --year 2023` → 146 cells, 6 requests; `profiles.py build --year 2023`. Reachable from this Mac (verified). Gives no demand series: pair with Smart Grid Dashboard demand | available, not fetched |
| Offshore + unplaced units | 82 records / 7,770 MW have no coordinates → no ERA5 profile. Coordinates in section E | need hand entry |

## C. Dispatch, constraint and unit registers

| Source | What | Grain | Status |
|---|---|---|---|
| **SEM-O BM-037 Daily Dispatch Instructions** | every WDT setpoint with code CURL/LOCL/CRLO/LCLO, to the second | per unit, per instruction, 2026-06-07 → today | have: `data/BM-037_dispatch_instructions_*.csv` (290k rows) |
| SEM-O BM-086 / BM-101 / BM-096 / BM-033 | metered MW / outturn availability / dispatch quantity / forecast availability | 30 min per unit, rolling ~3 months | API in `data/README.md` |
| **EirGrid DD Half-Hourly** | availability, output, dispatch-down split by cause (SNSP, RoCoF, transmission constraint, test, other) | 30 min, **IE / NI only**, 2021 → 2026 | https://cms.eirgrid.ie/sites/default/files/publications/DD-HH-2026-V8.xlsx (and DD-HH-2021…2025); local `ddhh2026.xlsx` |
| EirGrid DD Summary Report | monthly and quarterly dispatch-down by cause, **by region** (sheet "Regional Wind & Solar"), 2016 → | monthly/quarterly, region | https://cms.eirgrid.ie/sites/default/files/publications/DD-Summary-Report-V21.xlsx; local `dd_summary.xlsx` |
| EirGrid Annual Constraint & Curtailment Report 2025 | narrative + aggregates (monthly, hour-of-day, region). **No per-farm, no per-group figures** | — | https://cms.eirgrid.ie/sites/default/files/publications/Annual-Renewable-Constraint-and-Curtailment-Report-2025-V1.0.pdf |
| EirGrid WDT Constraint Group Overview | member stations per constraint group incl. outage variants; Appendix 1 pro-rata formula; Appendix 2 shift-factor procedure | — | this folder, `Wind-Dispatch-Tool-Constraint-Group-Overview_1.pdf` |
| **SEM-O IE CLAF 2025/26** | GU code → unit name, TSO id, transmission station, kV (233 IE units) | — | have: `data/semo_unit_map_IE.csv` |
| **SEM-O NI CLAF 2025/26** | same for 79 NI units (GU_5xxxxx) | — | https://www.sem-o.com/sites/semo/files/2025-09/2025%20-%2026%20NI%20CLAF%20Publication%20v1.pdf; local `ni_claf.txt` |
| SONI Approved TLAFs 2026/27 (xlsx) | all-island unit → market ID → station, one sheet, 324 GU rows | — | https://cms.soni.ltd.uk//sites/default/files/2026-09/2627%20Approved%20TLAFS%20.xlsx; local `soni_tlaf_2627.xlsx` |
| **EirGrid Controllability Status Update, June 2026** | every wind/PV plant: name, 110 kV station, MW, **Category (i)/(ii)/(iii)**, IE + NI (291 rows). Only 1 IE unit in category (i) | monthly | https://cms.eirgrid.ie/sites/default/files/publications/2026-06-June-Controllability-Status-Update.pdf; local `ctrl26.txt`. Join on plant name to CLAF |
| Non-priority dispatch (NPDR) per-unit list | **does not exist publicly** as of today. MPID 320 defines the category; designation still under TSO/RA review (FPM newsletter 27, Dec 2025) | — | https://cms.eirgrid.ie/sites/default/files/publications/MPID320-NPDR.pdf |
| Per-unit monthly dispatch-down reports | issued to each generator, **not published** | — | described in EirGrid Wind DD user guide |
| EirGrid Smart Grid Dashboard API | system wind actual/forecast, demand, generation, interconnection, SNSP; 15 min; back to 2014; ROI/NI/ALL only; **no availability, no dispatch-down** | 15 min | `https://www.smartgriddashboard.com/api/chart/?region=ROI&chartType=default&dateRange=day&dateFrom=YYYY-MM-DD&dateTo=YYYY-MM-DD&areas=windactual` (all five params required) |

## C2. EirGrid ECP constraint forecast studies — the closest existing product (verified 2026-09-07)

EirGrid runs a per-batch "Constraint Forecast Study" for connection applicants: PLEXOS, DC load flow,
N-1, full year, 2030 and 2035, 11 portfolio scenarios (Initial, 33/66/100 % ECP, + offshore, maintenance).
Wind and solar are modelled **at 110 kV node level**, constraints shared inside constraint groups
("subgroups"), two allocation rules (grandfathering: non-priority cut first; pro-rata).
Landing page: https://www.eirgrid.ie/industry/customer-information/ecp-constraint-forecast-reports

| File | What | Local |
|---|---|---|
| ECP-GSS-1 Constraint Analysis Excel Report (data freeze 2026-03-27) | 846 wind/solar/battery units with **node, controllability Y/N, priority / not-priority / uncontrolled**, MEC, status; per-node results (200 nodes × 2 years × 11 scenarios × 2 rules): installed, available, generated, surplus, curtailment, constraint GWh; binding line–contingency pairs with annual hours; reinforcements; outages; hourly interconnector flows | `data/EirGrid_ECP-GSS-1_Constraint_Analysis_2026-03.xlsx`, extracted `data/eirgrid_gss1_res_units.csv`, `data/eirgrid_gss1_node_results.csv` |
| Methodology | https://cms.eirgrid.ie/sites/default/files/publications/Constraint-Forecast-Studies-for-ECP-Methodology.pdf | scratchpad `ecp24_method.txt` |
| Ireland summary | https://cms.eirgrid.ie/sites/default/files/publications/Constraints-Forecast-Studies-for-ECP-GSS-1-Ireland-Summary.pdf | scratchpad `gss1.txt` |
| Earlier batches | ECP-2.1 Node-Results.xlsx … ECP-2.5 Excel, same page | — |

Unit classes in the GSS-1 list: controllable 632 / uncontrollable 214; wind priority 146, wind not-priority 157,
wind uncontrolled 110, solar not-priority 329, solar uncontrolled 6. Priority = connected before 2019-07-04
(EirGrid's own assumption, Article 12 of EU 2019/943). **This fills the priority and controllability gaps.**

What it does NOT contain: per-farm marginal impact (results are portfolio scenarios), attribution of
constraint to the entrant that causes it, a map. And the "nodal" results are uniform inside a subgroup:
every not-priority wind node in "A, B North" shows 37.8 % constraint in 2030 Initial and priority nodes 0 %,
because the study shares the cut pro rata inside the group. Nodal resolution *within* a group is exactly
what the kit's LOPF adds.

## D. Existing wind farms (for the occupied-bus check)

| Source | What | Caveat |
|---|---|---|
| **SEAI Wind Farms in Ireland** (CC-BY 4.0) | 334 ROI farms: name, DSO/TSO, county, status, MW, MEC, gate, **110 kV node name**, connection date, substation coordinates (ITM), type | frozen June 2022; coordinates are usually the substation, not the turbines. `F110kV_Node_Name` is the join key to kit stations. CSV https://seaiopendata.blob.core.windows.net/wind/WindFarmsConnectedJune2022.csv; shapefile `WindFarmsJune2022_ITM.zip` |
| Kit generators | 157 of 754 all-island buses host wind in WP2033 | already in the model; the SEAI file adds names and dates |
| WRI Global Power Plant DB | only 38 Irish wind rows | too thin |

## E. Coordinates for the unplaced offshore units (WGS84)

| Unit (kit name) | Array centroid | Onshore connection | Quality |
|---|---|---|---|
| NISA (W_NISA BELCA, 500 MW) | 53.680, −5.922 | Belcamp 220 kV | exact (EIAR boundary) |
| Sceirde Rocks (W_SKERD ROCK, 450 MW) | 53.263, −9.971 | Moneypoint 220 kV | exact (30 WTG positions) |
| Oriel (370 MW) | 53.920, −6.060 | new Stickillin 220 kV on Louth–Woodland | approx |
| Arklow Bank 2 (W_ARKLOW OFF, 800 MW) | 52.810, −5.950 | new Shelton Abbey 220 kV, Arklow | approx |
| Codling 1/2/3 (3 × 483 MW) | 53.100, −5.780 | Poolbeg 220 kV | approx |
| Dublin Array (824 MW) | 53.230, −5.918 | Carrickmines 220 kV via Jamestown | approx |
| Oweninny (W_OWENINEY_P, 172 MW) | Ph1+2 54.144, −9.743; Ph3 54.120, −9.565 | Srahnakilly 110 kV | good |

Sources: project EIARs on pleanala.ie (NISA, Sceirde, Oriel, Arklow, Codling), developer sites, GEM wiki. Offshore ERA5 needs `--model era5` (not era5_land).

## F. Zoning (for the policy slide, not the model)

No national wind-zoning GIS exists. Per-county open data: Kildare (gpkg, 2026), Galway (ArcGIS FeatureServer, 5 classes), Wexford (FeatureServer). Others are PDF appendices to county development plans.

## G. Still genuinely missing

- Per-farm priority / non-priority status (no public list; treat as a labelled sensitivity).
- Per-farm historical dispatch-down beyond the SEM-O 3-month window.
- Observed per-circuit loadings (never published; congestion hours are a model output, say so).
