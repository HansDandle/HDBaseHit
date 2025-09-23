self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('tv-media-cache-v1').then((cache) =>
      cache.addAll([
        '/',
        '/static/style.css',
        '/static/js/app.js',
        '/static/manifest.json'
      ])
    )
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((resp) => resp || fetch(e.request))
  );
});
