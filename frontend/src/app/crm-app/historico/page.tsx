"use client"

import HistoricoNegociacoesEncerradas from "@/components/crm/HistoricoNegociacoesEncerradas"

export default function CrmAppHistoricoPage(){
  return <main className="min-h-screen bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
    <div className="mx-auto w-full max-w-5xl"><HistoricoNegociacoesEncerradas modo="app"/></div>
  </main>
}
