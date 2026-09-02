"use client"

import type { ReactNode } from "react"

export default function PropostaLayout({ children }: { children: ReactNode }) {
  return <div className="[&>main]:!min-h-0">{children}</div>
}
