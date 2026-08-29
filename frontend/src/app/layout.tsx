import type { Metadata, Viewport } from "next"

import "./globals.css"

import { AuthProvider } from "@/core/auth"
import { I18nProvider } from "@/core/i18n"
import { OperationalContextProvider } from "@/context/OperationalContext"

export const metadata: Metadata = {
  title: {
    default: "CTI",
    template: "%s | CTI",
  },
  description: "Centro de Tecnologia e Inteligência Comercial",
  applicationName: "CTI — Inteligência Comercial",
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
        <AuthProvider>
          <I18nProvider>
            <OperationalContextProvider>{children}</OperationalContextProvider>
          </I18nProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
