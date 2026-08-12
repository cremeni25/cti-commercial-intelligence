import type { Metadata } from "next"

import { CrmAppShellNav } from "@/components/crm-app/CrmAppShellNav"
import { PwaRegister } from "@/components/pwa/PwaRegister"

export const metadata: Metadata = {
  title: "CRM Comercial",
  description: "CRM comercial móvel integrado ao CTI Inteligência Comercial.",
  manifest: "/crm-app/manifest.webmanifest",
  applicationName: "CTI / Viena São Paulo — CRM",
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
