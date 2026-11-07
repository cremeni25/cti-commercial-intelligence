"use client"

import Link from "next/link"
import { ArrowLeft, Loader2, RefreshCw } from "lucide-react"
import BriefingComercialView from "@/components/inteligencia/BriefingComercialView"
import { useBriefingComercial } from "@/components/inteligencia/useBriefingComercial"
import ResumoDiarioToggle from "@/components/inteligencia/ResumoDiarioToggle"

export default function CrmAppPrioridadesPage() {
  const { briefing, carregando, erro, atualizar } = useBriefingComercial({ limite: 15 })

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-5 flex items-center gap-3">
          <Link href="/crm-app" aria-label="Voltar ao início" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
          <div className="min-w-0 flex-1">
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p>
            <h1 className="text-2xl font-bold">Prioridades do dia</h1>
            <p className="text-sm text-slate-400">O que fazer agora, em ordem.</p>
          </div>
          <button type="button" onClick={() => void atualizar()} disabled={carregando} aria-label="Atualizar leitura" className="grid size-11 place-items-center rounded-2xl border border-cyan-800 bg-cyan-950/30 text-cyan-300"><RefreshCw size={18} className={carregando ? "animate-spin" : ""}/></button>
        </header>
        {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
        {briefing ? <BriefingComercialView briefing={briefing} canal="app" onAtualizar={atualizar}/> : carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : null}
        <div className="mt-6"><ResumoDiarioToggle/></div>
      </div>
    </main>
  )
}
