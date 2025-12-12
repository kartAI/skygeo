# Contributing to SkyGeo

Takk for at du vil bidra til SkyGeo! 🎉

## Legge til nye demoer under /docs

Når du lager en ny demo-side under `/docs`, skal den ha en felles header for konsistent navigasjon.

### Steg 1: Inkluder header-scriptet

Legg til følgende script-tag i `<head>`-seksjonen til HTML-filen din:

```html
<head>
  <!-- Dine andre scripts og styles -->
  <script src="../common-header.js"></script>
</head>
```

**Viktig:** Juster stien basert på hvor dyp mappen din er:
- Hvis demoen er i `/docs/demo-navn/index.html` → bruk `../common-header.js`
- Hvis demoen er i `/docs/demo-navn/undermappe/index.html` → bruk `../../common-header.js`

### Steg 2: Oppdater source code mapping

Hvis demoen din har kildekode i `/src`, må du legge til en mapping i `docs/common-header.js`:

1. Åpne `docs/common-header.js`
2. Finn `getCurrentDemoPath()` funksjonen (rundt linje 23-33)
3. Legg til en ny if-setning som mapper din demo-URL til riktig source-mappe:

```javascript
const getCurrentDemoPath = () => {
  const path = window.location.pathname;
  const baseGitHub = 'https://github.com/kartAI/skygeo/tree/main/src';
  
  // Map demo URLs to source code paths - order matters (check more specific paths first)
  if (path.includes('/docs/flatgeobuf/')) return `${baseGitHub}/flatgeobuf`;
  if (path.includes('/docs/parquet/')) return `${baseGitHub}/demo`;
  if (path.includes('/docs/pmtiles_bakgrunnskart/')) return `${baseGitHub}/planetiles2pmtiles`;
  if (path.includes('/docs/din-nye-demo/')) return `${baseGitHub}/din-source-mappe`;  // ← Legg til her
  
  return baseGitHub;
};
```

### Steg 3: Test demoen

1. Start en lokal webserver fra repository root:
   ```bash
   python3 -m http.server 8080
   ```

2. Åpne demoen i nettleseren:
   ```
   http://localhost:8080/docs/din-demo/index.html
   ```

3. Verifiser at headeren vises øverst på siden med:
   - ⛅ SkyGeo 🗺️ tittel
   - Prosjektbeskrivelse
   - Fire navigasjonslenker:
     - 📋 Alle demoer
     - 📖 README
     - 🔗 GitHub Repository
     - 💻 Kildekode for denne demoen

4. Test at alle lenker fungerer
5. Test at headeren ser bra ut både på desktop og mobil (bruk developer tools til å teste responsive design)

### Eksempel

Se på eksisterende demoer for referanse:
- `/docs/flatgeobuf/fgb.html` - Enkel demo med Leaflet
- `/docs/parquet/parquet.html` - Demo med DuckDB WASM
- `/docs/pmtiles_bakgrunnskart/index.html` - Demo med MapLibre og PMTiles

### Vanlige problemer

**Problem:** Headeren vises ikke
- **Løsning:** Sjekk at stien til `common-header.js` er riktig relativt til HTML-filen din

**Problem:** "Kildekode for denne demoen" lenken peker til feil sted
- **Løsning:** Legg til eller oppdater mapping i `getCurrentDemoPath()` funksjonen

**Problem:** Headeren overlapper med innholdet
- **Løsning:** Headeren har `position: relative` og skal ikke overlappe. Hvis du har custom CSS med `position: absolute` eller `fixed` på body-elementer, må du kanskje justere z-index

## Annen dokumentasjon

For mer informasjon om prosjektet, se [README.md](README.md).
