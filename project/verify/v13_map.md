# Verification - the constraint-group map

Independent re-derivation of everything `out/wpa_map.html` displays,
compared against the committed results, the organisers' network file and
the county boundaries. Neither generator module is imported.

Checks 19-22 are run against the *rendered* page in a browser, not the
source, and are recorded here with their results:

| 19 | no two labels overlap on the map | pass | 12 labels, 0 overlapping pairs |
| 20 | no label sits on top of a station mark | pass | 0 of 12 |
| 21 | no two labels overlap on the trajectory chart | pass | 20 labels, 0 pairs |
| 22 | nothing is drawn outside either viewBox | pass | 0 elements |

| # | check | result | detail |
|---|---|---|---|
| 1 | station set matches wpa_stations.csv | pass | 9 stations |
| 2 | displayed ratios equal cut/avail from source | pass | 27 values, worst 0.00e+00 |
| 3 | station cuts sum to the group totals | pass | observed 1.6e-16 effectiveness 0.0e+00 band 1.7e-16 |
| 4 | shift factors match WP2024s42_shift_factors.csv | pass | worst 2.78e-17 |
| 5 | coordinates are the model's bus positions | pass | worst 0.00e+00 deg |
| 6 | stations fall in their expected county | pass | all 9 correct |
| 7 | total cut ordering eff <= band 5 <= observed | pass | 10127 <= 10530 <= 11072 |
| 8 | headline saving reproduces from station rows | pass | 8.5349% vs 8.5349% |
| 9 | trajectory matches wpe_trajectory.csv | pass | 670 points, final observed 3.00 pp |
| 10 | 10 Corderry/Cunghill claim on the page is true | pass | 18.1 km vs 18.7 km, SF ratio 1.575 |
| 11 | 11 no-spatial-gradient statistic on the page is true | pass | Spearman +0.200, p=0.606 |
| 12 | 12 no interpolated surface in the page | pass | 9 discrete marks, no blur/IDW/kriging |
| 13 | 13 sequential ramp is monotone in lightness | pass | #eef4fc -> #0d2f63, 8 steps |
| 14 | 14 not colour-alone: table + size key + ramp | pass | table, size key, ramp legend, aria labels |
| 15 | 15 every CSS token used is defined | pass | 10 used, 15 defined |
| 16 | 16 warm-up statistics recompute from source | pass | warm-up 7.0 d = 336 half-hours, worst 0.00e+00 |
| 17 | 17 page is pure ASCII (charset-independent) | pass | no non-ASCII bytes |
| 18 | 18 rule views share a single colour scale | pass | RMAX spans observed, band3 and effectiveness |
| 19 | 19 map shows the recommended band | pass | b = 5 pp, saving 4.90 % (wpe_dominance.json) |

**19 of 19 checks pass.**

## Design parses

Five passes over the page against the brief: light-only, wordless,
uncluttered, not templated, minimal but complete.

| # | criterion | how it was tested | result |
|---|---|---|---|
| 1 | white, light only | grep for dark-mode rules; computed style with `prefers-color-scheme: dark` forced on the host | 0 dark rules; body and html both `rgb(255,255,255)` even on a dark host |
| 2 | no unnecessary words | extracted every visible string from the DOM and the injected JS | 48 static words + ~30 injected, all load-bearing. Cut: the lede, the how-to-read list, the callout prose, the notes, the footer sentence and the tooltip |
| 3 | uncluttered map | county borders dissolved to one coastline, counties 10 -> 5, contingency line and its two labels dropped; label boxes measured in the DOM | 0 label overlaps, 0 labels over marks, 0 outside the frame, at 1366x768 and 1920x1080 |
| 4 | not templated | 11 automated markers | no border-radius, shadow, gradient, emoji, centred text, Inter/Space Grotesk, serif display, cream ground, purple, or numbered eyebrows. Palette: 13 blues at hue 213-216 deg, one orange at 15 deg, white |
| 5 | minimal but complete, still accurate | one-screen fit at two projector sizes, plus checks 1-18 above | fits 768 and 1080 exactly, no horizontal overflow, 18/18 accuracy checks pass |
