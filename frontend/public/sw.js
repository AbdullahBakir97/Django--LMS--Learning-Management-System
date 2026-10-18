/* Offline support. Kept small on purpose; no build step, no library.
 *
 * - Pages: network first, the cached app shell when offline.
 * - /assets/: file names carry a content hash, so cache first is safe.
 * - Course reading (catalogue, course, lessons, progress) and who you are: network first,
 *   the last copy when offline. Nothing else from the API is stored; sign-out clears it all.
 */
// shortcut: old hashed assets stay cached until VERSION changes; bump it when the cache grows
const VERSION = 'v1'
const SHELL = `shell-${VERSION}`
const ASSETS = `assets-${VERSION}`
const API = `api-${VERSION}`
const READABLE = /^\/api\/(auth\/user\/|me\/enrollments\/|courses\/)/

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(SHELL).then((c) => c.add('/')).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  const keep = new Set([SHELL, ASSETS, API])
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('message', (event) => {
  if (event.data === 'sign-out') event.waitUntil(caches.delete(API))
})

async function networkFirst(request, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName)
  try {
    const response = await fetch(request)
    if (response.ok) await cache.put(fallbackUrl ?? request, response.clone())
    return response
  } catch (error) {
    const cached = await cache.match(fallbackUrl ?? request)
    if (cached) return cached
    throw error
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(ASSETS)
  const cached = await cache.match(request)
  if (cached) return cached
  const response = await fetch(request)
  if (response.ok) await cache.put(request, response.clone())
  return response
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin) return
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, SHELL, '/'))
  } else if (url.pathname.startsWith('/assets/')) {
    event.respondWith(cacheFirst(request))
  } else if (READABLE.test(url.pathname)) {
    event.respondWith(networkFirst(request, API))
  }
})
