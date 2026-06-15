# STAC struktur

## Eksempler STAC strukturer til forksjellige use-cases

```txt
catalog
└── collection
    └── item
        └── asset
```

## Dataprodukt "Rovdyrtetthet"

Example Rovdyrtetthet tidserie:'

```txt
catalog (geonorge/miljodir)
├── rovdyrtetthet (collection)
│   ├── rovdyrtetthet_2012 (item)
│   │   ├── rovdyrtetthet_2012_25833_cog.tif
│   │   ├── rovdyrtetthet_2012_25832_cog.tif
│   │   └── rovdyrtetthet_2012_beregningsgrunnlag.parquet
│   ├── rovdyrtetthet_2013 (item)
│   └── rovdyrtetthet_2014 (item)
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
└── grunnkart (collection)
```

Parquet-partisjonering
Et mulig oppsett for partisjonering er:

kommune/
└── kommunenummer\_\*.parquet

Aktiv-valg: Hva hvis en verneområder ligger i to kommuner (to partioneringer?)
per i dag: ligger "geometrier" dobbelt, 1 verneområde kan ligge i både partiotion kommune A og B
--> ikke optimalt heller bruk norge som fasit

## Geovekst

Get geovekst prosjekt/dataprodukt from space x og time x?

```txt
catalog (geovekst)
└── geovekst_place_time_prosjekt (collection)
    ├── sensor_place_time_1 (item)
        ├── bilde_place_time_1_metadata (asset)
        ├── bilde_place_time_1_tif (asset)
        └── bilde_place_time_1_cog (asset)
    ├── rgb_place_time_2
    ├── lidar_place_time_1
    ├── lidar_place_time_2
    └── mosaic_place_time
└── geovekst_place_time_prosjekt_2 (collection)
```

## Diskusjonspunkter

- Kan asset har sub boundinbox?
  --> model different spatial extens as separate items
- Tidsserie på collection eller item?
  --> item
