# Data Folder Mounting Guide

## Oversikt

STAC Katalog bruker Docker volumes for å gi containeren tilgang til geospatiale filer på din host-maskin. Dette gjør at du kan legge til, endre eller fjerne filer uten å rebuilde containeren.

## Standard Oppsett

### Gjeldende Konfigurasjon

I `docker-compose.yml`:
```yaml
volumes:
  - ./backend/data:/app/data
```

Dette betyr:
- **Host path:** `./backend/data` (på din maskin)
- **Container path:** `/app/data` (inne i containeren)
- **Tilgang:** Read/Write (begge veier synkronisert)

## Hvordan Bruke

### 1. Legg til filer i data-mappen

```powershell
# Kopier enkeltfiler
copy C:\mine_data\*.tif backend\data\

# Kopier hele mapper
xcopy C:\mine_data\raster backend\data\raster\ /E /I

# Eller bare flytt filer direkte til mappen
```

### 2. Refresh katalogen

Etter å ha lagt til filer:

**Via UI:**
- Gå til http://localhost:3000
- Klikk "Oppdater katalog"-knappen

**Via API:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

**Via container:**
```powershell
docker-compose exec backend curl -X POST http://localhost:8000/refresh
```

## Alternative Mounting Scenarios

### Scenario 1: Ekstern Datakatalog

Hvis dataen din ligger et annet sted på maskinen:

```yaml
volumes:
  # Mount fra annen lokasjon
  - C:/geodata:/app/data
  # Eller på Linux/Mac
  - /mnt/geodata:/app/data
```

### Scenario 2: Read-Only Mounting

For produksjon hvor du ikke vil at containeren skal kunne endre filer:

```yaml
volumes:
  - ./backend/data:/app/data:ro  # :ro = read-only
```

### Scenario 3: Multiple Data Sources

Hvis du har data fra flere steder:

```yaml
volumes:
  - ./backend/data:/app/data
  - D:/satelittbilder:/app/data/satellite:ro
  - E:/terrengdata:/app/data/terrain:ro
```

### Scenario 4: Navngitt Volume (for persistens)

Hvis du vil ha data som overlever selv om du sletter containers:

```yaml
services:
  backend:
    volumes:
      - geodata:/app/data
      
volumes:
  geodata:
    driver: local
```

## Praktiske Eksempler

### Eksempel 1: Organisere data etter type

```
backend/data/
├── raster/
│   ├── elevation/
│   │   └── dem_10m.tif
│   └── imagery/
│       └── satellite_2024.tif
├── vector/
│   ├── boundaries.fgb
│   └── roads.parquet
└── pointcloud/
    └── lidar_scan.copc.laz
```

### Eksempel 2: Bruke symbolske lenker (Windows)

```powershell
# Opprett symbolic link til ekstern mappe
New-Item -ItemType SymbolicLink -Path "backend\data\external" -Target "D:\GeoData"
```

### Eksempel 3: Bruke nettverksdrev

```yaml
volumes:
  - //server/geodata:/app/data:ro
```

## Docker Compose Override

For personlige tilpasninger uten å endre `docker-compose.yml`:

**Opprett `docker-compose.override.yml`:**

```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Legg til ekstra data sources
      - D:/mine_data:/app/data/mine_data:ro
      - E:/arkiv:/app/data/arkiv:ro
```

Dette merges automatisk med hovedfilen når du kjører `docker-compose up`.

## Vanlige Operasjoner

### Se nåværende volumes

```powershell
docker-compose config
```

### Liste alle filer i container

```powershell
docker-compose exec backend ls -la /app/data
```

### Kopier filer direkte til running container

```powershell
docker cp myfile.tif stac-backend:/app/data/
```

### Sjekk disk usage

```powershell
docker-compose exec backend du -sh /app/data
```

## Performance Tips

### Windows

1. **Bruk WSL2 backend** i Docker Desktop
2. **Plasser data i WSL filesystem** for best ytelse:
   ```powershell
   # Flytt data til WSL
   wsl
   cd /home/user/stac-data
   # Bruk denne i docker-compose:
   # - /home/user/stac-data:/app/data
   ```

3. **Unngå mange små filer** - bruk arkivformater når mulig

### Linux/Mac

Data mounting er allerede optimalt på disse plattformene.

## Sikkerhet

### Produksjon Beste Praksis

1. **Read-only mounting:**
   ```yaml
   volumes:
     - ./backend/data:/app/data:ro
   ```

2. **Spesifikke permissions:**
   ```yaml
   volumes:
     - ./backend/data:/app/data:ro
   user: "1000:1000"  # Non-root user
   ```

3. **Separate sensitive data:**
   ```yaml
   volumes:
     - ./backend/data/public:/app/data/public:ro
     - ./backend/data/restricted:/app/data/restricted:ro
   ```

## Feilsøking

### Problem: Filer vises ikke i container

**Løsning:**
```powershell
# Restart containeren
docker-compose restart backend

# Eller full restart
docker-compose down
docker-compose up -d
```

### Problem: Permission denied

**Windows:**
```powershell
# Sjekk Docker Desktop innstillinger
# Resources > File Sharing
# Legg til mappen som skal deles
```

**Linux:**
```bash
# Sett riktige permissions
chmod -R 755 backend/data
```

### Problem: Filer endres ikke på host

**Løsning:**
```powershell
# Sjekk at volume ikke er read-only
docker-compose config | Select-String "data"

# Sjekk actual mount
docker inspect stac-backend | Select-String "Mounts" -Context 10
```

### Problem: Treg performance

**Løsning:**
- Bruk WSL2 på Windows
- Reduser antall filer i mappen
- Vurder navngitte volumes i stedet for bind mounts

## Automatisk Scanning

Systemet scanner IKKE automatisk for nye filer. Du må manuelt refreshe katalogen:

### Oppsett for automatisk scanning (valgfritt)

**Opprett watch script:**

```python
# backend/watch_data.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import time

class DataWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            requests.post("http://localhost:8000/refresh")

observer = Observer()
observer.schedule(DataWatcher(), "/app/data", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

## Best Practices

### 1. Organisering
```
backend/data/
├── README.md           # Dokumenter hva som ligger her
├── cog/               # Organisert etter type
├── vector/
├── pointcloud/
└── metadata/          # Ekstra metadata filer
```

### 2. Naming Convention
- Bruk beskrivende filnavn
- Unngå mellomrom (bruk underscore)
- Inkluder dato hvis relevant: `elevation_2024-01-15.tif`

### 3. Metadata
Legg ved sidecar-filer hvis mulig:
```
elevation.tif
elevation.tif.aux.xml
elevation.json  # Ekstra metadata
```

### 4. Backup
```powershell
# Backup data directory
tar -czf stac-data-backup-$(Get-Date -Format 'yyyy-MM-dd').tar.gz backend/data/
```

## Eksempel på Full Workflow

### 1. Legg til ny data

```powershell
# Kopier filer
copy D:\newdata\*.tif backend\data\raster\

# Verifiser
ls backend\data\raster\
```

### 2. Refresh katalogen

```powershell
# Via API
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

### 3. Verifiser i UI

Åpne http://localhost:3000 og sjekk at nye items vises.

### 4. Sjekk logs

```powershell
docker-compose logs backend | Select-String "Scanning"
```

## Konklusjon

Data folder mounting er allerede konfigurert og klar til bruk!

- ✅ **Standard lokasjon:** `backend/data/`
- ✅ **Automatisk synkronisering** mellom host og container
- ✅ **Read/Write tilgang** fra begge sider
- ✅ **Persistent** - data overlever container restart

**Neste steg:**
1. Legg dine geospatiale filer i `backend/data/`
2. Klikk "Oppdater katalog" i UI
3. Utforsk dine data i STAC Katalog!

---

**Se også:**
- [DOCKER.md](DOCKER.md) - Full Docker dokumentasjon
- [README.md](README.md) - Prosjekt oversikt
- [docker-compose.yml](docker-compose.yml) - Gjeldende konfigurasjon

