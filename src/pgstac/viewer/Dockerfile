# Multi-stage: stage 1 builds the STAC Browser SPA, stage 2 serves it + the S3 proxy.

# ---- stage 1: build STAC Browser (pinned release) -------------------------
ARG STAC_BROWSER_VERSION=v4.0.1
ARG PATH_PREFIX=/

FROM node:20-alpine AS spa
ARG STAC_BROWSER_VERSION
ARG PATH_PREFIX
RUN apk add --no-cache git python3 make g++
WORKDIR /src
RUN git clone --depth 1 --branch "${STAC_BROWSER_VERSION}" \
    https://github.com/radiantearth/stac-browser.git .
RUN npm install
# MapLibre + pmtiles for the inline "Data preview" tab (renders the item's PMTiles data).
RUN npm install maplibre-gl@^4.7.1 pmtiles@^3.2.0
# Custom metadata-field rendering for the scanner's proc:*/pmtiles:* properties.
# Overwrites the upstream stub; imported by src/components/Metadata.vue at build.
COPY stac-browser/fields.config.js /src/fields.config.js
# Make "Open in Protomaps" emit the real S3 URL instead of the viewer proxy URL
# (pmtiles.io fetches client-side; s3Base is injected via /config.js).
COPY stac-browser/actions/Protomaps.js /src/src/actions/assets/Protomaps.js
# Inline MapLibre PMTiles preview: a new component + an Item view patched to mount it as a
# lazy "Data preview" tab. Item.vue is PINNED to v4.0.1 (re-sync on STAC_BROWSER_VERSION bump).
COPY stac-browser/components/MapLibrePreview.vue /src/src/components/MapLibrePreview.vue
COPY stac-browser/views/Item.vue /src/src/views/Item.vue
# DYNAMIC_CONFIG: uncomment the runtime <script src="config.js"> so the app reads
# window.STAC_BROWSER_CONFIG at load time (we serve that file dynamically from FastAPI).
RUN sed -i 's|<!-- <script defer="defer" src="/config.js"></script> -->|<script defer="defer" src="'"${PATH_PREFIX}"'config.js"></script>|g' public/index.html
# Hash history mode => no server-side SPA routing; deep-link refresh can't 404.
RUN npm run build -- --historyMode=hash --pathPrefix="${PATH_PREFIX}"
# In DYNAMIC_CONFIG mode the app reads the WHOLE config from window.STAC_BROWSER_CONFIG
# (build-time defaults are NOT embedded). Extract the pinned version's complete default
# config so the runtime config.js can merge our overrides onto a full, valid object.
RUN node -e "process.stdout.write(JSON.stringify(require('./config.js')))" > /src/config.default.json

# ---- stage 2: FastAPI app serving the SPA + signing/rewriting S3 proxy -----
FROM python:3.12-slim AS app
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY --from=spa /src/dist ./static
COPY --from=spa /src/config.default.json ./config.default.json
ENV STATIC_DIR=/app/static \
    PORT=8080 \
    PATH_PREFIX=/
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
