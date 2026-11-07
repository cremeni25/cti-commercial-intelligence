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

// Resumo diário do Agente de Inteligência (Web Push). A mensagem já chega
// pronta do backend e nunca é armazenada em cache.
self.addEventListener("push", event => {
  let dados = {}
  try { dados = event.data ? event.data.json() : {} } catch { dados = { body: event.data ? event.data.text() : "" } }
  const destino = typeof dados.url === "string" && dados.url.startsWith("/crm-app") ? dados.url : "/crm-app/prioridades"
  event.waitUntil(self.registration.showNotification(dados.title || "CTI · seu dia comercial", {
    body: dados.body || "Abra o CTI para ver suas prioridades.",
    icon: "/cti-crm-icon.svg",
    badge: "/cti-crm-icon.svg",
    tag: dados.tag || "cti-resumo-diario",
    renotify: false,
    data: { url: destino },
  }))
})
self.addEventListener("notificationclick", event => {
  event.notification.close()
  const destino = new URL(event.notification.data?.url || "/crm-app/prioridades", self.location.origin).href
  event.waitUntil((async () => {
    const janelas = await self.clients.matchAll({ type: "window", includeUncontrolled: true })
    for (const janela of janelas) {
      if (new URL(janela.url).pathname.startsWith("/crm-app") && "focus" in janela) {
        await janela.focus()
        if ("navigate" in janela) await janela.navigate(destino)
        return
      }
    }
    await self.clients.openWindow(destino)
  })())
})
