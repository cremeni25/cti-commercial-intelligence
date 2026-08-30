"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import AnfirWorkbookPanel from "@/components/AnfirWorkbookPanel"
import AnfirWorkbookCharts from "@/components/AnfirWorkbookCharts"
import { useAuth } from "@/core/auth/AuthContext"
import { possuiVisaoConsolidada } from "@/core/rbac/commercial-scope"
import { getResponsaveisComerciaisSeguros, type ResponsavelComercialSeguro } from "@/services/modulos-api"

export default function DashboardExecutivo(){
 const {usuario}=useAuth()
 const master=possuiVisaoConsolidada(usuario)
 const[responsaveis,setResponsaveis]=useState<ResponsavelComercialSeguro[]>([])
 const[responsavelId,setResponsavelId]=useState("")

 useEffect(()=>{let ativo=true;if(!master){setResponsaveis([]);setResponsavelId("");return()=>{ativo=false}};void getResponsaveisComerciaisSeguros().then(lista=>{if(ativo)setResponsaveis(lista)}).catch(()=>{if(ativo)setResponsaveis([])});return()=>{ativo=false}},[master])
 const responsavelSelecionado=useMemo(()=>responsaveis.find(item=>item.id===responsavelId),[responsaveis,responsavelId])

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
      <p className="mt-2 text-sm font-semibold text-emerald-300">Visão: {responsavelSelecionado?.nome||usuario?.nome||"Equipe comercial"}</p>
     </div>
     <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      {master&&<label className="flex min-w-[260px] flex-col gap-1 text-xs font-semibold text-slate-400"><span>Responsável comercial</span><select value={responsavelId} onChange={e=>setResponsavelId(e.target.value)} className="rounded-xl border border-cyan-500/40 bg-[#071427] px-3 py-2.5 text-sm text-white"><option value="">Toda a equipe comercial</option>{responsaveis.map(item=><option key={item.id} value={item.id}>{item.nome}</option>)}</select></label>}
      <Link href="/dashboard/anfir-historico" className="inline-flex shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2.5 text-sm font-semibold text-cyan-200 transition hover:border-cyan-400 hover:bg-cyan-500/20">Abrir histórico ANFIR</Link>
     </div>
    </header>
    <AnfirWorkbookPanel responsavelId={responsavelId||undefined}/>
    <AnfirWorkbookCharts responsavelId={responsavelId||undefined}/>
   </div>
  </section>
 </main>
}
