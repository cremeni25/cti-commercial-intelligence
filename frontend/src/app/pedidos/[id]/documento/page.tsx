/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

type Registro = Record<string, unknown>
type Detalhes = { pedido: Registro; proposta: Registro; item: Registro; aceite: Registro }

function texto(valor: unknown, padrao = "—") { const saida = String(valor ?? "").trim(); return saida || padrao }
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function dataHora(valor: unknown) { if (!valor) return "—"; const data = new Date(String(valor)); return Number.isNaN(data.getTime()) ? String(valor) : data.toLocaleString("pt-BR") }

export default function DocumentoPedidoPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const [dados, setDados] = useState<Detalhes | null>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!id) return
    fetch(`${API_URL}/carrier-operacional/pedidos/${id}`, { cache: "no-store" })
      .then(async (resposta) => { const payload = await resposta.json().catch(() => null); if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível carregar o pedido."); return payload })
      .then(setDados)
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Falha ao carregar o pedido."))
  }, [id])

  const propostaId = String(dados?.proposta.id || dados?.pedido.proposta_id || "")

  return <main className="min-h-screen bg-slate-200 px-3 py-5 text-slate-950 print:bg-white print:p-0">
    <div className="mx-auto mb-4 flex max-w-[210mm] flex-wrap items-center justify-between gap-3 print:hidden">
      <Link href={`/pedidos/${id}`} className="rounded-lg border border-slate-400 bg-white px-4 py-2 font-semibold">← Voltar ao dossiê</Link>
      <div className="flex gap-3">{propostaId && <Link href={`/propostas/${propostaId}/documento`} className="rounded-lg border border-blue-700 bg-white px-4 py-2 font-semibold text-blue-800">Ver proposta oficial CARRIER</Link>}<button onClick={() => window.print()} className="rounded-lg bg-blue-800 px-4 py-2 font-semibold text-white">Imprimir / salvar PDF</button></div>
    </div>

    {erro && <div className="mx-auto max-w-[210mm] rounded-xl bg-red-100 p-5 text-red-800">{erro}</div>}
    {!dados && !erro && <div className="mx-auto max-w-[210mm] rounded-xl bg-white p-8">Carregando pedido...</div>}

    {dados && <article className="mx-auto min-h-[297mm] max-w-[210mm] bg-white p-[16mm] shadow-xl print:min-h-0 print:max-w-none print:p-[12mm] print:shadow-none">
      <header className="border-b-4 border-blue-800 pb-5">
        <div className="flex items-start justify-between gap-6"><div><p className="text-sm font-bold uppercase tracking-[0.22em] text-blue-800">CTI • Documento de pedido</p><h1 className="mt-2 text-3xl font-bold">{texto(dados.pedido.numero, "Pedido comercial")}</h1><p className="mt-2 text-sm text-slate-600">Documento operacional vinculado à proposta oficial CARRIER.</p></div><div className="text-right text-sm"><p className="font-bold text-blue-800">CARRIER TRANSICOLD</p><p>Refrigeração para transporte</p></div></div>
      </header>

      <section className="mt-7 grid gap-5 sm:grid-cols-2">
        <Bloco titulo="Identificação"><Linha rotulo="Pedido" valor={texto(dados.pedido.numero)} /><Linha rotulo="Data" valor={dataHora(dados.pedido.data_pedido || dados.pedido.created_at)} /><Linha rotulo="Status" valor={texto(dados.pedido.status)} /><Linha rotulo="Valor" valor={moeda(dados.pedido.valor)} /></Bloco>
        <Bloco titulo="Vínculo documental"><Linha rotulo="Proposta" valor={texto(dados.proposta.numero)} /><Linha rotulo="Revisão" valor={texto(dados.proposta.versao, "1")} /><Linha rotulo="Hash" valor={texto(dados.proposta.hash_documento)} /><Linha rotulo="Status da proposta" valor={texto(dados.proposta.status_documento || dados.proposta.status)} /></Bloco>
      </section>

      <section className="mt-7"><Bloco titulo="Objeto do pedido"><Linha rotulo="Linha" valor={texto(dados.item.linha_produto || dados.proposta.produtos)} /><Linha rotulo="Equipamento" valor={texto(dados.item.equipamento || dados.proposta.equipamentos)} /><Linha rotulo="Configuração" valor={texto(dados.item.configuracao)} /><Linha rotulo="Quantidade" valor={texto(dados.item.quantidade, "1")} /><Linha rotulo="Preço unitário" valor={moeda(dados.item.preco_unitario || dados.proposta.valor)} /><Linha rotulo="Desconto" valor={`${texto(dados.item.desconto_percentual, "0")}%`} /><Linha rotulo="Valor total" valor={moeda(dados.pedido.valor || dados.proposta.valor)} /></Bloco></section>

      <section className="mt-7 grid gap-5 sm:grid-cols-2"><Bloco titulo="Condições comerciais"><Linha rotulo="Pagamento" valor={texto(dados.item.condicao_pagamento || dados.proposta.condicoes)} /><Linha rotulo="Prazo de entrega" valor={texto(dados.item.prazo_entrega)} /><Linha rotulo="Frete" valor={texto(dados.item.frete)} /><Linha rotulo="Local de entrega" valor={texto(dados.item.local_entrega)} /><Linha rotulo="Garantia" valor={texto(dados.item.garantia)} /></Bloco><Bloco titulo="Aceite vinculado"><Linha rotulo="Signatário" valor={texto(dados.aceite.nome_signatario)} /><Linha rotulo="Documento" valor={texto(dados.aceite.documento_signatario)} /><Linha rotulo="Método" valor={texto(dados.aceite.metodo)} /><Linha rotulo="Data e hora" valor={dataHora(dados.aceite.aceito_em)} /><Linha rotulo="Status" valor={texto(dados.aceite.status)} /></Bloco></section>

      <section className="mt-8 rounded-lg border-2 border-blue-800 p-5"><h2 className="font-bold uppercase text-blue-800">Confirmação documental</h2><p className="mt-3 text-sm leading-6">Este pedido foi gerado pelo CTI a partir da proposta comercial aceita. A proposta oficial CARRIER, sua respectiva revisão, o aceite registrado e as condições comerciais integram o mesmo dossiê. Divergências ou condições especiais devem ser formalizadas antes do encaminhamento definitivo.</p></section>

      <section className="mt-14 grid grid-cols-2 gap-12 text-center text-sm"><div className="border-t border-slate-900 pt-2">Responsável comercial</div><div className="border-t border-slate-900 pt-2">Cliente / representante autorizado</div></section>
      <footer className="mt-12 border-t border-slate-300 pt-4 text-xs text-slate-500"><p>Documento gerado pelo CTI — Centro de Tecnologia e Inteligência Comercial.</p><p className="mt-1 break-all">Pedido ID: {id}</p></footer>
    </article>}
  </main>
}

function Bloco({ titulo, children }: { titulo: string; children: React.ReactNode }) { return <div className="rounded-lg border border-slate-400"><h2 className="bg-blue-800 px-4 py-2 font-bold uppercase text-white">{titulo}</h2><dl className="p-4">{children}</dl></div> }
function Linha({ rotulo, valor }: { rotulo: string; valor: string }) { return <div className="grid grid-cols-[145px_1fr] gap-3 border-b border-slate-200 py-2 last:border-0"><dt className="font-semibold text-slate-700">{rotulo}</dt><dd className="break-words">{valor}</dd></div> }
