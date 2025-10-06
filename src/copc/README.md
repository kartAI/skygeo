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

**Excellent Results**: COPC shows dramatic performance improvements, especially for large datasets!

### Spatial Query Performance
- **Small regions (50m)**: **17.6x faster** than LAZ
- **Medium regions (100m)**: **9.1x faster** than LAZ  
- **Large regions (200m)**: **4.3x faster** than LAZ
- **Very large regions (500m)**: **1.2x faster** than LAZ

### Progressive Loading Performance
- **High detail (0.5m)**: 5.1x faster with 11.1% data reduction
- **Medium detail (2.0m)**: 10.9x faster with 84.3% data reduction
- **Low detail (10.0m)**: **75.4x faster** with 99.7% data reduction

### File Size Characteristics
- **COPC files can be smaller**: Observed 0.97x ratio (2.6% smaller)
- **Efficient compression**: Spatial indexing overhead offset by better compression
- **Use `forward: "all"`**: Preserves original compression settings

## 🏆 Key Performance Highlights

### Single Region Extraction
- **100m region**: COPC is **12.0x faster** (0.45s vs 5.39s)
- **Time saved**: 4.94 seconds per query
- **Same accuracy**: Identical point counts

### Multiple Region Performance
- **50m regions**: Average **17.6x speedup** (range: 9.0x to 37.7x)
- **100m regions**: Average **9.1x speedup** (range: 5.5x to 13.5x)
- **200m regions**: Average **4.3x speedup** (range: 2.3x to 6.9x)

### Progressive Loading Benefits
- **Overview mode (10m)**: **101.7x faster** for large regions
- **Bandwidth savings**: Up to 99.7% data reduction
- **Real-time visualization**: Perfect for web/mobile applications

## ⚠️ Important Notes

### Performance Scaling
The performance benefits scale with dataset size:
- **Small datasets (< 1M points)**: Moderate benefits
- **Large datasets (> 10M points)**: Dramatic improvements
- **Region size matters**: Smaller regions show greater benefits

### Best Practices
- **Always use `forward: "all"`**: Preserves compression and metadata
- **Test with your data**: Performance varies by dataset characteristics
- **Consider use case**: Benefits are most apparent for spatial queries

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
- COPC benefits scale with dataset size
- Test with your specific use case
- Performance varies by data characteristics

### 3. **Consider File Size Trade-offs**
- COPC files may be smaller or larger
- Benefits depend on data characteristics
- Spatial indexing overhead vs. compression gains

## 📊 Real-World Results

Based on testing with ISPRS dataset (19,253,870 points):
- **File size**: COPC 2.6% smaller than LAZ
- **Spatial queries**: **17.6x faster** for small regions
- **Progressive loading**: **75.4x faster** at low detail
- **Overall**: COPC provides exceptional spatial indexing with minimal size penalty

## 📊 When to Use COPC

### **Excellent for:**
- Large point cloud datasets (> 1M points)
- Web/mobile applications requiring fast queries
- Real-time visualization systems
- Multiple spatial queries on the same dataset
- Progressive loading requirements

### **Consider alternatives for:**
- Very small datasets (< 100K points)
- Single-use, non-spatial applications
- Storage-constrained environments

---

*For detailed examples and performance benchmarks, see the `las_to_copc.ipynb` notebook.*
