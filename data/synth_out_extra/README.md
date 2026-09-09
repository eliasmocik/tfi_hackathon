# Extra synthetic years and the WP2024 wind-in network (generated 2026-09-09)

Built with the organisers' unmodified `synthetic.py` (github.com/farrencc/Hackathons, commit 61efd7b) from the raw TYTFS cases in that repo.

- `TYTFS2024_WP2024_V35_synthetic_2030_seed42_*` — a year of profiles for the 2024 network, seed 42. 541 generator columns.
- `TYTFS2024_WP2033_V35_synthetic_2030_seed43_*` — a second seed for the 2033 network, for the robustness check.
- `*_p_max_pu.csv.gz`, `*_loads_p_set.csv.gz` — gzipped to fit the transfer limit; `pd.read_csv(path, index_col=0, parse_dates=True)` reads them directly.
- `WP2024_all-island_windin.nc` — the organisers' WP2024 network plus the 410 wind/solar records the case flags out of service (6,272 MW wind instead of the kit's 10 MW), p_min_pu = 0 for the added units. Built by `kit_build/build_wp2024_windin.py` (needs the organisers' repo checked out for `psse.py`, `pypsa_net.py` and the raw case). Go/no-go result on it (`research/n1_gonogo/wp2024_windin_pst_link_step8.log`): with the Letterkenny–Strabane tie as a 93 MW link, Flagford–Sligo 110 kV is over its rating under loss of Flagford–Srananagh 220 kV in 20.8 % of sampled hours — the WDT Group 3 constraint, on the grid that matches the 2026 measurement. This is a deviation from the shipped kit: the TYTFS winter-peak 2024 case has 510 of 597 machine records at STAT = 0, and the kit drops them, so the shipped WP2024 (and SV2024, SV2033) networks carry no wind fleet and cannot be used for a wind-constraint study.

Before solving any year: clip `p_min_pu` per hour to the year's `p_max_pu` for thermal units (the synthetic availability drops below the static minimum), or the LOPF is infeasible. See `research/n1_gonogo/n1_test.py` for the three lines that do it.
