/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

type DocumentoOficial = {
  preview?: boolean
  homologado?: boolean
  document: {
    filename?: string
    sha256?: string
    template_code?: string
    template_version?: number
    finalized_at?: string
  }
  url: string
  expires_in: number
}

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [documento, setDocumento] = useState<DocumentoOficial | null>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    if (!id) return
    void (async () => {
      try {
        const finalizar = await fetch(`${API_URL}/crm-documentos/propostas/${id}/finalizar-documento`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
        const finalizado = await finalizar.json().catch(() => null)

        if (!finalizar.ok) {
          const detalhe = String(finalizado?.detail || "")
          if (!detalhe.includes("não homologado visualmente")) {
            throw new Error(detalhe || "Não foi possível finalizar o documento oficial.")
          }
          const preview = await fetch(`${API_URL}/crm-documentos/propostas/${id}/previsualizar-documento`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
          })
          const previewPayload = await preview.json().catch(() => null)
          if (!preview.ok) throw new Error(previewPayload?.detail || "Não foi possível gerar a pré-visualização oficial.")
          setDocumento(previewPayload)
          return
        }

        const resposta = await fetch(`${API_URL}/crm-documentos/propostas/${id}/documento-oficial`, { cache: "no-store" })
        const payload = await resposta.json().catch(() => null)
        if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível acessar o documento oficial.")
        setDocumento(payload)
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Falha ao carregar o documento oficial.")
      } finally {
        setCarregando(false)
      }
    })()
  }, [id])

  const emPreview = documento?.preview === true

  return <main className="min-h-screen bg-slate-100 px-4 py-8">
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
        {documento?.url && <a href={documento.url} target="_blank" rel="noreferrer" className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">{emPreview ? "Abrir documento para validação" : "Abrir / baixar documento oficial"}</a>}
      </div>

      {carregando && <div className="rounded-xl bg-white p-8 text-slate-600 shadow-sm">Preparando e validando o documento oficial Carrier...</div>}
      {erro && <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}
      {documento && <section className="rounded-2xl bg-white p-6 shadow-sm">
        {emPreview && <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          Pré-visualização controlada para validação operacional. Este arquivo ainda não pode ser emitido, convertido ou enviado como documento definitivo.
        </div>}
        <h1 className="text-xl font-bold text-slate-900">{emPreview ? "Documento oficial Carrier para validação" : "Documento oficial Carrier finalizado"}</h1>
        <p className="mt-2 text-slate-600">{emPreview
          ? "Abra o arquivo e confira integralmente textos, tabelas, imagens, logomarca, paginação e campos preenchidos."
          : "A visualização, impressão e download utilizam o arquivo original preenchido e armazenado de forma imutável."}</p>
        <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
          <div><dt className="font-semibold text-slate-500">Arquivo</dt><dd className="mt-1 break-all text-slate-900">{documento.document.filename || "Documento oficial"}</dd></div>
          <div><dt className="font-semibold text-slate-500">Modelo</dt><dd className="mt-1 text-slate-900">{documento.document.template_code || "—"} v{documento.document.template_version || 1}</dd></div>
          <div className="sm:col-span-2"><dt className="font-semibold text-slate-500">SHA-256</dt><dd className="mt-1 break-all font-mono text-xs text-slate-900">{documento.document.sha256 || "—"}</dd></div>
        </dl>
      </section>}
    </div>
  </main>
}
