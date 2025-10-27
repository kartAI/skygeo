from typing import Iterator
import fiona
from fiona.transform import transform_geom
import geopandas as gpd
import os
from pathlib import Path


DATA_DIR = os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data")
FGDB_FILE = os.getenv(
    "FGDB_FILE", 
    "Basisdata_0000_Norge_25833_N50Kartdata_FGDB/Basisdata_0000_Norge_25833_N50Kartdata_FGDB.gdb"
)
FILE_PATH = Path(DATA_DIR, FGDB_FILE)


def transform_crs(input_file: Path, output_file: Path):
    target_crs = "EPSG:4326"

    with fiona.open(input_file) as src:
        meta = src.meta
        meta['crs'] = target_crs

        with fiona.open(output_file, 'w', **meta) as dst:
            for feat in src:
                geom = transform_geom(src.crs, target_crs, feat['geometry'])
                feat['geometry'] = geom
                dst.write(feat)

def main():
    dirs = {"parquet":None, "fgb":None, "temp":None}
    ignored_layers = ["N50_Arealdekke_omrade"]
    for dir in dirs.keys():
        dirs[dir] = Path(DATA_DIR, "out", dir)
        dirs[dir].mkdir(exist_ok=True)

    for layer in fiona.listlayers(FILE_PATH):
        print(layer)
        if layer in ignored_layers:
            print("layer is ignored..")
            continue
        layer_name = layer.lower()

        gdf = gpd.read_file(FILE_PATH, layer=layer)

        # gdf.to_parquet(
        #     path= dirs["parquet"]/f"{layer_name}.snappy.parquet",
        #     compression="snappy",
        #     geometry_encoding="WKB",
        #     write_covering_bbox=True,
        # )

        gdf.to_file(
            filename=dirs["temp"] / f"_{layer_name}.fgb",
            driver="FlatGeoBuf"
        )
        # Memory efficient crs transform to support leaflet
        transform_crs(
            dirs["temp"] / f"_{layer_name}.fgb",
            dirs["fgb"] / f"{layer_name}.fgb",
        )

if __name__ == "__main__":
    main()
