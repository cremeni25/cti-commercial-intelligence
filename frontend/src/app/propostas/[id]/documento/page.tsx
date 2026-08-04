/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [previewDisponivel, setPreviewDisponivel] = useState(false)

  const previewUrl = useMemo(
    () => `${API_URL}/crm-documentos/propostas/${id}/previsualizar-documento-arquivo?ts=${Date.now()}`,
    [id],
  )

  useEffect(() => {
    if (!id) return
    let ativo = true

    void (async () => {
      setCarregando(true)
      setErro("")
      setPreviewDisponivel(false)
      try {
        const resposta = await fetch(previewUrl, {
          method: "GET",
          cache: "no-store",
          headers: { Accept: "application/pdf" },
        })

        if (!resposta.ok) {
          const payload = await resposta.json().catch(() => null)
          throw new Error(String(payload?.detail || "Não foi possível gerar a prévia PDF oficial."))
        }

        const tipo = String(resposta.headers.get("content-type") || "").toLowerCase()
        if (!tipo.includes("application/pdf")) {
          throw new Error("O backend não retornou um PDF válido.")
        }

        if (ativo) setPreviewDisponivel(true)
      } catch (falha) {
        if (ativo) {
          setErro(falha instanceof Error ? falha.message : "Falha ao gerar a proposta oficial em PDF.")
        }
      } finally {
        if (ativo) setCarregando(false)
      }
    })()

    return () => { ativo = false }
  }, [id, previewUrl])

  return <main className="min-h-screen bg-slate-100 px-4 py-6">
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
        {previewDisponivel && <a href={previewUrl} target="_blank" rel="noreferrer" className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">Abrir PDF em nova guia</a>}
      </div>

      {carregando && <div className="rounded-xl bg-white p-8 text-slate-600 shadow-sm">Gerando a prévia da proposta oficial Carrier...</div>}
      {erro && <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}

      {previewDisponivel && <section className="overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h1 className="text-xl font-bold text-slate-900">Proposta oficial Carrier</h1>
          <p className="mt-1 text-sm text-slate-600">Prévia preenchida com os dados atuais do dossiê. A emissão definitiva e o envio serão liberados somente após a conferência.</p>
        </div>
        <iframe
          title="Proposta oficial Carrier em PDF"
          src={previewUrl}
          className="h-[78vh] w-full bg-slate-200"
        />
      </section>}
    </div>
  </main>
}
