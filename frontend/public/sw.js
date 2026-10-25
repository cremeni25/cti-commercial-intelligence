const CACHE_NAME = "cti-crm-v4"
// Somente documentos sem dados de usuário e arquivos estáticos entram no cache.
// Perfil, catálogo, atendimentos e tokens nunca são armazenados pelo service worker.
const DOCUMENTOS = new Set(["/crm-app", "/crm-app/", "/crm-app/feiras", "/crm-app/login"])
const ESTATICOS = new Set(["/crm-app/manifest.webmanifest", "/cti-crm-icon.svg"])

async function prepararShell() {
  const cache = await caches.open(CACHE_NAME)
  for (const path of ["/crm-app", "/crm-app/feiras", "/crm-app/login"]) {
    const response = await fetch(path, { cache: "reload", credentials: "omit" })
    if (!response.ok || !response.headers.get("content-type")?.includes("text/html")) throw Error("Shell CTI indisponível")
    const html = await response.clone().text()
    await cache.put(path, response)
    const assets = [...html.matchAll(/(?:src|href)="([^"<>]+)"/g)].map(m => new URL(m[1].replaceAll("&amp;", "&"), self.location.origin)).filter(u => u.origin === self.location.origin && u.pathname.startsWith("/_next/static/"))
    await Promise.all([...new Set(assets.map(u => u.href))].map(async url => {
      const asset = await fetch(url, { credentials: "omit" })
      if (!asset.ok) throw Error("Arquivo CTI indisponível")
      await cache.put(url, asset)
    }))
  }
}
self.addEventListener("message", event => {
  if (event.data?.type === "SKIP_WAITING") void self.skipWaiting()
})
self.addEventListener("install", event => { event.waitUntil(prepararShell().then(() => self.skipWaiting())) })
self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key.startsWith("cti-crm-") && key !== CACHE_NAME) await caches.delete(key)
    await self.clients.claim()
  })())
})
self.addEventListener("fetch", event => {
  const request = event.request
  if (request.method !== "GET") return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  const documento = request.mode === "navigate" && DOCUMENTOS.has(url.pathname)
  // Feiras exige sempre a versão publicada: não servir HTML antigo do cache.
  if (request.mode === "navigate" && url.pathname === "/crm-app/feiras") return
  const estatico = url.pathname.startsWith("/_next/static/") || ESTATICOS.has(url.pathname)
  if (!documento && !estatico) return
  const key = documento ? url.pathname.replace(/\/$/, "") : request
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME)
    try {
      const response = await fetch(request)
      const tipoValido = !documento || response.headers.get("content-type")?.includes("text/html")
      if (response.ok && !response.redirected && tipoValido) await cache.put(key, response.clone())
      return response
    } catch {
      return (await cache.match(key)) || new Response("CTI sem conexão. Abra Feiras após preparar este aparelho com internet.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } })
    }
  })())
})
