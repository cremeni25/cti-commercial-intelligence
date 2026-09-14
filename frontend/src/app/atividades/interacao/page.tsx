"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import InteracaoComercialForm from "@/components/crm/InteracaoComercialForm"

export default function NovaInteracaoWebPage(){
  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/><div className="p-4 sm:p-6 lg:p-8"><div className="mx-auto max-w-5xl"><header className="mb-6 flex items-start gap-3"><Link href="/atividades" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={21}/></Link><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">CTI Web · CRM integrado</p><h1 className="mt-1 text-3xl font-bold">Registrar interação comercial</h1><p className="mt-2 text-slate-400">O mesmo fluxo do CRM App: registra visita ou contato uma única vez e define se o resultado fica como lead, abre oportunidade ou encerra sem continuidade.</p></div></header><InteracaoComercialForm superficie="web"/></div></div></section></main>
}
