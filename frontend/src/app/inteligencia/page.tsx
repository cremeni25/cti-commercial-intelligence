"use client"

import { useEffect, useMemo, useState } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://cti-backend-5ugf.onrender.com"
const dimensoes = ["regiao", "uf", "dealer", "implementadora", "cliente", "linha", "familia", "produto"] as const
const periodos = [
  ["HOJE", "Hoje"], ["ULTIMOS_7_DIAS", "Últimos 7 dias"], ["ULTIMOS_30_DIAS", "Últimos 30 dias"],
  ["ULTIMOS_90_DIAS", "Últimos 90 dias"], ["MES_ATUAL", "Mês atual"], ["TRIMESTRE_ATUAL", "Trimestre atual"],
  ["ANO_ATUAL", "Ano atual"], ["PERSONALIZADO", "Personalizado"],
] as const

type Opcao = { valor: string; contagem: number }
type Filtros = Record<(typeof dimensoes)[number], string> & { contexto: string; segmento: string; periodo: string; comparacao: string; inicio: string; fim: string }
type Ranking = { nome: string; quantidade: number; valor: number; participacao_percentual: number }
type Dados = {
  metadata: { contexto_operacional: string; segmento: string; ultima_atualizacao: string; origem: string }
  kpis: { volume: number; valor: number; ticket_medio: number; conversao: number; comparacoes: Record<string, { anterior: number; diferenca: number; percentual: number; direcao: string }> }
  rankings: Record<string, Ranking[]>
  serie_temporal: Array<{ periodo: string; volume: number; valor: number; ticket_medio: number; conversao: number; perdas: number }>
  oportunidades_perdidas: { quantidade: number; valor: number }
  clientes_inativos: Array<{ nome: string; dias_sem_compra: number; ultima_compra: string }>
  heatmap: Array<{ regiao: string; uf: string }>
  drilldown: Record<string, Ranking[]>
  potencial: { valor: number | null; status: string }
  empty_state: string | null
}

const inicial: Filtros = { contexto: "brasil", segmento: "GERAL", periodo: "ULTIMOS_90_DIAS", comparacao: "PERIODO_ANTERIOR", inicio: "", fim: "", regiao: "", uf: "", dealer: "", implementadora: "", cliente: "", linha: "", familia: "", produto: "" }

function query(filtros: Filtros, extra: Record<string, string> = {}) {
  const params = new URLSearchParams()
  Object.entries({ ...filtros, ...extra }).forEach(([chave, valor]) => { if (valor) params.set(chave, valor) })
  return params.toString()
}

function Card({ titulo, valor, comparacao }: { titulo: string; valor: string; comparacao?: { percentual: number; direcao: string } }) {
  return <div className="rounded-xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{titulo}</p><p className="mt-2 text-2xl font-semibold">{valor}</p>{comparacao && <p className={`mt-2 text-xs ${comparacao.direcao === "alta" ? "text-emerald-700" : comparacao.direcao === "queda" ? "text-red-700" : "text-slate-500"}`}>{comparacao.percentual > 0 ? "+" : ""}{comparacao.percentual}% vs. comparação</p>}</div>
}

function Barras({ itens }: { itens: Ranking[] }) {
  const maximo = Math.max(1, ...itens.map((item) => item.quantidade))
  return <div className="space-y-3">{itens.slice(0, 10).map((item) => <div key={item.nome}><div className="flex justify-between text-xs"><span className="truncate pr-2">{item.nome}</span><strong>{item.quantidade}</strong></div><div className="mt-1 h-2 rounded bg-slate-100"><div className="h-2 rounded bg-blue-600" style={{ width: `${Math.max(3, item.quantidade / maximo * 100)}%` }} /></div></div>)}</div>
}

export default function InteligenciaPage() {
  const [edicao, setEdicao] = useState<Filtros>(inicial)
  const [filtros, setFiltros] = useState<Filtros>(inicial)
  const [dados, setDados] = useState<Dados | null>(null)
  const [opcoes, setOpcoes] = useState<Record<string, Opcao[]>>({})
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [nivel, setNivel] = useState<string[]>([])

  const consulta = useMemo(() => query(filtros), [filtros])

  useEffect(() => {
    const controller = new AbortController(); setLoading(true)
    Promise.all([
      fetch(`${API_URL}/analytics/intelligence?${consulta}`, { cache: "no-store", signal: controller.signal }),
      fetch(`${API_URL}/analytics/intelligence/filter-options?${consulta}`, { cache: "no-store", signal: controller.signal }),
    ]).then(async ([resDados, resOpcoes]) => {
      if (!resDados.ok || !resOpcoes.ok) throw new Error(`Backend respondeu ${resDados.status}/${resOpcoes.status}`)
      const [payload, filtrosPayload] = await Promise.all([resDados.json(), resOpcoes.json()])
      setDados(payload); setOpcoes(filtrosPayload.opcoes || {}); setErro(null)
    }).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") return
      setErro(error instanceof Error ? error.message : "Falha ao carregar a inteligência comercial")
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [consulta])

  function alterar(chave: keyof Filtros, valor: string) {
    const novo = { ...edicao, [chave]: valor }
    if (chave === "linha") { novo.familia = ""; novo.produto = "" }
    if (chave === "familia") novo.produto = ""
    setEdicao(novo)
  }

  function aplicar() { setFiltros(edicao); setNivel(dimensoes.filter((d) => edicao[d]).map(String)) }
  function limpar() { setEdicao(inicial); setFiltros(inicial); setNivel([]) }
  function exportar(formato: "csv" | "xlsx") { window.open(`${API_URL}/analytics/intelligence/export?${query(filtros, { formato })}`, "_blank") }

  const heatmap = useMemo(() => {
    const mapa = new Map<string, number>()
    dados?.heatmap.forEach((item) => { const chave = `${item.regiao} / ${item.uf}`; mapa.set(chave, (mapa.get(chave) || 0) + 1) })
    return [...mapa.entries()].sort((a, b) => b[1] - a[1])
  }, [dados])

  return <main className="min-h-screen bg-slate-50 p-4 md:p-8"><div className="mx-auto max-w-7xl space-y-6">
    <header><p className="text-sm font-medium uppercase tracking-wide text-blue-700">CTI Commercial Intelligence v18</p><h1 className="text-3xl font-bold">Inteligência Comercial</h1><p className="mt-2 text-slate-600">Filtros reais, comparação, tendências, oportunidades e navegação analítica.</p></header>

    <section className="rounded-xl border bg-white p-5 shadow-sm"><div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <label className="text-sm">Contexto<select className="mt-1 w-full rounded-lg border p-2" value={edicao.contexto} onChange={(e) => alterar("contexto", e.target.value)}><option value="brasil">Brasil</option><option value="viena-sp">VIENA SP</option><option value="outros-dealers">Outros Dealers</option></select></label>
      <label className="text-sm">Segmento<select className="mt-1 w-full rounded-lg border p-2" value={edicao.segmento} onChange={(e) => alterar(\"segmento\", e.target.value)}>{[\"GERAL\", \"TR\", \"DT\", \"DD\", \"UNKNOWN\"].map((v) => <option key={v}>{v}</option>)}</select></label>
      <label className="text-sm">Período<select className="mt-1 w-full rounded-lg border p-2" value={edicao.periodo} onChange={(e) => alterar(\"periodo\", e.target.value)}>{periodos.map(([v,l]) => <option value={v} key={v}>{l}</option>)}</select></label>
      <label className="text-sm">Comparação<select className="mt-1 w-full rounded-lg border p-2" value={edicao.comparacao} onChange={(e) => alterar(\"comparacao\", e.target.value)}><option value="SEM_COMPARACAO">Sem comparação</option><option value="PERIODO_ANTERIOR">Período anterior</option><option value="ANO_ANTERIOR">Ano anterior</option></select></label>
      {edicao.periodo === "PERSONALIZADO" && <><label className="text-sm">Início<input type="date" className="mt-1 w-full rounded-lg border p-2" value={edicao.inicio} onChange={(e) => alterar(\"inicio\", e.target.value)} /></label><label className="text-sm">Fim<input type="date" className="mt-1 w-full rounded-lg border p-2" value={edicao.fim} onChange={(e) => alterar(\"fim\", e.target.value)} /></label></>}
      {dimensoes.map((dimensao) => <label className="text-sm capitalize" key={dimensao}>{dimensao}<select className="mt-1 w-full rounded-lg border p-2" value={edicao[dimensao]} onChange={(e) => alterar(dimensao, e.target.value)}><option value="">Todos</option>{(opcoes[dimensao] || []).map((o) => <option key={o.valor} value={o.valor}>{o.valor} ({o.contagem})</option>)}</select></label>)}
    </div><div className="mt-4 flex flex-wrap gap-2"><button onClick={aplicar} className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-medium text-white">Aplicar filtros</button><button onClick={limpar} className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-medium">Limpar</button><button onClick={() => exportar(\"csv\")} className="rounded-lg border px-4 py-2 text-sm">Exportar CSV</button><button onClick={() => exportar(\"xlsx\")} className="rounded-lg border px-4 py-2 text-sm">Exportar XLSX</button></div></section>

    {nivel.length > 0 && <nav className="rounded-xl border bg-white p-3 text-sm"><button onClick={limpar} className="font-medium text-blue-700">Brasil</button>{nivel.map((item, index) => <span key={item}> <span className="text-slate-400">›</span> <button onClick={() => { const novo = { ...edicao }; dimensoes.slice(index + 1).forEach((d) => { novo[d] = "" }); setEdicao(novo); setFiltros(novo); setNivel(nivel.slice(0, index + 1)) }} className="font-medium text-blue-700">{item}: {filtros[item as keyof Filtros]}</button></span>)}</nav>}

    {loading && <div className="rounded-xl border bg-white p-10 text-center">Carregando inteligência comercial...</div>}
    {erro && <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800">{erro}</div>}
    {!loading && dados?.empty_state && <div className="rounded-xl border bg-white p-10 text-center">{dados.empty_state}</div>}

    {!loading && dados && !dados.empty_state && <>
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Card titulo="Volume" valor={dados.kpis.volume.toLocaleString("pt-BR")} comparacao={dados.kpis.comparacoes.volume} /><Card titulo="Valor" valor={dados.kpis.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} comparacao={dados.kpis.comparacoes.valor} /><Card titulo="Ticket médio" valor={dados.kpis.ticket_medio.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} comparacao={dados.kpis.comparacoes.ticket_medio} /><Card titulo="Conversão" valor={`${dados.kpis.conversao}%`} comparacao={dados.kpis.comparacoes.conversao} /></section>
      <section className="grid gap-6 lg:grid-cols-3"><div className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Evolução temporal</h2><div className="mt-4 space-y-2 text-sm">{dados.serie_temporal.slice(-12).map((item) => <div key={item.periodo} className="grid grid-cols-4 gap-2 border-b pb-2"><span>{item.periodo}</span><span>{item.volume} vendas</span><span>{item.conversao}%</span><span>{item.perdas} perdas</span></div>)}</div></div><div className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Comparação por UF</h2><div className="mt-4"><Barras itens={dados.rankings.uf || []} /></div></div><div className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Distribuição por produto</h2><div className="mt-4"><Barras items={dados.rankings.produto || []} /></div></div></section>
      <section className="grid gap-6 lg:grid-cols-2"><div className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Oportunidades e inatividade</h2><div className="mt-4 grid grid-cols-2 gap-4"><Card titulo="Perdidas" valor={String(dados.oportunidades_perdidas.quantidade)} /><Card titulo="Valor perdido" valor={dados.oportunidades_perdidas.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} /></div><h3 className="mt-5 font-medium">Clientes inativos</h3><div className="mt-2 max-h-64 overflow-auto text-sm">{dados.clientes_inativos.map((c) => <div key={c.nome} className="flex justify-between border-b py-2"><span>{c.nome}</span><strong>{c.dias_sem_compra} dias</strong></div>)}</div></div><div className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Heat map estratégico</h2><div className="mt-4 space-y-2 text-sm">{heatmap.map(([chave, quantidade]) => <div key={chave} className="flex justify-between rounded bg-slate-100 p-2"><span>{chave}</span><strong>{quantidade}</strong></div>)}</div></div></section>
      <section className="rounded-xl border bg-white p-5"><h2 className="font-semibold">Drill-down comercial</h2><div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">{dimensoes.map((d) => <div key={d}><h3 className="mb-2 text-sm font-medium capitalize">{d}</h3><div className="max-h-52 overflow-auto text-xs">{(dados.drilldown[d] || []).slice(0, 15).map((item) => <button key={item.nome} onClick={() => { const novo = { ...edicao, [d]: item.nome }; setEdicao(novo); setFiltros(novo); setNivel(dimensoes.filter((x) => novo[x]).map(String)) }} className="flex w-full justify-between border-b py-2 text-left hover:bg-blue-50"><span className="truncate pr-2">{item.nome}</span><strong>{item.quantidade}</strong></button>)}</div></div>)}</div></section>
      <section className="rounded-xl border bg-white p-4 text-sm text-slate-600">Origem: {dados.metadata.origem} · Contexto: {dados.metadata.contexto_operacional} · Segmento: {dados.metadata.segmento} · Atualização: {new Date(dados.metadata.ultima_atualizacao).toLocaleString("pt-BR")} · Potencial: {dados.potencial.status === "calculado" ? dados.potencial.valor?.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) : "fonte real ainda não disponível"}</section>
    </>}
  </div></main>
}
