/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Venda = Registro & { valor?: number; cliente_nome?: string; data_venda?: string }
type DadosRelatorio = { oportunidades: Registro[]; propostas: Registro[]; pedidos: Registro[]; vendas: Venda[] }
type TipoDetalhe = keyof DadosRelatorio

function numero(valor: unknown) {
  const convertido = Number(valor || 0)
  return Number.isFinite(convertido) ? convertido : 0
}
function moeda(valor: unknown) { return numero(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function texto(valor: unknown, padrao = "-") { const r = String(valor ?? "").trim(); return r || padrao }
function dataRegistro(item: Registro, tipo: "oportunidade" | "proposta" | "pedido" | "venda") {
  const candidatos = tipo === "venda" ? [item.data_venda, item.created_at, item.updated_at]
    : tipo === "pedido" ? [item.data_pedido, item.created_at, item.updated_at]
      : tipo === "proposta" ? [item.data_proposta, item.created_at, item.updated_at]
        : [item.created_at, item.updated_at, item.data_fechamento_prevista]
  const valor = candidatos.find(Boolean)
  if (!valor) return null
  const data = new Date(`${String(valor).slice(0, 10)}T12:00:00`)
  return Number.isNaN(data.getTime()) ? null : data
}
function dentroPeriodo(item: Registro, tipo: "oportunidade" | "proposta" | "pedido" | "venda", inicio: string, fim: string) {
  if (!inicio && !fim) return true
  const data = dataRegistro(item, tipo)
  if (!data) return false
  if (inicio && data < new Date(`${inicio}T00:00:00`)) return false
  if (fim && data > new Date(`${fim}T23:59:59`)) return false
  return true
}
function dataBr(valor: string) {
  if (!valor) return "-"
  const d = new Date(`${valor}T12:00:00`)
  return Number.isNaN(d.getTime()) ? valor : d.toLocaleDateString("pt-BR")
}

async function carregarRelatorio(): Promise<DadosRelatorio> {
  const response = await fetchCrmSeguroProxy("crm-seguro/relatorios", { cache: "no-store" })
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar o relatório comercial.")
  return {
    oportunidades: Array.isArray(payload?.oportunidades) ? payload.oportunidades : [],
    propostas: Array.isArray(payload?.propostas) ? payload.propostas : [],
    pedidos: Array.isArray(payload?.pedidos) ? payload.pedidos : [],
    vendas: Array.isArray(payload?.vendas) ? payload.vendas : [],
  }
}

export default function RelatoriosSegurosPage() {
  const [dados, setDados] = useState<DadosRelatorio>({ oportunidades: [], propostas: [], pedidos: [], vendas: [] })
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [inicio, setInicio] = useState("")
  const [fim, setFim] = useState("")
  const [detalhe, setDetalhe] = useState<TipoDetalhe>("oportunidades")

  useEffect(() => {
    let ativo = true
    setLoading(true); setErro("")
    void carregarRelatorio()
      .then(payload => { if (ativo) setDados(payload) })
      .catch(e => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao consolidar relatório comercial.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  const filtrados = useMemo<DadosRelatorio>(() => ({
    oportunidades: dados.oportunidades.filter(item => dentroPeriodo(item, "oportunidade", inicio, fim)),
    propostas: dados.propostas.filter(item => dentroPeriodo(item, "proposta", inicio, fim)),
    pedidos: dados.pedidos.filter(item => dentroPeriodo(item, "pedido", inicio, fim)),
    vendas: dados.vendas.filter(item => dentroPeriodo(item, "venda", inicio, fim)),
  }), [dados, fim, inicio])

  const valores = useMemo(() => ({
    oportunidades: filtrados.oportunidades.reduce((s, i) => s + numero(i.valor_estimado), 0),
    propostas: filtrados.propostas.reduce((s, i) => s + numero(i.valor_total ?? i.valor), 0),
    pedidos: filtrados.pedidos.reduce((s, i) => s + numero(i.valor), 0),
    vendas: filtrados.vendas.reduce((s, i) => s + numero(i.valor), 0),
  }), [filtrados])

  const ranking = useMemo(() => {
    const mapa = new Map<string, { cliente: string; vendas: number; valor: number }>()
    filtrados.vendas.forEach(v => {
      const cliente = texto(v.cliente_nome, "Cliente não identificado")
      const atual = mapa.get(cliente) || { cliente, vendas: 0, valor: 0 }
      atual.vendas += 1; atual.valor += numero(v.valor); mapa.set(cliente, atual)
    })
    return Array.from(mapa.values()).sort((a,b) => b.valor - a.valor).slice(0,5)
  }, [filtrados.vendas])

  const conversaoPedidoVenda = filtrados.pedidos.length ? (filtrados.vendas.length / filtrados.pedidos.length) * 100 : 0
  const conversaoOportunidadeVenda = filtrados.oportunidades.length ? (filtrados.vendas.length / filtrados.oportunidades.length) * 100 : 0
  const periodoTexto = inicio || fim ? `${inicio ? dataBr(inicio) : "início da base"} a ${fim ? dataBr(fim) : "hoje"}` : "Base completa"
  const detalhes = filtrados[detalhe]

  return <main className="flex min-h-screen bg-[#020817] text-white print:block print:bg-white print:text-black">
    <div className="print:hidden"><Sidebar /></div>
    <section className="min-w-0 flex-1">
      <div className="print:hidden"><Topbar /></div>
      <div className="space-y-6 p-4 sm:p-6 lg:p-8 print:p-0">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6 print:rounded-none print:border-0 print:bg-white print:p-0">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400 print:text-black">Gestão comercial</p>
          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><h1 className="text-3xl font-bold">Relatórios</h1><p className="mt-2 text-sm text-slate-400 print:text-gray-700">Fluxo real do CRM conforme a responsabilidade do usuário autenticado: oportunidade → proposta → pedido → venda.</p><p className="mt-2 text-xs text-slate-500">Período: {periodoTexto}</p></div><button type="button" onClick={() => window.print()} className="rounded-xl border border-cyan-700 bg-cyan-500/10 px-4 py-3 text-sm font-semibold text-cyan-200 print:hidden">Imprimir / Salvar PDF</button></div>
        </header>

        <section className="rounded-2xl border border-[#13203f] bg-[#071427] p-4 print:hidden"><div className="grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-end"><label className="text-sm text-slate-300">Data inicial<input type="date" value={inicio} onChange={e => setInicio(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label><label className="text-sm text-slate-300">Data final<input type="date" value={fim} onChange={e => setFim(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label><button type="button" onClick={() => { const hoje = new Date(); setInicio(`${hoje.getFullYear()}-01-01`); setFim(hoje.toISOString().slice(0,10)) }} className="rounded-xl border border-[#24466f] px-4 py-3 text-sm text-cyan-200">Ano atual</button><button type="button" onClick={() => { setInicio(""); setFim("") }} className="rounded-xl border border-[#24466f] px-4 py-3 text-sm text-slate-300">Base completa</button></div></section>

        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
        {loading ? <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-400">Consolidando dados comerciais...</div> : <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 print:grid-cols-4">
            <Kpi titulo="Oportunidades" valor={String(filtrados.oportunidades.length)} detalhe={moeda(valores.oportunidades)} onClick={() => setDetalhe("oportunidades")} />
            <Kpi titulo="Propostas" valor={String(filtrados.propostas.length)} detalhe={moeda(valores.propostas)} onClick={() => setDetalhe("propostas")} />
            <Kpi titulo="Pedidos" valor={String(filtrados.pedidos.length)} detalhe={moeda(valores.pedidos)} onClick={() => setDetalhe("pedidos")} />
            <Kpi titulo="Vendas" valor={String(filtrados.vendas.length)} detalhe={moeda(valores.vendas)} onClick={() => setDetalhe("vendas")} />
          </section>

          <section className="grid gap-5 xl:grid-cols-2"><div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><p className="text-xs uppercase tracking-[.18em] text-cyan-400">Conversão</p><div className="mt-5 grid gap-4 sm:grid-cols-2"><Kpi titulo="Pedido → Venda" valor={`${conversaoPedidoVenda.toFixed(1)}%`} detalhe={`${filtrados.vendas.length} de ${filtrados.pedidos.length}`} /><Kpi titulo="Oportunidade → Venda" valor={`${conversaoOportunidadeVenda.toFixed(1)}%`} detalhe={`${filtrados.vendas.length} de ${filtrados.oportunidades.length}`} /></div></div><div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><p className="text-xs uppercase tracking-[.18em] text-cyan-400">Top clientes por vendas</p><div className="mt-4 space-y-2">{ranking.length ? ranking.map(item => <div key={item.cliente} className="flex items-center justify-between rounded-xl bg-[#091a33] px-4 py-3"><div><strong>{item.cliente}</strong><div className="text-xs text-slate-500">{item.vendas} venda(s)</div></div><span className="text-emerald-300">{moeda(item.valor)}</span></div>) : <p className="text-sm text-slate-500">Sem vendas no recorte selecionado.</p>}</div></div></section>

          <section id="detalhamento-relatorio" className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><div className="flex flex-wrap gap-2">{(["oportunidades","propostas","pedidos","vendas"] as TipoDetalhe[]).map(tipo => <button key={tipo} onClick={() => setDetalhe(tipo)} className={`rounded-lg border px-3 py-2 text-xs ${detalhe === tipo ? "border-cyan-500 bg-cyan-500/10 text-cyan-200" : "border-slate-700 text-slate-400"}`}>{tipo.toUpperCase()}</button>)}</div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead><tr className="border-b border-[#13203f] text-slate-500"><th className="p-3">Identificação</th><th className="p-3">Cliente</th><th className="p-3">Status</th><th className="p-3">Data</th><th className="p-3">Valor</th></tr></thead><tbody>{detalhes.map((item, index) => <tr key={String(item.id || index)} className="border-b border-[#13203f]"><td className="p-3">{texto(item.numero ?? item.titulo ?? item.id)}</td><td className="p-3">{texto(item.cliente_nome ?? item.razao_social ?? item.nome_cliente)}</td><td className="p-3 text-cyan-300">{texto(item.status ?? item.status_ciclo)}</td><td className="p-3">{dataRegistro(item, detalhe === "vendas" ? "venda" : detalhe === "pedidos" ? "pedido" : detalhe === "propostas" ? "proposta" : "oportunidade")?.toLocaleDateString("pt-BR") || "-"}</td><td className="p-3 text-emerald-300">{moeda(item.valor_total ?? item.valor_estimado ?? item.valor)}</td></tr>)}</tbody></table></div></section>
        </>}
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor, detalhe, onClick }: { titulo: string; valor: string; detalhe: string; onClick?: () => void }) {
  const classes = "rounded-2xl border border-[#16325c] bg-[#091a33] p-5 text-left"
  const body = <><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p><p className="mt-1 text-xs text-slate-500">{detalhe}</p></>
  return onClick ? <button type="button" onClick={onClick} className={`${classes} transition hover:border-cyan-500/70`}>{body}</button> : <div className={classes}>{body}</div>
}
