# ⛅ SkyGeo 🗺️

Utforskning av cloud-native formater og STAC-metadata for norske geografiske datasett.

## Oppsett og bruk av Jupyter Notebooks

Gjennom SkyGeo-prosjektet har vi utviklet en rekke Jupyter-notebooks som kan brukes til å teste både bruksområder og konverteringsløyper for cloud-native formater. Alle notebookene er skrevet i Python og krever et lokalt virtuelt Python-miljø for å laste ned nødvendige pakker og kjøre koden.

Vi anbefaler følgende fremgangsmåte for å sette opp dette miljøet:

1. Åpne din foretrukne terminal og naviger til SkyGeo-mappen.
2. Skriv inn følgende kommando: `python -m venv venv`
3. Aktiver det virtuelle miljøet med kommandoen som samsvarer med ditt operativsystem.

### Aktiver virtuelt miljø

* **Windows (cmd):**
  `venv\Scripts\activate`

* **Windows (PowerShell):**
  `venv\Scripts\Activate.ps1`

* **Linux/macOS:**
  `source venv/bin/activate`

---

### Installasjon av nødvendige Python-pakker og biblioteker

I hver notebook vil du mest sannsynlig trenge én eller flere eksterne Python-pakker eller biblioteker. Disse avhengighetene er som regel definert i hver notebook og kan enkelt installeres i ditt lokale virtuelle miljø ved hjelp av en `requirements.txt`-fil.

For å installere pakkene gjør du følgende:

1. Sørg for at det virtuelle miljøet ditt er aktivert.
2. Naviger til prosjektmappen, eller finn ut hvor den relevante `requirements.txt`-filen ligger.
3. Kjør følgende kommando, eller spesifisere pathen til filen:

   ```bash
   pip install -r path/til/requirements.txt
   ```

   Eksempel:

   ```bash
   pip install -r src/geoparquet/requirements.txt
   ```

Dette vil installere alle nødvendige avhengigheter slik at du kan kjøre notebookene uten problemer.

> 💡 Tips: Hvis du får feilmeldinger under installasjonen, kan det være lurt å oppdatere `pip` først med `pip install --upgrade pip`.