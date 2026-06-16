# STAC-struktur

## Hvorfor er STAC lurt?
- Eksempler på bruk av STAC
  - Integrasjon GeoNorge API
  - Dynamisk oppslag / visning
  - QGIS-integrasjon (gif)
  - ArcGIS Pro (gif)
  - Python-eksempel (notebook fks)
  - KI-agenter (claude-eksempel ++)

**Hva er STAC og hvordan lære mer om det**

| Ressurs | Beskrivelse |
|---------|-------------|
| [stacspec.org](https://stacspec.org) | Offisiell spesifikasjon |
| [Intro til STAC](https://stacspec.org/en/tutorials/intro-to-stac/) | Kom i gang-tutorial |
| [stacindex.org](https://stacindex.org) | Oversikt over kataloger og verktøy |
| [STAC Browser](https://radiantearth.github.io/stac-browser/) | Utforsk STAC-kataloger i nettleseren |

## Best practice

### Hierarki

```txt
catalog
└── collection
    └── item
        └── asset
```

### Ansvar per nivå

| Nivå | Representerer | Nøkkelansvar |
|------|---------------|--------------|
| **Collection** | Dataprodukt eller prosjekt | Rik metadata, lisensinformasjon, utstrekning |
| **Item** | En konkret forekomst (tid/sted) | `bbox`, `datetime`, navnekonvensjoner, metadata-tags |
| **Asset** | Én datafil knyttet til et item | Filformat, projeksjon, rolle (data/metadata/klipp) |

Assets arver `bbox` og `datetime` fra sitt Item — ikke dupliser disse.

### Navnekonvensjoner

Bruk konsistente, maskinlesbare navnekonvensjoner på alle nivå i hierarkiet

```
# Collection-navn
{produkt}
# eks: bjoernetetthet, vern, grunnkart_for_arealanalyse

# Item-navn
{produkt}_{område}_{år}
# eks: bjoernetetthet_2024, vern_kristiansand_2024

# Asset-navn
{produkt}_{område}_{år}_{epsg}_{format}
# eks: bjoernetetthet_norge_2024_25833_cog
```

## Dataprodukt: Rovdyrtetthet

Eksempel på tidsserie for rovdyrtetthet:

```txt
catalog (miljodir)
├── bjoernetetthet (collection)
│   ├── bjoernetetthet_2012 (item)
│   │   ├── bjoernetetthet_2012_25833_cog.tif
│   │   ├── bjoernetetthet_2012_25832_cog.tif
│   │   └── bjoernetetthet_2012_extent.parquet
│   ├── bjoernetetthet_2013 (item)
│   └── bjoernetetthet_2014 (item)
├── vern (collection)
│   ├── vern_norge_2024 (item)
│   │   ├── vern_norge_2024_25833_geoparquet
│   │   ├── vern_norge_2024_25833_stil
│   │   └── vern_norge_2024_25833_wms
│   ├── vern_kristiansand_2024 (item)
│   │   ├── vern_kristiansand_2024_25833_gpkg
│   │   ├── vern_kristiansand_2024_25833_geoparquet
│   │   └── vern_kristiansand_2024_25833_filegdb
│   └── vern_kristiansand_2025 (item)
└── grunnkart_for_arealanalyse (collection)
```


### Parquet-partisjonering

**TODO: **
- utdype - beskrive diskusjon - autoritative data
- eksempler / guidelines for hive-partisjonering. "where - statistikk", "distinct-data"

Et mulig oppsett for partisjonering:

```txt
kommune/
└── kommunenummer_*.parquet
```

Avklaring: Hva gjør vi når et verneområde ligger i to kommuner (to partisjoner)?

- Dagens løsning: Geometri lagres dobbelt. Ett verneområde kan ligge i både
  partisjon kommune A og B.
- Vurdering: Dette er ikke optimalt. Heller bruk Norge som fasit og unngå duplisering.

## Geovekst

Get geovekst prosjekt/dataprodukt from space x og time x?

```txt
catalog (geovekst)
├── geovekst_place_time_prosjekt (collection)
│   ├── sensor_place_time_1 (item)
│   │   ├── bilde_place_time_1_metadata (asset)
│   │   ├── bilde_place_time_1_tif (asset)
│   │   └── bilde_place_time_1_cog (asset)
│   ├── rgb_place_time_2 (item)
│   ├── lidar_place_time_1 (item)
│   ├── lidar_place_time_2 (item)
│   └── mosaic_place_time (item)
└── geovekst_place_time_prosjekt_2 (collection)
```