# Historical Data to COG Conversion Project

## Overview

This project demonstrates the conversion of historical map data from WMS (Web Map Service) to COG (Cloud Optimized GeoTIFF) format. The goal is to showcase the performance benefits of COGs over traditional WMS services and demonstrate scalable approaches for handling large geographic datasets.

## Project Structure

```
use_case/historiske_data/
├── main.py                    # Basic WMS to COG conversion
├── prepare_benchmark_data.py  # Data preparation and tiling
├── benchmark_setup.py         # Performance benchmarking server
├── cogs/                      # Generated COG files
│   ├── oslo_small.cog.tif    # Small area COG
│   ├── oslo_medium.cog.tif   # Medium area COG
│   ├── oslo_large.cog.tif    # Large area COG
│   └── demo_tiles/           # Tiled COG demonstration
└── README.md                  # This file
```

## Current Implementation

### Single COG Approach (Small Areas)

The project currently supports three test areas around Oslo:
- **oslo_small**: 1024×1024 pixels
- **oslo_medium**: 2048×2048 pixels  
- **oslo_large**: 4096×4096 pixels

Each area demonstrates direct WMS to COG conversion, suitable for manageable geographic regions.

### Multi-COG Tiling Approach (Larger Areas)

For larger areas, the project implements a tiling strategy:
- **3×3 grid** covering Oslo and surrounding regions
- **9 individual COG files** (2048×2048 pixels each)
- **Total coverage**: Approximately 600km × 600km
- **Tile index**: JSON metadata file for easy access

## Performance Benefits Demonstrated

### Load Time Comparison
- Direct timing of WMS vs COG access
- Progressive loading capabilities
- Tiled access for specific regions

### File Size Analysis
- Storage efficiency improvements
- Compression benefits
- Bandwidth optimization

### Scalability Features
- Performance across different resolutions
- Real-world web server performance
- Caching and distribution advantages

## Scaling Techniques for Large Datasets

When dealing with 100,000+ COG files, the current simple JSON index approach becomes impractical. Here are the recommended scaling strategies:

### 1. Hierarchical Directory Structure

**Most Common Approach**
```
/tiles/
  /zoom_10/
    /x_1234/
      /y_5678.cog
      /y_5679.cog
    /x_1235/
      /y_5678.cog
  /zoom_11/
    /x_2468/
      /y_11356.cog
```

**Benefits:**
- Easy to navigate and understand
- Excellent for CDN caching
- Scales to millions of files
- Simple to implement and maintain

**Use Case:** Most production deployments, especially when using traditional web servers or CDNs.

### 2. Quadkey/Geohash Encoding

**Spatial Encoding Approach**
```
/tiles/
  /quadkey_1234567890.cog
  /quadkey_1234567891.cog
  /quadkey_1234567892.cog
```

**Benefits:**
- Fast spatial queries
- Optimal for CDN distribution
- Compact URLs
- Excellent compatibility with web mapping libraries

**Use Case:** Web mapping applications, global tile services, CDN-heavy deployments.

### 3. Spatial Database + API

**Enterprise Solution**
```python
GET /api/tiles?bbox=minx,miny,maxx,maxy&zoom=10
GET /api/tiles/quadkey/1234567890
GET /api/tiles/search?region=oslo&resolution=high
```

**Benefits:**
- Flexible and complex queries
- Rich metadata support
- Dynamic filtering capabilities
- Good for complex use cases

**Use Case:** Enterprise applications, complex GIS systems, applications requiring rich metadata.

### 4. Cloud Storage + Serverless

**Modern Cloud Approach**
```
s3://bucket/tiles/zoom_10/x_1234/y_5678.cog
gcs://bucket/tiles/quadkey_1234567890.cog
```

**Benefits:**
- Auto-scaling capabilities
- Cost-effective for variable loads
- Global distribution
- Built-in CDN integration

**Use Case:** Cloud-native applications, global services, variable traffic patterns.

## Implementation Recommendations

### For Small to Medium Scale (Current Project)
- **Current approach**: Simple JSON index with file-based access
- **Suitable for**: Up to 1,000 COG files
- **Implementation**: Direct file system access with metadata files

### For Large Scale (100,000+ Files)
- **Recommended**: Hierarchical directory structure
- **Alternative**: Quadkey encoding for web mapping
- **Implementation**: Automated tile generation with consistent naming

### For Enterprise Scale (1M+ Files)
- **Recommended**: Spatial database + API approach
- **Alternative**: Cloud storage with serverless functions
- **Implementation**: Distributed architecture with caching layers

## Getting Started

### Prerequisites
```bash
pip install owslib pillow rasterio numpy fastapi uvicorn aiofiles python-multipart
```

### Data Preparation
```bash
cd use_case/historiske_data
python prepare_benchmark_data.py
```

### Start Benchmark Server
```bash
python benchmark_setup.py
```

### Access Endpoints
- **Root**: http://localhost:8000/
- **WMS Test**: http://localhost:8000/wms/oslo_medium
- **COG Test**: http://localhost:8000/cog/oslo_medium
- **Benchmark**: http://localhost:8000/benchmark/oslo_medium
- **Demo Tiles**: http://localhost:8000/demo_tiles
- **Tiling Benchmark**: http://localhost:8000/tiling_benchmark

## Real-World Applications

### Web Mapping
- Progressive loading of map tiles
- Efficient caching at CDN level
- Responsive user experience

### Mobile Applications
- Offline tile downloads
- Bandwidth optimization
- Progressive detail loading

### GIS Systems
- Efficient data access patterns
- Scalable architecture
- Cost-effective storage

### Scientific Computing
- Large dataset management
- Efficient spatial queries
- Distributed processing support

## Future Enhancements

### Planned Features
- Hierarchical tiling demonstration
- Cloud storage integration examples
- Performance benchmarking tools
- Automated tile generation pipelines

### Research Areas
- Optimal tile size calculations
- Compression algorithm comparisons
- Caching strategy optimization
- Distribution network analysis

## Conclusion

This project demonstrates the fundamental benefits of COG format over WMS services and provides a foundation for understanding scalable approaches to large geographic datasets. The current implementation shows the basic concepts, while the scaling techniques outline the path forward for production deployments handling thousands to millions of COG files.

The key insight is that COGs provide not just performance improvements, but also architectural flexibility that enables efficient serving of geographic data at any scale.