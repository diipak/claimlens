// PWA Service Worker for ClaimLens
const CACHE_NAME = "claimlens-cache-v3";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/favicon.svg",
  "/manifest.json"
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {
        // Safe fallback if some assets fail to load during caching
        console.log("Pre-caching skipped some non-critical files.");
      });
    })
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    self.clients.claim().then(() => {
      // Clear out old caches if needed
      return caches.keys().then((keys) => {
        return Promise.all(
          keys.map((key) => {
            if (key !== CACHE_NAME) {
              return caches.delete(key);
            }
          })
        );
      });
    })
  );
});

// Simple pass-through fetch handler (with cache fallback for static shell)
self.addEventListener("fetch", (event) => {
  // Let the browser handle standard POST/API calls directly
  if (event.request.method !== "GET" || event.request.url.includes("/api/")) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache static assets dynamically
        if (response && response.status === 200 && response.type === "basic") {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline fallback to cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return new Response("Offline mode. Connect to internet to use ClaimLens.", {
            status: 503,
            statusText: "Service Unavailable"
          });
        });
      })
  );
});
