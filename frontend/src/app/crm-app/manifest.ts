import type { MetadataRoute } from "next"

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/crm-app/",
    name: "CTI / Viena São Paulo — CRM",
    short_name: "CTI CRM",
    description: "CRM comercial móvel integrado ao CTI Inteligência Comercial.",
    start_url: "/crm-app/",
    scope: "/crm-app/",
    display: "standalone",
    background_color: "#020817",
    theme_color: "#061126",
    lang: "pt-BR",
    categories: ["business", "productivity"],
    icons: [
      {
        src: "/cti-crm-icon.svg?v=2",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  }
}
