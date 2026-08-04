"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const wordUrl = `${API_URL}/crm-documentos/propostas/${id}/previsualizar-documento-arquivo`

  return <main className="min-h-screen bg-slate-100 px-4 py-6">
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
        <a href={wordUrl} className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">Abrir documento Word</a>
      </div>

      <section className="rounded-2xl border border-slate-300 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900">Proposta oficial Carrier em Word</h1>
        <p className="mt-2 text-slate-600">O documento oficial recebe somente os dados comerciais disponíveis no dossiê e permanece no formato Word original.</p>
        <div className="mt-5 rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-sm text-emerald-900">
          Imagens, logomarca, tabelas, fontes, margens, parágrafos e paginação permanecem preservados. Nenhuma conversão para PDF é realizada.
        </div>
        <a href={wordUrl} className="mt-6 inline-flex rounded-xl bg-[#17468f] px-5 py-3 font-semibold text-white">Gerar e abrir Word preenchido</a>
      </section>
    </div>
  </main>
}
