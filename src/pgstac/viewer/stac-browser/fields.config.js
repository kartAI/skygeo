// Custom STAC Browser metadata-field rendering for the scanner.
//
// The scanner (stac_scan) writes custom Item properties that stac-fields doesn't
// know about, so by default they render with auto-generated labels and raw JSON.
// Here we register them so they show as proper, labelled rows:
//   proc:*     provenance written for every item (source object, datetime origin)
//   proc:sample  first sampled feature rows (vector) -> rendered as an HTML table
//   pmtiles:*  PMTiles header/metadata (tile type, zoom range, center, layers)
//
// This is imported by STAC Browser's src/components/Metadata.vue at BUILD time,
// so it is baked into the SPA — changing labels here means rebuilding the image,
// not just tweaking runtime /config.js.
//
// Registry/field-spec reference (pinned to stac-fields ~1.5.7, shipped with
// STAC Browser v4.0.1): https://github.com/stac-utils/stac-fields
// A custom `formatter` may return HTML (rendered via v-html in MetadataTable.vue);
// all data-derived strings MUST be escaped with Helper.e() to avoid breaking layout.

import { Registry, Helper } from '@radiantearth/stac-fields';

const e = Helper.e;

function cell(value) {
  if (value === null || typeof value === 'undefined' || value === '') {
    return '—'; // em dash for empty
  }
  return e(String(value));
}

// proc:sample is an array of row objects whose columns are the dataset's own
// (dynamic per dataset), so a fixed `items` table schema can't describe it.
// Build the column set as the union of keys across the sampled rows and render
// a plain HTML table ourselves.
function formatSampleRows(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return cell(null);
  }
  const cols = [];
  for (const row of rows) {
    if (row && typeof row === 'object') {
      for (const key of Object.keys(row)) {
        if (!cols.includes(key)) {
          cols.push(key);
        }
      }
    }
  }
  // Wide values (esp. geometry WKT) would otherwise stretch the table off-screen. Cap each
  // cell's width with an ellipsis and put the whole table in a horizontal-scroll box; the
  // full value stays available via the cell's title (hover) tooltip.
  const wrapStyle = 'max-width:100%;overflow-x:auto;';
  const cellStyle = 'max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
  const head = cols.map(c => `<th style="${cellStyle}">${e(c)}</th>`).join('');
  const body = rows.map(row => {
    const cells = cols.map(c => {
      const raw = row ? row[c] : null;
      const title = (raw === null || typeof raw === 'undefined' || raw === '')
        ? '' : ` title="${e(String(raw))}"`;
      return `<td style="${cellStyle}"${title}>${cell(raw)}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');
  return `<div style="${wrapStyle}"><table class="metadata-custom-table"><thead><tr>${head}</tr></thead>`
    + `<tbody>${body}</tbody></table></div>`;
}

// pmtiles:vector_layers is a TileJSON-style list; each layer carries a `fields`
// object (attribute name -> type) that is also dynamic, so render manually.
function formatVectorLayers(layers) {
  if (!Array.isArray(layers) || layers.length === 0) {
    return cell(null);
  }
  const rows = layers.map(layer => {
    const id = cell(layer && layer.id);
    const minz = layer && typeof layer.minzoom !== 'undefined' ? layer.minzoom : '?';
    const maxz = layer && typeof layer.maxzoom !== 'undefined' ? layer.maxzoom : '?';
    const zoom = (layer && (layer.minzoom != null || layer.maxzoom != null))
      ? `${e(String(minz))}–${e(String(maxz))}` : '—';
    const fields = (layer && layer.fields && typeof layer.fields === 'object')
      ? Object.entries(layer.fields).map(([k, v]) => `${e(k)}: ${e(String(v))}`).join('<br>')
      : '—';
    const desc = cell(layer && layer.description);
    return `<tr><td>${id}</td><td>${zoom}</td><td>${fields}</td><td>${desc}</td></tr>`;
  }).join('');
  return `<table class="metadata-custom-table"><thead><tr>`
    + `<th>Layer</th><th>Zoom</th><th>Fields</th><th>Description</th>`
    + `</tr></thead><tbody>${rows}</tbody></table>`;
}

// pmtiles:center is [lon, lat, zoom] from the PMTiles header.
function formatCenter(value) {
  if (!Array.isArray(value) || value.length < 2) {
    return cell(value);
  }
  const [lon, lat, zoom] = value;
  const ll = `${cell(lat)}, ${cell(lon)}`;
  return (zoom !== null && typeof zoom !== 'undefined')
    ? `${ll} (zoom ${e(String(zoom))})` : ll;
}

// --- proc: provenance written by the scanner ---------------------
Registry.addExtension('proc', 'Provenance & processing');

Registry.addMetadataField('proc:source_key', {
  label: 'Source object',
  explain: 'Key of the source file in the bucket this item was extracted from.'
});

Registry.addMetadataField('proc:datetime_source', {
  label: 'Datetime source',
  explain: 'Where the item datetime came from.',
  mapping: {
    s3_last_modified: 'S3 last-modified',
    override: 'Manual override'
  }
});

Registry.addMetadataField('proc:sample', {
  label: 'Sample rows',
  explain: 'First feature rows read from the dataset when it was scanned.',
  formatter: formatSampleRows
});

// --- pmtiles: PMTiles header + metadata ------------------------------------
Registry.addExtension('pmtiles', 'PMTiles');

Registry.addMetadataField('pmtiles:name', { label: 'Name' });

Registry.addMetadataField('pmtiles:tile_type', {
  label: 'Tile type',
  mapping: {
    mvt: 'Vector (MVT)',
    png: 'Raster (PNG)',
    jpeg: 'Raster (JPEG)',
    webp: 'Raster (WebP)',
    avif: 'Raster (AVIF)',
    unknown: 'Unknown'
  }
});

Registry.addMetadataField('pmtiles:minzoom', { label: 'Min zoom' });
Registry.addMetadataField('pmtiles:maxzoom', { label: 'Max zoom' });

Registry.addMetadataField('pmtiles:center', {
  label: 'Center',
  explain: 'Default map center from the PMTiles header: longitude, latitude, zoom.',
  formatter: formatCenter
});

Registry.addMetadataField('pmtiles:vector_layers', {
  label: 'Vector layers',
  explain: 'Layers and attribute fields declared in the PMTiles metadata.',
  formatter: formatVectorLayers
});
