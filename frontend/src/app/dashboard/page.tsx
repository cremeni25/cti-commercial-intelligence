"use client"

import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import AnfirWorkbookPanel from "@/components/AnfirWorkbookPanel"
import AnfirWorkbookCharts from "@/components/AnfirWorkbookCharts"

export default function DashboardExecutivo(){
 return <main className="flex min-h-screen bg-[#020817] text-white">
  <Sidebar/>
  <section className="min-w-0 flex-1 overflow-hidden">
   <Topbar/>
   <div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
     <div>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura estratégica ANFIR</p>
      <h1 className="mt-2 text-3xl font-bold">Dashboard Executivo</h1>
      <p className="mt-2 max-w-4xl text-sm text-slate-400">Fotografia estratégica Viena SP 2026 construída a partir do workbook auditado Carrier/JOV.</p>
     </div>
     <Link href="/dashboard/anfir-historico" className="inline-flex shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2.5 text-sm font-semibold text-cyan-200 transition hover:border-cyan-400 hover:bg-cyan-500/20">
      Abrir histórico ANFIR
     </Link>
    </header>

    <AnfirWorkbookPanel/>
    <AnfirWorkbookCharts/>
   </div>
  </section>
 </main>
}
