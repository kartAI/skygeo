# STAC Katalog

**Et komplett STAC (SpatioTemporal Asset Catalog) system for å katalogisere og utforske geospatiale data.**

## 📋 Innholdsfortegnelse

- [Oversikt](#oversikt)
- [Funksjoner](#funksjoner)
- [Støttede formater](#støttede-formater)
- [Hurtigstart](#hurtigstart)
- [Installasjon](#installasjon)
- [Bruk](#bruk)
- [QGIS-integrasjon](#qgis-integrasjon)
- [API-dokumentasjon](#api-dokumentasjon)
- [Prosjektstruktur](#prosjektstruktur)
- [Utvikling](#utvikling)
- [Feilsøking](#feilsøking)

## 🎯 Oversikt

STAC Katalog er et fullstendig system for å automatisk katalogisere geospatiale datafiler og gjøre dem tilgjengelige gjennom en STAC-kompatibel API. Systemet scanner automatisk en datamappe, ekstraherer metadata fra filene, og eksponerer dem gjennom både en REST API og et moderne webgrensesnitt.

### Arkitektur

```
┌─────────────────────────────────────────────────────────┐
│                     KLIENTER                             │
│  • Web Browser (Next.js Frontend)                       │
│  • QGIS (med STAC plugin eller direkte HTTP)            │
│  • Python scripts (requests, pystac-client)             │
│  • Curl / Postman / andre HTTP klienter                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              STAC API (FastAPI Backend)                  │
│  • STAC 1.0.0 kompatibel API                            │
│  • HTTP Range Request støtte (COG streaming)            │
│  • Automatisk metadata-ekstraksjon                       │
│  • Dynamisk katalog-generering                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  DATA DIRECTORY                          │
│  • Geospatiale filer (COG, FlatGeobuf, etc.)           │
│  • Automatisk scanning og metadata-ekstraksjon          │
│  • Organisert i collections basert på filtype           │
└─────────────────────────────────────────────────────────┘
```

## ✨ Funksjoner

### Backend
- ✅ **Automatisk filscanning** - Scanner datamappe for støttede formater
- ✅ **Metadata-ekstraksjon** - Leser metadata direkte fra geospatiale filer
- ✅ **STAC 1.0.0 API** - Fullt kompatibel med STAC-spesifikasjonen
- ✅ **HTTP Range Requests** - Støtte for COG streaming med /vsicurl/
- ✅ **Spatial søk** - Søk med bounding box
- ✅ **Dynamisk oppdatering** - Refresh-endpoint for å oppdatere katalog
- ✅ **CORS-støtte** - Klar for frontend-integrasjon
- ✅ **Docker-støtte** - Enkel deployment med docker-compose

### Frontend
- ✅ **Moderne UI** - Bygget med Next.js 14 og Tailwind CSS
- ✅ **Interaktivt kart** - Leaflet-basert kartvisning
- ✅ **Collection-browser** - Utforsk collections og items
- ✅ **Metadata-visning** - Detaljert informasjon om alle assets
- ✅ **Søkefunksjon** - Spatial søk med kartgrensesnitt
- ✅ **Dark/Light mode** - Responsivt design med tema-støtte
- ✅ **Sanntidsoppdatering** - Refresh katalog fra UI

### QGIS-integrasjon
- ✅ **Direkte URL-lasting** - Last inn filer via HTTP
- ✅ **COG streaming** - Med /vsicurl/ for effektiv streaming
- ✅ **FlatGeobuf** - Direkte støtte for .fgb filer
- ✅ **Python scripting** - Batch-lasting av layers
- ✅ **STAC API-kompatibilitet** - Bruk med QGIS STAC plugin

## 📦 Støttede formater

| Format | Filutvidelse | QGIS-støtte | HTTP Streaming | Notater |
|--------|-------------|-------------|----------------|---------|
| **COG** (Cloud Optimized GeoTIFF) | `.tif`, `.tiff` | ✅ Utmerket | ✅ Ja | Bruk /vsicurl/ for streaming |
| **FlatGeobuf** | `.fgb` | ✅ Utmerket | ✅ Ja | Beste valg for vektordata |
| **GeoParquet** | `.parquet`, `.geoparquet` | ⚠️ Begrenset | ⚠️ Delvis | Krever GDAL 3.5+ |
| **PMTiles** | `.pmtiles` | ⚠️ Plugin | ⚠️ Delvis | Krever PMTiles QGIS plugin |
| **COPC** (Cloud Optimized Point Cloud) | `.laz`, `.copc.laz` | ✅ God | ✅ Ja | Krever PDAL |

## 🚀 Hurtigstart

### Docker (Anbefalt)

**Den enkleste måten å komme i gang på!**

```powershell
# Klon repositoryet
git clone <repo-url>
cd STAC-katalog

# Start alle tjenester
docker-compose up -d

# Åpne i nettleser
start http://localhost:3000
```

**Tjenester:**
- ✅ Backend API: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ Frontend: http://localhost:3000

### Legg til data

```powershell
# Kopier dine geospatiale filer til data-mappen
copy C:\mine_data\*.tif backend\data\
copy C:\mine_data\*.fgb backend\data\

# Oppdater katalogen (via API)
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST

# Eller bruk "Oppdater katalog"-knappen i frontend
```

## 📥 Installasjon

### Forutsetninger

- **Docker & Docker Compose** (anbefalt)
  
  ELLER
  
- **Python 3.9+** med pip
- **Node.js 18+** med npm
- **PowerShell** (Windows)

### Alternativ 1: Docker (Anbefalt)

```powershell
# Bygg og start
docker-compose up -d

# Se logger
docker-compose logs -f

# Stopp tjenester
docker-compose down
```

### Alternativ 2: Lokal utvikling

#### Backend Setup

```powershell
# Naviger til backend
cd backend

# Opprett virtuelt miljø (anbefalt)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installer avhengigheter
pip install -r requirements.txt

# Opprett .env fil
@"
DATA_DIRECTORY=./data
CATALOG_TITLE=Min STAC Catalog
CATALOG_DESCRIPTION=Dynamisk STAC katalog for geospatiale data
API_HOST=0.0.0.0
API_PORT=8000
"@ | Out-File -FilePath .env -Encoding utf8

# Opprett datamappe
mkdir data -ErrorAction SilentlyContinue

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```powershell
# Åpne nytt terminal-vindu
cd frontend

# Installer avhengigheter
npm install

# Opprett .env.local
@"
NEXT_PUBLIC_STAC_API_URL=http://localhost:8000
"@ | Out-File -FilePath .env.local -Encoding utf8

# Start utviklingsserver
npm run dev
```

#### Automatisk start (PowerShell-script)

Fra rot-mappen:
```powershell
.\start-dev.ps1
```

## 💻 Bruk

### Web Frontend

1. Åpne http://localhost:3000
2. Bla gjennom collections
3. Klikk på en collection for å se items
4. Bruk kartet for spatial søk
5. Klikk "Oppdater katalog" etter å ha lagt til nye filer

### API-bruk

#### Hent root catalog
```powershell
Invoke-RestMethod -Uri http://localhost:8000/
```

#### Liste alle collections
```powershell
Invoke-RestMethod -Uri http://localhost:8000/collections
```

#### Hent items fra en collection
```powershell
Invoke-RestMethod -Uri http://localhost:8000/collections/flatgeobuf/items
```

#### Søk med bounding box
```powershell
$bbox = "10.0,59.0,11.0,60.0"  # minx,miny,maxx,maxy
Invoke-RestMethod -Uri "http://localhost:8000/search?bbox=$bbox&limit=10"
```

#### Oppdater katalog
```powershell
Invoke-RestMethod -Uri http://localhost:8000/refresh -Method POST
```

### Python-bruk

```python
import requests

# Hent alle collections
response = requests.get('http://localhost:8000/collections')
collections = response.json()['collections']

for collection in collections:
    print(f"Collection: {collection['id']}")
    print(f"  Title: {collection['title']}")
    print(f"  Items: {collection.get('extent', {}).get('spatial', {})}")

# Søk etter items
search_params = {
    'bbox': '10.0,59.0,11.0,60.0',
    'limit': 10
}
response = requests.get('http://localhost:8000/search', params=search_params)
items = response.json()['features']

for item in items:
    print(f"Item: {item['id']}")
    print(f"  Assets: {list(item['assets'].keys())}")
```

## 🗺️ QGIS-integrasjon

### Last inn FlatGeobuf

**Metode 1: Direkte URL**
1. **Layer** → **Add Layer** → **Add Vector Layer**
2. **Source Type:** `Protocol: HTTP(S)`
3. **URI:** `http://localhost:8000/data/yourfile.fgb`
4. **Add**

**Metode 2: Python Console**
```python
from qgis.core import QgsVectorLayer, QgsProject

url = 'http://localhost:8000/data/yourfile.fgb'
layer = QgsVectorLayer(url, 'My Layer', 'ogr')
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
```

### Last inn COG (Cloud Optimized GeoTIFF)

**Med streaming (anbefalt):**
1. **Layer** → **Add Layer** → **Add Raster Layer**
2. **Source:** 
```
/vsicurl/http://localhost:8000/data/yourfile.tif
```
3. **Add**

**Python Console:**
```python
from qgis.core import QgsRasterLayer, QgsProject

url = '/vsicurl/http://localhost:8000/data/yourfile.tif'
layer = QgsRasterLayer(url, 'COG Layer', 'gdal')
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
```

### Batch-lasting av alle items

```python
import requests
from qgis.core import QgsVectorLayer, QgsProject

# Hent alle FlatGeobuf items
response = requests.get('http://localhost:8000/collections/flatgeobuf/items')
items = response.json()['features']

# Last inn alle
for item in items:
    href = item['assets']['data']['href']
    name = item['id']
    layer = QgsVectorLayer(href, name, 'ogr')
    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
        print(f'✓ Loaded: {name}')
    else:
        print(f'✗ Failed: {name}')
```

### Liste tilgjengelige URLs

Bruk PowerShell-scriptet:
```powershell
.\list-qgis-urls.ps1
```

## 📚 API-dokumentasjon

### STAC API Endpoints

| Endpoint | Metode | Beskrivelse |
|----------|--------|-------------|
| `/` | GET | Root catalog med conformance classes |
| `/collections` | GET | Liste alle collections |
| `/collections/{id}` | GET | Hent spesifikk collection |
| `/collections/{id}/items` | GET | Liste items i collection (med pagination) |
| `/collections/{id}/items/{item_id}` | GET | Hent spesifikt item |
| `/search` | GET | Søk etter items (bbox, datetime, collections) |
| `/data/{filepath}` | GET | Direkte filtilgang med Range Request støtte |

### Admin Endpoints

| Endpoint | Metode | Beskrivelse |
|----------|--------|-------------|
| `/refresh` | POST | Start asynkron katalog-refresh |
| `/refresh/status` | GET | Sjekk status på refresh-prosess |
| `/health` | GET | Helsesjekk |

### Interaktiv dokumentasjon

Åpne http://localhost:8000/docs for interaktiv Swagger UI dokumentasjon.

## 📁 Prosjektstruktur

```
STAC-katalog/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app og endpoints
│   │   ├── models/
│   │   │   └── config.py      # Konfigurasjon (pydantic settings)
│   │   ├── scanner/
│   │   │   └── file_scanner.py # Fil-scanning og metadata-ekstraksjon
│   │   └── stac/
│   │       ├── catalog.py     # STAC Catalog-generering
│   │       ├── collection.py  # STAC Collection-håndtering
│   │       └── item.py        # STAC Item-generering
│   ├── data/                  # Datamappe (mount point)
│   ├── Dockerfile
│   ├── requirements.txt       # Python-avhengigheter
│   └── test_api.py           # API-tester
│
├── frontend/                   # Next.js React frontend
│   ├── app/
│   │   ├── layout.tsx         # App layout
│   │   ├── page.tsx           # Hovedside (collections)
│   │   ├── collections/[id]/
│   │   │   └── page.tsx       # Collection-detaljside
│   │   └── search/
│   │       └── page.tsx       # Søkeside
│   ├── components/
│   │   ├── CollectionCard.tsx # Collection card-komponent
│   │   ├── ItemList.tsx       # Item liste-komponent
│   │   ├── MapView.tsx        # Leaflet kart-komponent
│   │   └── SearchBar.tsx      # Søk-komponent
│   ├── lib/
│   │   └── stac-client.ts     # STAC API klient
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
│
├── docker-compose.yml         # Docker Compose konfigurasjon
├── start-dev.ps1             # PowerShell utviklingsscript
├── list-qgis-urls.ps1        # QGIS URL-liste script
└── README.md                  # Denne filen
```

## 🛠️ Utvikling

### Backend-utvikling

```powershell
# Kjør med hot reload
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Kjør tester
python test_api.py

# Installer nye pakker
pip install <package-name>
pip freeze > requirements.txt
```

### Frontend-utvikling

```powershell
# Utviklingsserver (hot reload)
cd frontend
npm run dev

# Build for produksjon
npm run build

# Kjør produksjonsbygg
npm start

# Lint kode
npm run lint

# Installer nye pakker
npm install <package-name>
```

### Docker-utvikling

```powershell
# Bygg containere på nytt
docker-compose build

# Start med rebuild
docker-compose up -d --build

# Se logger
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart enkelt tjeneste
docker-compose restart backend

# Stopp og fjern containere
docker-compose down

# Fjern volumes også
docker-compose down -v
```

### Testing

```powershell
# Test backend API
cd backend
python test_api.py

# Test manuelt med curl/Invoke-WebRequest
Invoke-WebRequest -Uri http://localhost:8000/health
Invoke-WebRequest -Uri http://localhost:8000/collections

# Test frontend
cd frontend
npm run build  # Sjekk for build-feil
```

## 🔧 Feilsøking

### Backend starter ikke

**Problem:** Port 8000 er opptatt
```powershell
# Sjekk hvilken prosess som bruker porten
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Get-Process -Id <PID>

# Eller endre port i .env
API_PORT=8001
```

**Problem:** Avhengigheter mangler
```powershell
pip install -r requirements.txt
```

**Problem:** Data directory ikke funnet
```powershell
# Sjekk at mappen eksisterer
Test-Path backend/data

# Opprett hvis den mangler
mkdir backend/data
```

### Frontend kan ikke koble til backend

**Problem:** CORS-feil
- Sjekk at `NEXT_PUBLIC_STAC_API_URL` i `.env.local` er korrekt
- Verifiser at backend kjører: http://localhost:8000/health

**Problem:** Connection refused
```powershell
# Sjekk at backend kjører
Invoke-WebRequest -Uri http://localhost:8000/health

# Sjekk Docker-containere
docker-compose ps
```

### Ingen collections vises

1. **Sjekk at filer finnes:**
```powershell
ls backend/data/
```

2. **Verifiser filformater:**
- Må være støttede formater (.tif, .fgb, .parquet, .pmtiles, .laz)

3. **Refresh katalog:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

4. **Sjekk backend-logger:**
```powershell
docker-compose logs backend | Select-String "error"
```

### QGIS kan ikke laste filer

**Problem:** 404 Not Found
```powershell
# Test at filen er tilgjengelig
Invoke-WebRequest -Uri http://localhost:8000/data/yourfile.fgb -Method Head
```

**Problem:** COG streaming virker ikke
- Sørg for å bruke `/vsicurl/` prefix
- Sjekk at GDAL versjon støtter HTTP Range Requests
- Test uten streaming først (last ned filen)

**Problem:** GeoParquet virker ikke i QGIS
- Krever GDAL 3.5+
- Sjekk GDAL versjon: **Help** → **About** → **Information**

### Docker-problemer

**Problem:** Container starter ikke
```powershell
# Se logger for feil
docker-compose logs backend

# Rebuild container
docker-compose up -d --build backend
```

**Problem:** Volume mounting virker ikke
```powershell
# Sjekk at filer er synlige i container
docker exec stac-backend ls -la /app/data/

# Verifiser volume i docker-compose.yml
```

**Problem:** Out of disk space
```powershell
# Rydd opp gamle images og containere
docker system prune -a
```

## 🌟 Best Practices

### Data-organisering

Organiser filer i undermapper for bedre struktur:

```
backend/data/
├── raster/
│   ├── satellite/
│   │   └── sentinel2_2024.tif
│   └── elevation/
│       └── dtm_10m.tif
├── vector/
│   ├── administrative/
│   │   ├── counties.fgb
│   │   └── municipalities.fgb
│   └── infrastructure/
│       └── roads.parquet
└── pointcloud/
    └── lidar_2024.copc.laz
```

### Filnavn-konvensjoner

- Bruk beskrivende navn: `elevation_10m_utm33.tif` ikke `data1.tif`
- Inkluder metadata i filnavn der det er hensiktsmessig
- Unngå mellomrom (bruk underscore eller bindestrek)
- Bruk lowercase for konsistens

### Performance-tips

- **COG-filer:** Bruk alltid Cloud Optimized GeoTIFF for raster-data
- **FlatGeobuf:** Foretrekk for vektordata (raskere enn Shapefile/GeoJSON)
- **Store filer:** Vurder å splitte i mindre tiles
- **Metadata:** La systemet ekstrahere metadata automatisk

### Sikkerhet

- I produksjon: konfigurer spesifikke CORS origins (ikke `"*"`)
- Bruk HTTPS i produksjon
- Vurder autentisering for sensitive data
- Valider input i custom endpoints

## 📄 Lisens

Dette prosjektet er utviklet for demonstrasjons- og utviklingsformål.

## 🤝 Bidrag

For å bidra til prosjektet:

1. Fork repositoryet
2. Opprett en feature branch (`git checkout -b feature/amazing-feature`)
3. Commit dine endringer (`git commit -m 'Add amazing feature'`)
4. Push til branchen (`git push origin feature/amazing-feature`)
5. Åpne en Pull Request

## 📞 Support

- **API dokumentasjon:** http://localhost:8000/docs
- **Issues:** Opprett en issue i repositoryet
- **Docker logs:** `docker-compose logs -f`

---

**Status:** ✅ Produksjonsklar  
**STAC Version:** 1.0.0  
**Sist oppdatert:** November 2024
