const filePath = "n250_samferdsel_senterlinje.fgb"

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', event => {
  const req = event.request;

  // Only care about .fgb files from unpkg
  if (req.url.includes(filePath)) {
    const range = req.headers.get('range') || null;
    if (range) {
      let [start, end] = range.split("=")[1].split("-").map(Number)

      // Send the info to any open client pages
      event.waitUntil((async () => {
        const clients = await self.clients.matchAll();
        for (const c of clients) {
          c.postMessage({ type: 'range-log', start, end });
        }
      })());
    }
  }

  // Always forward the request to the network
  event.respondWith(fetch(req));
});
