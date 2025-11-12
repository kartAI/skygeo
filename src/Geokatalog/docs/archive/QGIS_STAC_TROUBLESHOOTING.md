# QGIS STAC Plugin Troubleshooting

## Problem: Cannot open files from STAC catalog in QGIS

Hvis du kan se collections i QGIS STAC plugin, men ikke kan åpne filene, prøv disse løsningene:

### Løsning 1: Manuell loading via direkte URL

QGIS STAC plugin viser bare metadata. For å faktisk laste dataene:

**For FlatGeobuf:**
1. Finn item i STAC browser
2. Kopier asset href: `http://localhost:8000/data/UScounties.fgb`
3. **Layer** → **Add Layer** → **Add Vector Layer**
4. **Source Type:** Protocol
5. **URI:** `http://localhost:8000/data/UScounties.fgb`
6. **Add**

### Løsning 2: Bruk GDAL Virtual File System

GDAL's `/vsicurl/` kan streame filer over HTTP:

**QGIS:**
1. **Layer** → **Add Layer** → **Add Vector Layer**
2. **Source Type:** File/Directory
3. **Vector Dataset(s):** 
   ```
   /vsicurl/http://localhost:8000/data/UScounties.fgb
   ```
4. **Add**

**For raster (COG):**
```
/vsicurl/http://localhost:8000/data/elevation.tif
```

### Løsning 3: Last ned først, åpne lokalt

```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/data/UScounties.fgb" -OutFile "UScounties.fgb"
```

Deretter drag & drop filen til QGIS.

### Løsning 4: QGIS Python Console (Automatisk loading)

**Ctrl+Alt+P** i QGIS for å åpne Python Console:

```python
import requests
from qgis.core import QgsVectorLayer, QgsProject

# Hent item fra STAC
response = requests.get('http://localhost:8000/collections/flatgeobuf/items')
items = response.json()['features']

# Last inn første item
if items:
    item = items[0]
    href = item['assets']['data']['href']
    name = item['id']
    
    # Metode 1: Direkte URL
    layer = QgsVectorLayer(href, name, 'ogr')
    
    # Metode 2: Via vsicurl (anbefalt for store filer)
    # layer = QgsVectorLayer(f'/vsicurl/{href}', name, 'ogr')
    
    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
        print(f'Loaded: {name}')
    else:
        print(f'Failed to load: {name}')
        print(f'Error: {layer.error().message()}')
```

### Løsning 5: Batch load alle items

```python
import requests
from qgis.core import QgsVectorLayer, QgsProject

# Hent alle collections
collections_response = requests.get('http://localhost:8000/collections')
collections = collections_response.json()['collections']

# Last inn alle items fra alle collections
for collection in collections:
    collection_id = collection['id']
    print(f'Loading collection: {collection_id}')
    
    # Hent items
    items_response = requests.get(f'http://localhost:8000/collections/{collection_id}/items')
    items = items_response.json()['features']
    
    # Last inn hvert item
    for item in items:
        href = item['assets']['data']['href']
        name = f"{collection_id}_{item['id']}"
        
        layer = QgsVectorLayer(href, name, 'ogr')
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            print(f'  ✓ {name}')
        else:
            print(f'  ✗ {name}: {layer.error().message()}')
```

## Kjente begrensninger

### QGIS STAC Plugin
- **Ikke alle QGIS STAC plugins** støtter automatisk download/loading av assets
- Noen plugins viser bare metadata og krever manuell loading
- Hvis du bruker "STAC API Browser", kan det hende den ikke har "Add to Map" funksjonalitet

### Workaround: Lag egen loading-funksjon

**Lagre som `load_stac_items.py`:**
```python
"""
QGIS Script: Load items from local STAC catalog
Usage: Processing Toolbox → Scripts → Load STAC Items
"""

from qgis.core import QgsVectorLayer, QgsProject
from qgis.PyQt.QtWidgets import QInputDialog
import requests

def load_collection():
    # Ask user for collection
    collections = requests.get('http://localhost:8000/collections').json()['collections']
    collection_ids = [c['id'] for c in collections]
    
    collection_id, ok = QInputDialog.getItem(
        None, 
        "Select Collection", 
        "Collection:", 
        collection_ids, 
        0, 
        False
    )
    
    if not ok:
        return
    
    # Load items
    items_response = requests.get(f'http://localhost:8000/collections/{collection_id}/items')
    items = items_response.json()['features']
    
    loaded = 0
    for item in items:
        href = item['assets']['data']['href']
        name = item['id']
        
        layer = QgsVectorLayer(href, name, 'ogr')
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            loaded += 1
    
    print(f'Loaded {loaded}/{len(items)} items from {collection_id}')

# Run
load_collection()
```

### Alternative: Bruk vår helper script

```powershell
# list-qgis-urls.ps1 viser alle tilgjengelige URLs
.\list-qgis-urls.ps1

# Kopier URL og bruk Add Layer i QGIS
```

## Sjekkliste for feilsøking

- [ ] STAC server kjører: `docker-compose ps`
- [ ] Collections laster i QGIS STAC plugin
- [ ] Filer er tilgjengelig: `curl -I http://localhost:8000/data/UScounties.fgb`
- [ ] QGIS kan laste filer via direkte URL (Add Vector Layer)
- [ ] Prøvd `/vsicurl/` metode
- [ ] GDAL/OGR driver installert for format (flatgeobuf, geoparquet, etc)

## Format-spesifikke tips

### FlatGeobuf (.fgb)
```
Direkte URL: http://localhost:8000/data/file.fgb
QGIS: Fungerer ut av boksen (OGR driver)
```

### GeoParquet (.parquet)
```
Krever: GDAL 3.5+ med Parquet driver
Sjekk: QGIS → Help → About → GDAL version
Hvis <3.5: Last ned fil først, eller oppgrader QGIS
```

### COG (.tif)
```
Direkte URL: /vsicurl/http://localhost:8000/data/file.tif
Anbefalt: Bruk alltid /vsicurl/ for raster
```

### PMTiles (.pmtiles)
```
Krever: QGIS PMTiles plugin
Install: Plugins → Manage and Install → PMTiles
```

### COPC (.laz)
```
Krever: PDAL support i QGIS
Alternativ: Bruk CloudCompare for point clouds
```

## Test direkte URL i QGIS

**Quick test:**
1. Open QGIS
2. **Layer** → **Add Layer** → **Add Vector Layer**
3. **Protocol:** HTTP/HTTPS/FTP
4. **URI:** `http://localhost:8000/data/UScounties.fgb`
5. **Add**

Hvis dette fungerer, så er problemet med STAC plugin, ikke med serveren.

## Debugging

### Check QGIS Log
**View** → **Panels** → **Log Messages**

Look for errors like:
- "Failed to open datasource"
- "Driver not found"
- "Network error"

### Check Server Logs
```powershell
docker-compose logs -f backend | Select-String "/data/"
```

### Test with curl
```bash
curl -I http://localhost:8000/data/UScounties.fgb
```

Should return:
```
HTTP/1.1 200 OK
content-type: application/flatgeobuf
content-length: 14100008
```

---

## Anbefalt Workflow

**For nå:**
1. Bruk STAC plugin til å **browse** collections og metadata
2. Kopier asset href fra STAC metadata
3. **Manuelt load** filer via "Add Vector/Raster Layer"

**Eller:**
- Bruk Python Console script for automatisk loading
- Bruk `.\list-qgis-urls.ps1` for å se alle tilgjengelige URLs

Dette er normal oppførsel for mange STAC plugins - de viser katalogen, men krever manuell loading av assets.

---

**Oppdatert:** 11. november 2025

