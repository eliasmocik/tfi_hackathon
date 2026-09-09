# Verification section 10.1 - LODF re-derived from the PTDF

Case `WP2024s42`. Contingency `2522-5042-1`, end buses 2522 and 5042.

LODF[l,k] = (H[l,a] - H[l,b]) / (1 - (H[k,a] - H[k,b])), H the bus PTDF.

- re-derived denominator: **0.224264205328567**
- denominator in `WP2024s42_lodf.csv`: **0.224264205328388** (difference 1.795e-13)

| monitored row | re-derived | lodf_kit | bodf_pypsa | max abs diff |
|---|---|---|---|---|
| 2521-4981-1 | 0.304138987224756 | 0.304138987225447 | 0.304138987225029 | 6.914e-13 |
| T2522-2521-25221-1-w1 | -0.292434226954430 | -0.292434226954765 | -0.292434226954540 | 3.346e-13 |
| T2522-2521-25222-2-w1 | -0.281229008641375 | -0.281229008641698 | -0.281229008641481 | 3.225e-13 |

- worst |re-derived - saved|: **6.914e-13**

The saved table already carries the kit's own LODF and pypsa's BODF and
reports them agreeing to 4e-13. This is a third, independent route to the
same three numbers.

Note for a future verifier: `ptdf_rows.parquet` is the post-contingency
row sensitivity, so its bus difference already equals the LODF. The
intact bus PTDF for this derivation is `ptdf_full.parquet`, keyed by the
branch name.
