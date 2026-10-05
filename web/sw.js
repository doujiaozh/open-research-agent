var CACHE = "ora-v1";
var FILES = ["/", "/index.html"];

self.addEventListener("install", function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(c) { return c.addAll(FILES); })
  );
});

self.addEventListener("fetch", function(e) {
  if (e.request.method !== "GET") return;
  if (e.request.url.indexOf("/research") !== -1) return;
  e.respondWith(
    caches.match(e.request).then(function(r) {
      return r || fetch(e.request);
    })
  );
});