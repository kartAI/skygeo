# GIS-søk

Dette prosjektet prøver å løse problemet beskrevet i [GitHub Issue #36](https://github.com/kartAI/skygeo/issues/36):

**Hvordan finne samme polygon (med små variasjoner) fra to store datasett på en effektiv måte**

## Løsningsmetode

Prosjektet benytter:
- **DuckDB** - For effektiv håndtering og spørring av store geodatasett
- **Dev Containers** - For reproduserbar utviklingsmiljø

## Problemstilling

Når man jobber med GIS-data fra ulike kilder, er det ofte behov for å identifisere polygoner som representerer det samme geografiske objektet, selv om de kan ha små variasjoner i form av:
- Litt forskjellige koordinater
- Forskjellig oppløsning/detaljnivå
- Små forskjeller i grensedragning

Dette prosjektet utforsker metoder for å gjøre dette på en effektiv måte, spesielt når datasettene er store.

## Utviklingsmiljø

Prosjektet bruker en Dev Container basert på `duckdb/duckdb` med følgende verktøy installert:
- **Python 3** - For databehandling og scripting
- **Jupyter Notebook/Lab** - For interaktiv utvikling og analyse
- **DuckDB Python library** - For å jobbe med DuckDB fra Python
- **Kepler.gl** - For visualisering av geodata
- **GeoPandas** - For GIS-databehandling

### Kom i gang

1. Åpne prosjektet i Visual Studio Code
2. Installer "Dev Containers" extension hvis du ikke har det
3. Trykk `F1` og velg "Dev Containers: Reopen in Container"
4. Vent til containeren er bygget og startet
5. Start Jupyter med kommandoen:
   ```bash
   jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
   ```

Jupyter vil være tilgjengelig på `http://localhost:8888`

