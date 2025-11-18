# Volume Mounting - Visuelt Eksempel

## Hvordan Data Mounting Fungerer

```
┌─────────────────────────────────────────────────────────────┐
│                      HOST MACHINE                            │
│  (Din Windows/Linux/Mac datamaskin)                          │
│                                                              │
│  C:\Users\...\STAC-katalog\                                  │
│  └── backend\                                                │
│      └── data\                    ← DU LEGGER FILER HER     │
│          ├── elevation.tif                                   │
│          ├── boundaries.fgb                                  │
│          └── lidar.copc.laz                                  │
│                                                              │
│          ↕ SYNKRONISERT (docker volume mount)                │
│                                                              │
│  ┌────────────────────────────────────────────────┐          │
│  │         DOCKER CONTAINER                       │          │
│  │         (stac-backend)                         │          │
│  │                                                │          │
│  │  /app/data/               ← CONTAINER SER HER │          │
│  │  ├── elevation.tif                             │          │
│  │  ├── boundaries.fgb                            │          │
│  │  └── lidar.copc.laz                            │          │
│  │                                                │          │
│  │  Backend scanner leser filer fra /app/data/   │          │
│  │  STAC API serverer metadata                   │          │
│  └────────────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Praktisk Eksempel

### Scenario: Legge til ny GeoTIFF

**Steg 1:** Kopier fil til host
```powershell
copy D:\geodata\norway_dem.tif C:\...\STAC-katalog\backend\data\
```

**Visuelt:**
```
HOST:       backend/data/norway_dem.tif    [NY FIL ✓]
            ↓ (umiddelbart synkronisert)
CONTAINER:  /app/data/norway_dem.tif        [NY FIL ✓]
```

**Steg 2:** Refresh katalogen
```powershell
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

**Visuelt:**
```
1. Scanner /app/data/          → Finner norway_dem.tif
2. Ekstraherer metadata        → Bbox, CRS, størrelse, etc.
3. Genererer STAC Item         → JSON metadata
4. Oppdaterer Collection       → Legger til i COG collection
5. API eksponerer data         → http://localhost:8000/collections/cog/items
```

**Steg 3:** Se i frontend
```
http://localhost:3000
  → Collections
    → COG
      → norway_dem [NY ITEM ✓]
        → Vis på kart
```

## Dataflyt Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FULL WORKFLOW                             │
└─────────────────────────────────────────────────────────────┘

1. DU:                 Kopierer fil til backend/data/
                       ↓
2. DOCKER:             Synkroniserer til /app/data/
                       ↓
3. DU:                 Klikker "Oppdater katalog"
                       ↓
4. FRONTEND:           Sender POST /refresh til backend
                       ↓
5. BACKEND:            Scanner /app/data/
                       ├── Finner nye/endrede filer
                       ├── Ekstraherer metadata
                       ├── Genererer STAC Items
                       └── Oppdaterer Collections
                       ↓
6. FRONTEND:           Henter oppdaterte collections
                       ↓
7. DU:                 Ser nye data i UI! 🎉
```

## Filtyper og Collections

```
backend/data/
├── elevation.tif          → COG Collection
├── satellite.tiff         → COG Collection
├── boundaries.fgb         → FlatGeobuf Collection
├── roads.parquet          → GeoParquet Collection
├── basemap.pmtiles        → PMTiles Collection
└── scan.copc.laz          → COPC Collection

                ↓ Scanning

STAC Catalog
├── COG Collection
│   ├── elevation (Item)
│   └── satellite (Item)
├── FlatGeobuf Collection
│   └── boundaries (Item)
├── GeoParquet Collection
│   └── roads (Item)
├── PMTiles Collection
│   └── basemap (Item)
└── COPC Collection
    └── scan (Item)
```

## Volume Mounting Types

### 1. Standard Bind Mount (Current)
```yaml
volumes:
  - ./backend/data:/app/data
```

**Fordeler:**
- ✅ Lett å legge til filer
- ✅ Direkte tilgang fra host
- ✅ Ingen ekstra konfigur asjon

**Ulemper:**
- ⚠️ Kan være tregere på Windows
- ⚠️ Krever file sharing i Docker Desktop

### 2. Named Volume
```yaml
volumes:
  - geodata:/app/data

volumes:
  geodata:
    driver: local
```

**Fordeler:**
- ✅ Bedre performance
- ✅ Overlever container sletting
- ✅ Enklere backup med Docker

**Ulemper:**
- ⚠️ Vanskeligere å legge til filer manuelt
- ⚠️ Krever docker cp kommandoer

### 3. External Volume
```yaml
volumes:
  - D:/geodata:/app/data
```

**Fordeler:**
- ✅ Bruk eksisterende datakatalog
- ✅ Ingen kopiering nødvendig
- ✅ Del data mellom prosjekter

**Ulemper:**
- ⚠️ Path må være absolutt
- ⚠️ Krever file sharing permissions

## Multippel Data Sources

```yaml
volumes:
  # Primary data
  - ./backend/data:/app/data
  
  # Additional read-only sources
  - D:/satellite_imagery:/app/data/satellite:ro
  - E:/terrain:/app/data/terrain:ro
  - //network/geodata:/app/data/network:ro
```

**Resulterer i:**
```
Container: /app/data/
          ├── (fra ./backend/data)
          ├── satellite/  (fra D:/)
          ├── terrain/    (fra E:/)
          └── network/    (fra network share)
```

## Synkronisering i Aksjon

### Test: Sanntids synkronisering

**Terminal 1 (Host):**
```powershell
# Opprett ny fil
echo "test" > backend/data/test.txt
```

**Terminal 2 (Container):**
```powershell
# Sjekk umiddelbart
docker-compose exec backend ls -la /app/data/test.txt

# Output: -rw-r--r-- 1 root root 5 Nov 11 13:00 /app/data/test.txt
```

**Resultat:** Filen vises UMIDDELBART i containeren! ⚡

## Backup Strategi

### 1. Host Backup (Enklest)
```powershell
# Backup hele data directory fra host
tar -czf stac-data-backup.tar.gz backend/data/
```

### 2. Container Backup
```powershell
# Backup fra container
docker-compose exec backend tar -czf /tmp/backup.tar.gz /app/data
docker cp stac-backend:/tmp/backup.tar.gz ./backup.tar.gz
```

### 3. Volume Backup (for named volumes)
```powershell
# Backup named volume
docker run --rm -v geodata:/data -v ${PWD}:/backup alpine tar -czf /backup/geodata-backup.tar.gz /data
```

## Troubleshooting Visuelt

### Problem: "File not found"

```
❌ FEIL SCENARIO:

HOST:      backend/data/myfile.tif         [EXISTS ✓]
           ↓ ??? (ikke synkronisert)
CONTAINER: /app/data/myfile.tif            [NOT FOUND ✗]

LØSNING:
1. Restart container: docker-compose restart backend
2. Sjekk Docker file sharing settings
3. Verifiser volume mount: docker inspect stac-backend
```

### Problem: "Permission denied"

```
❌ FEIL SCENARIO:

HOST:      backend/data/myfile.tif         [OWNER: You]
           ↓ (mountet)
CONTAINER: /app/data/myfile.tif            [OWNER: root, MODE: 600]
           ↓
BACKEND:   FileScanner.read()              [PERMISSION DENIED ✗]

LØSNING (Windows):
- Sjekk Docker Desktop settings
- Resources → File Sharing → Enable folder

LØSNING (Linux):
chmod -R 755 backend/data/
```

## Quick Reference

| Handling | Host Command | Container sees |
|----------|--------------|----------------|
| Legg til fil | `copy file.tif backend/data/` | Umiddelbart |
| Slett fil | `del backend/data/file.tif` | Umiddelbart |
| Endre fil | `notepad backend/data/file.txt` | Ved lagring |
| Ny mappe | `mkdir backend/data/newfolder` | Umiddelbart |

## Konklusjon

Volume mounting er transparent og automatisk!

```
┌──────────────────────────────────────────┐
│  DU                                      │
│  ↓ (legger til fil)                      │
│  BACKEND/DATA/                           │
│  ↓ (docker synk)                         │
│  CONTAINER /APP/DATA/                    │
│  ↓ (scanner leser)                       │
│  STAC ITEMS                              │
│  ↓ (API serverer)                        │
│  FRONTEND VISER DATA                     │
└──────────────────────────────────────────┘
```

**Alt du trenger å gjøre:**
1. Legg filer i `backend/data/`
2. Klikk "Oppdater katalog"
3. Se data i UI! 🎉

---

Se også: [DATA_MOUNTING.md](DATA_MOUNTING.md) for detaljert guide

