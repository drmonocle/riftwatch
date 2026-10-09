// RiftWatch web: pass-through service worker for /riftwatch/.
// lolworlds.com's site-wide /sw.js answers requests cache-first, which would keep live scores
// stale. This worker's narrower scope takes over /riftwatch/ and lets every request go straight
// to the network (no fetch handler = normal browser behaviour).
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
