/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

type DocumentoOficial = {
  document: {
    filename?: string
    sha256?: string
    template_code?: string
    template_version?: number
    finalized_at?: string
    mime_type?: string
  }
  url: string
  expires_in: number
}

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [documento, setDocumento] = useState<DocumentoOficial | null>(null)
  const [previewPendente, setPreviewPendente] = useState(false)
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
          if (detalhe.includes("não homologado visualmente")) {
            setPreviewPendente(true)
            return
          }
          throw new Error(detalhe || "Não foi possível gerar o PDF oficial.")
        }

        const resposta = await fetch(`${API_URL}/crm-documentos/propostas/${id}/documento-oficial`, { cache: "no-store" })
        const payload = await resposta.json().catch(() => null)
        if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível acessar o PDF oficial.")
        setDocumento(payload)
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Falha ao carregar o PDF oficial.")
      } finally {
        setCarregando(false)
      }
    })()
  }, [id])

  const previewUrl = `${API_URL}/crm-documentos/propostas/${id}/previsualizar-documento-arquivo`
  const pdfUrl = documento?.url || (previewPendente ? previewUrl : "")

  return <main className="min-h-screen bg-slate-100 px-4 py-6">
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
        {documento?.url && <a href={documento.url} target="_blank" rel="noreferrer" className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">Abrir PDF em nova guia</a>}
      </div>

      {carregando && <div className="rounded-xl bg-white p-8 text-slate-600 shadow-sm">Gerando a proposta oficial em PDF...</div>}
      {erro && <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}

      {pdfUrl && <section className="overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h1 className="text-xl font-bold text-slate-900">Proposta oficial Carrier</h1>
          <p className="mt-1 text-sm text-slate-600">Documento preenchido com os dados do dossiê comercial e apresentado em PDF dentro do CTI.</p>
        </div>
        <iframe
          title="Proposta oficial Carrier em PDF"
          src={pdfUrl}
          className="h-[78vh] w-full bg-slate-200"
        />
      </section>}

      {documento && <section className="mt-4 rounded-2xl bg-white p-5 shadow-sm">
        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div><dt className="font-semibold text-slate-500">Arquivo PDF</dt><dd className="mt-1 break-all text-slate-900">{documento.document.filename || "Proposta oficial.pdf"}</dd></div>
          <div><dt className="font-semibold text-slate-500">Modelo</dt><dd className="mt-1 text-slate-900">{documento.document.template_code || "—"} v{documento.document.template_version || 1}</dd></div>
          <div className="sm:col-span-2"><dt className="font-semibold text-slate-500">SHA-256</dt><dd className="mt-1 break-all font-mono text-xs text-slate-900">{documento.document.sha256 || "—"}</dd></div>
        </dl>
      </section>}
    </div>
  </main>
}
