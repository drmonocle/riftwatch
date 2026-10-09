// RiftWatch web: service worker for /riftwatch/.
// lolworlds.com's site-wide /sw.js answers requests cache-first, which would keep live scores
// stale. This worker's narrower scope takes over /riftwatch/ and passes every request straight
// to the network. It only steps in when the page itself can't be loaded (offline), and it is
// what lets browsers offer "Add to Home Screen".
const OFFLINE_HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RiftWatch</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#091428;color:#f0e6d2;
font:15px/1.5 system-ui,sans-serif;text-align:center;padding:24px}h1{color:#c8aa6e;font-size:22px;margin:0 0 8px}
p{color:#9bb3c9;margin:0 0 20px}button{background:#c8aa6e;color:#091428;border:0;border-radius:8px;
padding:10px 18px;font-weight:700;font-size:14px}</style></head><body><div><h1>RiftWatch is offline</h1>
<p>Live scores need a connection. Try again once you're back online.</p>
<button onclick="location.reload()">Retry</button></div></body></html>`;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  if (event.request.mode !== "navigate") return; // assets and APIs: plain network, no caching
  event.respondWith(
    fetch(event.request).catch(
      () => new Response(OFFLINE_HTML, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } }),
    ),
  );
});
