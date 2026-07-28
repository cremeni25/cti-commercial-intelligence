import type { Metadata, Viewport } from "next"

import "./globals.css"

import { AuthProvider } from "@/core/auth"
import { OperationalContextProvider } from "@/context/OperationalContext"
import { PwaRegister } from "@/components/pwa/PwaRegister"

export const metadata: Metadata = {
  title: {
    default: "CTI",
    template: "%s | CTI",
  },
  description: "Centro de Tecnologia e Inteligência Comercial",
  manifest: "/manifest.webmanifest",
  applicationName: "CTI / Viena São Paulo — CRM",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "CTI CRM",
  },
  formatDetection: {
    telephone: false,
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  minimumScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <PwaRegister />
        <AuthProvider>
          <OperationalContextProvider>{children}</OperationalContextProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
