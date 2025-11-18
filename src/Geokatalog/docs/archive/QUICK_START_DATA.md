# Quick Start - Legge til Data

## ✅ Data Mounting er Allerede Konfigurert!

Volume mounting er satt opp og klar til bruk:

```
HOST:       backend/data/     ↔  CONTAINER: /app/data/
            (synkronisert i sanntid)
```

## 🚀 Kom i Gang på 3 Steg

### Steg 1: Legg til Filer

```powershell
# Kopier dine geospatiale filer
copy C:\mine_data\*.tif backend\data\
copy C:\mine_data\*.fgb backend\data\
copy C:\mine_data\*.parquet backend\data\
```

### Steg 2: Refresh Katalogen

**Via UI:**
- Gå til http://localhost:3000
- Klikk "Oppdater katalog" knappen

**Via API:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

### Steg 3: Utforsk Data

Åpne http://localhost:3000 og se dine nye collections!

## 📂 Støttede Formater

| Format | Extensions | Collection |
|--------|-----------|------------|
| COG | `.tif`, `.tiff` | Cloud Optimized GeoTIFF |
| GeoParquet | `.parquet`, `.geoparquet` | GeoParquet |
| FlatGeobuf | `.fgb` | FlatGeobuf |
| PMTiles | `.pmtiles` | PMTiles |
| COPC | `.copc.laz`, `.laz` | Cloud Optimized Point Cloud |

## 💡 Eksempel Data

Du har allerede en eksempelfil:
- `UScounties.fgb` (14 MB) - US counties boundaries

Test den:
1. Gå til http://localhost:3000
2. Klikk "Oppdater katalog"
3. Se "FlatGeobuf" collection
4. Klikk på den for å se items og kart!

## 🔄 Synkronisering

Endringer synkroniseres **umiddelbart**:

| Du gjør | Resultat |
|---------|----------|
| Legger til fil | ✓ Synlig i container umiddelbart |
| Sletter fil | ✓ Fjernet fra container umiddelbart |
| Endrer fil | ✓ Oppdatert i container ved lagring |

## 📍 Nåværende Status

**Data directory:** `backend/data/`

**Mounted to container:** `/app/data/`

**Aktuelle filer:**
```powershell
ls backend/data/
# Output:
# - README.md
# - UScounties.fgb (14 MB)
```

## 🛠️ Nyttige Kommandoer

### Se filer i container
```powershell
docker-compose exec backend ls -lah /app/data/
```

### Sjekk disk usage
```powershell
docker-compose exec backend du -sh /app/data
```

### Kopier fil direkte til container
```powershell
docker cp myfile.tif stac-backend:/app/data/
```

### Test synkronisering
```powershell
# Opprett fil på host
echo "test" > backend/data/test.txt

# Sjekk i container
docker-compose exec backend cat /app/data/test.txt
```

## 📖 Mer Informasjon

- **[DATA_MOUNTING.md](DATA_MOUNTING.md)** - Komplett guide
- **[VOLUME_MOUNTING_EXAMPLE.md](VOLUME_MOUNTING_EXAMPLE.md)** - Visuelle eksempler
- **[backend/data/README.md](backend/data/README.md)** - Data directory guide

## 🎯 Best Practices

1. **Organiser i mapper:**
   ```
   backend/data/
   ├── raster/
   ├── vector/
   └── pointcloud/
   ```

2. **Bruk beskrivende navn:**
   - ✅ `elevation_norway_10m.tif`
   - ❌ `data1.tif`

3. **Backup regelmessig:**
   ```powershell
   tar -czf data-backup.tar.gz backend/data/
   ```

## ⚡ Performance Tips

- Bruk WSL2 backend i Docker Desktop (Windows)
- Unngå veldig mange små filer
- Vurder eksterne volumes for store datasett

---

**Alt er klart! Legg til dine data og start å utforske! 🎉**

