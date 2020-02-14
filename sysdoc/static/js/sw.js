var CACHE_NAME = 'static-cache';
var urlsToCache = [
  '/offline',
];
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
    .then(function(cache) {
      return cache.addAll(urlsToCache);
    })
  );
});
