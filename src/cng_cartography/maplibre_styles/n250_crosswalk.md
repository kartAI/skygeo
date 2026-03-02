# N50 MapServer → N250 PMTiles crosswalk

## Scope
This crosswalk ports cartographic intent from N50 MapServer `.map` files to N250 PMTiles vector layers in `n250_metadata.json`.

## Status legend
- **Exact**: direct semantic and attribute match.
- **Renamed**: same concept, different value spelling/encoding.
- **Collapsed**: multiple N50 classes merged into one N250 filter group.
- **Approximate**: no exact attribute equivalent; closest N250 mapping used.

## Layer mapping matrix

| N50 source | N50 class / rule | N250 source-layer | N250 filter attributes | Status | Notes |
|---|---|---|---|---|---|
| `arealdekkeflate.map` | Skog, DyrketMark, ÅpentOmråde, BymessigBebyggelse, Tettbebyggelse | `N250_Arealdekke_omrade` | `objtype` | Exact/Renamed | UTF-8 normalization required for `Å`, `ø`. |
| `arealdekkeflate.map` | Myr, SnøIsbre, Industriområde, Steinbrudd, Steintipp | `N250_Arealdekke_omrade` | `objtype` | Exact/Renamed | Same classes; some source spellings differ by encoding. |
| `arealdekkeflate.map` | Park/Sport/Gravplass/Alpinbakke/Golfbane | `N250_Arealdekke_omrade` | `objtype` | Collapsed | Grouped as leisure/green. |
| `vannflate.map` | Havflate, Elv, Innsjø, InnsjøRegulert, FerskvannTørrfall | `N250_Arealdekke_omrade` | `objtype` | Exact/Renamed | Unified water polygon styling. |
| `vannkontur.map` | Kystkontur, Innsjøkant, ElveKant, InnsjøkantRegulert | `N250_Arealdekke_grense` | `objtype` | Exact/Renamed | Water edge line class. |
| `veger.map` | E/R/F/K/P roads, tunnel, bridge, planned, motorveg | `N250_Samferdsel_senterlinje` | `vegkategori`, `medium`, `vegfase`, `motorvegtype`, `typeveg` | Exact | Implemented with stacked casing/fill layers. |
| `veger.map` | Bilferje, passasjerferje | `N250_Samferdsel_senterlinje` | `typeveg` | Exact | Dashed ferry lines. |
| `veger.map` | Sti, merket sti, traktorveg | `N250_Samferdsel_senterlinje` | `typeveg`, `rutemerking` | Exact | Patterned path symbology. |
| `jernbane.map` | Rail main, bridge, tunnel, planned | `N250_Samferdsel_senterlinje` | `objtype`, `anleggstype`, `medium`, `banestatus` | Approximate | N250 may mix rail in samferdsel with varying `objtype` literals. |
| `administrativegrenser.map` | Kommune/Fylke/Riks/Grunnlinje/Territorialgrense | `N250_AdministrativeOmråder_grense` | `objtype` | Exact | Width and dash hierarchy preserved. |
| `hoydekurver.map` | Høydekurve, hjelpekurve, forsenkningskurve, index contours | `N250_Høyde_senterlinje` | `objtype`, `medium`, `hoyde` | Exact/Renamed | Index contour every 100m emulated with modulo expression. |
| `hoydepunkt.map` | Terrengpunkt, trigpunkt labels | `N250_Høyde_posisjon` | `objtype`, `medium`, `hoyde` | Approximate | Symbol-only in v1; elevation text deferred to label pass. |
| `turisthytte.map` | Betjent/selvbetjent/ubetjent etc. | `N250_BygningerOgAnlegg_posisjon` | `betjeningsgrad`, `tilgjengelighet`, `objtype` | Approximate | Direct DNT-style symbols approximated with circle categories. |
| `bygningspunkt.map` | bygningstype numeric groups | `N250_BygningerOgAnlegg_posisjon` | `bygningskategori`, `objtype` | Approximate | `bygningstype` not present in N250 metadata. |
| `stedsnavn.map` | Dynamic label style from feature fields | `N250_Stedsnavn_tekstplassering` | `TextString`, `FontSize`, `Angle`, `HorizontalAlignment` | Exact | Data-driven label size/rotation included in style. |
| n/a (N250 only) | Restrictions polygons/lines | `N250_Restriksjonsområder_omrade`, `N250_Restriksjonsområder_grense` | `objtype`, `verneform` | Added | No explicit N50 file found in repository scan. |
| n/a (N250 only) | Administrative area fills | `N250_AdministrativeOmråder_omrade` | `fylkesnummer`, `kommunenummer` | Added | Optional subtle fill baseline for hierarchy context. |

## Known gaps
1. `N250_BygningerOgAnlegg_senterlinje` has no direct high-fidelity N50 equivalent in loaded map files; rendered as low-priority utility lines.
2. Exact icon glyph parity (church/hospital/tourist-hut symbols) is not available in current MapLibre sprite set.
3. Some Norwegian literals in legacy MapServer files are mojibake encoded; filters in JSON use normalized UTF-8 forms.

## Normalization rules used in style filters
- Treat `ÅpentOmråde` and legacy mojibake variants equivalently.
- Treat `Industriområde` and `IndustriomrÃ¥de` equivalently.
- Treat `SnøIsbre` and `SnÃ¸Isbre` equivalently.
- Treat `Innsjø` and `InnsjÃ¸` variants equivalently where relevant.

## Deliverables linked to this crosswalk
- `style_n250_complete.json`
- `n250_qa_checklist.md`
