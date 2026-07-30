/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { FormEvent, useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth"
import { API_URL } from "@/lib/api"

type Registro = Record<string, unknown>
type Destinatario = { id: string; nome?: string; email?: string; cargo?: string; regiao?: string }
type Detalhes = { pedido: Registro; proposta: Registro; item: Registro; aceite: Registro; destinatarios_disponiveis: Destinatario[]; envios: Registro[] }

function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function dataHora(valor: unknown) { if (!valor) return "-"; const d = new Date(String(valor)); return Number.isNaN(d.getTime()) ? String(valor) : d.toLocaleString("pt-BR") }

export default function PedidoDetalhesPage() {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const { usuario } = useAuth()
  const [dados, setDados] = useState<Detalhes | null>(null)
  const [selecionados, setSelecionados] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  async function carregar() {
    setLoading(true)
    setErro("")
    try {
      const response = await fetch(`${API_URL}/carrier-operacional/pedidos/${id}`, { cache: "no-store" })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar o dossiê.")
      setDados(payload)
      setSelecionados((payload.destinatarios_disponiveis || []).filter((item: Destinatario) => Boolean((item as Destinatario & { copia_obrigatoria?: boolean }).copia_obrigatoria)).map((item: Destinatario) => item.id))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar dossiê.") }
    finally { setLoading(false) }
  }

  useEffect(() => { if (id) void carregar() }, [id])

  async function prepararEnvio(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true)
    setErro("")
    setMensagem("")
    const form = new FormData(evento.currentTarget)
    try {
      const response = await fetch(`${API_URL}/carrier-operacional/pedidos/${id}/preparar-envio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enviado_por: String(usuario?.id || "") || null,
          destinatario_ids: selecionados,
          assunto: String(form.get("assunto") || "") || null,
          corpo: String(form.get("corpo") || "") || null,
        }),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível preparar o envio.")
      setMensagem("Dossiê preparado e registrado para encaminhamento à Carrier.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao preparar envio.") }
    finally { setSalvando(false) }
  }

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <Link href="/pedidos" className="text-sm font-semibold text-cyan-300">← Voltar para pedidos</Link>
          <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Dossiê comercial</p><h1 className="mt-2 text-3xl font-bold">{String(dados?.pedido.numero || "Pedido")}</h1><p className="mt-2 text-sm text-slate-400">Proposta aceita, aceite registrado e documentos Carrier.</p></div>
            {dados && <span className="w-fit rounded-full border border-cyan-800 px-4 py-2 text-sm text-cyan-200">{String(dados.pedido.status_envio_carrier || "NAO_ENVIADO")}</span>}
          </div>
        </header>

        {loading && <Aviso>Carregando dossiê...</Aviso>}
        {erro && <div className="rounded-xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
        {mensagem && <div className="rounded-xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}

        {dados && <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi titulo="Valor" valor={moeda(dados.pedido.valor)} />
            <Kpi titulo="Equipamento" valor={String(dados.item.equipamento || dados.proposta.equipamentos || "-")} />
            <Kpi titulo="Quantidade" valor={String(dados.item.quantidade || 1)} />
            <Kpi titulo="Proposta" valor={String(dados.proposta.numero || "-")} />
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Resumo do pedido</h2>
              <dl className="mt-5 space-y-3 text-sm">
                <Linha label="Linha" valor={String(dados.item.linha_produto || dados.proposta.produtos || "-")} />
                <Linha label="Equipamento" valor={String(dados.item.equipamento || dados.proposta.equipamentos || "-")} />
                <Linha label="Pagamento" valor={String(dados.item.condicao_pagamento || dados.proposta.condicoes || "-")} />
                <Linha label="Entrega" valor={String(dados.item.prazo_entrega || "-")} />
                <Linha label="Garantia" valor={String(dados.item.garantia || "-")} />
                <Linha label="Data do pedido" valor={dataHora(dados.pedido.data_pedido)} />
              </dl>
            </article>
            <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Aceite registrado</h2>
              <dl className="mt-5 space-y-3 text-sm">
                <Linha label="Signatário" valor={String(dados.aceite.nome_signatario || "-")} />
                <Linha label="Documento" valor={String(dados.aceite.documento_signatario || "-")} />
                <Linha label="Método" valor={String(dados.aceite.metodo || "-")} />
                <Linha label="Data e hora" valor={dataHora(dados.aceite.aceito_em)} />
                <Linha label="Status" valor={String(dados.aceite.status || "-")} />
                <Linha label="Hash da proposta" valor={String(dados.proposta.hash_documento || "-")} />
              </dl>
            </article>
          </section>

          <form onSubmit={prepararEnvio} className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
            <h2 className="text-xl font-bold">Preparar encaminhamento à Carrier</h2>
            <p className="mt-2 text-sm text-slate-400">Selecione os destinatários autorizados. O envio será registrado na auditoria antes da integração com o provedor de e-mail.</p>
            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {dados.destinatarios_disponiveis.length === 0 ? <p className="text-sm text-amber-300">Nenhum destinatário Carrier ativo cadastrado.</p> : dados.destinatarios_disponiveis.map((item) => <label key={item.id} className="flex gap-3 rounded-xl border border-[#16325c] bg-[#091a33] p-4 text-sm"><input type="checkbox" checked={selecionados.includes(item.id)} onChange={(e) => setSelecionados((atual) => e.target.checked ? [...new Set([...atual, item.id])] : atual.filter((idAtual) => idAtual !== item.id))} /><span><strong className="block text-white">{item.nome || item.email}</strong><span className="text-slate-500">{item.cargo || item.regiao || item.email}</span></span></label>)}
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <label className="text-sm text-slate-300">Assunto<input name="assunto" defaultValue={`Pedido comercial ${String(dados.pedido.numero || "")}`} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
              <label className="text-sm text-slate-300 md:col-span-2">Mensagem<textarea name="corpo" defaultValue="Encaminhamento do dossiê comercial gerado pelo CTI." rows={4} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
            </div>
            <button disabled={salvando || selecionados.length === 0} className="mt-5 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{salvando ? "Preparando..." : "Preparar dossiê Carrier"}</button>
          </form>

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
            <h2 className="text-xl font-bold">Histórico de encaminhamentos</h2>
            <div className="mt-5 space-y-3">{dados.envios.length === 0 ? <p className="text-sm text-slate-500">Nenhum encaminhamento registrado.</p> : dados.envios.map((envio) => <article key={String(envio.id)} className="rounded-xl border border-[#16325c] bg-[#091a33] p-4 text-sm"><div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between"><div><p className="font-semibold text-white">{String(envio.assunto || "Encaminhamento Carrier")}</p><p className="mt-1 text-slate-500">{dataHora(envio.created_at)}</p></div><span className="w-fit rounded-full border border-cyan-800 px-3 py-1 text-xs text-cyan-200">{String(envio.status || "PENDENTE")}</span></div></article>)}</div>
          </section>
        </>}
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 break-words text-xl font-bold text-cyan-300">{valor}</p></div> }
function Linha({ label, valor }: { label: string; valor: string }) { return <div className="flex items-start justify-between gap-4 border-b border-[#13203f] pb-3 last:border-0"><dt className="text-slate-500">{label}</dt><dd className="max-w-[65%] break-words text-right text-slate-200">{valor}</dd></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">{children}</div> }
