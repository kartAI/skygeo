# MapServer N50 layers

Denne mappen inneholder alle layer-filene som definerer kartografien til N50-kartadata i WMS-tjenesten https://wms.geonorge.no/skwms1/wms.kartdata?service=WMS&request=GetCapabilities (denne tjenesten inneholder også resten av N-serien).

Kartografien baserer seg på [spesifikasjonen for skjermkartografi](https://register.geonorge.no/tegneregler/spesifikasjon-for-skjermkartografi), men følger ikke strukturen til [SOSI-produktspesifikasjonen](https://objektkatalog.geonorge.no/Pakke/Index/EAPK_20938D3D_0D15_466e_85CB_65D658EBF8FD). Kilden til MapServer er PostGIS, slik den forekommer i PostGIS-filene fra Geonorge, *men* det er også gjort en del tilpasninger av dataene i materialized views (derfor går mange av spørringene mot tabeller som ender med "_matview").

Disse filene vil uansett gi oss et utgangspunkt for å kunne style N50 vector tiles!
