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
            {"type": "writers.copc", "filename": output_file, "forward": "all"}
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
region_bounds = "([453600.0,453700.0],[6456000.0,6456100.0])"

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

**Important Update**: Performance results vary significantly based on dataset characteristics and region sizes.

### Spatial Query Performance
- **Small regions (50m)**: Variable performance (0.3x speedup observed)
- **Medium regions (100m)**: Variable performance (0.2x speedup observed)  
- **Large regions (500m)**: Minimal benefit (0.0x speedup observed)

### File Size Characteristics
- **COPC files can be smaller than LAZ**: Observed 0.97x ratio (2.6% smaller)
- **Size depends on dataset**: Some datasets show compression benefits
- **Spatial indexing overhead**: May be offset by better compression

## ⚠️ Important Notes

### Performance Variability
The performance benefits of COPC are **highly dataset-dependent**:
- **Small datasets**: May show minimal or no performance improvement
- **Large datasets**: Benefits become more apparent
- **Region size matters**: Small regions may not benefit from spatial indexing

### File Size Expectations
- **COPC files can be smaller**: Not always larger as commonly expected
- **Compression varies**: Depends on input data characteristics
- **Use `forward: "all"`**: Preserves original compression settings

## 📁 Files

- `environment.yml` - Conda environment setup
- `las_to_copc.ipynb` - Complete examples and benchmarks
- `README.md` - This file

## 🚀 Getting Started

1. Install: `conda env create -f environment.yml`
2. Activate: `conda activate copc_api`
3. Download test data: `wget https://github.com/PDAL/data/raw/refs/heads/main/isprs/CSite2_orig-utm.laz`
4. Open: `jupyter notebook las_to_copc.ipynb`
5. Follow the examples in the notebook

## 📁 Test Data

You can download a sample LAZ file for testing from the [PDAL data repository](https://github.com/PDAL/data/raw/refs/heads/main/isprs/CSite2_orig-utm.laz):

```bash
wget https://github.com/PDAL/data/raw/refs/heads/main/isprs/CSite2_orig-utm.laz
```

This file contains ISPRS test data that's perfect for experimenting with COPC conversion and spatial queries.

## 🔍 Best Practices

### 1. **Always Use `forward: "all"`**
```python
{
    "type": "writers.copc",
    "filename": output_file,
    "forward": "all"  # Preserves compression and metadata
}
```

### 2. **Test Performance on Your Data**
- COPC benefits vary by dataset
- Test with your specific use case
- Don't assume universal performance improvements

### 3. **Consider File Size Trade-offs**
- COPC files may be smaller or larger
- Benefits depend on data characteristics
- Spatial indexing overhead vs. compression gains

## 📊 Real-World Results

Based on testing with ISPRS dataset (486,800 points):
- **File size**: COPC 2.6% smaller than LAZ
- **Spatial queries**: Performance varies by region size
- **Progressive loading**: Works as expected
- **Overall**: COPC provides spatial indexing with minimal size penalty

---

*For detailed examples and performance benchmarks, see the `las_to_copc.ipynb` notebook.*
