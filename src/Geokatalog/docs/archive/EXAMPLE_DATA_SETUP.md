# Example: Setting Up External Data Sources

Praktiske eksempler på hvordan du setter opp eksterne datakilder for STAC Katalog.

## Scenario 1: Enkel lokal utvikling

**Situasjon:** Du har testdata på din lokale disk

```powershell
# Kopier noen testfiler
Copy-Item C:\mine_data\*.tif backend\data\
Copy-Item C:\mine_data\*.fgb backend\data\

# Start systemet
docker-compose up -d

# Trigger refresh
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

**Resultat:** Filene er umiddelbart tilgjengelig i STAC katalogen.

---

## Scenario 2: Stor ekstern disk

**Situasjon:** Du har 500GB geodata på en ekstern disk (D:)

### Steg 1: Opprett override fil

```powershell
# Kopier eksempel-filen
Copy-Item docker-compose.override.yml.example docker-compose.override.yml
```

### Steg 2: Rediger docker-compose.override.yml

```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Mount hele eksterne disken (read-only for sikkerhet)
      - D:/geodata:/app/data/external:ro
```

### Steg 3: Restart containere

```powershell
docker-compose down
docker-compose up -d
```

### Steg 4: Verifiser

```powershell
# Sjekk at filer er tilgjengelig
docker exec stac-backend ls -lh /app/data/external/

# Trigger refresh
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

**Struktur i STAC:**
- Local data: `backend/data/` → `/app/data/`
- External data: `D:/geodata/` → `/app/data/external/`

---

## Scenario 3: Flere datakilder

**Situasjon:** Du har data spredt over flere lokasjoner

### docker-compose.override.yml:

```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Satellite imagery på en disk
      - D:/satellite:/app/data/satellite:ro
      
      # Elevation data på en annen
      - E:/elevation:/app/data/elevation:ro
      
      # Vector data lokalt
      - D:/vector:/app/data/vector:ro
      
      # Point clouds på NAS
      - //nas-server/pointclouds:/app/data/pointclouds:ro
```

**Før bruk på Windows:**
```powershell
# Map nettverks-share
net use Z: \\nas-server\pointclouds /persistent:yes

# Oppdater override fil til å bruke Z:
# - Z:/:/app/data/pointclouds:ro
```

---

## Scenario 4: Team delt data

**Situasjon:** Team deler data på en nettverks-share

### Windows Setup:

```powershell
# 1. Map nettverks-share
net use S: \\company-server\geodata /user:domain\username /persistent:yes

# 2. Opprett override
@"
version: '3.8'

services:
  backend:
    volumes:
      - S:/:/app/data/shared:ro
"@ | Out-File docker-compose.override.yml
```

### Linux/Mac Setup:

```bash
# 1. Mount SMB share
sudo mount -t cifs //company-server/geodata /mnt/shared -o username=user,password=pass

# 2. Opprett override
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  backend:
    volumes:
      - /mnt/shared:/app/data/shared:ro
EOF
```

---

## Scenario 5: Read-Write for prosessering

**Situasjon:** Du vil prosessere data og lagre output

```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Input data (read-only)
      - D:/raw_data:/app/data/input:ro
      
      # Output/processed data (read-write)
      - D:/processed:/app/data/output
      
      # Temporary scratch space
      - ./backend/temp:/app/data/temp
```

**Bruk:**
1. Legg raw data i `D:/raw_data/`
2. Prosesser med backend (via API eller scripts)
3. Output havner i `D:/processed/`

---

## Scenario 6: Symbolske lenker (uten Docker override)

**Situasjon:** Du vil unngå å endre docker-compose

### Windows (PowerShell som Administrator):

```powershell
# Opprett symbolsk lenke
New-Item -ItemType SymbolicLink `
  -Path "backend\data\satellite" `
  -Target "D:\large_satellite_data"

New-Item -ItemType SymbolicLink `
  -Path "backend\data\lidar" `
  -Target "E:\lidar_repository"
```

### Linux/Mac:

```bash
# Opprett symbolske lenker
ln -s /mnt/external/satellite backend/data/satellite
ln -s /mnt/nas/lidar backend/data/lidar
```

**Fordel:** Ingen endringer i Docker-konfigurasjon nødvendig!

---

## Scenario 7: Cloud storage (OneDrive, Dropbox, etc)

**Situasjon:** Data ligger i cloud sync folder

### OneDrive:

```yaml
services:
  backend:
    volumes:
      - C:/Users/YourName/OneDrive/GeoData:/app/data/cloud:ro
```

### Dropbox:

```yaml
services:
  backend:
    volumes:
      - C:/Users/YourName/Dropbox/GeoData:/app/data/dropbox:ro
```

**Merk:** Cloud sync kan være tregt for store filer!

---

## Testing av Mounting

### Test 1: Opprett test-fil på host

```powershell
# Opprett en test-fil
"TEST" | Out-File backend\data\test.txt

# Sjekk i container
docker exec stac-backend cat /app/data/test.txt

# Rydd opp
Remove-Item backend\data\test.txt
```

### Test 2: Sjekk eksterne mounts

```powershell
# Liste alle mounted paths
docker exec stac-backend ls -lh /app/data/

# Sjekk spesifikk mount
docker exec stac-backend ls -lh /app/data/external/
```

### Test 3: Verifiser permissions

```powershell
# Sjekk om vi kan lese
docker exec stac-backend cat /app/data/external/somefile.tif > $null
Write-Host "✓ Read OK"

# Sjekk om read-only fungerer
docker exec stac-backend touch /app/data/external/test.txt 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✓ Read-only fungerer!"
}
```

---

## Performance Tips

### Tip 1: Bruk read-only når mulig
```yaml
# Read-only er raskere og tryggere
- D:/data:/app/data/archive:ro
```

### Tip 2: Unngå for mange små filer
```
❌ Dårlig: 10,000 små GeoJSON filer
✅ Bra: 10 store GeoParquet filer
```

### Tip 3: Bruk optimaliserte formater
```
✅ COG i stedet for vanlig GeoTIFF
✅ FlatGeobuf i stedet for Shapefile
✅ GeoParquet i stedet for GeoJSON
✅ COPC i stedet for LAS
```

### Tip 4: Windows - bruk WSL2 backend
Docker Desktop → Settings → General → Use WSL 2 based engine

---

## Troubleshooting

### Problem: "Path not found"

**Windows:**
```powershell
# Sjekk at disken er delt med Docker
# Docker Desktop → Settings → Resources → File Sharing
# Legg til D:/ hvis den ikke er der
```

### Problem: "Permission denied"

**Linux:**
```bash
# Fix ownership
sudo chown -R $USER:$USER /path/to/data

# Fix permissions
chmod -R 755 /path/to/data
```

### Problem: Treg ytelse

```yaml
# Prøv delegated mode (Mac)
volumes:
  - /path/to/data:/app/data:delegated
```

---

## Kompleks Eksempel

**Scenario:** Enterprise setup med multiple kilder

```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Local development data
      - ./backend/data:/app/data
      
      # Production archive (read-only)
      - //prod-nas/geodata:/app/data/production:ro
      
      # Satellite imagery (read-only)
      - D:/satellite_repository:/app/data/satellite:ro
      
      # Vector data (read-only)
      - D:/vector_repository:/app/data/vector:ro
      
      # Point cloud archive (read-only)
      - //nas/lidar:/app/data/lidar:ro
      
      # Processing output (read-write)
      - D:/processing_output:/app/data/output
      
      # Temporary workspace (read-write)
      - ./backend/temp:/app/data/temp
    
    environment:
      - CATALOG_TITLE=Enterprise STAC Catalog
      - CATALOG_DESCRIPTION=Multi-source geospatial data catalog
    
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

**Tilgang i katalog:**
- `/app/data/` - Local dev data
- `/app/data/production/` - Production archive
- `/app/data/satellite/` - Satellite imagery
- `/app/data/vector/` - Vector data
- `/app/data/lidar/` - Point clouds
- `/app/data/output/` - Processed output
- `/app/data/temp/` - Scratch space

---

## Verifikasjon Checklist

```powershell
# ✓ Sjekk at container kjører
docker-compose ps

# ✓ Sjekk at volumes er mounted
docker inspect stac-backend | Select-String "Mounts" -Context 20

# ✓ Liste tilgjengelige filer
docker exec stac-backend find /app/data -name "*.tif" -o -name "*.fgb"

# ✓ Sjekk disk space
docker exec stac-backend df -h /app/data

# ✓ Test refresh
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST

# ✓ Sjekk collections
Invoke-WebRequest -Uri http://localhost:8000/collections | ConvertFrom-Json
```

---

**Ferdig!** Dine data er nå tilgjengelig i STAC katalogen via http://localhost:3000

