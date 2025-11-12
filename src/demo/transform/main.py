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


def reproject_flatgeobuf(src_path, dst_path, target_epsg, src_epsg=None):
    import subprocess
    cmd = ["ogr2ogr", "-f", "FlatGeobuf", dst_path, src_path, "-t_srs", f"EPSG:{target_epsg}"]
    if src_epsg:
        cmd.extend(["-s_srs", f"EPSG:{src_epsg}"])
    subprocess.run(cmd, check=True)

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
    include_layers = ["N50_samferdsel_senterlinje"]
    for dir in dirs.keys():
        dirs[dir] = Path(DATA_DIR, "out", dir)
        dirs[dir].mkdir(exist_ok=True)

    for layer in fiona.listlayers(FILE_PATH):
        print(layer)
        if layer in include_layers:
            layer_name = layer.lower()

            gdf = gpd.read_file(FILE_PATH, layer=layer)

            gdf.to_parquet(
                path= dirs["parquet"]/f"{layer_name}.snappy.parquet",
                compression="snappy",
                geometry_encoding="WKB",
                write_covering_bbox=True,
            )

            # fgb needs to be reprojected to EPSG:4326 for leaflet support
            temp_file = dirs["temp"] / f"_{layer_name}.fgb"
            fgb_file = dirs["fgb"] / f"{layer_name}.fgb"

            gdf.to_file(
                filename=temp_file,
                driver="FlatGeoBuf"
            )

            # Pythonic transform
            transform_crs(
                input_file=temp_file,
                output_file=fgb_file
            )

            # # Using this function is faster and more memmory efficient,
            # # but it requires ogr2ogr in your Path.
            # reproject_flatgeobuf(
            #     src_path=temp_file,
            #     dst_path=fgb_file,
            #     target_epsg="4326"
            # )
        else:
            print("layer is ignored")

if __name__ == "__main__":
    main()
