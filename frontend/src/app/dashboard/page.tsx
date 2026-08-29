"use client"

import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import AnfirWorkbookPanel from "@/components/AnfirWorkbookPanel"
import AnfirWorkbookCharts from "@/components/AnfirWorkbookCharts"
import { useI18n } from "@/core/i18n"

const text={
 "pt-BR":{eyebrow:"Leitura estratégica ANFIR",title:"Dashboard Executivo",subtitle:"Fotografia estratégica Viena SP 2026 construída a partir do workbook auditado Carrier/JOV.",history:"Abrir histórico ANFIR"},
 en:{eyebrow:"ANFIR strategic reading",title:"Executive Dashboard",subtitle:"Viena SP 2026 strategic snapshot built from the audited Carrier/JOV workbook.",history:"Open ANFIR history"},
 es:{eyebrow:"Lectura estratégica ANFIR",title:"Panel Ejecutivo",subtitle:"Fotografía estratégica Viena SP 2026 construida a partir del workbook auditado Carrier/JOV.",history:"Abrir histórico ANFIR"},
} as const

export default function DashboardExecutivo(){
 const{locale}=useI18n();const tx=text[locale]
 return <main className="flex min-h-screen bg-[#020817] text-white">
  <Sidebar/>
  <section className="min-w-0 flex-1 overflow-hidden">
   <Topbar/>
   <div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
     <div>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">{tx.eyebrow}</p>
      <h1 className="mt-2 text-3xl font-bold">{tx.title}</h1>
      <p className="mt-2 max-w-4xl text-sm text-slate-400">{tx.subtitle}</p>
     </div>
     <Link href="/dashboard/anfir-historico" className="inline-flex shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2.5 text-sm font-semibold text-cyan-200 transition hover:border-cyan-400 hover:bg-cyan-500/20">{tx.history}</Link>
    </header>
    <AnfirWorkbookPanel/>
    <AnfirWorkbookCharts/>
   </div>
  </section>
 </main>
}
