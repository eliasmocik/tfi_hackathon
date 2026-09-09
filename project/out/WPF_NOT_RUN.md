# WP-F (scenario layer) — not run, and why

Design brief v2 section 3 asks for three regimes, each with the full band
sweep: today's pro rata, non-priority-dispatch-first (SEM-24-044's stated
intent), and price-based ordering for post-2019 units.

## What blocks it on the real replay

The replay (WP-A) works on the 15 SEM-O units at CG3 stations. Classifying
those units as priority or non-priority requires matching them to
`data/eirgrid_gss1_res_units.csv`. **None of the 15 matches by name** — SEM-O
uses operational names ("Cloghervaddy 2 Windfarm", "Meentycat Generator Unit")
and the gss1 register uses site names with ordinals ("Corkermore (1)").

Matching on station plus capacity, as MASTER section 2.1 does for the model
generators, is not available here either: BM-101 gives a half-hourly declared
availability, not a registered MEC, and several CG3 stations carry more than
one unit of similar size.

A fuzzy name match over 15 units would produce a number, and the number would
not be defensible. The handoff already records that the official non-priority
list is not public and that the model-side classification is EirGrid's own
commissioning-date proxy matching 51 of 66 units. Guessing the split for the
real fleet and then reporting a euro or MWh consequence of it is exactly the
kind of claim the brief's evidence discipline exists to prevent.

## What is already established, and stands

The non-priority-first scenario **has** been run on the simulated side, as
rule 1N, and is in `out/RESULTS.md` and the per-case `summary.csv`:

> Rule 1N spills **more** than pro rata in all three cases (+0.07 to +0.28
> percentage points). The non-priority fleet has a lower capacity-weighted
> shift factor, so clearing through it first is less effective per MW.

That is the finding about SEM-24-044's stated intent, and it does not depend
on the real-unit classification. It should be reported as a simulated result,
which is what it is.

## What would unblock it

1. The official non-priority list, or a mapping from SEM-O resource IDs to the
   gss1 register (a registered-capacity column in the unit map would do it).
2. For the price-based regime, unit bid/offer data, which is not in the pulled
   BM reports at all.

Until then WP-F stays a simulated sensitivity, not a measured one.
