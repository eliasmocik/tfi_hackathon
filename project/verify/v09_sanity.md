# Verification section 10.9 - sanity

Case `WP2024s42`.

- total overload energy, all rows: **34,817.1 MWh** (`WP2024s42_overload_stats.json`)
- total cut under rule 1: **157,180.9 MWh**
- ratio cut / overload: **4.514**
- capacity-weighted mean effective shift factor: **0.2204**, so 1 / mean SF = **4.538**

MASTER section 10.9 expects the ratio to be of order 1 / mean SF: cutting 1 MW of wind removes only SF MW of flow, so relieving 1 MWh of overload costs about 1/SF MWh of spill.
- agreement: ratio / (1/mean SF) = **0.995** (1.0 would be exact)

- tie link `LKY-STRABANE-PST`: |flow| max 93.00 MW, at cap in **100.0 %** of hours
