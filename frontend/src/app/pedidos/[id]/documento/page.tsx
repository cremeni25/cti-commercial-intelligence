/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"
import { useClosureI18n } from "@/core/i18n/closure"

type Registro = Record<string, unknown>
type Detalhes = { pedido: Registro; proposta: Registro; item: Registro; aceite: Registro }
function texto(valor: unknown, padrao = "—") { const saida = String(valor ?? "").trim(); return saida || padrao }

export default function DocumentoPedidoPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const { tc, formatCurrency, formatDate } = useClosureI18n()
  const [dados, setDados] = useState<Detalhes | null>(null)
  const [erro, setErro] = useState("")
  const moeda = (valor: unknown) => formatCurrency(Number(valor || 0))
  const dataHora = (valor: unknown) => !valor ? "—" : formatDate(String(valor), { dateStyle: "short", timeStyle: "short" })

  useEffect(() => {
    if (!id) return
    fetchCrmSeguroProxy(`crm-seguro/pedidos/${encodeURIComponent(id)}/carrier-pacote`, { cache: "no-store" })
      .then(async (resposta) => { const payload = await resposta.json().catch(() => null); if (!resposta.ok) throw new Error(payload?.detail || tc("order.loadFailed")); return payload })
      .then(setDados).catch((falha) => setErro(falha instanceof Error ? falha.message : tc("order.loadFailed")))
  }, [id, tc])

  const propostaId = String(dados?.proposta.id || dados?.pedido.proposta_id || "")
  return <main className="min-h-screen bg-slate-200 px-3 py-5 text-slate-950 print:bg-white print:p-0">
    <div className="mx-auto mb-4 flex max-w-[210mm] flex-wrap items-center justify-between gap-3 print:hidden"><Link href={`/pedidos/${id}`} className="rounded-lg border border-slate-400 bg-white px-4 py-2 font-semibold">← {tc("orderDoc.back")}</Link><div className="flex gap-3">{propostaId && <Link href={`/propostas/${propostaId}/documento`} className="rounded-lg border border-blue-700 bg-white px-4 py-2 font-semibold text-blue-800">{tc("orderDoc.viewProposal")}</Link>}<button onClick={() => window.print()} className="rounded-lg bg-blue-800 px-4 py-2 font-semibold text-white">{tc("orderDoc.print")}</button></div></div>
    {erro && <div className="mx-auto max-w-[210mm] rounded-xl bg-red-100 p-5 text-red-800">{erro}</div>}
    {!dados && !erro && <div className="mx-auto max-w-[210mm] rounded-xl bg-white p-8">{tc("orderDoc.loading")}</div>}
    {dados && <article className="mx-auto min-h-[297mm] max-w-[210mm] bg-white p-[16mm] shadow-xl print:min-h-0 print:max-w-none print:p-[12mm] print:shadow-none">
      <header className="border-b-4 border-blue-800 pb-5"><div className="flex items-start justify-between gap-6"><div><p className="text-sm font-bold uppercase tracking-[0.22em] text-blue-800">{tc("orderDoc.eyebrow")}</p><h1 className="mt-2 text-3xl font-bold">{texto(dados.pedido.numero, tc("orderDoc.title"))}</h1><p className="mt-2 text-sm text-slate-600">{tc("orderDoc.subtitle")}</p></div><div className="text-right text-sm"><p className="font-bold text-blue-800">CARRIER TRANSICOLD</p><p>Transport Refrigeration</p></div></div></header>
      <section className="mt-7 grid gap-5 sm:grid-cols-2"><Bloco titulo={tc("orderDoc.identification")}><Linha rotulo={tc("proposal.order")} valor={texto(dados.pedido.numero)} /><Linha rotulo={tc("order.orderDate")} valor={dataHora(dados.pedido.data_pedido || dados.pedido.created_at)} /><Linha rotulo={tc("common.status")} valor={texto(dados.pedido.status)} /><Linha rotulo={tc("common.value")} valor={moeda(dados.pedido.valor)} /></Bloco><Bloco titulo={tc("orderDoc.link")}><Linha rotulo={tc("order.proposal")} valor={texto(dados.proposta.numero)} /><Linha rotulo={tc("orderDoc.revision")} valor={texto(dados.proposta.versao, "1")} /><Linha rotulo={tc("proposal.hash")} valor={texto(dados.proposta.hash_documento)} compacto /><Linha rotulo={tc("orderDoc.proposalStatus")} valor={texto(dados.proposta.status_documento || dados.proposta.status)} /></Bloco></section>
      <section className="mt-7"><Bloco titulo={tc("orderDoc.object")}><Linha rotulo={tc("proposal.line")} valor={texto(dados.item.linha_produto || dados.proposta.produtos)} /><Linha rotulo={tc("proposal.equipment")} valor={texto(dados.item.equipamento || dados.proposta.equipamentos)} /><Linha rotulo={tc("proposal.configuration")} valor={texto(dados.item.configuracao)} /><Linha rotulo={tc("common.quantity")} valor={texto(dados.item.quantidade, "1")} /><Linha rotulo={tc("proposal.unitPrice")} valor={moeda(dados.item.preco_unitario || dados.proposta.valor)} /><Linha rotulo={tc("proposal.discount")} valor={`${texto(dados.item.desconto_percentual, "0")}%`} /><Linha rotulo={tc("orderDoc.totalValue")} valor={moeda(dados.pedido.valor || dados.proposta.valor)} /></Bloco></section>
      <section className="mt-7 grid gap-5 sm:grid-cols-2"><Bloco titulo={tc("orderDoc.terms")}><Linha rotulo={tc("proposal.payment")} valor={texto(dados.item.condicao_pagamento || dados.proposta.condicoes)} /><Linha rotulo={tc("proposal.deliveryTerm")} valor={texto(dados.item.prazo_entrega)} /><Linha rotulo={tc("orderDoc.freight")} valor={texto(dados.item.frete)} /><Linha rotulo={tc("proposal.deliveryPlace")} valor={texto(dados.item.local_entrega)} /><Linha rotulo={tc("proposal.warranty")} valor={texto(dados.item.garantia)} /></Bloco><Bloco titulo={tc("orderDoc.linkedAcceptance")}><Linha rotulo={tc("order.signer")} valor={texto(dados.aceite.nome_signatario)} /><Linha rotulo={tc("order.document")} valor={texto(dados.aceite.documento_signatario)} /><Linha rotulo={tc("order.method")} valor={texto(dados.aceite.metodo)} /><Linha rotulo={tc("order.dateTime")} valor={dataHora(dados.aceite.aceito_em)} /><Linha rotulo={tc("common.status")} valor={texto(dados.aceite.status)} /></Bloco></section>
      <section className="mt-8 rounded-lg border-2 border-blue-800 p-5"><h2 className="font-bold uppercase text-blue-800">{tc("orderDoc.confirmation")}</h2><p className="mt-3 text-sm leading-6">{tc("orderDoc.confirmationText")}</p></section>
      <section className="mt-14 grid grid-cols-2 gap-12 text-center text-sm"><div className="border-t border-slate-900 pt-2">{tc("orderDoc.salesOwner")}</div><div className="border-t border-slate-900 pt-2">{tc("orderDoc.accountSignature")}</div></section><footer className="mt-12 border-t border-slate-300 pt-4 text-xs text-slate-500"><p>{tc("orderDoc.footer")}</p><p className="mt-1 break-all">{tc("orderDoc.id")}: {id}</p></footer>
    </article>}
  </main>
}
function Bloco({ titulo, children }: { titulo: string; children: React.ReactNode }) { return <div className="min-w-0 rounded-lg border border-slate-400"><h2 className="bg-blue-800 px-4 py-2 font-bold uppercase text-white">{titulo}</h2><dl className="min-w-0 p-4">{children}</dl></div> }
function Linha({ rotulo, valor, compacto = false }: { rotulo: string; valor: string; compacto?: boolean }) { return <div className="grid min-w-0 grid-cols-[105px_minmax(0,1fr)] gap-3 border-b border-slate-200 py-2 last:border-0 sm:grid-cols-[145px_minmax(0,1fr)]"><dt className="font-semibold text-slate-700">{rotulo}</dt><dd className={`min-w-0 break-all ${compacto ? "font-mono text-[10px] leading-4" : ""}`}>{valor}</dd></div> }
