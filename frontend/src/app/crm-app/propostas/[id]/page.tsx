"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowLeft, CheckCircle2, FileText, Loader2, PackageCheck } from "lucide-react"
import { useParams } from "next/navigation"

type Registro = Record<string, unknown>
type Pacote = { proposta: Registro; item: Registro | null; oportunidade: Registro | null; cliente: Registro | null; aceites: Registro[]; pedidos: Registro[] }

function texto(valor: unknown, padrao = "—") { const v = String(valor ?? "").trim(); return v || padrao }
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }

export default function PropostaCrmAppPage() {
  const params = useParams<{ id: string }>()
  const id = String(params.id || "")
  const [dados, setDados] = useState<Pacote | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(id)}`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível carregar a proposta (${resposta.status}).`))
      setDados(payload)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar a proposta.") }
    finally { setCarregando(false) }
  }

  useEffect(() => { if (id) void carregar() }, [id])

  async function executar(sufixo: string, body: Registro = {}) {
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(id)}${sufixo}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Operação não concluída (${resposta.status}).`))
      setMensagem("Operação registrada com sucesso.")
      await carregar()
      return payload
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha na operação.") }
    finally { setProcessando(false) }
  }

  async function aceite(metodo: "PRESENCIAL_TELA" | "REMOTO_LINK") {
    const nome = window.prompt("Nome completo do cliente/signatário:")?.trim()
    if (!nome) return
    const email = window.prompt("E-mail do cliente, quando disponível:")?.trim() || null
    const payload = await executar("/aceites", { metodo, nome_signatario: nome, email_signatario: email })
    const token = payload && typeof payload === "object" ? String((payload as Registro).link_token || "") : ""
    if (token) {
      const link = `${window.location.origin}/aceite/${token}`
      await navigator.clipboard?.writeText(link)
      setMensagem(`Link de aceite copiado: ${link}`)
    }
  }

  const status = texto(dados?.proposta.status_documento, "RASCUNHO").toUpperCase()
  const podeEmitir = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"].includes(status)
  const podeAceite = ["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podePedido = status === "ACEITA"
  const pedido = dados?.pedidos?.[0]

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-4xl">
      <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Proposta, aceite e pedido</h1></div></header>
      {carregando && <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {mensagem && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
      {dados && <div className="space-y-4">
        <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><p className="text-sm text-slate-400">Proposta comercial</p><h2 className="mt-1 text-xl font-bold">{texto(dados.proposta.numero, "Proposta em elaboração")}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full border border-cyan-800 px-3 py-1 text-cyan-200">{status.replaceAll("_", " ")}</span><span className="rounded-full border border-[#24466f] px-3 py-1 text-slate-300">{moeda(dados.proposta.valor)}</span></div></section>
        <section className="grid gap-3 sm:grid-cols-2"><Info label="Cliente" valor={texto(dados.cliente?.razao_social || dados.cliente?.nome || dados.oportunidade?.cliente_nome)}/><Info label="Equipamento" valor={texto(dados.item?.equipamento)}/><Info label="Quantidade" valor={texto(dados.item?.quantidade, "1")}/><Info label="Condição de pagamento" valor={texto(dados.item?.condicao_pagamento)}/></section>
        <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><h3 className="font-bold">Ações comerciais</h3><div className="mt-4 grid gap-3">
          {podeEmitir && <button disabled={processando} onClick={() => void executar("/emitir")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40"><FileText className="mr-2 inline" size={18}/>Emitir proposta</button>}
          {podeAceite && <><button disabled={processando} onClick={() => void aceite("PRESENCIAL_TELA")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40"><CheckCircle2 className="mr-2 inline" size={18}/>Aceite presencial</button><button disabled={processando} onClick={() => void aceite("REMOTO_LINK")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">Gerar link de aceite</button></>}
          {podePedido && <button disabled={processando} onClick={() => void executar("/converter-pedido")} className="rounded-xl border border-emerald-700 px-4 py-3 text-emerald-300 disabled:opacity-40"><PackageCheck className="mr-2 inline" size={18}/>Converter em pedido</button>}
          {pedido && <Link href={`/crm-app/pedidos/${String(pedido.id)}`} className="rounded-xl border border-emerald-700 px-4 py-3 text-center font-semibold text-emerald-300">Abrir pedido</Link>}
          {!podeEmitir && !podeAceite && !podePedido && !pedido && <p className="text-sm text-slate-400">Nenhuma ação disponível para o status atual.</p>}
        </div></section>
      </div>}
    </div>
  </main>
}

function Info({ label, valor }: { label: string; valor: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">{label}</p><strong className="mt-1 block">{valor}</strong></div> }
