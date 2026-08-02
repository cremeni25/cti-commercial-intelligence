/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

interface PacoteProposta {
  proposta: Record<string, unknown>
  item: Record<string, unknown> | null
  oportunidade: Record<string, unknown> | null
  cliente: Record<string, unknown> | null
  aceites: Record<string, unknown>[]
  pedidos: Record<string, unknown>[]
}

function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function texto(valor: unknown, padrao = "—") { const resultado = String(valor ?? "").trim(); return resultado || padrao }
function dataHora(valor: unknown) { if (!valor) return "—"; const data = new Date(String(valor)); return Number.isNaN(data.getTime()) ? String(valor) : data.toLocaleString("pt-BR") }

export default function PropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [dados, setDados] = useState<PacoteProposta | null>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [mensagem, setMensagem] = useState("")

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(id)}`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || `Não foi possível carregar a proposta (${resposta.status}).`)
      setDados(payload)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar a proposta.") }
    finally { setCarregando(false) }
  }

  useEffect(() => { if (id) void carregar() }, [id])

  const status = texto(dados?.proposta.status_documento, "RASCUNHO")
  const podeEmitir = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"].includes(status)
  const podeAceite = ["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podePedido = status === "ACEITA"
  const encerrada = ["ACEITA", "CONVERTIDA_PEDIDO", "REJEITADA", "EXPIRADA", "CANCELADA", "SUBSTITUIDA"].includes(status)
  const snapshot = useMemo(() => (dados?.proposta.snapshot_dados || {}) as Record<string, unknown>, [dados])
  const aceiteValido = dados?.aceites.find((item) => String(item.status || "").toUpperCase() === "ACEITO")
  const pedido = dados?.pedidos[0]

  async function executar(endpoint: string, body?: Record<string, unknown>) {
    setProcessando(true); setMensagem(""); setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || `A operação não pôde ser concluída (${resposta.status}).`)
      setMensagem("Operação registrada com sucesso."); await carregar(); return payload
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha na operação."); return null }
    finally { setProcessando(false) }
  }

  async function solicitarAceite(metodo: "PRESENCIAL_TELA" | "REMOTO_LINK") {
    const nome = window.prompt("Nome completo do cliente/signatário:")?.trim(); if (!nome) return
    const email = window.prompt("E-mail do cliente, quando disponível:")?.trim() || null
    const payload = await executar(`/crm-documentos/propostas/${id}/aceites`, { metodo, nome_signatario: nome, email_signatario: email })
    const token = payload?.link_token
    if (token) { const link = `${window.location.origin}/aceite/${token}`; await navigator.clipboard?.writeText(link); setMensagem(`Link de aceite copiado: ${link}`) }
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
      <Link href={dados?.proposta.oportunidade_id ? `/oportunidades/${dados.proposta.oportunidade_id}` : "/propostas"} className="text-sm font-semibold text-cyan-300">← Voltar</Link>
      <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Proposta comercial</p><h1 className="mt-2 text-3xl font-bold">{texto(dados?.proposta.numero, "Proposta em elaboração")}</h1><p className="mt-2 text-slate-400">Versão {texto(dados?.proposta.versao, "1")} • {texto(dados?.item?.equipamento)}</p></div><span className="w-fit rounded-full border border-cyan-800 bg-cyan-950/30 px-4 py-2 text-sm text-cyan-200">{status.replaceAll("_", " ")}</span></div>
    </header>
    {carregando && <Aviso>Carregando proposta...</Aviso>}{erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-5 text-red-200">{erro}</div>}{mensagem && <div className="rounded-2xl border border-emerald-900 bg-emerald-950/30 p-5 text-emerald-200">{mensagem}</div>}
    {dados && <>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi titulo="Valor" valor={moeda(dados.proposta.valor)} /><Kpi titulo="Quantidade" valor={texto(dados.item?.quantidade, "1")} /><Kpi titulo="Aceite válido" valor={aceiteValido ? "1" : "0"} /><Kpi titulo="Pedido" valor={pedido ? "1" : "0"} /></section>
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Dados comerciais</h2><dl className="mt-5 space-y-3 text-sm"><Linha label="Cliente" valor={texto(dados.cliente?.razao_social || dados.cliente?.nome || dados.oportunidade?.cliente_nome)} /><Linha label="Linha" valor={texto(dados.item?.linha_produto)} /><Linha label="Equipamento" valor={texto(dados.item?.equipamento)} /><Linha label="Configuração" valor={texto(dados.item?.configuracao)} /><Linha label="Preço unitário" valor={moeda(dados.item?.preco_unitario)} /><Linha label="Desconto" valor={`${texto(dados.item?.desconto_percentual, "0")}%`} /><Linha label="Pagamento" valor={texto(dados.item?.condicao_pagamento)} /><Linha label="Prazo" valor={texto(dados.item?.prazo_entrega)} /><Linha label="Garantia" valor={texto(dados.item?.garantia)} /><Linha label="Local de entrega" valor={texto(dados.item?.local_entrega)} /></dl></article>
        <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Documentos e ações</h2><div className="mt-5 grid gap-3">
          <Link href={`/propostas/${id}/documento`} className="rounded-xl bg-cyan-500 px-4 py-3 text-center font-semibold text-slate-950">Visualizar proposta oficial CARRIER</Link>
          {pedido && <Link href={`/pedidos/${String(pedido.id)}`} className="rounded-xl border border-emerald-700 px-4 py-3 text-center font-semibold text-emerald-300">Abrir pedido e dossiê</Link>}
          {!encerrada && podeEmitir && <button disabled={processando} onClick={() => void executar(`/crm-documentos/propostas/${id}/emitir`)} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">Emitir proposta</button>}
          {!encerrada && podeAceite && <><button disabled={processando} onClick={() => void solicitarAceite("PRESENCIAL_TELA")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">Aceite presencial</button><button disabled={processando} onClick={() => void solicitarAceite("REMOTO_LINK")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">Gerar link de aceite</button></>}
          {podePedido && <button disabled={processando} onClick={() => void executar(`/crm-documentos/propostas/${id}/converter-pedido`, {})} className="rounded-xl border border-emerald-700 px-4 py-3 text-emerald-300 disabled:opacity-40">Gerar pedido</button>}
        </div></article>
      </section>
      <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Auditoria do documento</h2><div className="mt-4 grid gap-3 text-sm sm:grid-cols-2"><Linha label="Hash" valor={texto(dados.proposta.hash_documento)} /><Linha label="Modelo" valor={texto(dados.proposta.modelo_proposta_id, "Modelo provisório")}/><Linha label="Emitida em" valor={dataHora(dados.proposta.emitida_em)} /><Linha label="Aceita em" valor={dataHora(dados.proposta.aceita_em)} /></div><details className="mt-5 rounded-2xl border border-[#13203f] p-4"><summary className="cursor-pointer text-sm font-semibold text-cyan-300">Snapshot imutável</summary><pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-xs text-slate-400">{JSON.stringify(snapshot, null, 2)}</pre></details></section>
    </>}
  </div></section></main>
}
function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function Linha({ label, valor }: { label: string; valor: string }) { return <div className="flex items-start justify-between gap-4 border-b border-[#13203f] pb-3"><dt className="text-slate-500">{label}</dt><dd className="max-w-[65%] text-right text-slate-200">{valor}</dd></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
