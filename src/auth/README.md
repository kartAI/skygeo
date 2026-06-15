# STAC Asset Auth Demo

Eksempel på autentisering av STAC assets ved bruk av pre-signed-urls.
Denne demoen tar noen snarveier for å eksemplifisere en flyt hvor
STAC API peker på en auth server som genererer og redirecter til
en pre-singed-url.


## Getting started

```bash
# Start STAC API and storage
# pwd: src/auth/
cd api/
docker compose up -d
./init_db.sh
```

```bash
# Start Auth server
# pwd src/auth/
pip install -r requrements.txt
fastapi dev
```

```bash
# Test connections

# Authenticated directly to storage
curl -i http://localhost:8080/test.txt?token=demo123
# Not authenticated directly to storage
curl -i http://localhost:8080/test.txt

# Authenticated to auth server (redirect)
curl -H "Authorization: bearer mysecrettoken123" http://localhost:8000/test.txt -L
# Not authenticated to auth server
curl http://localhost:8000/test.txt -L

# Find the item using STAC search
curl -X 'GET' \
  'http://localhost:8082/search?collections=auth-test&ids=the-message&limit=10&filter-lang=cql2-text' \
  -H 'accept: application/geo+json'
```



