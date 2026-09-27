"use client"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import HistoricoNegociacoesEncerradas from "@/components/crm/HistoricoNegociacoesEncerradas"

export default function OportunidadesEncerradasPage(){
  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar/>
    <section className="min-w-0 flex-1"><Topbar/><div className="p-4 sm:p-6 lg:p-8"><HistoricoNegociacoesEncerradas modo="web"/></div></section>
  </main>
}
