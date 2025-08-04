# COPC (Cloud Optimized Point Cloud) Conversion Tool

Convert LAS/LAZ point cloud files to COPC format for faster spatial queries and progressive loading.

## 🚀 Features

- Convert LAS/LAZ files to COPC format
- Fast spatial region extraction using built-in indexing
- Progressive loading at different detail levels
- Performance benchmarking tools

## 🛠️ Installation

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate copc_api
```

## 📦 Dependencies

- **PDAL**: Point cloud processing library
- **pandas**: Data manipulation
- **pyarrow**: Fast data serialization
- **fastparquet**: Parquet file support

## 🎯 Quick Start

### 1. Convert LAS/LAZ to COPC

```python
import pdal
import json

def convert_to_copc(input_file: str, output_file: str = "output.copc"):
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            {"type": "readers.las", "filename": input_file},
            {"type": "writers.copc", "filename": output_file}
        ]
    }))
    pipeline.execute()
    return output_file

# Usage
convert_to_copc("your_file.laz")
```

### 2. Extract Spatial Region

```python
# Extract data from specific region
region_bounds = "([513449.7,513549.7],[5402649.9,5402749.9])"

pipeline = pdal.Pipeline(json.dumps({
    "pipeline": [
        {
            "type": "readers.copc",
            "filename": "output.copc",
            "bounds": region_bounds
        }
    ]
}))
pipeline.execute()
points = len(pipeline.arrays[0])
print(f"Extracted {points:,} points")
```

### 3. Progressive Loading

```python
# Load at different detail levels
resolutions = [0.5, 2.0, 10.0]  # meters

for resolution in resolutions:
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            {
                "type": "readers.copc",
                "filename": "output.copc",
                "bounds": region_bounds,
                "resolution": resolution
            }
        ]
    }))
    pipeline.execute()
    points = len(pipeline.arrays[0])
    print(f"Resolution {resolution}m: {points:,} points")
```

## 📊 Performance Benefits

- **Small regions (50m)**: COPC is ~3.8x faster than LAZ
- **Medium regions (100m)**: COPC is ~2.7x faster than LAZ
- **Large regions (200m)**: COPC is ~1.6x faster than LAZ

## 📁 Files

- `environment.yml` - Conda environment setup
- `las_to_copc.ipynb` - Complete examples and benchmarks
- `README.md` - This file

## 🚀 Getting Started

1. Install: `conda env create -f environment.yml`
2. Activate: `conda activate copc_api`
3. Download test data: `wget https://github.com/PDAL/data/blob/main/isprs/CSite2_orig-utm.laz`
4. Open: `jupyter notebook las_to_copc.ipynb`
5. Follow the examples in the notebook

## 📁 Test Data

You can download a sample LAZ file for testing from the [PDAL data repository](https://github.com/PDAL/data/blob/main/isprs/CSite2_orig-utm.laz):

```bash
wget https://github.com/PDAL/data/blob/main/isprs/CSite2_orig-utm.laz
```

This file contains ISPRS test data that's perfect for experimenting with COPC conversion and spatial queries.

## ⚠️ Notes

- COPC files are larger than LAZ files (2-3x) but enable fast spatial queries
- Benefits are most pronounced for small to medium spatial queries
- PDAL installation may take several minutes

---

*For detailed examples and performance benchmarks, see the `las_to_copc.ipynb` notebook.*
