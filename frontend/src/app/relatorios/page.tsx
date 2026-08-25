/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Registro = Record<string, unknown>
type Venda = Registro & { valor?: number; cliente_nome?: string; equipamento_nome?: string; equipamento_codigo?: string; data_venda?: string }
type DadosRelatorio = { oportunidades: Registro[]; propostas: Registro[]; pedidos: Registro[]; vendas: Venda[] }
type TipoDetalhe = keyof DadosRelatorio

type Serie = { rotulo: string; valor: number; tipo: TipoDetalhe }

function numero(valor: unknown) {
  const convertido = Number(valor || 0)
  return Number.isFinite(convertido) ? convertido : 0
}

function moeda(valor: unknown) {
  return numero(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function texto(valor: unknown, padrao = "-") {
  const resultado = String(valor ?? "").trim()
  return resultado || padrao
}

function dataRegistro(item: Registro, tipo: "oportunidade" | "proposta" | "pedido" | "venda") {
  const candidatos = tipo === "venda"
    ? [item.data_venda, item.created_at, item.updated_at]
    : tipo === "pedido"
      ? [item.data_pedido, item.created_at, item.updated_at]
      : tipo === "proposta"
        ? [item.data_proposta, item.created_at, item.updated_at]
        : [item.created_at, item.updated_at, item.data_fechamento_prevista]
  const valor = candidatos.find(Boolean)
  if (!valor) return null
  const data = new Date(String(valor).slice(0, 10) + "T12:00:00")
  return Number.isNaN(data.getTime()) ? null : data
}

function dentroPeriodo(item: Registro, tipo: "oportunidade" | "proposta" | "pedido" | "venda", inicio: string, fim: string) {
  if (!inicio && !fim) return true
  const data = dataRegistro(item, tipo)
  if (!data) return false
  const inicioData = inicio ? new Date(`${inicio}T00:00:00`) : null
  const fimData = fim ? new Date(`${fim}T23:59:59`) : null
  if (inicioData && data < inicioData) return false
  if (fimData && data > fimData) return false
  return true
}

function dataBr(valor: unknown) {
  if (!valor) return "-"
  const data = new Date(`${String(valor).slice(0, 10)}T12:00:00`)
  return Number.isNaN(data.getTime()) ? String(valor) : data.toLocaleDateString("pt-BR")
}

async function carregarLista(url: string) {
  const resposta = await fetch(url, { cache: "no-store" })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new Error(payload?.detail || `Falha ao consultar ${url}.`)
  if (!Array.isArray(payload)) throw new Error(`Resposta inesperada em ${url}.`)
  return payload as Registro[]
}

export default function RelatoriosPage() {
  const [dados, setDados] = useState<DadosRelatorio>({ oportunidades: [], propostas: [], pedidos: [], vendas: [] })
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [inicio, setInicio] = useState("")
  const [fim, setFim] = useState("")
  const [detalheAtivo, setDetalheAtivo] = useState<TipoDetalhe>("oportunidades")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    Promise.all([
      carregarLista(`${API_URL}/crm-visao/oportunidades`),
      carregarLista(`${API_URL}/crm-documentos/propostas`),
      carregarLista(`${API_URL}/crm-documentos/pedidos`),
      carregarLista(`${API_URL}/vendas`),
    ])
      .then(([oportunidades, propostas, pedidos, vendas]) => {
        if (ativo) setDados({ oportunidades, propostas, pedidos, vendas: vendas as Venda[] })
      })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao consolidar relatório comercial.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  const filtrados = useMemo<DadosRelatorio>(() => ({
    oportunidades: dados.oportunidades.filter((item) => dentroPeriodo(item, "oportunidade", inicio, fim)),
    propostas: dados.propostas.filter((item) => dentroPeriodo(item, "proposta", inicio, fim)),
    pedidos: dados.pedidos.filter((item) => dentroPeriodo(item, "pedido", inicio, fim)),
    vendas: dados.vendas.filter((item) => dentroPeriodo(item, "venda", inicio, fim)),
  }), [dados, inicio, fim])

  const resumo = useMemo(() => {
    const valorOportunidades = filtrados.oportunidades.reduce((total, item) => total + numero(item.valor_estimado), 0)
    const valorPropostas = filtrados.propostas.reduce((total, item) => total + numero(item.valor_total ?? item.valor), 0)
    const valorPedidos = filtrados.pedidos.reduce((total, item) => total + numero(item.valor), 0)
    const valorVendas = filtrados.vendas.reduce((total, item) => total + numero(item.valor), 0)
    const conversaoPedidoVenda = filtrados.pedidos.length ? (filtrados.vendas.length / filtrados.pedidos.length) * 100 : 0
    const conversaoOportunidadeVenda = filtrados.oportunidades.length ? (filtrados.vendas.length / filtrados.oportunidades.length) * 100 : 0
    return { valorOportunidades, valorPropostas, valorPedidos, valorVendas, conversaoPedidoVenda, conversaoOportunidadeVenda }
  }, [filtrados])

  const ranking = useMemo(() => {
    const acumulado = new Map<string, { cliente: string; vendas: number; valor: number }>()
    for (const venda of filtrados.vendas) {
      const cliente = texto(venda.cliente_nome, "Cliente não identificado")
      const atual = acumulado.get(cliente) || { cliente, vendas: 0, valor: 0 }
      atual.vendas += 1
      atual.valor += numero(venda.valor)
      acumulado.set(cliente, atual)
    }
    return Array.from(acumulado.values()).sort((a, b) => b.valor - a.valor).slice(0, 5)
  }, [filtrados.vendas])

  const funil: Serie[] = [
    { rotulo: "Oportunidades", valor: filtrados.oportunidades.length, tipo: "oportunidades" },
    { rotulo: "Propostas", valor: filtrados.propostas.length, tipo: "propostas" },
    { rotulo: "Pedidos", valor: filtrados.pedidos.length, tipo: "pedidos" },
    { rotulo: "Vendas", valor: filtrados.vendas.length, tipo: "vendas" },
  ]
  const maxFunil = Math.max(1, ...funil.map((item) => item.valor))

  const vendasMensais = useMemo(() => {
    const meses = new Map<string, number>()
    for (const venda of filtrados.vendas) {
      const data = dataRegistro(venda, "venda")
      if (!data) continue
      const chave = `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}`
      meses.set(chave, (meses.get(chave) || 0) + numero(venda.valor))
    }
    return Array.from(meses.entries()).sort(([a], [b]) => a.localeCompare(b)).slice(-12).map(([chave, valor]) => {
      const [ano, mes] = chave.split("-")
      return { rotulo: `${mes}/${ano.slice(2)}`, valor }
    })
  }, [filtrados.vendas])
  const maxMensal = Math.max(1, ...vendasMensais.map((item) => item.valor))

  const periodoTexto = inicio || fim ? `${inicio ? dataBr(inicio) : "início da base"} a ${fim ? dataBr(fim) : "hoje"}` : "Base completa"
  const abrirDetalhe = (tipo: TipoDetalhe) => {
    setDetalheAtivo(tipo)
    window.setTimeout(() => document.getElementById("detalhamento-relatorio")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0)
  }

  return <main className="flex min-h-screen bg-[#020817] text-white print:block print:bg-white print:text-black">
    <div className="print:hidden"><Sidebar /></div>
    <section className="min-w-0 flex-1">
      <div className="print:hidden"><Topbar /></div>
      <div className="space-y-6 p-4 sm:p-6 lg:p-8 print:p-0">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6 print:rounded-none print:border-0 print:bg-white print:p-0">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400 print:text-black">Gestão comercial</p>
          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div><h1 className="text-3xl font-bold">Relatórios</h1><p className="mt-2 max-w-3xl text-sm text-slate-400 print:text-gray-700">Consolidação gerencial do fluxo real do CRM: oportunidade → proposta → pedido → venda.</p><p className="mt-2 text-xs text-slate-500 print:text-gray-600">Período: {periodoTexto}</p></div>
            <button type="button" onClick={() => window.print()} className="rounded-xl border border-cyan-700 bg-cyan-500/10 px-4 py-3 text-sm font-semibold text-cyan-200 print:hidden">Imprimir / Salvar PDF</button>
          </div>
        </header>

        <section className="rounded-2xl border border-[#13203f] bg-[#071427] p-4 print:hidden">
          <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-end">
            <label className="text-sm text-slate-300">Data inicial<input type="date" value={inicio} onChange={(e) => setInicio(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
            <label className="text-sm text-slate-300">Data final<input type="date" value={fim} onChange={(e) => setFim(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
            <button type="button" onClick={() => { const hoje = new Date(); const inicioAno = `${hoje.getFullYear()}-01-01`; setInicio(inicioAno); setFim(hoje.toISOString().slice(0, 10)) }} className="rounded-xl border border-[#24466f] px-4 py-3 text-sm text-cyan-200">Ano atual</button>
            <button type="button" onClick={() => { setInicio(""); setFim("") }} className="rounded-xl border border-[#24466f] px-4 py-3 text-sm text-slate-300">Base completa</button>
          </div>
        </section>

        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
        {loading ? <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-400">Consolidando dados comerciais...</div> : <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 print:grid-cols-4">
            <Kpi titulo="Oportunidades" valor={String(filtrados.oportunidades.length)} detalhe={moeda(resumo.valorOportunidades)} onOpen={() => abrirDetalhe("oportunidades")} />
            <Kpi titulo="Propostas" valor={String(filtrados.propostas.length)} detalhe={moeda(resumo.valorPropostas)} onOpen={() => abrirDetalhe("propostas")} />
            <Kpi titulo="Pedidos" valor={String(filtrados.pedidos.length)} detalhe={moeda(resumo.valorPedidos)} onOpen={() => abrirDetalhe("pedidos")} />
            <Kpi titulo="Vendas" valor={String(filtrados.vendas.length)} detalhe={moeda(resumo.valorVendas)} destaque onOpen={() => abrirDetalhe("vendas")} />
          </section>

          <section className="grid gap-4 xl:grid-cols-2 print:grid-cols-2">
            <GraficoCard titulo="Funil comercial" subtitulo="Volume por etapa no período selecionado. Clique em uma etapa para abrir exatamente os registros que a compõem.">
              <div className="space-y-4">{funil.map((item) => <button type="button" onClick={() => abrirDetalhe(item.tipo)} key={item.rotulo} className="block w-full rounded-xl p-2 text-left transition hover:bg-cyan-500/10 print:pointer-events-none"><div className="mb-1 flex justify-between text-sm"><span>{item.rotulo}</span><strong>{item.valor}</strong></div><div className="h-7 overflow-hidden rounded-lg bg-[#020817] print:bg-gray-200"><div className="flex h-full items-center justify-end rounded-lg bg-cyan-500/70 px-2 text-xs font-bold text-white print:bg-gray-500" style={{ width: `${Math.max(6, (item.valor / maxFunil) * 100)}%` }}>{item.valor}</div></div><p className="mt-1 text-right text-[11px] text-cyan-400 print:hidden">Clique para detalhar</p></button>)}</div>
            </GraficoCard>
            <GraficoCard titulo="Vendas por mês" subtitulo="Valor vendido nos últimos meses do período selecionado.">
              {vendasMensais.length === 0 ? <p className="rounded-xl border border-dashed border-[#24466f] p-6 text-center text-sm text-slate-400">Sem vendas no período selecionado.</p> : <div className="flex h-64 items-end gap-2 overflow-x-auto border-b border-[#24466f] pb-2">{vendasMensais.map((item) => <div key={item.rotulo} className="flex min-w-14 flex-1 flex-col items-center justify-end gap-2"><span className="text-[10px] text-slate-400 print:text-gray-600">{moeda(item.valor)}</span><div className="w-full rounded-t-lg bg-emerald-500/70 print:bg-gray-500" style={{ height: `${Math.max(8, (item.valor / maxMensal) * 170)}px` }} /><span className="text-xs text-slate-400 print:text-gray-600">{item.rotulo}</span></div>)}</div>}
            </GraficoCard>
          </section>

          <section className="grid gap-4 lg:grid-cols-2 print:grid-cols-2">
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:bg-white">
              <h2 className="text-xl font-bold">Conversão comercial</h2>
              <p className="mt-1 text-sm text-slate-400 print:text-gray-600">Leitura direta dos registros existentes no CRM e no painel de vendas.</p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2"><Indicador titulo="Pedido → Venda" valor={`${resumo.conversaoPedidoVenda.toFixed(1)}%`} /><Indicador titulo="Oportunidade → Venda" valor={`${resumo.conversaoOportunidadeVenda.toFixed(1)}%`} /></div>
            </div>
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:bg-white">
              <h2 className="text-xl font-bold">Top clientes por vendas</h2><p className="mt-1 text-sm text-slate-400 print:text-gray-600">Ranking financeiro da base de vendas registrada.</p>
              <div className="mt-5 space-y-3">{ranking.length === 0 ? <p className="rounded-2xl border border-dashed border-[#24466f] p-6 text-center text-sm text-slate-400">Nenhuma venda disponível para ranking.</p> : ranking.map((item, index) => <div key={item.cliente} className="flex items-center justify-between gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 print:bg-white"><div><p className="text-xs text-slate-500">#{index + 1} · {item.vendas} venda{item.vendas === 1 ? "" : "s"}</p><p className="mt-1 font-semibold">{item.cliente}</p></div><strong className="text-emerald-300 print:text-black">{moeda(item.valor)}</strong></div>)}</div>
            </div>
          </section>

          <DetalhamentoRelatorio tipo={detalheAtivo} dados={filtrados[detalheAtivo]} periodo={periodoTexto} />

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:bg-white">
            <h2 className="text-xl font-bold">Últimas vendas</h2><p className="mt-1 text-sm text-slate-400 print:text-gray-600">Fechamentos mais recentes no período selecionado.</p>
            <div className="mt-5 overflow-x-auto"><table className="min-w-full text-sm"><thead><tr className="border-b border-[#16325c] text-left text-slate-400 print:text-gray-600"><th className="p-3">Cliente</th><th className="p-3">Equipamento</th><th className="p-3">Data</th><th className="p-3">Valor</th></tr></thead><tbody>{filtrados.vendas.slice(0, 20).map((venda, index) => <tr key={String(venda.id || index)} className="border-b border-[#13203f]"><td className="p-3 font-semibold">{texto(venda.cliente_nome)}</td><td className="p-3">{texto(venda.equipamento_nome || venda.equipamento_codigo)}</td><td className="p-3">{dataBr(venda.data_venda)}</td><td className="p-3 font-semibold text-emerald-300 print:text-black">{moeda(venda.valor)}</td></tr>)}</tbody></table></div>
          </section>
        </>}
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor, detalhe, destaque = false, onOpen }: { titulo: string; valor: string; detalhe: string; destaque?: boolean; onOpen?: () => void }) {
  const classes = `rounded-2xl border p-5 text-left print:bg-white ${destaque ? "border-emerald-800 bg-emerald-950/20" : "border-[#13203f] bg-[#091a33]"}`
  const body = <><p className="text-sm text-slate-400 print:text-gray-600">{titulo}</p><p className={`mt-2 text-3xl font-bold ${destaque ? "text-emerald-300 print:text-black" : "text-cyan-300 print:text-black"}`}>{valor}</p><p className="mt-1 text-sm text-slate-300 print:text-gray-700">{detalhe}</p>{onOpen && <p className="mt-2 text-[11px] text-cyan-400 print:hidden">Clique para abrir os registros</p>}</>
  return onOpen ? <button type="button" onClick={onOpen} className={`${classes} transition hover:border-cyan-500/70 hover:bg-[#0b1d38] print:pointer-events-none`}>{body}</button> : <div className={classes}>{body}</div>
}

function DetalhamentoRelatorio({ tipo, dados, periodo }: { tipo: TipoDetalhe; dados: Registro[]; periodo: string }) {
  const titulos: Record<TipoDetalhe, string> = { oportunidades: "Oportunidades", propostas: "Propostas", pedidos: "Pedidos", vendas: "Vendas" }
  return <section id="detalhamento-relatorio" className="scroll-mt-24 rounded-3xl border border-cyan-800/70 bg-[#071427] p-6 print:bg-white">
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400 print:text-black">Composição do indicador</p><h2 className="mt-1 text-xl font-bold">{titulos[tipo]} · {dados.length.toLocaleString("pt-BR")} registro{dados.length === 1 ? "" : "s"}</h2><p className="mt-1 text-sm text-slate-400 print:text-gray-600">Mesma coleção e mesmo filtro de data usados no total acima · {periodo}.</p></div><a href="#" className="text-xs text-cyan-300 print:hidden">Voltar ao topo</a></div>
    {dados.length === 0 ? <p className="mt-5 rounded-xl border border-dashed border-[#24466f] p-6 text-center text-sm text-slate-400">Nenhum registro compõe este indicador no período selecionado.</p> : <div className="mt-5 max-h-[560px] overflow-auto rounded-2xl border border-[#16325c]"><table className="min-w-full text-sm"><thead className="sticky top-0 bg-[#091a33] print:static print:bg-white"><tr className="border-b border-[#16325c] text-left text-slate-400 print:text-gray-600"><th className="p-3">#</th><th className="p-3">Cliente / referência</th><th className="p-3">Identificação</th><th className="p-3">Status</th><th className="p-3">Data</th><th className="p-3">Valor</th></tr></thead><tbody>{dados.map((item, index) => <tr key={`${tipo}-${String(item.id || item.numero || index)}`} className="border-b border-[#13203f]"><td className="p-3 text-slate-500">{index + 1}</td><td className="p-3 font-semibold">{texto(item.cliente_nome ?? item.cliente ?? item.empresa ?? item.cliente_id)}</td><td className="p-3">{texto(item.numero ?? item.titulo ?? item.equipamento_nome ?? item.equipamento_codigo ?? item.id)}</td><td className="p-3 text-cyan-300 print:text-black">{texto(item.status_documento ?? item.status_ciclo ?? item.status)}</td><td className="p-3">{dataBr(item.data_venda ?? item.data_pedido ?? item.data_proposta ?? item.created_at ?? item.data_fechamento_prevista)}</td><td className="p-3 font-semibold text-emerald-300 print:text-black">{moeda(item.valor_total ?? item.valor ?? item.valor_estimado)}</td></tr>)}</tbody></table></div>}
  </section>
}

function Indicador({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4 print:bg-white"><p className="text-sm text-slate-400 print:text-gray-600">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300 print:text-black">{valor}</p></div>
}

function GraficoCard({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: React.ReactNode }) {
  return <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:bg-white"><h2 className="text-xl font-bold">{titulo}</h2><p className="mt-1 text-sm text-slate-400 print:text-gray-600">{subtitulo}</p><div className="mt-5">{children}</div></div>
}
