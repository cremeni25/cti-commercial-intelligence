"use client"

import Link from "next/link"
import { Suspense } from "react"
import { CheckCircle2, ChevronRight, Home, Plus } from "lucide-react"
import { useSearchParams } from "next/navigation"

function ConteudoConcluido() {
  const params = useSearchParams()
  const cliente = params.get("cliente") || "Cliente"
  const oportunidade = params.get("oportunidade") || ""

  return (
    <div className="mx-auto max-w-2xl">
      <section className="rounded-3xl border border-emerald-900/80 bg-emerald-950/20 p-6 text-center">
        <CheckCircle2 size={46} className="mx-auto text-emerald-300" />
        <h1 className="mt-4 text-3xl font-bold">Registrado</h1>
        <p className="mt-2 text-base leading-6 text-emerald-100/80">A interação com <strong>{cliente}</strong> já foi incorporada ao histórico do CRM.</p>
      </section>

      <div className="mt-5 grid gap-3">
        {oportunidade && (
          <Link href={`/crm-app/historico/${encodeURIComponent(oportunidade)}?origem=campo`} className="flex min-h-20 items-center gap-4 rounded-3xl bg-cyan-500 p-5 font-bold text-slate-950">
            <span className="min-w-0 flex-1"><span className="block text-lg">Continuar esta negociação</span><span className="mt-1 block text-sm font-medium opacity-70">O CTI abre exatamente o processo que você acabou de atualizar.</span></span><ChevronRight size={22}/>
          </Link>
        )}
        <Link href="/crm-app/acao" className="flex min-h-16 items-center gap-3 rounded-2xl border border-[#24466f] bg-[#091a33] px-5 text-base font-semibold text-cyan-200"><Plus size={20}/>Registrar outra ação</Link>
        <Link href="/crm-app" className="flex min-h-16 items-center gap-3 rounded-2xl border border-[#24466f] bg-[#091a33] px-5 text-base font-semibold text-slate-300"><Home size={20}/>Voltar ao Meu dia</Link>
      </div>
    </div>
  )
}

export default function AcaoConcluidaPage() {
  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 pb-28 pt-8 text-white sm:px-6">
      <Suspense fallback={<div className="mx-auto max-w-2xl rounded-3xl border border-[#16325c] bg-[#07162b] p-6 text-center text-slate-400">Confirmando registro...</div>}>
        <ConteudoConcluido />
      </Suspense>
    </main>
  )
}
