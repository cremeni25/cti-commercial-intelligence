/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import CarrierProposalDocument from "@/components/crm/CarrierProposalDocument"
import { API_URL } from "@/lib/api"

type Registro = Record<string, unknown>

type PacoteProposta = {
  proposta: Registro
  item: Registro | null
  oportunidade: Registro | null
  cliente: Registro | null
  aceites: Registro[]
  pedidos: Registro[]
}

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [dados, setDados] = useState<PacoteProposta | null>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!id) return
    void (async () => {
      try {
        const resposta = await fetch(`${API_URL}/crm-documentos/propostas/${id}`, { cache: "no-store" })
        const payload = await resposta.json().catch(() => null)
        if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível carregar a proposta.")
        setDados(payload)
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Falha ao carregar a proposta.")
      }
    })()
  }, [id])

  return <main className="min-h-screen bg-slate-200 px-3 py-6 print:bg-white print:p-0">
    <div className="mx-auto mb-6 flex max-w-[794px] flex-wrap items-center justify-between gap-3 print:hidden">
      <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-400 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
      <button type="button" onClick={() => window.print()} className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">Imprimir / salvar PDF</button>
    </div>
    {erro && <div className="mx-auto max-w-[794px] rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}
    {!dados && !erro && <div className="mx-auto max-w-[794px] rounded-xl bg-white p-8 text-slate-600">Carregando documento oficial Carrier...</div>}
    {dados && <CarrierProposalDocument proposta={dados.proposta} item={dados.item} oportunidade={dados.oportunidade} cliente={dados.cliente}/>} 
    <style jsx global>{`
      @media print {
        body { background: white !important; }
        aside, header { display: none !important; }
        .carrier-page { page-break-after: always; break-after: page; }
        .carrier-page:last-child { page-break-after: auto; break-after: auto; }
      }
    `}</style>
  </main>
}
