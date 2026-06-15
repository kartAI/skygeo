# STAC-struktur

## Eksempel på grunnstruktur

**Notater**
- Collections representerer et dataprodukt, et prosjekt eller lignende
- Collections bør ha rikelig med metadatainformasjon
- Items definerer bbox og timestamp
- Items bør ha definerte metadata-tags og navnekonvensjoner
- Assets arver bbox og timestamp
- Assets har data knyttet til item'et. 
    - Fks forskjellige filformater, forskjellige projeksjoner, metadata-filer, klippepolygoner

```txt
catalog
└── collection
    └── item
        └── asset
```

## Dataprodukt: Rovdyrtetthet

Eksempel på tidsserie for rovdyrtetthet:

```txt
catalog (miljodir)
├── bjoernetetthet_2012 (collection)
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

## Diskusjonspunkter

- Kan asset har sub boundinbox?
  --> model different spatial extens as separate items
- Tidsserie på collection eller item?
  --> item
