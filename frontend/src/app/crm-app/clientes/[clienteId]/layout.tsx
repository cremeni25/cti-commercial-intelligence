"use client"

import { useRouter } from "next/navigation"
import type { MouseEvent, ReactNode } from "react"

export default function ClienteDossieLayout({ children }: { children: ReactNode }) {
  const router = useRouter()

  function preservarOrigem(event: MouseEvent<HTMLDivElement>) {
    const alvo = event.target
    if (!(alvo instanceof Element)) return

    const link = alvo.closest('a[href="/crm-app/clientes"]')
    if (!link) return

    event.preventDefault()
    router.back()
  }

  return <div onClickCapture={preservarOrigem}>{children}</div>
}
