# Locational pricing — source list for a research direction

Compiled 2026-09-08. Every link was fetched or HEAD-checked that day. Grouped so you can read in order:
foundations → Ireland's own history → the UK case study → Europe → what to read first.

## 1. Foundations (the theory everyone cites)

| Work | Why it matters |
|---|---|
| Schweppe, Caramanis, Tabors, Bohn, *Spot Pricing of Electricity*, Kluwer 1988 | The origin: hourly prices that vary by location because of congestion and losses. Book, not free online; university library. |
| Hogan, "Contract Networks for Electric Power Transmission", *Journal of Regulatory Economics* 1992 | Turns nodal prices into a tradeable market with financial transmission rights. Basis of PJM (1998) and every US nodal market. |
| Hogan & Harvey, "Locational Marginal Prices and Electricity Markets", 2022 — https://lmpmarketdesign.com/papers/locational_marginal_prices_and_electricity_markets_hogan_and_harvey_paper_101722.pdf | Current, readable summary by the people who designed it. |
| Pollitt, "LMPs for Electricity in Europe? The Untold Story", EPRG WP 2318, Cambridge, July 2023 — https://www.jbs.cam.ac.uk/wp-content/uploads/2023/12/eprg-wp2318.pdf | The sceptic's review: "the theory and modelling behind LMPs is strong, their wider theoretical rationale is less clear cut and the evidence on their impact in use is surprisingly weak." Read this before claiming LMP fixes anything. |
| Eicke & Schittekatte, "Fighting the wrong battle? A critical assessment of arguments against nodal electricity prices in the European debate", MIT Energy Initiative WP 2022-01 — https://energy.mit.edu/wp-content/uploads/2022/02/MITEI-WP-2022-01.pdf | The rebuttal to the sceptics. Pair with Pollitt. |
| "Locational Marginal Pricing: Towards a Free Market in Power", arXiv 2103.10937 — https://arxiv.org/pdf/2103.10937 | Short technical intro with worked examples; good for the maths. |

Physics link to your model: an LMP at bus b is exactly `n.buses_t.marginal_price` from the kit's optimiser, and its
congestion part equals minus the sum over lines of (shadow price × PTDF). You already compute this in `q4_siting.py`.
Your Tier-1 map *is* a nodal price map for a single week.

## 2. Ireland's own history (the "research from 20 years ago")

| Document | Date | What it decided |
|---|---|---|
| CER / NIAER, *SEM High Level Design Decision Paper*, AIP/SEM/42/05 | 10 June 2005 | Designed the SEM as a gross pool with **one island-wide price**. Locational signals were pushed out of the energy price into loss factors (TLAFs) and transmission use-of-system charges. Original PDF is not online; cited in the AFRY paper below. |
| AFRY (Pöyry), *Day-Ahead Market Coupling Options for the SEM* — https://afry.com/sites/default/files/2020-11/day-ahead-market-options-in-the-sem.pdf | 2020 | Cites and summarises the 2005 design choices. |
| SEM Committee, *System Operators' Review of Locational Signals*, SEM-09-046 — https://www.semcommittee.com/news/sem-09-046-systems-operators-review-locational-signals (PDF: https://www.semcommittee.com/files/semcommittee/media-files/SEM-09-046.pdf) | May 2009 | EirGrid/SONI questionnaire + workshop + industry papers on **locational TUoS charges and loss factors**. Options: locational vs postage stamp vs zonal TLAFs. Most respondents (Synergen, ESBI, wind developers) argued for postage stamp, i.e. *weaker* locational signals. Eight industry submissions attached (SEM-09-046A to H). This is the closest thing to a locational-pricing debate in the SEM. |
| SEM Committee, transmission losses review, SEM-10-039 / SEM-10-066 responses (e.g. https://www.semcommittee.com/files/semcommittee/media-files/SEM-10-066aj%20VPE%20response%20to%20SEM-10-039%20(Appendix%201).pdf) | 2010 | Follow-up on TLAFs; outcome was to keep generator-specific loss factors. |
| SEM Committee, *I-SEM High Level Design Decision*, SEM-14-085a — https://www.uregni.gov.uk/files/uregni/media-files/I-SEM_HLD_Decision_Paper.pdf | 17 Sept 2014 | The 2018 redesign. Locational energy pricing was **not** considered; "zonal" appears only in the EU cross-border sense. Any zone split "would be taken as part of the zonal reviews required by the EU". |
| SEM Committee, CRM T-4 2023/24 *Locational Capacity Constraint Areas* — https://www.semcommittee.com/news/crm-202324-t-4-locational-capacity-constraint-areas | ongoing | The one place the SEM already has locational signals in a market: the capacity auction defines constrained areas with local minimum requirements. Precedent to cite. |
| ESRI, Lynch, Longoria, Curtis, *Future market design options for electricity markets with high RES-E: lessons from the Irish SEM*, WP 702 — https://www.esri.ie/system/files/publications/WP702.pdf | May 2021 | Irish academic review of market redesign options for high renewables (co-authored at TCD). Mentions locational/nodal 17 times. |
| ACER Decision 11-2022 on alternative bidding zone configurations — https://www.acer.europa.eu/sites/default/files/documents/Individual%20Decisions/ACER%20Decision%2011-2022%20on%20alternative%20BZ%20configurations.pdf | Aug 2022 | ACER proposed zone splits for Germany, France, Italy, Netherlands, Sweden. **Ireland: no alternative configuration**, the island stays one zone. |

Summary of the Irish story: locational pricing in the *energy* market was never seriously on the table. Since 2005 the
signals have lived in loss factors and use-of-system charges, and the 2009 review shows industry pushing to weaken even
those. The 2014 redesign did not reopen it. Nothing in the 2020s has either.

## 3. The UK case study (the live one)

The most complete public record of a country trying to decide on locational pricing and stopping at the last step.

| Document | Date | Role in the story |
|---|---|---|
| National Grid ESO, *Net Zero Market Reform, Phase 3 Assessment and Conclusions* — https://www.neso.energy/document/258871/download (assessment of options: https://www.neso.energy/document/258876/download) | May 2022 | **The system operator itself recommended nodal pricing with central dispatch** as the most efficient net-zero design. Constraint costs had risen from £170m (2010) to £1.3bn (2022). International evidence: 2 to 4 percent operating-cost savings. |
| DESNZ, *Review of Electricity Market Arrangements* consultation — https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1098100/review-electricity-market-arrangements.pdf (collection: https://www.gov.uk/government/collections/review-of-electricity-market-arrangements-rema) | July 2022 | Government opens the question: nodal, zonal, or reformed national. |
| FTI Consulting for Ofgem, *Assessment of locational wholesale electricity market design options in GB* — https://www.ofgem.gov.uk/sites/default/files/2023-10/FINAL%20FTI%20Assessment%20of%20locational%20wholesale%20electricity%20market%20design%20options%20-%2027%20Oct%202023%205.pdf | Oct 2023 | The regulator's quantitative study of nodal vs zonal vs national. |
| Pollitt and Newbery academic reviews of the FTI study — https://www.ofgem.gov.uk/sites/default/files/2023-10/Michael%20Pollitt%20Academic%20Review%20of%20FTI%20Findings%20.pdf , https://www.ofgem.gov.uk/sites/default/files/2023-10/David%20Newbery%20Academic%20Review%20of%20FTI%20Findings%201698403308829_0.pdf | Oct 2023 | Two Cambridge economists picking the modelling apart. Good template for how to critique a siting model. |
| Aurora Energy Research, *Locational Marginal Pricing in GB*, public report — https://auroraer.com/wp-content/uploads/2023/09/Locational-Marginal-Pricing-GB-Aurora-Public-Report.pdf | Sept 2023 | Independent modelling of nodal prices for GB. |
| Strathclyde / UKERC, *Exploring Market Change in the GB Electricity System: the Potential Impact of LMP* — https://strathprints.strath.ac.uk/83869/ | 2023 | Stakeholder view; warns LMP without network investment risks the 2035 target. |
| Energy Systems Catapult, *Locational Energy Pricing in the GB Power Market* — https://es.catapult.org.uk/report/locational-energy-pricing-in-the-gb-power-market/ | 2021 | Early nodal modelling for GB. |
| FTI for Octopus, *Impact of zonal pricing on Energy Intensive Industries in GB* — https://octoenergy-production-media.s3.amazonaws.com/documents/FINAL_FTI_-_Impact_of_zonal_pricing_on_EIIs_in_GB_-_3_June_2025.pdf | June 2025 | The advocacy case: £55 to 74bn consumer savings claimed. |
| DESNZ, *REMA Summer Update 2025* — https://assets.publishing.service.gov.uk/media/686f71412557debd867cbeff/review-of-electricity-market-arrangements-rema-summer-update-2025.pdf | 10 July 2025 | **Decision: zonal pricing rejected, reformed national pricing kept.** Locational signals to come through network charges, connections reform, and strategic spatial planning instead. |

Why this matters for you: the UK reached the same end state Ireland is in, one price plus locational network charges,
but only after the TSO, the regulator, and four modelling houses had published nodal price maps. The GB map became
the argument; the argument lost on distributional grounds (Scottish generators, consumer bills), not on physics.
A siting map that shows the *external* cost, not the price, sidesteps the fight that killed zonal in GB.

## 4. Europe

| Document | Date | Note |
|---|---|---|
| ENTSO-E, *Locational Marginal Pricing Study of the Bidding Zone Review* — https://eepublicdownloads.blob.core.windows.net/public-cdn-container/clean-documents/Publications/Market%20Committee%20publications/ENTSO-E%20LMP%20Report_publication.pdf | June 2022 | First nodal simulation of Continental Europe **and Ireland**: 25,000 nodes, 22,000 lines. Nodal prices for Irish nodes exist inside this study. |
| ENTSO-E, Bidding Zone Review study release — https://www.entsoe.eu/news/2025/04/28/bidding-zone-study-released/ | April 2025 | Latest BZR outcome. |
| ENTSO-E BZR page — https://www.entsoe.eu/network_codes/bzr/ | — | Methodology and all reports. |

## 5. Read in this order for a research proposal

1. Pollitt 2023 (the sceptic) and Eicke & Schittekatte 2022 (the reply): one afternoon, gives you the whole debate.
2. NESO Phase 3 (2022) and the REMA Summer Update (2025): the case study, start and end.
3. SEM-09-046 (2009): what Ireland's industry said last time locational signals were on the table.
4. ENTSO-E LMP report (2022): confirm whether Irish nodal results are extractable; if yes, that is a validation set for your map.
5. Hogan & Harvey (2022) for the mechanics, when you write the method section.

## 6. Gaps

- The 2005 SEM design decision (AIP/SEM/42/05) is not online. Ask CRU or the SEM Committee library, or check the
  TCD library for the printed all-island project papers.
- No Irish-specific nodal price study exists outside the ENTSO-E 2022 exercise. That is the open space.
