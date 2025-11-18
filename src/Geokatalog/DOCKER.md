# STAC Katalog - Docker Deployment

Dette dokumentet beskriver hvordan du kjører STAC Katalog med Docker og Docker Compose.

## ✅ Systemet kjører nå!

Begge tjenestene er oppe og kjører:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Dokumentasjon**: http://localhost:8000/docs

## Oversikt

Systemet består av to Docker-containere:
1. **stac-backend**: Python FastAPI applikasjon (port 8000)
2. **stac-frontend**: Next.js applikasjon (port 3000)

## Forutsetninger

- Docker Desktop installert og kjørende
- Docker Compose (inkludert med Docker Desktop)

## Hurtigstart

### 1. Bygg containers

```powershell
docker-compose build
```

### 2. Start tjenester

```powershell
docker-compose up -d
```

### 3. Sjekk status

```powershell
docker-compose ps
```

### 4. Se logger

```powershell
# Alle tjenester
docker-compose logs

# Kun backend
docker-compose logs backend

# Kun frontend
docker-compose logs frontend

# Følg logger i sanntid
docker-compose logs -f
```

### 5. Stopp tjenester

```powershell
docker-compose down
```

## Kommandoer

### Bygging

```powershell
# Bygg begge tjenester
docker-compose build

# Bygg uten cache (ved problemer)
docker-compose build --no-cache

# Bygg kun en tjeneste
docker-compose build backend
docker-compose build frontend
```

### Kjøring

```powershell
# Start i bakgrunnen
docker-compose up -d

# Start og se logger
docker-compose up

# Start kun en tjeneste
docker-compose up -d backend
```

### Stopp og restart

```powershell
# Stopp tjenester (beholder data)
docker-compose stop

# Start tjenester igjen
docker-compose start

# Restart en tjeneste
docker-compose restart backend

# Stopp og fjern containers
docker-compose down

# Stopp, fjern containers og volumes
docker-compose down -v
```

### Logging og debugging

```powershell
# Se logger (siste 100 linjer)
docker-compose logs --tail=100

# Følg logger i sanntid
docker-compose logs -f backend

# Gå inn i en container
docker-compose exec backend /bin/sh
docker-compose exec frontend /bin/sh
```

## Datamappe

Datamappen er montert som et volume mellom host og container:

```yaml
volumes:
  - ./backend/data:/app/data
```

Dette betyr:
- Filer i `backend/data/` på din maskin er tilgjengelig i containeren
- Du kan legge til filer uten å rebuilde containeren
- Data persisterer selv om containeren stoppes

## Legg til geodata

1. Kopier geospatiale filer til `backend/data/`:

```powershell
copy C:\mine_filer\*.tif backend\data\
copy C:\mine_filer\*.parquet backend\data\
```

2. Trigger en refresh i UI:
   - Gå til http://localhost:3000
   - Klikk "Oppdater katalog"

Eller via API:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

## Feilsøking

### Containers starter ikke

```powershell
# Sjekk logger for feilmeldinger
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port allerede i bruk

Hvis port 8000 eller 3000 er i bruk, endre i `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Bruk port 8001 i stedet
  frontend:
    ports:
      - "3001:3000"  # Bruk port 3001 i stedet
```

Husk å oppdatere `NEXT_PUBLIC_STAC_API_URL` i frontend environment hvis du endrer backend port.

### Backend krasjernpm 

Sjekk logger:

```powershell
docker-compose logs backend
```

Vanlige problemer:
- **NumPy versjon**: Fikset med `numpy<2.0` i requirements.txt
- **GDAL**: Installert i Dockerfile
- **PDAL**: Valgfritt, kun for avansert COPC-støtte

### Frontend bygger ikke

Hvis frontend feiler under bygging:
- Sjekk at `next.config.js` har `output: 'standalone'`
- Sjekk at `public/` mappen eksisterer
- Sjekk at MapView bruker dynamisk import

### Ingen collections vises

1. Sjekk at `backend/data/` inneholder geospatiale filer
2. Sjekk backend-logger:
   ```powershell
   docker-compose logs backend
   ```
3. Trigger refresh:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
   ```

## Produksjonsdeployment

### Miljøvariabler

Opprett `.env` fil i prosjektroot:

```env
# Backend
DATA_DIRECTORY=./data
CATALOG_TITLE=Production STAC Catalog
CATALOG_DESCRIPTION=Geospatial data catalog
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_STAC_API_URL=http://your-domain.com/api
```

### Sikkerhet

For produksjon, vurder:

1. **Bruk eksterne volumes** for data:
   ```yaml
   volumes:
     - /mnt/geodata:/app/data:ro  # read-only
   ```

2. **Legg til autentisering** i backend

3. **Bruk reverse proxy** (nginx, Traefik) foran tjenestene

4. **SSL/TLS** via reverse proxy

5. **Ressursbegrensninger**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

### Skalering

For større datasett:

1. **Øk memory** for backend container
2. **Legg til caching** (Redis)
3. **Bruk database** for metadata (PostgreSQL/PostGIS)
4. **Horizontal skalering** med load balancer

## Docker Compose Konfigurasjon

### Nåværende konfigurasjon

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
      - ./backend/app:/app/app  # For utvikling
    environment:
      - DATA_DIRECTORY=/app/data
      - CATALOG_TITLE=STAC Catalog
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_STAC_API_URL=http://backend:8000
    restart: unless-stopped
```

### Tilpasninger

#### Utviklingsmodus

For utvikling med live reload:

```yaml
services:
  backend:
    volumes:
      - ./backend/app:/app/app  # Allerede inkludert
    command: uvicorn app.main:app --reload --host 0.0.0.0
```

#### Produksjonsmodus

Fjern utviklingsvolumes:

```yaml
services:
  backend:
    volumes:
      - ./backend/data:/app/data  # Kun data
```

## Helsesjekker

Backend har innebygd healthcheck:

```powershell
# Sjekk helse
Invoke-WebRequest -Uri http://localhost:8000/health

# Docker healthcheck status
docker inspect stac-backend | Select-String -Pattern "Health"
```

## Backup

### Backup av metadata

```powershell
# Backup datamappen
tar -czf stac-data-backup.tar.gz backend/data/
```

### Restore

```powershell
# Restore datamappen
tar -xzf stac-data-backup.tar.gz

# Refresh katalogen
docker-compose exec backend curl -X POST http://localhost:8000/refresh
```

## Performance

### Docker-ytelse på Windows

For bedre ytelse:
1. Bruk WSL 2 backend i Docker Desktop
2. Lagre prosjektet i WSL filesystem
3. Alloker mer memory til Docker Desktop

### Overvåking

```powershell
# Ressursbruk
docker stats

# Kun for STAC containers
docker stats stac-backend stac-frontend
```

## Vanlige oppgaver

### Oppdater kode

```powershell
# Stopp containers
docker-compose down

# Pull ny kode (hvis fra git)
git pull

# Rebuild og start
docker-compose build
docker-compose up -d
```

### Vis container info

```powershell
# Alle containers
docker ps

# Med docker-compose
docker-compose ps

# Detaljert info
docker inspect stac-backend
```

### Fjern alt og start på nytt

```powershell
# Stopp og fjern containers
docker-compose down

# Fjern images
docker rmi stac-katalog-backend stac-katalog-frontend

# Rebuild fra scratch
docker-compose build --no-cache

# Start igjen
docker-compose up -d
```

## Nyttige tips

### 1. Live logs i to vinduer

**Vindu 1:**
```powershell
docker-compose logs -f backend
```

**Vindu 2:**
```powershell
docker-compose logs -f frontend
```

### 2. Rask restart

```powershell
docker-compose restart backend
```

### 3. Sjekk disk usage

```powershell
docker system df
```

### 4. Cleanup

```powershell
# Fjern ubrukte images
docker image prune

# Fjern alt ubrukt
docker system prune -a
```

## Neste steg

- ✅ Systemet kjører på http://localhost:3000
- ✅ Legg til geodata i `backend/data/`
- ✅ Test med eksempelfiler
- ⚡ Vurder produksjonsoppsett
- 📊 Implementer overvåking
- 🔐 Legg til autentisering

## Lenker

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Health Check: http://localhost:8000/health

## Support

Ved problemer:
1. Sjekk logs: `docker-compose logs`
2. Sjekk status: `docker-compose ps`
3. Restart: `docker-compose restart`
4. Rebuild: `docker-compose build --no-cache`

