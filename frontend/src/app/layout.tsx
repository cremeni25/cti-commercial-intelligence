import type { Metadata } from "next";

import "./globals.css";

import { AuthProvider } from "@/core/auth";

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
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
