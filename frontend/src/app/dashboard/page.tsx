"use client"

import Link from "next/link"
import { useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import AnfirWorkbookPanel from "@/components/AnfirWorkbookPanel"
import AnfirWorkbookCharts from "@/components/AnfirWorkbookCharts"

const links = [
  ["Histórico Comercial", "/historico-comercial", "Consultar histórico consolidado e períodos anteriores."],
  ["TR · Trailer", "/equipamentos/trailer", "Detalhar a linha Trailer fora da fotografia ANFIR 2026."],
  ["DT · Diesel Truck", "/equipamentos/diesel-truck", "Detalhar a linha Diesel Truck fora da fotografia ANFIR 2026."],
  ["DD · Direct Drive", "/equipamentos/direct-drive", "Detalhar a linha Direct Drive fora da fotografia ANFIR 2026."],
  ["Empresas", "/empresas", "Aprofundar contas e razões sociais."],
  ["Implementadoras", "/implementadoras", "Aprofundar canais e implementadoras."],
  ["Mapa Estratégico", "/mapa-estrategico", "Aprofundar território, DDD e distribuição geográfica."],
  ["CRM / Oportunidades", "/oportunidades", "Tratar o que está acontecendo agora no processo comercial."],
] as const

export default function DashboardHub(){
  const [mostrarContexto,setMostrarContexto]=useState(false)
  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar/>
    <section className="min-w-0 flex-1 overflow-hidden">
      <Topbar/>
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura estratégica ANFIR</p>
          <h1 className="mt-2 text-3xl font-bold">Dashboard Executivo</h1>
          <p className="mt-2 max-w-4xl text-sm text-slate-400">Fotografia estratégica Viena SP 2026 baseada na auditoria Carrier/JOV. O Dashboard não repete CRM, Histórico, Mapa ou páginas de produto.</p>
        </header>

        <AnfirWorkbookPanel/>
        <AnfirWorkbookCharts/>

        <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5">
          <button type="button" onClick={()=>setMostrarContexto(v=>!v)} className="flex w-full items-center justify-between gap-4 text-left">
            <div>
              <p className="text-sm font-semibold text-cyan-300">Como esta leitura se relaciona com o restante do CTI</p>
              <p className="mt-1 text-xs text-slate-500">Brasil, UF, período histórico e operação atual continuam disponíveis nos módulos próprios; eles não alteram a fotografia ANFIR 2026 acima.</p>
            </div>
            <span className="text-xl text-cyan-300">{mostrarContexto?"−":"+"}</span>
          </button>
          {mostrarContexto&&<div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{links.map(([titulo,href,descricao])=><Link key={href} href={href} className="rounded-xl border border-[#193354] bg-[#08162d] p-4 transition hover:border-cyan-500/60"><p className="font-semibold text-white">{titulo}</p><p className="mt-2 text-xs leading-5 text-slate-400">{descricao}</p></Link>)}</div>}
        </section>
      </div>
    </section>
  </main>
}
