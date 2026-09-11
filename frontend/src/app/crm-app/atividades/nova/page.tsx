"use client"

import Link from "next/link"
import { useEffect } from "react"

export default function NovaAtividadeRedirect() {
  useEffect(() => {
    const destino = `/crm-app/acao/registrar${window.location.search || ""}`
    window.location.replace(destino)
  }, [])

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 py-8 text-white sm:px-6">
      <div className="mx-auto max-w-xl rounded-3xl border border-[#16325c] bg-[#07162b] p-6 text-center">
        <p className="text-sm text-slate-400">Abrindo o registro de atividade...</p>
        <Link href="/crm-app/acao/registrar" className="mt-4 inline-flex min-h-12 items-center justify-center rounded-2xl bg-cyan-500 px-5 font-bold text-slate-950">
          Continuar
        </Link>
      </div>
    </main>
  )
}
