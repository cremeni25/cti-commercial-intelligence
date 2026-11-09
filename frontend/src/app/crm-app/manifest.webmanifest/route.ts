// Manifesto do app instalável (Android e iPhone). Um `manifest.ts` só é
// publicado na raiz de `app/`; dentro de /crm-app ele virava 404 e o celular
// não oferecia a instalação. Por isso o manifesto é servido por esta rota.
export const dynamic = "force-static"

const MANIFESTO = {
  id: "/crm-app/",
  name: "CTI / Viena São Paulo — CRM",
  short_name: "CTI CRM",
  description: "CRM comercial móvel integrado ao CTI Inteligência Comercial.",
  start_url: "/crm-app/",
  scope: "/crm-app/",
  display: "standalone",
  orientation: "portrait",
  background_color: "#020817",
  theme_color: "#061126",
  lang: "pt-BR",
  categories: ["business", "productivity"],
  icons: [
    { src: "/crm-app-icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
    { src: "/crm-app-icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
    { src: "/crm-app-icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    { src: "/cti-crm-icon.svg?v=2", sizes: "any", type: "image/svg+xml", purpose: "any" },
  ],
}

export function GET() {
  return new Response(JSON.stringify(MANIFESTO), {
    headers: { "content-type": "application/manifest+json; charset=utf-8", "cache-control": "public, max-age=3600" },
  })
}
