/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type PreviewWord = {
  filename: string
  sha256: string
  viewer_url: string
  expires_in: number
}

export default function DocumentoPropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [preview, setPreview] = useState<PreviewWord | null>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    if (!id) return
    let ativo = true

    void (async () => {
      setCarregando(true)
      setErro("")
      setPreview(null)
      try {
        const resposta = await fetchCrmSeguroProxy(
          `crm-seguro/propostas/${encodeURIComponent(id)}/previsualizar-documento`,
          { cache: "no-store", headers: { Accept: "application/json" } },
        )
        const payload = await resposta.json().catch(() => null)
        if (!resposta.ok) {
          throw new Error(String(payload?.detail || "Não foi possível preparar a visualização do Word oficial."))
        }
        if (!payload?.viewer_url) {
          throw new Error("O CTI não recebeu a URL temporária de visualização do Word oficial.")
        }
        if (ativo) setPreview(payload as PreviewWord)
      } catch (falha) {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao visualizar a proposta oficial.")
      } finally {
        if (ativo) setCarregando(false)
      }
    })()

    return () => { ativo = false }
  }, [id])

  return <main className="min-h-screen bg-slate-100 px-4 py-6">
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/propostas/${id}`} className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800">← Voltar aos dados da proposta</Link>
        {preview?.viewer_url && <a href={preview.viewer_url} target="_blank" rel="noreferrer" className="rounded-xl bg-[#17468f] px-5 py-2 font-semibold text-white">Ampliar visualização</a>}
      </div>

      {carregando && <div className="rounded-xl bg-white p-8 text-slate-600 shadow-sm">Preparando acesso temporário ao Word oficial preenchido...</div>}
      {erro && <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}

      {preview && <section className="overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h1 className="text-xl font-bold text-slate-900">Proposta oficial Carrier</h1>
          <p className="mt-1 text-sm text-slate-600">Word oficial preenchido, autorizado pela sessão CTI e entregue ao visualizador por acesso temporário assinado.</p>
        </div>
        <iframe
          title="Proposta oficial Carrier em Word"
          src={preview.viewer_url}
          className="h-[82vh] w-full bg-white"
          allow="fullscreen"
        />
        <div className="grid gap-3 border-t border-slate-200 px-5 py-4 text-xs text-slate-600 sm:grid-cols-2">
          <div><span className="font-semibold">Arquivo:</span> {preview.filename}</div>
          <div className="break-all"><span className="font-semibold">SHA-256:</span> {preview.sha256}</div>
        </div>
      </section>}
    </div>
  </main>
}