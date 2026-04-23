# Vector Tiles → WMS

A small demo that renders vector tiles through MapLibre Native and exposes a minimal WMS-compatible image endpoint.

## Overview

This project uses:
- `@maplibre/maplibre-gl-native` for server-side map rendering
- `express` to provide a simple HTTP service
- `proj4` to transform geographic coordinates
- `@mapbox/geo-viewport` to calculate center/zoom from a bounding box
- `sharp` to encode rendered images as PNG or JPEG

The service is intentionally minimal and is not a complete OGC WMS implementation.

## Installation

Requirements:
- Node.js 18+ (ES module support and built-in fetch)

Install dependencies:

```bash
npm install
```

Start the demo server:

```bash
npm run server
```

Open the browser at:

```text
http://localhost:3000/
```

## Endpoints

### `/`
Serves the demo HTML page for quick testing.

### `/ows`
Minimal WMS-style endpoint for image rendering.

Supported query parameters:
- `SERVICE=WMS`
- `REQUEST=GetMap`
- `VERSION=1.3.0` or other `1.x`
- `CRS=EPSG:3857`
- `BBOX=minx,miny,maxx,maxy`
- `WIDTH=<pixels>`
- `HEIGHT=<pixels>`
- `FORMAT=image/png` or `image/jpeg`

Example request:

```text
http://localhost:3000/ows?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&CRS=EPSG:3857&BBOX=-20037508.34,-20037508.34,20037508.34,20037508.34&WIDTH=512&HEIGHT=512&FORMAT=image/png
```

## How it works

1. The app loads a MapLibre style from `https://demotiles.maplibre.org/style.json`.
2. Incoming `/ows` requests are validated for the required WMS parameters.
3. The requested `BBOX` is transformed from Web Mercator coordinates to geographic coordinates for viewport calculation.
4. `@mapbox/geo-viewport` computes the map `center` and `zoom` for the requested image size.
5. MapLibre renders a raw RGBA buffer.
6. `sharp` encodes the buffer to the requested image format and returns it.

## Limitations

- Not a full WMS server
- Supports only `EPSG:3857`
- Only `GetMap` requests are handled
- Only `image/png` and `image/jpeg` output
- No feature info, capabilities, or tiled WMS support
- Style is fixed and loaded from an external source

## Notes

This demo is mainly intended as a proof of concept for using vector tiles and server-side rendering to expose raster images through a WMS-like API.
