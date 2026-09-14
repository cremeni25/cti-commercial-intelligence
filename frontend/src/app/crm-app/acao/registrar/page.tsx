"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import InteracaoComercialForm from "@/components/crm/InteracaoComercialForm"

export default function RegistroRapidoPage() {
  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-4xl">
        <header className="mb-5 flex items-start gap-3">
          <Link href="/crm-app/acao" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={21}/></Link>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">CTI CRM · interação comercial</p>
            <h1 className="mt-1 text-3xl font-bold">Registrar interação</h1>
            <p className="mt-1 text-sm leading-6 text-slate-400">Visita, ligação, reunião, mensagem ou follow-up no mesmo fluxo. O resultado define se fica como lead, abre oportunidade ou encerra.</p>
          </div>
        </header>
        <InteracaoComercialForm superficie="app" />
      </div>
    </main>
  )
}
