const CACHE_NAME = 'kaf-roll-v1';
const ASSETS = [
    '/kaf/roll.html',
    '/kaf/roll-manifest.json',
];

// Install — cache app shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch — network first, fall back to cache for app shell
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Don't cache Airtable API calls
    if (url.hostname === 'api.airtable.com') return;

    // For app assets: try network first, fall back to cache
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Update cache with fresh copy
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
