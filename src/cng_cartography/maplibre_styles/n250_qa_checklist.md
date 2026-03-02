# N250 style QA checklist

## 1) Structural validation
- [ ] `style_n250_complete.json` parses as valid JSON.
- [ ] Style loads in MapLibre without spec errors.
- [ ] All `source-layer` names resolve against `n250.pmtiles` metadata.

## 2) Layer coverage validation
- [ ] `N250_AdministrativeOmråder_grense` is rendered.
- [ ] `N250_AdministrativeOmråder_omrade` is rendered.
- [ ] `N250_AdministrativeOmråder_posisjon` is rendered.
- [ ] `N250_Arealdekke_grense` is rendered.
- [ ] `N250_Arealdekke_omrade` is rendered.
- [ ] `N250_Arealdekke_posisjon` is rendered.
- [ ] `N250_Arealdekke_senterlinje` is rendered.
- [ ] `N250_BygningerOgAnlegg_posisjon` is rendered.
- [ ] `N250_BygningerOgAnlegg_senterlinje` is rendered.
- [ ] `N250_Høyde_omrade` is rendered.
- [ ] `N250_Høyde_posisjon` is rendered.
- [ ] `N250_Høyde_senterlinje` is rendered.
- [ ] `N250_Restriksjonsområder_grense` is rendered.
- [ ] `N250_Restriksjonsområder_omrade` is rendered.
- [ ] `N250_Samferdsel_posisjon` is rendered.
- [ ] `N250_Samferdsel_senterlinje` is rendered.
- [ ] `N250_Stedsnavn_tekstplassering` is rendered.

## 3) Thematic parity checks (N50-inspired)
### Arealdekke
- [ ] Forest/cultivated/open/built-up classes are visually distinct.
- [ ] Water polygons match expected coastline/lake extents.
- [ ] Myr and glacier classes are visible and not confused with water fill.

### Samferdsel
- [ ] E/R/F roads are visually prioritized over K/P roads.
- [ ] Bridge (`medium=L`) and tunnel (`medium=U|B`) variants differ clearly.
- [ ] Planned roads (`vegfase=P`) use planned symbology.
- [ ] Sti and merket sti are distinguishable.
- [ ] Ferry routes (`bilferje`, `passasjerferje`) are visible and dashed.

### Jernbane
- [ ] Rail appears with separate normal/bridge/tunnel variants where data exists.

### Administrative boundaries
- [ ] Kommune/Fylke/Riks/Territorial/Grunnlinje classes are visually distinct.

### Høyde
- [ ] Minor and index contours are both visible.
- [ ] Depression/helper contours use alternative pattern.
- [ ] Height points are visible at inspection zoom.

### Labels
- [ ] Place names render from `TextString`/fallback fields.
- [ ] Label rotation follows `Angle` where populated.
- [ ] Font size changes with `FontSize` values.
- [ ] Road number labels appear for E/R/F with `vegnummer`.

## 4) Edge-case checks
- [ ] Encoding variants (e.g. `Å`/mojibake literals) do not cause missing classes.
- [ ] No dominant class disappears because of overly strict filters.
- [ ] No major cartographic collisions at low zoom in dense urban areas.

## 5) Acceptance gate for v1
- [ ] Full source-layer coverage achieved.
- [ ] No MapLibre runtime style errors.
- [ ] Parity review passes for at least three representative extents: coast, mountains, and city.
