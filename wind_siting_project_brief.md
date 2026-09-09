---
title: "Locational Value of New Wind Capacity on the Irish Grid"
subtitle: "Project direction, method and context briefing --- TPSA Hackathon 2026"
date: "September 2026"
geometry: margin=2.5cm
fontsize: 11pt
colorlinks: true
toc: true
toc-depth: 2
---

\newpage

# 0. How to use this document

This is a **context dump**, written to be pasted into an AI assistant at the start of a
working session so that it understands the project without further explanation. It is
deliberately verbose and repeats itself where repetition prevents misunderstanding.

If you are an AI assistant reading this: the human is a second-year engineering student
at Trinity College Dublin working in a small hackathon team. They want short, precise,
technically accurate answers with no filler. They work in SI units. Assume competence in
MATLAB, Python, linear algebra and mechanical engineering; assume **no** prior background
in power systems, so define power-systems jargon the first time it appears.

The single most important instruction: **do not let this project drift into producing
numbers that the underlying data cannot support.** Section 6 explains exactly which
outputs are defensible and which are not. Every claim the team makes must survive the
question "would this still be true if the random seed changed?"

---

# 1. The competition and the problem domain

## 1.1 The event

TPSA Hackathon 2026, run by The Problem Solving Association CLG with the Trinity Floating
Wind Team and the Theoretical Physics Student Association of Ireland. Theme: *Efficiency
in Ireland's Electrical Grid*. Fourteen teams. The organisers had assistance from EirGrid
(Ireland's transmission system operator) in designing the problems and retrieving data.

The brief states that the organisers value robust, simple solutions over elaborate ones,
and that difficulty levels were deliberately not assigned to the listed problems.

## 1.2 The physical problem: dispatch-down

**Dispatch-down** is the umbrella term for renewable generation being ordered to reduce
output even though the wind is blowing or the sun is shining. In 2025, approximately
12--14 percent of Irish renewable generation was dispatched down. Total wind generated
across the island in 2025 was about 13,364 GWh.

Dispatch-down has three distinct causes, and conflating them is the most common error in
this problem domain:

**Curtailment** --- reduction for *system-wide* reasons, principally the System
Non-Synchronous Penetration (SNSP) limit. SNSP caps the fraction of demand that may be
met by non-synchronous generation (wind and solar, which connect through power
electronics and contribute no rotational inertia). Inertia is kinetic energy stored in
the spinning masses of conventional synchronous generators; it resists sudden frequency
change and buys operators time after a fault. As wind displaces conventional plant,
inertia falls and the Rate of Change of Frequency (RoCoF) after a credible event rises
toward operational limits. When SNSP binds, EirGrid's Wind Dispatch Tool applies a
**single system-wide scalar** across the whole wind fleet. It is not locational.

**Constraint** --- reduction because of *congestion on transmission infrastructure*. A
particular circuit would exceed its thermal rating, so generation that feeds that circuit
is cut. This **is** locational: it depends entirely on where the plant sits electrically.
Around 5--6 percent of Irish renewable energy is constrained, and the figure is forecast
to rise.

**Surplus** --- generation exceeds demand net of the minimum output that conventional
plant must maintain to stay online for reserve and stability. Thermal units have minimum
load levels, minimum up and down times, and start-up costs, so a must-run fleet stays on
the system even when wind alone could cover demand.

**This project is about constraint.** Curtailment is global and cannot be studied
locationally with the tools available. Surplus appears in the model as a by-product but
is not the target.

## 1.3 Constraint groups (how it works today)

When a network violation is anticipated, EirGrid's real-time lever is a **constraint
group**: a predefined set of wind and solar farms that receives a joint MW reduction
instruction. Membership is determined offline by an effectiveness study, so the control
room can fire a group instantly rather than solving a network problem live.

Membership is decided by **shift factor**. For each unresolved violation, the study
perturbs one representative farm at each candidate node by dP = 10 MW, balances
the change at a fixed remote conventional generator, re-runs the case, and measures the
change in flow on the monitored circuit:

```
SF(n) = (I2 - I1) / dP
```

Nodes whose shift factor magnitude clears a materiality threshold tau join the group;
the rest do not, regardless of geographic proximity. The study is run under a contingency
set Theta comprising the intact base case, N-1 (any one element out), and N-1-1 (a
second element out during repair of the first). Before violations are counted, mitigations
attributed by the brief to **SEM-11-062** are applied: dispatch down conventional and
lower-priority generation first, and sectionalise transmission equipment where possible.

Once a group is invoked, the required MW reduction is split across its members
**pro-rata** --- proportionally to capacity, not to effectiveness. A farm with a shift
factor of 0.05 is cut in the same proportion as one at 0.40.

Two consequences matter for this project:

1. Pro-rata splitting is energetically wasteful. It spills wind that barely relieves the
   violation alongside wind that relieves it strongly.
2. The group definitions are a **picture in the problem brief, not a dataset**. There is
   no machine-readable membership list in the participant kit.

---

# 2. The dataset

## 2.1 What the participant kit is

EirGrid publishes its Ten Year Transmission Forecast Statement (TYTFS) as four PSS/E
load-flow cases. The organisers converted these into PyPSA networks, geocoded the buses,
extracted a 15-node North-West region, attached a week of hourly profiles, and packaged
the result as a standalone kit with six worked example scripts.

| Case | Condition | Peak demand | Connected capacity |
|---|---|---|---|
| WP2024 | Winter peak, 2024 network | 7,325 MW | 22,650 MW |
| SV2024 | Summer valley, 2024 network | 4,948 MW | 14,591 MW |
| WP2033 | Winter peak, 2033 network | 8,792 MW | 42,574 MW |
| SV2033 | Summer valley, 2033 network | 6,058 MW | 18,283 MW |

Four cases times two scopes (transmission-only at 110 kV and above, and full-voltage)
gives eight networks. All are connected, all solve a DC power flow, all solve a linear
optimal power flow. **WP2033 is where constraint lives**: 42.6 GW of connected plant
against an 8.8 GW peak.

## 2.2 Kit contents

| File | Contents |
|---|---|
| `networks/` | 4 scenarios x 2 scopes, as `.nc` and as CSV folders |
| `gridkit.py` | load, edit, reset, save a network; read results back |
| `flowmath.py` | PTDF, edge-to-edge susceptibility, shift factors |
| `plotstyle.py` | shared palette |
| `examples/` | six worked scripts, (a) to (f) |
| `test_kit.py` | 20 checks, runnable without pytest |

The six example scripts: (a) DC power flow; (b) dispatch-down split into constraint-based
and surplus-based; (c) capacity expansion with a battery offered at every renewable bus;
(d) PTDF from the pseudoinverse of the weighted graph Laplacian; (e) edge-to-edge
susceptibility; (f) shift factors, reproducing the Wind Dispatch Tool calculation from the
same linear algebra as (d).

Repository: `https://github.com/farrencc/Hackathons`

Quickstart: `python -m venv .venv && source .venv/bin/activate`, then
`pip install -r requirements.txt`, then `python examples/a_dc_power_flow.py`.

## 2.3 What is real and what is fabricated

**Real, and trustworthy:**

- Network topology, reactances, transformer equivalents. Verified against each case's own
  solved voltage angles at correlation at least 0.99 on seven of eight networks (the eighth,
  WP2033 full-voltage, is 0.90).
- Circuit thermal ratings, taken as TYTFS RATE1. Note this is an *inference*: PSS/E carries
  up to 12 rating slots, RATE1 equals RATE2 exactly across all 4,841 branch records, and
  RATE3/RATE1 is 1.0 or 1.1, which the organisers read as normal/LTE/STE. Siemens' format
  manual is not public, so this is not a documented property.
- Line lengths. 83 percent of transmission branches carry one, correlating at r = 0.983
  with great-circle distance between independently geocoded endpoints. Seven circuits (six
  in Northern Ireland) carry no length; a per-km calculation must skip these rather than
  treat the gap as zero.
- Bus coordinates. 87 percent of transmission buses geocoded from OpenStreetMap and
  cross-checked against EirGrid's station register at a median separation of 14 metres.
  Nothing is interpolated: unmatched stations are left uncoordinated. The 2033 cases place
  only 78 percent, because stations that do not exist yet are not in OpenStreetMap.
- PTDF and shift factor machinery, checked against a power flow to roughly 10^-6 MW.

**Fabricated:**

- **Every hour of every time series.** `synthetic.py` generates profiles as a spatially
  correlated random field: exponential correlation decay with distance (L = 400 km) and
  an Ornstein-Uhlenbeck process in time, mapped through a Gaussian copula to a Weibull wind
  distribution. Seeded at `SEED = 42`, so deterministic and reproducible. Each scenario's
  week is anchored on an hour chosen to reproduce that case's own state, tapering back to
  the unconstrained field over 18 hours either side. No hour in them ever happened.
  Generators without a geocoded site borrow a neighbour's profile, making those pairs
  perfectly correlated when they should not be.
- **All costs.** Gas 90, biomass 40, hydro 1, imports 150 EUR/MWh; wind and solar bid
  -1 (representing a support-scheme generator willing to pay to stay on, so that being
  dispatched down is a last resort rather than a free choice); load-shedding at 10,000
  EUR/MWh, chosen to sit far above everything else and explicitly *not* the Single
  Electricity Market's real Value of Lost Load (12,533 EUR/MWh, 2022). **Only differences
  between two solves' objectives are meaningful.**

**Partly unreliable:**

- About one fifth of generation carries the carrier `unknown`. Carriers are inferred from
  bus-name prefixes and a keyword list; the files do not label plant by technology. Any
  result turning on the gas/unknown split is unsupported.
- The hand-built North-West dataset has a units bug: Cathaleen's Fall, Cliff and Golagh
  hydro all show capacity "38", which is not a real MW figure. Cathaleen's Fall is actually
  two machines of 22.5 and 23 MW in the TYTFS file. The 24-node and 15-node views disagree
  by exactly Cunghill's 35 MW because one includes it and the other does not.

## 2.4 Stated model limitations

- **DC approximation of an AC model.** Flows are linear in angle differences, voltages are
  1.0 per unit everywhere, losses are zero. Standard for transmission constraint work and
  good to a few percent on real flows, but it says nothing about voltage, reactive support
  or stability.
- **Ratings are planning values, not operational limits.** A control room works to seasonal,
  weather-dependent and dynamic limits absent from these files. Ratings also change between
  scenarios, so the same circuit carries a different rating in each of the four cases.
- **DC interconnectors are simplified.** Moyle, EWIC and Greenlink are PyPSA `Link`
  components (controllable injections), not part of the linear AC network, because the file
  does not model the GB side of two of them. Fixed efficiency, no ramp limits, no minimum
  stable export, no market coupling.
- **An unmodelled control device sits on the constrained north-western tie.** Both
  north-western cross-border ties (to Strabane and to Enniskillen) terminate at a
  phase-shifting transformer whose tap the model holds fixed. A tie's flow limit here is
  therefore thermal, not a control action; in reality SONI would redispatch around a
  binding constraint.
- The TYTFS data is EirGrid's, provided for reference only, describing a planning forecast
  rather than the operational system. Nothing in the kit is an EirGrid product or position.

## 2.5 The North-West region

Extracted as a 15-node, 18-circuit subnetwork covering Donegal, Sligo and Mayo. It has
**1,329 MW of plant against 239 MW of demand** --- it is a strong net exporter, which is
precisely why it is constrained.

Named substations in the region include: Ardnagappary, Trillick, Letterkenny, Tievebrack,
Drumkeen, Binbane, Clogher, Croaghonagh, Cathaleen's Fall, Cliff, Golagh, Sligo,
Srananagh, Corderry, Moy, Glenree, Cunghill.

**Critical preprocessing step.** The 15-node view merges Srananagh's two busbars into a
single node, which short-circuits the 250 MVA transformer between them and introduces up
to 21.6 MW of flow error against the full network. Almost all of the view's total error
comes from this one fold. Splitting Srananagh back into separate 110 kV and 220 kV buses
(16 nodes instead of 15) cuts the error to 1.7 MW. **Do this before trusting any number.**

---

# 3. Our chosen direction

## 3.1 The question

> For every candidate connection point on the network, if a new wind farm were built
> there, what would it cost or save the system as a whole --- and does that ranking agree
> with what a private developer would choose?

This is known in the literature as **hosting capacity analysis**, or a locational
connection impact assessment. EirGrid performs a version of this inside its ECP connection
process, but the published output is a queue position, not a map. Producing the map is the
contribution.

## 3.2 The two costs that must never be merged

When a new farm of size S connects at bus b, two separate things happen.

**Private cost.** The new farm is itself dispatched down for some fraction of the period.
This is what a developer sees and prices. Bad sites are self-punishing, so the market
already handles this reasonably well.

**External cost.** Every *existing* generator sharing the congested corridor is dispatched
down more than before. The new entrant does not pay this, does not observe it, and Irish
connection policy does not price it.

Keep these as two separate output columns. **Never combine them into a single score.** The
interesting result is where they disagree: buses that look attractive privately and are
destructive systemically. That divergence is the argument for locational connection policy
and is the headline finding if the project produces nothing else.

## 3.3 Metric definitions

Work in energy, not money, because the costs are placeholders.

Let E_own(b) be MWh delivered by the new farm over the study period, and
dE_ext(b) be the change in MWh delivered by all pre-existing renewables
(normally negative).

```
Private index(b) = E_own(b) / S

System  index(b) = ( E_own(b) + dE_ext(b) ) / S
```

Both are in MWh per MW installed. Report both as maps, plus a scatter of one against the
other. Treat all values as **ordinal**, not absolute.

---

# 4. The core insight: the three-factor decomposition

This is the conceptual heart of the project and the thing that distinguishes it from a
naive shift-factor map.

A site is only costly when **three conditions coincide**:

**Factor 1 --- WHERE (electrical sensitivity, static).** The shift factor
SF(b,e): how much flow lands on circuit e per MW injected at bus b. Derived
purely from topology and reactances. It is **signed** --- a negative value means injecting
at b *relieves* circuit e. It does not vary hour to hour.

**Factor 2 --- WHEN (network state, time-varying).** Whether circuit e is actually at or
near its thermal rating in a given hour. Depends on demand, on every other generator's
output, and on the rating itself.

**Factor 3 --- WHETHER (resource, time-varying).** Whether the farm at b is generating
in that hour. A becalmed farm cannot be dispatched down. Exposure is weighted by the
site's own output profile.

Combining them, the expected constraint energy for a unit of capacity at b is

```
C(b) = SUM over hours h, SUM over circuits e, of:

         [ 1 if circuit e is binding in hour h, else 0 ]
       x  | SF(b,e) |
       x  p_b(h)
```

where p_b(h) is the per-unit output of a farm at b in hour h.

**Why this matters.** A site with a large shift factor onto a circuit that rarely binds
costs almost nothing. A site with a small shift factor onto a permanently saturated
circuit costs a great deal. Most teams will produce a shift-factor map, which measures
Factor 1 alone and is therefore a property of the wires only. The metric above is a
property of the wires, the weather and the load together.

A further consequence: the *timing* of a site's output matters as much as its position. A
site whose windy hours fall outside the congested hours is systemically cheap even at a
mediocre electrical position.

**Caveat specific to this dataset.** The synthetic wind field uses a 400 km correlation
length, so all sites within the North-West are roughly 90 percent correlated. Within that
region Factor 3 is nearly constant across candidates, so the map is measuring almost pure
electrical position with resource differences stripped out. That is a clean experiment and
a real limitation --- state it explicitly. The effect only becomes visible all-island.

## 4.1 Everything else that must be considered

**Thermal rating.** The denominator in Factor 2. Ratings are scenario-dependent: the same
circuit carries different RATE1 values across the four TYTFS cases, so a site's score is
partly an artefact of which scenario was run. Run at least two cases and report where the
rankings agree. Dynamic Line Rating (allowing higher ratings in cold or windy conditions,
which is exactly when wind output is high) is a natural sensitivity to bolt on later.

**Sign of the shift factor.** Some buses relieve congested circuits. These are the
genuinely valuable sites, and they vanish if absolute values are taken everywhere. Keep
the sign in the physics; take magnitudes only when summing exposure.

**Contingency state (N-1).** A circuit that never binds intact may bind constantly after a
credible outage. EirGrid plans to N-1-1, so an intact-only map overstates headroom. At
minimum, screen against the worst single circuit outage. Full N-1-1 is likely out of scope.

**Saturation and nonlinearity.** Shift factors give the *marginal* effect of 1 MW. At
100 MW the ranking reorders as new circuits begin to bind. This motivates a capacity sweep
(Section 5), and "this bus is the best site up to 60 MW and among the worst above 120 MW"
is a far more interesting claim than a static ranking.

**Local demand.** A bus with substantial local load absorbs generation before it reaches a
constrained corridor. The North-West's 1,329 MW against 239 MW is the extreme case.

**Merit order and priority status.** In the model, dispatch-down order follows bid cost.
Priority and non-priority wind can be represented by a two-tier bid (-2 and -1), which
makes the optimiser cut non-priority first. The *mechanism* is trivial to implement. The
*data* --- which real farms hold priority status --- is not in the kit. Treat any priority
analysis as a clearly labelled sensitivity, never as a result.

---

# 5. Method

## 5.1 The simplifying assumption, and why it is legitimate

**We assume perfectly fluid dispatch-down: every generator can be curtailed
individually, in real time, against the network's actual thermal limits.**

This is not an extra assumption to implement. **It is what the kit's LOPF already does.**
A linear optimal power flow dispatches each generator independently against circuit
limits; there is no group structure in it. Script (b) is already the perfectly-fluid world.
The earlier, harder version of this project would have required *bolting groups on*.
Skipping that is a cleaner problem statement, not a shortcut.

It is also the only rung fully supported by the data, because the group definitions are
not in the dataset.

A useful property falls out for free: with all wind bidding -1, the optimiser spills
whichever wind relieves the binding circuit most efficiently. That is shift-factor-weighted
dispatch-down happening automatically, with no implementation effort.

This gives a three-rung ladder in which the gaps between rungs are themselves findings:

| Rung | Description | Status |
|---|---|---|
| 1 | Perfect nodal dispatch-down | LOPF as shipped |
| 2 | Grouped, shift-factor-weighted split | moderate extra work |
| 3 | Grouped, pro-rata split (today's practice) | needs group definitions (unavailable) |

The gap between rungs 1 and 3 is the energy cost of the current control scheme. The siting
map lives on rung 1 and must be **labelled as an upper bound on achievable performance**.

**Do not overclaim that this is free.** Perfect nodal dispatch-down requires no *network*
capital, but it does require: real-time security-constrained dispatch fast enough for a
control room under N-1-1; telemetry and setpoint control to every farm including currently
non-controllable ones; a state estimator good enough that the optimiser solves against
reality; and a connection-terms and compensation regime that works per-farm rather than
per-group. That is software, telemetry and regulation --- cheaper than a new 110 kV
circuit, but not zero. Constraint groups also exist for a real reason: they are precomputed
offline so the tool fires instantly, whereas a live optimiser must meet the same N-1-1
security standard in seconds. Say "no network capital", not "no capital".

## 5.2 Two-tier computation

Do not brute-force an LOPF at every bus.

**Tier 1 --- screen every candidate, cheaply.** For all candidate buses, compute the shift
factor onto every circuit and weight by that circuit's congestion hours in the baseline:

```
Score_1(b) = SUM over circuits e of  | SF(b,e) | x H_e
```

where H_e is the number of hours circuit e binds. This is one matrix operation on top
of a single baseline solve. It yields a full-island heatmap in seconds and is already a
presentable artefact.

**Tier 2 --- confirm the extremes with full simulation.** Take roughly the top 20 and
bottom 20 from Tier 1. For each, actually add a generator with a borrowed profile, re-solve
the LOPF over the study period, and measure E_own(b) and
dE_ext(b) directly. This is where saturation and nonlinearity appear.

**Then plot Tier 1 against Tier 2.** Points far off the diagonal are where the cheap linear
proxy misranks sites. This is a result in its own right, because the cheap proxy is what
gets used in practice.

## 5.3 Full pipeline

1. Split Srananagh into 110 kV and 220 kV buses (16 nodes, not 15).
2. Baseline LOPF over the study period. Call `gridkit.freeze_dispatch()` before any
   subsequent power flow.
3. Record per-circuit congestion hours H_e and per-generator dispatch-down. This is the
   reference state.
4. Tier 1 screen across all candidate buses. Produce the heatmap.
5. Tier 2 confirmation on the top and bottom 20.
6. Scatter Tier 1 against Tier 2; identify and explain misrankings.
7. Capacity sweep at 20 / 50 / 100 / 200 MW on the top ten. Expect reordering.
8. Re-run the final ranking on two or three different random seeds. Report which sites move.

Steps 1--4 constitute a complete, presentable deliverable on their own. Everything after
is upside. Build in that order.

## 5.4 Candidate set

"Every possible building location" is not well defined --- the model has buses, not land.
**Restrict candidates to existing transmission buses**, since connecting at a substation is
what actually happens, and state the restriction. Going further would require planning,
wind resource and land-use datasets that are not available.

---

# 6. What is defensible and what is not

This section governs every claim the team makes.

**Robust (real inputs, deterministic linear algebra --- survives a change of seed):**

- PTDF, LODF, shift factors, electrical distance
- Topology sensitivity, N-1 screening, min-cut and export ceilings
- **Rankings and ordinal maps**
- Structural statements about which circuits bind and which buses feed them

**Contaminated (inherits synthetic profiles or placeholder costs --- does not survive a
change of seed):**

- Any figure in euro
- Any absolute GWh per year
- Battery MWh sizing
- Claims of the form "reduces curtailment by X percent"
- Capacity factors

**Rule: present results as ordinal maps and relative indices.** Where an absolute number is
unavoidable, attach the seed and the scenario to it.

The multi-seed re-run in step 8 is the single cheapest way to pre-empt the strongest
objection available to a judge who has read the kit's appendix. Almost no other team will
do it.

---

# 7. Data audit

**Available and solid:** topology, reactances, ratings, line lengths, bus coordinates,
generator locations and capacities, PTDF and shift factor machinery, four demand scenarios.

**Available but requires care:** carrier labels (one fifth are `unknown`); North-West hydro
capacities (units bug on Cathaleen's Fall, Cliff, Golagh); demand shaping (synthetic).

**Not available --- must be assumed or dropped, and said out loud:**

- **Constraint group membership.** Figure 2 of the brief is a picture, not a table.
- **Priority versus non-priority status per farm.** The mechanism is easy; the assignment
  is unknown.
- **Observed historical line loadings.** Per-circuit loading is not published, and every
  hour in the kit is synthetic. Congestion frequencies H_e are therefore an **output of
  our own model, not an input from the world.** This must be stated plainly wherever H_e
  appears, or the work will look like it is claiming more than it can.
- Real wind resource data (ERA5 pipeline is documented in the repo but blocked).

**One thing to check in the repository:** the documentation says `synthetic.py` generates a
full year, but the shipped profiles are one week per scenario, and the participant kit
deliberately imports nothing from the build pipeline. If `synthetic.py` is present,
regenerate a full year --- seasonal variation matters considerably for a siting claim. If
it is absent, state plainly that the result covers one synthetic week.

---

# 8. Implementation traps

These are documented in the problem brief and will silently corrupt results.

**`freeze_dispatch`.** `n.optimize()` writes its answer to `generators_t.p`, but `n.lpf()`
reads `generators_t.p_set`. Running `lpf` straight after `optimize` without freezing gives
a power flow with no generation in it: the reference bus supplies the whole island and
circuits can show at 1600 percent of rating. Always call `gridkit.freeze_dispatch()`.

**A component with no profile silently runs flat out.** PyPSA defaults a missing
`p_max_pu` series to 1.0 rather than raising an error. Add a generator or battery without
a profile and it runs at full output every hour, with no warning. This is exactly how
7.8 GW of phantom wind entered the kit during its own build. **Every candidate generator
this project adds must be given an explicit profile** --- borrow the nearest geocoded
site's.

**Buses at 0 degrees N, 0 degrees E.** PyPSA's netCDF writer turns a missing coordinate
into 0.0 rather than NaN, which is in the Gulf of Guinea. Use `gridkit.placed_buses(n)`,
which drops these and respects the `coordinate_source` column. They turn out to be external
interconnectors.

**Folding machines together loses the carrier split.** If merging several generators at one
station, do it per carrier. Folding wind, solar and everything else into one generic unit
makes a wind-dominated region incapable of dispatching anything down, because there is no
"wind" left to lower. An early version of the North-West extraction had this bug.

**Shift factors depend on a chosen reference.** `shift_factors()` offers three conventions
for where the balancing megawatt comes from: spread over loads (`reference="load"`), spread
evenly over every bus (`reference="uniform"`, what the pseudoinverse gives statically), or
all at one named bus (the textbook slack convention). **Absolute numbers differ between
conventions; the ranking does not.** Use any one for ranking and treat raw magnitudes as
convention-dependent. Pick one, state it, and never mix.

**Solver degeneracy.** With all wind bidding an identical -1, the solver may be
indifferent between equivalent spill patterns, making results unstable between runs. If
this appears, add tiny per-generator cost jitter to break ties deterministically.

---

# 9. Validation

**The occupied-bus check --- run this early, it is the cheapest validation available.**
Overlay the Tier 1 ranking on where wind farms already exist. If the highly-ranked buses
are mostly already occupied, the method tracks the decisions real developers made, which is
strong evidence it is not producing noise. If the best buses are empty, either something
genuine has been found or there is a sign error --- and either way it must be explained.
Running this before the results reach a slide will catch a sign error in the shift factor
convention, which is the most likely single bug in the whole pipeline.

**Other checks:**

- Reproduce a known quantity from the kit's own example scripts before trusting new code.
- Confirm Tier 1 and Tier 2 agree in sign for the clearest cases.
- Confirm the Srananagh split reduces flow error as the brief states.
- Sanity-check that adding capacity at a bus with no congested circuits downstream produces
  a near-zero external cost.

---

# 10. Deliverables

**Primary:** a two-panel map of Ireland (or of the North-West), one panel per index ---
private and system --- with buses coloured by rank.

**Secondary:** the private-versus-system scatter, with the off-diagonal sites named. This
is the policy finding.

**Tertiary, if time allows:** the capacity sweep showing rank reordering with size; the
Tier 1 versus Tier 2 misranking plot; the seed-sensitivity table.

**Framing for the presentation.** Lead with the question, not the method: *"Ireland is
about to connect a great deal of new wind. Where it goes is currently decided by
landowners and developers, not by the network. Here is what that costs."* The
private-versus-system divergence is the argument. Everything else is supporting evidence.

State the limitations directly rather than waiting to be asked. A team that declares "our
absolute numbers are meaningless, our rankings are not, and here is the seed test that
proves it" is in a stronger position than one that presents confident euro figures built on
placeholder costs.

---

# 11. Glossary

**Bus** --- a node in the network model, corresponding roughly to a substation busbar.

**Circuit / branch** --- a transmission line or transformer connecting two buses.

**Constraint** --- dispatch-down caused by thermal congestion on a specific circuit.
Locational.

**Constraint group** --- a predefined set of farms that receives a joint reduction
instruction.

**Curtailment** --- dispatch-down for system-wide reasons, principally SNSP. Global, not
locational.

**DC power flow** --- linearised approximation in which flows depend linearly on voltage
angle differences, voltage magnitudes are fixed at 1.0 per unit, and losses are ignored.

**Dispatch-down** --- umbrella term for renewable output being reduced by instruction.

**Hosting capacity** --- how much new generation a network location can accept before
causing violations.

**Inertia** --- kinetic energy in spinning synchronous machines; resists frequency change.

**LODF (Line Outage Distribution Factor)** --- how flow redistributes onto remaining
circuits when one circuit is lost.

**LOPF (Linear Optimal Power Flow)** --- least-cost dispatch subject to linear network
constraints.

**N-1 / N-1-1** --- security standards requiring the system to survive the loss of any one
element, or a second loss during repair of the first.

**PTDF (Power Transfer Distribution Factor)** --- matrix mapping nodal injections to
circuit flows.

**PyPSA** --- Python for Power System Analysis, the open-source modelling framework the kit
is built on.

**Reactance** --- opposition to AC flow, roughly proportional to line length. Determines
how flow *splits* between parallel paths. Independent of thermal rating.

**RoCoF** --- Rate of Change of Frequency.

**Shift factor** --- change in flow on a monitored circuit per MW of injection change at a
node. Signed.

**SNSP (System Non-Synchronous Penetration)** --- share of demand met by non-synchronous
generation; capped to preserve inertia.

**Surplus** --- dispatch-down because generation exceeds demand net of must-run plant.

**Thermal rating** --- maximum MW a circuit can carry before overheating. Independent of
reactance.

**TYTFS** --- EirGrid's Ten Year Transmission Forecast Statement, the source of the network
cases.

**WDT (Wind Dispatch Tool)** --- EirGrid's real-time tool for issuing dispatch-down
instructions.

---

# 12. Open questions for the assisting AI

1. Is the Tier 1 congestion-weighted shift factor score the best cheap proxy, or is there a
   better closed-form screen that accounts for the sign of the shift factor and for
   whether the injection pushes flow toward or away from the binding direction?
2. How should the external cost be attributed when adding capacity at b causes a
   *different* circuit to become the binding one? The counterfactual is no longer a simple
   difference.
3. What is a defensible way to weight results across the four TYTFS scenarios into a single
   ranking, given that ratings and demand both differ between them?
4. Is there a cheap way to include the worst single contingency in the Tier 1 screen
   without a full N-1 sweep at every candidate --- for instance, precomputing the worst-case
   LODF-adjusted rating per circuit once, then reusing it?
5. How should saturation be detected automatically, so the capacity sweep can report the
   size at which each site's ranking breaks rather than testing fixed sizes?
