<!--
  Inline MapLibre GL preview of a STAC item's PMTiles asset (viewer override).

  Mounted as a lazy <b-tab> in the patched views/Item.vue, so this component (and the
  basemap + the archive's tiles) only load when the user opens the "Data preview" tab.

  - basemap: window.STAC_BROWSER_CONFIG.basemapStyleUrl (defaults to the free MapLibre demo
    style; swappable to the Norkart style later via the viewer's /config.js).
  - item overlay: the item's own PMTiles asset, fetched through the viewer's same-origin
    /s3 signing proxy (range-aware) via the `pmtiles://` protocol — works for private assets.
  - vector items get one highlighted fill/line/circle layer set per source-layer, derived
    from the `pmtiles:vector_layers` metadata the scanner already stores (no archive re-read
    for setup). raster items (tile_type png/jpeg/webp/avif) get a single raster layer.
  - click a feature on the overlay -> popup with its attributes (vector only).
-->
<template>
  <div class="maplibre-preview">
    <div v-if="!pmtilesAsset" class="ml-empty">No PMTiles asset on this item.</div>
    <template v-else>
      <div ref="map" class="maplibre-map" />
      <div v-if="zoom !== null" class="ml-zoom">z {{ zoom }}</div>
      <div v-if="error" class="ml-error">{{ error }}</div>
    </template>
  </div>
</template>

<script>
import maplibregl from 'maplibre-gl';
import { Protocol } from 'pmtiles';
import 'maplibre-gl/dist/maplibre-gl.css';

const DEMO_STYLE = 'https://demotiles.maplibre.org/style.json';
const PMTILES_TYPE = 'application/vnd.pmtiles';
const RASTER_TYPES = ['png', 'jpeg', 'webp', 'avif'];
const SRC = '__item';
const FIELD_CAP = 500;

// Register the pmtiles:// protocol with MapLibre exactly once for the whole SPA.
let protocolRegistered = false;
function ensureProtocol() {
  if (!protocolRegistered) {
    maplibregl.addProtocol('pmtiles', new Protocol().tile);
    protocolRegistered = true;
  }
}

// Stable, distinct-ish color per source-layer name (so layers read like pmtiles.io).
function colorFor(name) {
  let h = 0;
  const s = String(name || '');
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) % 360;
  }
  return `hsl(${h}, 75%, 50%)`;
}

function escapeHtml(v) {
  return String(v).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export default {
  name: 'MapLibrePreview',
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      map: null,
      zoom: null,
      error: null,
      hasCenter: false,
      overlayLayerIds: []
    };
  },
  computed: {
    assets() {
      return (this.item && this.item.assets) || {};
    },
    // First asset that is a PMTiles archive (by media type or .pmtiles suffix).
    pmtilesAsset() {
      for (const asset of Object.values(this.assets)) {
        if (!asset || typeof asset.href !== 'string') {
          continue;
        }
        if (asset.type === PMTILES_TYPE || asset.href.toLowerCase().endsWith('.pmtiles')) {
          return asset;
        }
      }
      return null;
    },
    props_() {
      return (this.item && this.item.properties) || {};
    },
    isRaster() {
      return RASTER_TYPES.includes(this.props_['pmtiles:tile_type']);
    },
    vectorLayers() {
      const vl = this.props_['pmtiles:vector_layers'];
      return Array.isArray(vl) ? vl : [];
    }
  },
  mounted() {
    if (this.pmtilesAsset) {
      this.initMap();
    }
  },
  beforeDestroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  },
  methods: {
    basemapStyle() {
      const cfg = (typeof window !== 'undefined' && window.STAC_BROWSER_CONFIG) || {};
      return cfg.basemapStyleUrl || DEMO_STYLE;
    },
    initMap() {
      ensureProtocol();
      const center = this.props_['pmtiles:center']; // [lon, lat, zoom]
      const opts = {
        container: this.$refs.map,
        style: this.basemapStyle()
      };
      // Open at the header center+zoom (like pmtiles.io). For a single-zoom archive
      // (minzoom==maxzoom, e.g. nseries z11) fitBounds(bbox) would underzoom below
      // minzoom and render NOTHING — so only fit when we have no center to open at.
      this.hasCenter = false;
      if (Array.isArray(center) && center.length >= 2) {
        opts.center = [center[0], center[1]];
        if (typeof center[2] === 'number') {
          opts.zoom = center[2];
        }
        this.hasCenter = true;
      }
      this.map = new maplibregl.Map(opts);
      this.map.addControl(new maplibregl.NavigationControl(), 'top-left');
      this.map.addControl(new maplibregl.ScaleControl());
      this.map.on('zoom', () => {
        this.zoom = this.map.getZoom().toFixed(2);
      });
      this.map.on('load', () => {
        try {
          this.addOverlay();
          if (!this.hasCenter) {
            this.fitToItem(); // only when the header gave us no center to open at
          }
        } catch (e) {
          this.error = `Preview failed: ${e && e.message ? e.message : e}`;
        }
      });
    },
    addOverlay() {
      const url = `pmtiles://${this.pmtilesAsset.href}`;
      if (this.isRaster) {
        this.map.addSource(SRC, { type: 'raster', url });
        const id = '__item-raster';
        this.map.addLayer({ id, type: 'raster', source: SRC });
        this.overlayLayerIds = [id];
        return;
      }
      // Vector: needs source-layer names. We get them from the scanner's
      // pmtiles:vector_layers metadata; without it we can't style vector tiles.
      if (this.vectorLayers.length === 0) {
        this.error = 'No vector_layers metadata — cannot style this vector archive.';
        return;
      }
      this.map.addSource(SRC, { type: 'vector', url });
      const ids = [];
      for (const layer of this.vectorLayers) {
        const sl = layer && layer.id;
        if (!sl) {
          continue;
        }
        const color = colorFor(sl);
        const fillId = `__item-${sl}-fill`;
        const lineId = `__item-${sl}-line`;
        const circId = `__item-${sl}-circle`;
        this.map.addLayer({
          id: fillId, type: 'fill', source: SRC, 'source-layer': sl,
          filter: ['==', ['geometry-type'], 'Polygon'],
          paint: { 'fill-color': color, 'fill-opacity': 0.3, 'fill-outline-color': color }
        });
        this.map.addLayer({
          id: lineId, type: 'line', source: SRC, 'source-layer': sl,
          filter: ['==', ['geometry-type'], 'LineString'],
          paint: { 'line-color': color, 'line-width': 1.5 }
        });
        this.map.addLayer({
          id: circId, type: 'circle', source: SRC, 'source-layer': sl,
          filter: ['==', ['geometry-type'], 'Point'],
          paint: { 'circle-color': color, 'circle-radius': 3 }
        });
        ids.push(fillId, lineId, circId);
      }
      this.overlayLayerIds = ids;
      this.wireInspect();
    },
    wireInspect() {
      this.map.on('click', (e) => {
        const feats = this.map.queryRenderedFeatures(e.point, { layers: this.overlayLayerIds });
        if (!feats.length) {
          return;
        }
        new maplibregl.Popup({ maxWidth: '360px' })
          .setLngLat(e.lngLat)
          .setHTML(this.inspectHtml(feats[0]))
          .addTo(this.map);
      });
      this.map.on('mouseenter', () => {}); // no-op; per-layer cursor below
      for (const id of this.overlayLayerIds) {
        this.map.on('mouseenter', id, () => { this.map.getCanvas().style.cursor = 'pointer'; });
        this.map.on('mouseleave', id, () => { this.map.getCanvas().style.cursor = ''; });
      }
    },
    inspectHtml(feature) {
      const p = (feature && feature.properties) || {};
      const layer = feature && feature.sourceLayer;
      const rows = Object.keys(p).map((k) => {
        let v = p[k];
        if (v === null || typeof v === 'undefined') {
          v = '—';
        }
        v = String(v).slice(0, FIELD_CAP);
        return `<tr><th>${escapeHtml(k)}</th><td>${escapeHtml(v)}</td></tr>`;
      }).join('');
      const head = layer ? `<div class="ml-popup-layer">${escapeHtml(layer)}</div>` : '';
      return `${head}<table class="ml-popup-table">${rows || '<tr><td>(no attributes)</td></tr>'}</table>`;
    },
    fitToItem() {
      const bbox = this.item && this.item.bbox;
      if (!Array.isArray(bbox) || bbox.length < 4) {
        return;
      }
      this.map.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], { padding: 20, duration: 0 });
      // Don't underzoom below the archive's minzoom or the overlay renders nothing.
      const minz = this.props_['pmtiles:minzoom'];
      if (typeof minz === 'number' && this.map.getZoom() < minz) {
        this.map.setZoom(minz);
      }
    }
  }
};
</script>

<style lang="scss">
#stac-browser .maplibre-preview {
  position: relative;

  .maplibre-map {
    height: 500px;
    width: 100%;
  }

  .ml-empty,
  .ml-error {
    padding: 1rem;
    font-size: 0.9rem;
  }

  .ml-error {
    position: absolute;
    bottom: 0.5rem;
    left: 0.5rem;
    background: rgba(180, 0, 0, 0.85);
    color: #fff;
    border-radius: 3px;
    z-index: 2;
  }

  .ml-zoom {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-size: 0.8rem;
    z-index: 2;
  }

  .ml-popup-layer {
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  .ml-popup-table {
    font-size: 0.8rem;
    border-collapse: collapse;

    th, td {
      text-align: left;
      vertical-align: top;
      padding: 1px 6px 1px 0;
    }

    th {
      color: #555;
      white-space: nowrap;
    }
  }
}
</style>
