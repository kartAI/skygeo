# 📂 Data Mounting - Visuell Oversikt

## ✅ Status: Data-mappen er allerede mounted og fungerer!

```
┌─────────────────────────────────────────────────────────────┐
│                    Din Windows PC                           │
│                                                             │
│  C:\...\STAC-katalog\                                      │
│  └── backend\                                              │
│      └── data\              ←─────────────────┐            │
│          ├── README.md                        │            │
│          └── UScounties.fgb                   │            │
│                                               │            │
│  ┌──────────────────────────────────────────┐ │            │
│  │   Docker Container: stac-backend         │ │            │
│  │                                          │ │            │
│  │   /app/                                  │ │            │
│  │   └── data/              ←───────────────┘ BIND MOUNT   │
│  │       ├── README.md                        (LIVE SYNC)  │
│  │       └── UScounties.fgb                                │
│  │                                                          │
│  │   Backend kan lese disse filene umiddelbart!            │
│  └──────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Hvordan det fungerer

### Steg 1: Du legger til en fil
```powershell
Copy-Item D:\mine_data\elevation.tif backend\data\
```

### Steg 2: Filen er umiddelbart tilgjengelig
```
Host:      backend\data\elevation.tif
Container: /app/data/elevation.tif  ← Samme fil!
```

### Steg 3: Backend scanner filen
```powershell
# Trigger refresh
Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
```

### Steg 4: Vis i frontend
```
Åpne: http://localhost:3000
```

## 📊 Nåværende oppsett

```yaml
# docker-compose.yml (linje 19-20)
volumes:
  - ./backend/data:/app/data
```

**Dette betyr:**
- ✅ Real-time synkronisering
- ✅ Ingen kopiering - direkte tilgang
- ✅ Data bevares ved container restart
- ✅ Kan redigere filer på host

## 🎯 Verifisering

### På Host (din maskin):
```powershell
Get-ChildItem backend\data\
```
**Output:**
```
Name             Length LastWriteTime        
----             ------ -------------        
README.md          5272 2025-11-11 4:01:37 PM
UScounties.fgb 14100008 2025-11-11 2:01:05 PM
```

### I Container:
```powershell
docker exec stac-backend ls -lh /app/data/
```
**Output:**
```
total 14M
-rwxrwxrwx 1 root root 5.2K Nov 11 15:01 README.md
-rwxrwxrwx 1 root root  14M Nov 11 13:01 UScounties.fgb
```

✅ **Samme filer! Mounting fungerer!**

## 🚀 Legg til mer data

### Alternativ 1: Direkte kopiering
```powershell
# Kopier en fil
Copy-Item D:\geodata\myfile.tif backend\data\

# Kopier flere filer
Copy-Item D:\geodata\*.tif backend\data\

# Kopier en hel mappe
Copy-Item D:\geodata\raster backend\data\ -Recurse
```

### Alternativ 2: Mount ekstern disk

**Opprett `docker-compose.override.yml`:**
```yaml
version: '3.8'

services:
  backend:
    volumes:
      # Din store eksterne disk
      - D:/large_geodata:/app/data/external:ro
```

**Restart:**
```powershell
docker-compose down
docker-compose up -d
```

**Resultat:**
```
Host:      D:\large_geodata\file.tif
Container: /app/data/external/file.tif
```

### Alternativ 3: Symbolsk lenke
```powershell
# PowerShell som Administrator
New-Item -ItemType SymbolicLink `
  -Path "backend\data\satellite" `
  -Target "D:\satellite_data"
```

**Resultat:**
```
backend\data\satellite\  →  D:\satellite_data\
```

## 📂 Anbefalt struktur

```
backend/data/
├── README.md                    # Dokumentasjon
├── UScounties.fgb              # Eksisterende testdata
│
├── local/                       # Dine lokale filer
│   ├── test.tif
│   └── sample.fgb
│
├── external/                    # Mounted ekstern disk
│   └── large_files/            (via docker-compose.override.yml)
│
└── satellite/                   # Symbolsk lenke
    └── imagery/                (lenke til D:\satellite_data)
```

## 🔍 Feilsøking

### Test 1: Opprett test-fil
```powershell
"TEST" | Out-File backend\data\test.txt
docker exec stac-backend cat /app/data/test.txt
# Forventet output: TEST
Remove-Item backend\data\test.txt
```

### Test 2: Sjekk mounting
```powershell
docker inspect stac-backend | Select-String "Mounts" -Context 10
```

### Test 3: Sjekk tilgjengelighet
```powershell
# I container
docker exec stac-backend find /app/data -type f -name "*.fgb"
# Output: /app/data/UScounties.fgb
```

## 📖 Relaterte guider

| Guide | Beskrivelse |
|-------|-------------|
| [backend/data/README.md](backend/data/README.md) | Detaljert info om data-mappen |
| [DATA_MOUNTING_GUIDE.md](DATA_MOUNTING_GUIDE.md) | Omfattende mounting guide |
| [EXAMPLE_DATA_SETUP.md](EXAMPLE_DATA_SETUP.md) | Praktiske eksempler |
| [DOCKER.md](DOCKER.md) | Docker dokumentasjon |

## 💡 Tips

### Tip 1: Sjekk tilgjengelighet
```powershell
# Quick check
docker exec stac-backend ls -lh /app/data/
```

### Tip 2: Watch for changes
```powershell
# På host - se nye filer
while ($true) { 
    Clear-Host
    Get-ChildItem backend\data\ -Recurse | Select-Object Name, Length
    Start-Sleep 5
}
```

### Tip 3: Automatisk refresh script
```powershell
# add-data.ps1
param($FilePath)

Copy-Item $FilePath backend\data\
Write-Host "✓ Fil kopiert: $(Split-Path $FilePath -Leaf)"

Invoke-WebRequest -Uri http://localhost:8000/refresh -Method POST
Write-Host "✓ Katalog oppdatert"

Start-Process "http://localhost:3000"
```

**Bruk:**
```powershell
.\add-data.ps1 D:\geodata\myfile.tif
```

## 🎉 Konklusjon

**Data mounting er allerede konfigurert og fungerer!**

```
✅ ./backend/data/ (host) ←→ /app/data (container)
✅ Real-time sync
✅ Ingen ekstra oppsett nødvendig
✅ Klar til bruk!
```

**Neste steg:**
1. Legg filer i `backend/data/`
2. Klikk "Oppdater katalog" på http://localhost:3000
3. Utforsk dataene i katalogen!

---

**Verifisert:** 11. november 2025 ✓

