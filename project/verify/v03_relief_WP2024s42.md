# Verification section 10.3 - relief delivered and cut feasibility

Case `WP2024s42`. Rules found: band0, band1, band10, band2, band3, band5, bandinf, rule1, rule1N, rule2, rule3.

Rows that ever overload: FLG_SLIGO_N1, FLG_SLIGO_N0.

- hour-rule-row samples checked: **2244**
- samples where relief fell short of the overload by more than 1e-4: **0**
- worst shortfall: **1.421e-14 MW**

A non-zero shortfall is expected where a rule is capped by availability;
it is reported rather than asserted away.
