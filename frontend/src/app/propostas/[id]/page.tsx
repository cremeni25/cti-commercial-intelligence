/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"
import { useClosureI18n } from "@/core/i18n/closure"

interface PacoteProposta {
  proposta: Record<string, unknown>
  item: Record<string, unknown> | null
  oportunidade: Record<string, unknown> | null
  cliente: Record<string, unknown> | null
  aceites: Record<string, unknown>[]
  pedidos: Record<string, unknown>[]
}

function texto(valor: unknown, padrao = "—") { const resultado = String(valor ?? "").trim(); return resultado || padrao }
function emails(valor: string) { return valor.split(/[;,\n]+/).map((item) => item.trim()).filter(Boolean) }

export default function PropostaPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const { locale, tc, formatCurrency, formatDate } = useClosureI18n()
  const [dados, setDados] = useState<PacoteProposta | null>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [mensagem, setMensagem] = useState("")
  const [envioAberto, setEnvioAberto] = useState(false)
  const [para, setPara] = useState("")
  const [cc, setCc] = useState("")
  const [cco, setCco] = useState("")
  const [mensagemEmail, setMensagemEmail] = useState("Segue a proposta comercial para sua análise.")

  const moeda = (valor: unknown) => formatCurrency(Number(valor || 0))
  const dataHora = (valor: unknown) => !valor ? "—" : formatDate(String(valor), { dateStyle: "short", timeStyle: "short" })
  const statusTexto = (valor: string) => {
    const mapa: Record<string, Record<string, string>> = {
      "pt-BR": { RASCUNHO:"Rascunho", EM_REVISAO:"Em revisão", APROVADA_INTERNA:"Aprovada internamente", EMITIDA:"Emitida", ENVIADA:"Enviada", VISUALIZADA:"Visualizada", EM_NEGOCIACAO:"Em negociação", ACEITA:"Aceita", CONVERTIDA_PEDIDO:"Convertida em pedido", REJEITADA:"Rejeitada", EXPIRADA:"Expirada", CANCELADA:"Cancelada", SUBSTITUIDA:"Substituída" },
      en: { RASCUNHO:"Draft", EM_REVISAO:"Under review", APROVADA_INTERNA:"Internally approved", EMITIDA:"Issued", ENVIADA:"Sent", VISUALIZADA:"Viewed", EM_NEGOCIACAO:"In negotiation", ACEITA:"Accepted", CONVERTIDA_PEDIDO:"Converted to order", REJEITADA:"Rejected", EXPIRADA:"Expired", CANCELADA:"Cancelled", SUBSTITUIDA:"Superseded" },
      es: { RASCUNHO:"Borrador", EM_REVISAO:"En revisión", APROVADA_INTERNA:"Aprobada internamente", EMITIDA:"Emitida", ENVIADA:"Enviada", VISUALIZADA:"Visualizada", EM_NEGOCIACAO:"En negociación", ACEITA:"Aceptada", CONVERTIDA_PEDIDO:"Convertida en pedido", REJEITADA:"Rechazada", EXPIRADA:"Vencida", CANCELADA:"Cancelada", SUBSTITUIDA:"Sustituida" },
    }
    return mapa[locale]?.[valor] || valor.replaceAll("_", " ")
  }

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/pacote`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || tc("proposal.loadFailed"))
      setDados(payload)
      const emailCliente = texto(payload?.cliente?.email, "")
      if (emailCliente) setPara((atual) => atual || emailCliente)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : tc("proposal.loadFailed")) }
    finally { setCarregando(false) }
  }

  useEffect(() => { if (id) void carregar() }, [id])

  const status = texto(dados?.proposta.status_documento, "RASCUNHO").toUpperCase()
  const podeEmitir = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"].includes(status)
  const podeEnviar = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA", "EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const jaEnviada = ["ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podeAceite = ["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podePedido = status === "ACEITA"
  const encerrada = ["ACEITA", "CONVERTIDA_PEDIDO", "REJEITADA", "EXPIRADA", "CANCELADA", "SUBSTITUIDA"].includes(status)
  const snapshot = useMemo(() => (dados?.proposta.snapshot_dados || {}) as Record<string, unknown>, [dados])
  const aceiteValido = dados?.aceites.find((item) => String(item.status || "").toUpperCase() === "ACEITO")
  const pedido = dados?.pedidos[0]

  async function executar(sufixo: string, body?: Record<string, unknown>) {
    setProcessando(true); setMensagem(""); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}${sufixo}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || tc("common.error"))
      setMensagem(tc("common.success")); await carregar(); return payload
    } catch (falha) { setErro(falha instanceof Error ? falha.message : tc("common.error")); return null }
    finally { setProcessando(false) }
  }

  async function enviarProposta() {
    const destinatarios = emails(para)
    if (!destinatarios.length) { setErro("Informe ao menos um endereço no campo Para."); return }
    setProcessando(true); setMensagem(""); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/enviar-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ destinatarios, cc: emails(cc), cco: emails(cco), mensagem: mensagemEmail.trim() || null }),
      })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível enviar a proposta.")
      setMensagem(`${jaEnviada ? "Proposta reenviada" : "Proposta enviada"} com sucesso. Protocolo: ${texto(payload?.message_id, "OK")}.`)
      setEnvioAberto(false)
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível enviar a proposta.") }
    finally { setProcessando(false) }
  }

  async function solicitarAceite(metodo: "PRESENCIAL_TELA" | "REMOTO_LINK") {
    const nome = window.prompt(tc("proposal.signerName"))?.trim(); if (!nome) return
    const email = window.prompt(tc("proposal.signerEmail"))?.trim() || null
    const payload = await executar("/aceites", { metodo, nome_signatario: nome, email_signatario: email })
    const token = payload?.link_token
    if (token) { const link = `${window.location.origin}/aceite/${token}`; await navigator.clipboard?.writeText(link); setMensagem(tc("proposal.linkCopied", { link })) }
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
      <Link href={dados?.proposta.oportunidade_id ? `/oportunidades/${dados.proposta.oportunidade_id}` : "/propostas"} className="text-sm font-semibold text-cyan-300">← {tc("common.back")}</Link>
      <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">{tc("proposal.title")}</p><h1 className="mt-2 text-3xl font-bold">{texto(dados?.proposta.numero, tc("proposal.draft"))}</h1><p className="mt-2 text-slate-400">{tc("proposal.version")} {texto(dados?.proposta.versao, "1")} • {texto(dados?.item?.equipamento)}</p></div><span className="w-fit rounded-full border border-cyan-800 bg-cyan-950/30 px-4 py-2 text-sm text-cyan-200">{statusTexto(status)}</span></div>
    </header>
    {carregando && <Aviso>{tc("proposal.loading")}</Aviso>}{erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-5 text-red-200">{erro}</div>}{mensagem && <div className="rounded-2xl border border-emerald-900 bg-emerald-950/30 p-5 text-emerald-200">{mensagem}</div>}
    {dados && <>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi titulo={tc("common.value")} valor={moeda(dados.proposta.valor)} /><Kpi titulo={tc("common.quantity")} valor={texto(dados.item?.quantidade, "1")} /><Kpi titulo={tc("proposal.validAcceptance")} valor={aceiteValido ? "1" : "0"} /><Kpi titulo={tc("proposal.order")} valor={pedido ? "1" : "0"} /></section>
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">{tc("proposal.commercialData")}</h2><dl className="mt-5 space-y-3 text-sm"><Linha label={locale === "en" ? "Account" : "Cliente"} valor={texto(dados.cliente?.razao_social || dados.cliente?.nome || dados.oportunidade?.cliente_nome)} /><Linha label={tc("proposal.line")} valor={texto(dados.item?.linha_produto)} /><Linha label={tc("proposal.equipment")} valor={texto(dados.item?.equipamento)} /><Linha label={tc("proposal.configuration")} valor={texto(dados.item?.configuracao)} /><Linha label={tc("proposal.unitPrice")} valor={moeda(dados.item?.preco_unitario)} /><Linha label={tc("proposal.discount")} valor={`${texto(dados.item?.desconto_percentual, "0")}%`} /><Linha label={tc("proposal.payment")} valor={texto(dados.item?.condicao_pagamento)} /><Linha label={tc("proposal.deliveryTerm")} valor={texto(dados.item?.prazo_entrega)} /><Linha label={tc("proposal.warranty")} valor={texto(dados.item?.garantia)} /><Linha label={tc("proposal.deliveryPlace")} valor={texto(dados.item?.local_entrega)} /></dl></article>
        <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">{tc("proposal.documentsActions")}</h2><div className="mt-5 grid gap-3">
          <Link href={`/propostas/${id}/documento`} className="rounded-xl bg-cyan-500 px-4 py-3 text-center font-semibold text-slate-950">{tc("proposal.viewOfficial")}</Link>
          {pedido && <Link href={`/pedidos/${String(pedido.id)}`} className="rounded-xl border border-emerald-700 px-4 py-3 text-center font-semibold text-emerald-300">{tc("proposal.openOrder")}</Link>}
          {!encerrada && podeEmitir && <button disabled={processando} onClick={() => void executar("/emitir")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">{tc("proposal.issue")}</button>}
          {podeEnviar && !envioAberto && <button disabled={processando} onClick={() => setEnvioAberto(true)} className="rounded-xl border border-cyan-700 px-4 py-3 font-semibold text-cyan-200 disabled:opacity-40">{jaEnviada ? "Reenviar proposta comercial" : "Enviar proposta por e-mail"}</button>}
          {!encerrada && podeAceite && <><button disabled={processando} onClick={() => void solicitarAceite("PRESENCIAL_TELA")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">{tc("proposal.inPersonAcceptance")}</button><button disabled={processando} onClick={() => void solicitarAceite("REMOTO_LINK")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">{tc("proposal.acceptanceLink")}</button></>}
          {podePedido && <button disabled={processando} onClick={() => void executar("/converter-pedido", {})} className="rounded-xl border border-emerald-700 px-4 py-3 text-emerald-300 disabled:opacity-40">{tc("proposal.generateOrder")}</button>}
        </div></article>
      </section>
      {envioAberto && <section className="rounded-3xl border border-cyan-800 bg-cyan-950/15 p-6"><h2 className="text-xl font-bold">{jaEnviada ? "Reenviar proposta comercial" : "Enviar proposta comercial"}</h2><p className="mt-1 text-sm text-slate-400">Revise ou acrescente destinatários antes do envio. Separe vários e-mails por vírgula, ponto e vírgula ou nova linha.</p><div className="mt-5 grid gap-4"><CampoEmail titulo="Para" valor={para} alterar={setPara} obrigatorio/><CampoEmail titulo="CC — cópia" valor={cc} alterar={setCc}/><CampoEmail titulo="CCO — cópia oculta" valor={cco} alterar={setCco}/><label className="block"><span className="mb-2 block text-sm">Mensagem</span><textarea value={mensagemEmail} onChange={(evento) => setMensagemEmail(evento.target.value)} rows={4} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><button type="button" onClick={() => setEnvioAberto(false)} className="rounded-xl border border-[#24466f] px-4 py-3">Cancelar</button><button type="button" disabled={processando || !emails(para).length} onClick={() => void enviarProposta()} className="rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-40">{processando ? "Enviando..." : jaEnviada ? "Reenviar PDF oficial" : "Enviar PDF oficial"}</button></div></section>}
      <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">{tc("proposal.audit")}</h2><div className="mt-4 grid gap-3 text-sm sm:grid-cols-2"><Linha label={tc("proposal.hash")} valor={texto(dados.proposta.hash_documento)} /><Linha label={tc("proposal.model")} valor={texto(dados.proposta.modelo_proposta_id, tc("common.notDefined"))}/><Linha label={tc("proposal.issuedAt")} valor={dataHora(dados.proposta.emitida_em)} /><Linha label={tc("proposal.acceptedAt")} valor={dataHora(dados.proposta.aceita_em)} /></div><details className="mt-5 rounded-2xl border border-[#13203f] p-4"><summary className="cursor-pointer text-sm font-semibold text-cyan-300">{tc("proposal.snapshot")}</summary><pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-xs text-slate-400">{JSON.stringify(snapshot, null, 2)}</pre></details></section>
    </>}
  </div></section></main>
}
function CampoEmail({titulo,valor,alterar,obrigatorio=false}:{titulo:string;valor:string;alterar:(valor:string)=>void;obrigatorio?:boolean}) { return <label className="block"><span className="mb-2 block text-sm">{titulo}{obrigatorio ? " *" : ""}</span><textarea value={valor} onChange={(evento) => alterar(evento.target.value)} rows={2} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label> }
function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function Linha({ label, valor }: { label: string; valor: string }) { return <div className="flex items-start justify-between gap-4 border-b border-[#13203f] pb-3"><dt className="text-slate-500">{label}</dt><dd className="max-w-[65%] text-right text-slate-200">{valor}</dd></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
