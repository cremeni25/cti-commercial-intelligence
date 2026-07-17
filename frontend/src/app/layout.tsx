import type { Metadata } from "next";

import "./globals.css";

import { AuthProvider } from "@/core/auth";
import { OperationalContextProvider } from "@/context/OperationalContext";

export const metadata: Metadata = {
  title: "CTI",
  description: "Centro de Tecnologia e Inteligência Comercial",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <OperationalContextProvider>
            {children}
          </OperationalContextProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
