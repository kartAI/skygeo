## Plan: N50 → N250 Complete Vector Style Port (DRAFT)

Goal is high visual parity with existing N50 MapServer cartography while delivering one complete production MapLibre style for N250 PMTiles. The approach uses a hybrid scale model (N250 metadata zoom bounds + MapServer-inspired tuning), preserves full thematic coverage, and implements data-driven labels from N250 text-placement attributes. The plan is structured to reduce mapping risk from schema differences (notably buildings, transport variants, and label fields) by producing a formal crosswalk first, then building style groups in strict cartographic draw order, and finally validating feature-by-feature against N50 expectations. It includes explicit acceptance criteria so the first “complete” style is objectively testable.

**Steps**
1. Build an authoritative N50 rule inventory from the MapServer sources in src/cng_cartography/n50_mapserver/veger.map, src/cng_cartography/n50_mapserver/arealdekkeflate.map, src/cng_cartography/n50_mapserver/vannflate.map, src/cng_cartography/n50_mapserver/vannkontur.map, src/cng_cartography/n50_mapserver/hoydekurver.map, src/cng_cartography/n50_mapserver/stedsnavn.map, src/cng_cartography/n50_mapserver/bygningsflate.map, src/cng_cartography/n50_mapserver/bygningspunkt.map, and src/cng_cartography/n50_mapserver/turisthytte.map; capture per-rule filter logic, symbolization recipe, and scale denominators.
2. Create a formal N50→N250 crosswalk matrix using src/cng_cartography/maplibre_styles/n250_metadata.json and src/planetiles2pmtiles/data/n250.yml, classifying each N50 rule as Exact, Renamed, Collapsed, or Missing; include primary filter attributes (objtype, vegkategori, vegfase, medium, anleggstype, banestatus, bygningskategori, vannbredde).
3. Define target style architecture from existing patterns in src/cng_cartography/maplibre_styles/style_n250_dark.json and src/cng_cartography/maplibre_styles/testapp/style_n250_arealdekkeflate.json: source definition, layer naming convention, ordered groups, and reusable paint/layout token strategy.
4. Specify canonical draw-order groups and lock them before implementation: background, landcover polygons, water polygons, protected/restriction polygons, contour/terrain lines, hydrology lines, admin boundaries, transport casing/core/overlays, POI/building points, and text labels.
5. Port polygon themes first (Arealdekke + water + restriction areas): implement complete objtype mapping tables and zoom windows per layer, using N250 min/max bounds as hard limits and MapServer parity for visibility tuning.
6. Port hydrology linework (shorelines, river centerlines) with multi-layer casing where needed; convert width/importance cues from N50 rules to MapLibre line-width expressions using vannbredde and zoom interpolation.
7. Port transport system fully from N250_Samferdsel_senterlinje: road hierarchy, tunnel/bridge/planned variants, ferries/trails, and rail classes via stacked layers (casing + fill + pattern/dash variants) to preserve N50 visual semantics.
8. Port administrative boundaries with priority-specific casing/dash patterns and collision-safe z-ordering so boundaries remain legible above landcover but below labels.
9. Port built-environment points (N250_BygningerOgAnlegg_posisjon and relevant arealdekke points) with explicit fallback classes where N50 bygningstype distinctions do not exist in N250; ensure every encountered class has a visible rule.
10. Implement data-driven labels using N250_Stedsnavn_tekstplassering (TextString, FontSize, Angle, alignment fields) and road-name labeling from transport attributes; add normalization policy for problematic literal values (Unicode/spelling variants) in filters.
11. Produce the complete production style JSON as the primary deliverable, and include a companion crosswalk document plus a QA checklist in the same style folder for maintainability and future regeneration.
12. Validate in the PMTiles viewer workflow used by docs/pmtiles_bakgrunnskart/n250/index.html, then run thematic QA passes (landcover, hydrography, transport, boundaries, labels) and a final unresolved-class sweep.

**Verification**
- Structural validation: style JSON loads in MapLibre without spec errors; all declared source-layer names match N250 metadata.
- Coverage validation: every N250 vector layer in metadata has at least one intentional style rule or explicit “not rendered” entry in crosswalk.
- Cartographic parity checks: side-by-side screenshots at low/mid/high zoom for representative extents (coast, urban, mountains, rail/road junctions).
- Label QA: collision behavior, orientation correctness, and font-size progression from data-driven fields.
- Regression checklist: no invisible major roads/water bodies, no unclassified dominant polygons, no symbol draw-order inversions.

**Decisions**
- Visual target: high parity with N50 MapServer output.
- Scale strategy: hybrid (N250 metadata bounds + MapServer-inspired tuning).
- Label strategy: data-driven where N250 fields allow it.
- First delivery scope: single complete production style JSON + documented crosswalk + validation checklist.
