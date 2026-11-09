import type { Metadata } from "next"

import { CrmAppShellNav } from "@/components/crm-app/CrmAppShellNav"
import { PwaRegister } from "@/components/pwa/PwaRegister"

export const metadata: Metadata = {
  title: "CRM Comercial",
  description: "CRM comercial móvel integrado ao CTI Inteligência Comercial.",
  manifest: "/crm-app/manifest.webmanifest",
  applicationName: "CTI / Viena São Paulo — CRM",
  icons: {
    icon: [{ url: "/crm-app-icons/icon-192.png", sizes: "192x192", type: "image/png" }],
    apple: [{ url: "/crm-app-icons/apple-touch-icon.png", sizes: "180x180" }],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "CTI CRM",
  },
}

export default function CrmAppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PwaRegister />
      {children}
      <CrmAppShellNav />
    </>
  )
}
