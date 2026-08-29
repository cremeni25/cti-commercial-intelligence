"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useI18n } from "@/core/i18n/I18nContext"
import { useOperationalContext } from "@/context/OperationalContext"

const API_URL = "/api/cti"
const dims = ["regiao", "uf", "dealer", "implementadora", "cliente", "linha", "familia", "produto"] as const
type Dim = (typeof dims)[number]
type Option = { valor: string; contagem: number }
type Rank = { nome: string; quantidade: number; valor: number }
type Serie = { periodo: string; volume: number; valor: number; ticket_medio: number }
type Compare = { atual: number; anterior: number; diferenca: number; percentual: number; direcao: string }
type Competitive = { categoria: string; quantidade: number; participacao_mercado_percentual: number; participacao_classificados_percentual: number }
type Cause = { causa: string; quantidade: number; participacao_percentual: number }
type OriginalReason = { motivo: string; quantidade: number; participacao_motivos_percentual: number }
type ObservationTheme = { tema: string; ocorrencias: number; clientes_distintos: number }
type Priority = {
  cliente: string
  score_prioridade: number
  volume: number
  meses_com_ocorrencia: number
  segmentos: { nome: string; quantidade: number }[]
  categorias_competitivas: { nome: string; quantidade: number }[]
  causas: { nome: string; quantidade: number }[]
  implementadoras: { nome: string; quantidade: number }[]
}
type MarketIntel = {
  mercado: { volume: number; comparacao: Compare; competencia_min: string | null; competencia_max: string | null }
  competitividade: {
    registros_classificados: number
    cobertura_classificacao_percentual: number
    distribuicao: Competitive[]
    carrier_observado: { quantidade: number; participacao_observada_percentual: number; natureza: string; nao_e: string }
  }
  causas_estrategicas: Cause[]
  motivos_originais: OriginalReason[]
  cobertura_comercial: { nao_participamos_proposta: number; sem_contato: number; concorrencia_direta_observada: number; percentual_nao_participacao: number }
  inteligencia_observacoes: { temas: ObservationTheme[]; metodo: string }
  prioridades_recuperacao: Priority[]
  avisos_metodologicos: string[]
}
type Data = {
  metadata: { contexto_operacional: string; segmento: string; ultima_atualizacao: string; origem: string; natureza_dados?: string }
  kpis: { volume: number; valor: number; ticket_medio: number }
  resumo?: { clientes_unicos?: number }
  rankings: Record<string, Rank[]>
  serie_temporal: Serie[]
  empty_state: string | null
  inteligencia_mercado?: MarketIntel
}
type SegmentCode = "TR" | "DT" | "DD"
type LocalFilters = Record<Dim, string> & { segmento: string; comparacao: string }

const initial: LocalFilters = { segmento: "GERAL", comparacao: "PERIODO_ANTERIOR", regiao: "", uf: "", dealer: "", implementadora: "", cliente: "", linha: "", familia: "", produto: "" }
const segmentNames: Record<SegmentCode, string> = { TR: "Trailer", DT: "Diesel Truck", DD: "Direct Drive" }
const categoryNames: Record<string, Record<string, string>> = {
  "pt-BR": { CARRIER: "Carrier", TK: "Thermo King", NACIONAL: "Nacionais", USADO_CARRIER: "Usado Carrier", USADO_CONCORRENTE: "Usado concorrente", SEM_CONTATO: "Sem contato", OUTROS: "Outros", NAO_CLASSIFICADO: "Não classificado" },
  en: { CARRIER: "Carrier", TK: "Thermo King", NACIONAL: "Domestic brands", USADO_CARRIER: "Used Carrier", USADO_CONCORRENTE: "Used competitor", SEM_CONTATO: "No contact", OUTROS: "Other", NAO_CLASSIFICADO: "Unclassified" },
  es: { CARRIER: "Carrier", TK: "Thermo King", NACIONAL: "Nacionales", USADO_CARRIER: "Carrier usado", USADO_CONCORRENTE: "Competidor usado", SEM_CONTATO: "Sin contacto", OUTROS: "Otros", NAO_CLASSIFICADO: "No clasificado" },
}
const causeNames: Record<string, Record<string, string>> = {
  "pt-BR": { COBERTURA_COMERCIAL: "Cobertura comercial / não participação", SEM_CONTATO: "Sem contato", RELACIONAMENTO: "Relacionamento", PRECO_VALOR: "Preço / valor", CONDICAO_FINANCEIRA: "Condição financeira", TECNICO_PRODUTO: "Produto / técnico", USADO_REAPROVEITAMENTO: "Usado / reaproveitamento", OUTRA_CAUSA_ESTRUTURADA: "Outra causa estruturada", SEM_CAUSA_ESTRUTURADA: "Sem causa estruturada" },
  en: { COBERTURA_COMERCIAL: "Commercial coverage / no participation", SEM_CONTATO: "No contact", RELACIONAMENTO: "Relationship", PRECO_VALOR: "Price / value", CONDICAO_FINANCEIRA: "Financial terms", TECNICO_PRODUTO: "Product / technical", USADO_REAPROVEITAMENTO: "Used / reuse", OUTRA_CAUSA_ESTRUTURADA: "Other structured cause", SEM_CAUSA_ESTRUTURADA: "No structured cause" },
  es: { COBERTURA_COMERCIAL: "Cobertura comercial / sin participación", SEM_CONTATO: "Sin contacto", RELACIONAMENTO: "Relación", PRECO_VALOR: "Precio / valor", CONDICAO_FINANCEIRA: "Condición financiera", TECNICO_PRODUTO: "Producto / técnico", USADO_REAPROVEITAMENTO: "Usado / reaprovechamiento", OUTRA_CAUSA_ESTRUTURADA: "Otra causa estructurada", SEM_CAUSA_ESTRUTURADA: "Sin causa estructurada" },
}
const themeNames: Record<string, Record<string, string>> = {
  "pt-BR": { CONCORRENTE_TK: "Thermo King", CONCORRENTE_NACIONAL: "Concorrente nacional", IMPLEMENTADORA_INTEGRADA: "Implementadora integrada", PRECO_VALOR: "Preço / valor", RELACIONAMENTO: "Relacionamento / visita", TECNICO_PRODUTO: "Produto / técnico", USADO_REAPROVEITAMENTO: "Usado / reaproveitamento", POS_VENDA_MANUTENCAO: "Pós-venda / manutenção", TESTE_DEMO: "Teste / demonstração", CONTEXTO_LIVRE: "Contexto livre" },
  en: { CONCORRENTE_TK: "Thermo King", CONCORRENTE_NACIONAL: "Domestic competitor", IMPLEMENTADORA_INTEGRADA: "Integrated Body Builder", PRECO_VALOR: "Price / value", RELACIONAMENTO: "Relationship / visit", TECNICO_PRODUTO: "Product / technical", USADO_REAPROVEITAMENTO: "Used / reuse", POS_VENDA_MANUTENCAO: "After-sales / maintenance", TESTE_DEMO: "Test / demo", CONTEXTO_LIVRE: "Free context" },
  es: { CONCORRENTE_TK: "Thermo King", CONCORRENTE_NACIONAL: "Competidor nacional", IMPLEMENTADORA_INTEGRADA: "Carrocero integrado", PRECO_VALOR: "Precio / valor", RELACIONAMENTO: "Relación / visita", TECNICO_PRODUTO: "Producto / técnico", USADO_REAPROVEITAMENTO: "Usado / reaprovechamiento", POS_VENDA_MANUTENCAO: "Posventa / mantenimiento", TESTE_DEMO: "Prueba / demostración", CONTEXTO_LIVRE: "Contexto libre" },
}
const text = {
  "pt-BR": { eyebrow: "LEITURA DE MERCADO ANFIR", title: "Inteligência de Mercado", intro: "Mercado realizado ANFIR, separado do Funil e do CRM operacional.", evidence: "ANFIR = mercado realizado · CRM = operação comercial · Funil = oportunidades", segment: "Segmento", comparison: "Comparação", previous: "Período anterior", previousYear: "Ano anterior", none: "Sem comparação", all: "Todos", apply: "Aplicar filtros", clear: "Limpar", csv: "Exportar CSV", xlsx: "Exportar XLSX", loading: "Carregando inteligência de mercado...", retrying: "Reconectando ao núcleo analítico...", failed: "Não foi possível carregar a inteligência de mercado.", retry: "Tentar novamente", executive: "Leitura executiva", market: "Mercado no período", trend: "Tendência", carrier: "Presença Carrier observada", coverage: "Cobertura da classificação", records: "registros", classified: "classificados", growth: "crescimento", decline: "retração", stable: "estável", segments: "Comparativo dos três segmentos", direct: "Concorrência direta", noParticipation: "Não participamos", noContact: "Sem contato", competitive: "Panorama competitivo observado", causes: "Por que estamos perdendo espaço", reasons: "Motivos originais Carrier", observations: "Sinais das observações", priorities: "Onde agir primeiro", account: "Cliente", score: "Prioridade", occurrences: "Ocorrências", scenario: "Cenário", cause: "Causa principal", bodyBuilder: "Implementadora", evolution: "Evolução mensal", bodyBuilders: "Implementadoras com maior volume", accounts: "Clientes com maior volume", methodology: "Critérios metodológicos", source: "Origem", updated: "Atualização", noData: "Sem dados", filters: "Filtros analíticos", global: "Território e período são controlados no topo do CTI." },
  en: { eyebrow: "ANFIR MARKET READING", title: "Market Intelligence", intro: "Realized ANFIR market, separated from Funnel and operational CRM.", evidence: "ANFIR = realized market · CRM = commercial operation · Funnel = opportunities", segment: "Segment", comparison: "Comparison", previous: "Previous period", previousYear: "Previous year", none: "No comparison", all: "All", apply: "Apply filters", clear: "Clear", csv: "Export CSV", xlsx: "Export XLSX", loading: "Loading market intelligence...", retrying: "Reconnecting to analytics core...", failed: "Market intelligence could not be loaded.", retry: "Try again", executive: "Executive reading", market: "Market in period", trend: "Trend", carrier: "Observed Carrier presence", coverage: "Classification coverage", records: "records", classified: "classified", growth: "growth", decline: "decline", stable: "stable", segments: "Three-segment comparison", direct: "Direct competition", noParticipation: "No participation", noContact: "No contact", competitive: "Observed competitive landscape", causes: "Why we are losing space", reasons: "Original Carrier reasons", observations: "Signals from notes", priorities: "Where to act first", account: "Account", score: "Priority", occurrences: "Occurrences", scenario: "Scenario", cause: "Main cause", bodyBuilder: "Body Builder", evolution: "Monthly evolution", bodyBuilders: "Body Builders with highest volume", accounts: "Accounts with highest volume", methodology: "Methodological criteria", source: "Source", updated: "Updated", noData: "No data", filters: "Analytical filters", global: "Territory and period are controlled at the top of CTI." },
  es: { eyebrow: "LECTURA DE MERCADO ANFIR", title: "Inteligencia de Mercado", intro: "Mercado realizado ANFIR, separado del Embudo y del CRM operativo.", evidence: "ANFIR = mercado realizado · CRM = operación comercial · Embudo = oportunidades", segment: "Segmento", comparison: "Comparación", previous: "Período anterior", previousYear: "Año anterior", none: "Sin comparación", all: "Todos", apply: "Aplicar filtros", clear: "Limpiar", csv: "Exportar CSV", xlsx: "Exportar XLSX", loading: "Cargando inteligencia de mercado...", retrying: "Reconectando al núcleo analítico...", failed: "No fue posible cargar la inteligencia de mercado.", retry: "Intentar nuevamente", executive: "Lectura ejecutiva", market: "Mercado en el período", trend: "Tendencia", carrier: "Presencia Carrier observada", coverage: "Cobertura de clasificación", records: "registros", classified: "clasificados", growth: "crecimiento", decline: "retracción", stable: "estável", segments: "Comparativo de los tres segmentos", direct: "Competencia directa", noParticipation: "No participamos", noContact: "Sin contacto", competitive: "Panorama competitivo observado", causes: "Por qué estamos perdiendo espacio", reasons: "Motivos originales Carrier", observations: "Señales de observaciones", priorities: "Dónde actuar primero", account: "Cliente", score: "Prioridad", occurrences: "Ocurrencias", scenario: "Escenario", cause: "Causa principal", bodyBuilder: "Carrocero", evolution: "Evolución mensual", bodyBuilders: "Carroceros con mayor volume", accounts: "Clientes con mayor volume", methodology: "Criterios metodológicos", source: "Origen", updated: "Actualización", noData: "Sin datos", filters: "Filtros analíticos", global: "Territorio y período se controlan en la parte superior de CTI." },
} as const

function queryString(base: string, filters: LocalFilters, segmento = filters.segmento) {
  const params = new URLSearchParams(base)
  params.set("segmento", segmento)
  params.set("comparacao", filters.comparacao)
  for (const dim of dims) if (filters[dim]) params.set(dim, filters[dim])
  return params.toString()
}
async function getJson<T>(url: string): Promise<T> {
  let last: unknown = null
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(url, { cache: "no-store" })
      const payload = await response.json().catch(() => null)
      if (response.ok) return payload as T
      last = new Error(payload?.detail || `CTI ${response.status}`)
      if (![502, 503, 504].includes(response.status)) break
    } catch (error) { last = error }
    if (attempt < 2) await new Promise(resolve => window.setTimeout(resolve, 700 * (attempt + 1)))
  }
  throw last instanceof Error ? last : new Error("CTI indisponível")
}
function pct(value: number) { return `${value > 0 ? "+" : ""}${Number(value || 0).toFixed(1)}%` }
function direction(value: string, tx: typeof text["pt-BR"] | typeof text.en | typeof text.es) { return value === "alta" ? tx.growth : value === "queda" ? tx.decline : tx.stable }
function maxValue(items: { quantidade: number }[]) { return Math.max(1, ...items.map(item => item.quantidade)) }
function Bar({ label, value, max }: { label: string; value: number; max: number }) { return <div><div className="flex justify-between gap-3 text-sm text-slate-300"><span className="truncate">{label}</span><strong className="text-white">{value}</strong></div><div className="mt-1 h-2 rounded-full bg-[#13203f]"><div className="h-2 rounded-full bg-cyan-400" style={{ width: `${Math.max(value > 0 ? 4 : 0, value / max * 100)}%` }} /></div></div> }
function Kpi({ title, value, detail }: { title: string; value: string; detail?: string }) { return <div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><p className="text-xs uppercase tracking-wide text-slate-400">{title}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{value}</p>{detail && <p className="mt-2 text-xs text-slate-400">{detail}</p>}</div> }

export default function InteligenciaPage() {
  const { locale, formatDate, formatNumber } = useI18n()
  const { contextoAtual, queryString: globalQuery } = useOperationalContext()
  const tx = text[locale]
  const [edit, setEdit] = useState<LocalFilters>(initial)
  const [filters, setFilters] = useState<LocalFilters>(initial)
  const [data, setData] = useState<Data | null>(null)
  const [segments, setSegments] = useState<Record<SegmentCode, Data | null>>({ TR: null, DT: null, DD: null })
  const [options, setOptions] = useState<Record<string, Option[]>>({})
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestKey = useMemo(() => queryString(globalQuery, filters), [globalQuery, filters])

  async function load() {
    setLoading(true); setError(null); setRetrying(false)
    try {
      const [main, optionData] = await Promise.all([
        getJson<Data>(`${API_URL}/analytics/intelligence?${requestKey}`),
        getJson<{ opcoes: Record<string, Option[]> }>(`${API_URL}/analytics/intelligence/filter-options?${requestKey}`),
      ])
      setData(main); setOptions(optionData.opcoes || {})
      const results = await Promise.allSettled(((["TR", "DT", "DD"] as SegmentCode[])).map(code => getJson<Data>(`${API_URL}/analytics/intelligence?${queryString(globalQuery, filters, code)}`)))
      setSegments({ TR: results[0].status === "fulfilled" ? results[0].value : null, DT: results[1].status === "fulfilled" ? results[1].value : null, DD: results[2].status === "fulfilled" ? results[2].value : null })
    } catch (err) { setError(err instanceof Error ? err.message : tx.failed) }
    finally { setLoading(false); setRetrying(false) }
  }
  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer) }, [requestKey])

  function change(key: keyof LocalFilters, value: string) { const next = { ...edit, [key]: value }; if (key === "linha") { next.familia = ""; next.produto = "" }; if (key === "familia") next.produto = ""; setEdit(next) }
  function clear() { setEdit(initial); setFilters(initial) }
  function apply() { setFilters(edit) }
  function retry() { setRetrying(true); void load() }
  function exportFile(format: "csv" | "xlsx") { window.open(`${API_URL}/analytics/intelligence/export?${queryString(globalQuery, filters)}&formato=${format}`, "_blank") }

  const market = data?.inteligencia_mercado
  const comparison = market?.mercado.comparacao
  const competition = market?.competitividade.distribuicao || []
  const causes = market?.causas_estrategicas || []
  const reasons = market?.motivos_originais || []
  const themes = market?.inteligencia_observacoes.temas || []

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1 overflow-hidden"><Topbar/><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">{tx.eyebrow}</p><h1 className="mt-2 text-3xl font-bold">{tx.title}</h1><p className="mt-2 text-sm text-slate-400">{tx.intro}</p><p className="mt-2 text-sm text-cyan-300">{contextoAtual.label} — {contextoAtual.description}</p></header>
    <div className="rounded-2xl border border-cyan-900 bg-cyan-950/20 p-4 text-sm text-cyan-100">{tx.evidence}</div>
    <section className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><div className="mb-4"><h2 className="font-semibold">{tx.filters}</h2><p className="mt-1 text-xs text-slate-400">{tx.global}</p></div><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      <label className="text-xs text-slate-400">{tx.segment}<select className="mt-1 w-full rounded-lg border border-[#29456f] bg-[#0b1730] p-2 text-white" value={edit.segmento} onChange={e => change("segmento", e.target.value)}><option value="GERAL">GERAL</option><option value="TR">Trailer</option><option value="DT">Diesel Truck</option><option value="DD">Direct Drive</option><option value="UNKNOWN">UNKNOWN</option></select></label>
      <label className="text-xs text-slate-400">{tx.comparison}<select className="mt-1 w-full rounded-lg border border-[#29456f] bg-[#0b1730] p-2 text-white" value={edit.comparacao} onChange={e => change("comparacao", e.target.value)}><option value="PERIODO_ANTERIOR">{tx.previous}</option><option value="ANO_ANTERIOR">{tx.previousYear}</option><option value="SEM_COMPARACAO">{tx.none}</option></select></label>
      {dims.map(dim => <label className="text-xs capitalize text-slate-400" key={dim}>{dim}<select className="mt-1 w-full rounded-lg border border-[#29456f] bg-[#0b1730] p-2 text-white" value={edit[dim]} onChange={e => change(dim, e.target.value)}><option value="">{tx.all}</option>{(options[dim] || []).map(option => <option key={option.valor} value={option.valor}>{option.valor} ({option.contagem})</option>)}</select></label>)}
    </div><div className="mt-4 flex flex-wrap gap-2"><button onClick={apply} className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950">{tx.apply}</button><button onClick={clear} className="rounded-lg border border-[#29456f] px-4 py-2 text-sm text-slate-300">{tx.clear}</button><button onClick={() => exportFile("csv")} className="rounded-lg border border-[#29456f] px-4 py-2 text-sm text-slate-300">{tx.csv}</button><button onClick={() => exportFile("xlsx")} className="rounded-lg border border-[#29456f] px-4 py-2 text-sm text-slate-300">{tx.xlsx}</button></div></section>
    {loading && <div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-10 text-center text-slate-300">{retrying ? tx.retrying : tx.loading}</div>}
    {!loading && error && <div className="rounded-2xl border border-red-800 bg-red-950/20 p-5 text-red-200"><p>{tx.failed}</p><p className="mt-1 text-xs text-red-300">{error}</p><button onClick={retry} className="mt-4 rounded-lg border border-red-700 px-3 py-2 text-sm">{tx.retry}</button></div>}
    {!loading && !error && data?.empty_state && <div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-10 text-center text-slate-300">{data.empty_state}</div>}
    {!loading && !error && data && !data.empty_state && <>
      <section><h2 className="mb-3 text-xl font-semibold">{tx.executive}</h2><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi title={tx.market} value={`${formatNumber(market?.mercado.volume ?? data.kpis.volume)} ${tx.records}`} detail={comparison ? `${pct(comparison.percentual)} · ${direction(comparison.direcao, tx)}` : undefined}/><Kpi title={tx.trend} value={comparison ? direction(comparison.direcao, tx) : tx.noData} detail={comparison ? `${formatNumber(comparison.atual)} × ${formatNumber(comparison.anterior)}` : undefined}/><Kpi title={tx.carrier} value={`${(market?.competitividade.carrier_observado.participacao_observada_percentual ?? 0).toFixed(1)}%`} detail={`${formatNumber(market?.competitividade.carrier_observado.quantidade ?? 0)} ${tx.records}`}/><Kpi title={tx.coverage} value={`${(market?.competitividade.cobertura_classificacao_percentual ?? 0).toFixed(1)}%`} detail={`${formatNumber(market?.competitividade.registros_classificados ?? 0)} ${tx.classified}`}/></div></section>
      <section className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="text-xl font-semibold">{tx.segments}</h2><div className="mt-4 grid gap-4 xl:grid-cols-3">{(["TR","DT","DD"] as SegmentCode[]).map(code => { const intel = segments[code]?.inteligencia_mercado; const comp = intel?.mercado.comparacao; return <div key={code} className="rounded-xl border border-[#29456f] bg-[#0b1730] p-4"><p className="text-xs font-semibold text-cyan-400">{code}</p><h3 className="mt-1 text-lg font-semibold">{segmentNames[code]}</h3><div className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><span className="text-slate-400">{tx.market}</span><p className="font-bold">{formatNumber(intel?.mercado.volume ?? 0)}</p></div><div><span className="text-slate-400">{tx.carrier}</span><p className="font-bold">{(intel?.competitividade.carrier_observado.participacao_observada_percentual ?? 0).toFixed(1)}%</p></div><div><span className="text-slate-400">{tx.direct}</span><p className="font-bold">{formatNumber(intel?.cobertura_comercial.concorrencia_direta_observada ?? 0)}</p></div><div><span className="text-slate-400">{tx.noParticipation}</span><p className="font-bold">{formatNumber(intel?.cobertura_comercial.nao_participamos_proposta ?? 0)}</p></div></div>{comp && <p className="mt-4 text-xs text-slate-400">{pct(comp.percentual)} · {direction(comp.direcao, tx)}</p>}</div>})}</div></section>
      <section className="grid gap-5 xl:grid-cols-2"><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.competitive}</h2><div className="mt-4 space-y-4">{competition.filter(i=>i.quantidade>0).map(item => <Bar key={item.categoria} label={categoryNames[locale][item.categoria] || item.categoria} value={item.quantidade} max={maxValue(competition)} />)}</div></div><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.causes}</h2><div className="mt-4 space-y-4">{causes.slice(0,9).map(item => <Bar key={item.causa} label={causeNames[locale][item.causa] || item.causa} value={item.quantidade} max={maxValue(causes)} />)}</div></div></section>
      <section className="grid gap-4 md:grid-cols-3"><Kpi title={tx.noParticipation} value={formatNumber(market?.cobertura_comercial.nao_participamos_proposta ?? 0)} detail={`${(market?.cobertura_comercial.percentual_nao_participacao ?? 0).toFixed(1)}%`}/><Kpi title={tx.noContact} value={formatNumber(market?.cobertura_comercial.sem_contato ?? 0)}/><Kpi title={tx.direct} value={formatNumber(market?.cobertura_comercial.concorrencia_direta_observada ?? 0)}/></section>
      <section className="grid gap-5 xl:grid-cols-2"><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.reasons}</h2><div className="mt-4 space-y-4">{reasons.slice(0,10).map(item => <Bar key={item.motivo} label={item.motivo} value={item.quantidade} max={maxValue(reasons)} />)}</div></div><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.observations}</h2><div className="mt-4 space-y-4">{themes.slice(0,10).map(item => <Bar key={item.tema} label={`${themeNames[locale][item.tema] || item.tema} · ${item.clientes_distintos}`} value={item.ocorrencias} max={Math.max(1,...themes.map(t=>t.ocorrencias))} />)}</div></div></section>
      <section className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="text-xl font-semibold">{tx.priorities}</h2><div className="mt-4 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead className="text-xs uppercase text-slate-400"><tr className="border-b border-[#29456f]"><th className="py-3 pr-4">{tx.account}</th><th className="py-3 pr-4">{tx.score}</th><th className="py-3 pr-4">{tx.occurrences}</th><th className="py-3 pr-4">{tx.scenario}</th><th className="py-3 pr-4">{tx.cause}</th><th className="py-3">{tx.bodyBuilder}</th></tr></thead><tbody>{(market?.prioridades_recuperacao || []).slice(0,15).map(item => <tr key={item.cliente} className="border-b border-[#172744]"><td className="py-3 pr-4 font-medium">{item.cliente}</td><td className="py-3 pr-4 text-cyan-300">{item.score_prioridade}</td><td className="py-3 pr-4">{item.volume}</td><td className="py-3 pr-4">{categoryNames[locale][item.categorias_competitivas[0]?.nome] || item.categorias_competitivas[0]?.nome || tx.noData}</td><td className="py-3 pr-4">{causeNames[locale][item.causas[0]?.nome] || item.causas[0]?.nome || tx.noData}</td><td className="py-3">{item.implementadoras[0]?.nome || tx.noData}</td></tr>)}</tbody></table></div></section>
      <section className="grid gap-5 xl:grid-cols-3"><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.evolution}</h2><div className="mt-3 space-y-2 text-sm">{data.serie_temporal.slice(-12).map(item => <div key={item.periodo} className="flex justify-between border-b border-[#172744] py-2"><span className="text-slate-400">{item.periodo}</span><strong>{formatNumber(item.volume)}</strong></div>)}</div></div><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.bodyBuilders}</h2><div className="mt-4 space-y-4">{(data.rankings.implementadora || []).slice(0,10).map(item => <Bar key={item.nome} label={item.nome} value={item.quantidade} max={maxValue(data.rankings.implementadora || [])}/>)}</div></div><div className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.accounts}</h2><div className="mt-4 space-y-4">{(data.rankings.cliente || []).slice(0,10).map(item => <Bar key={item.nome} label={item.nome} value={item.quantidade} max={maxValue(data.rankings.cliente || [])}/>)}</div></div></section>
      <section className="rounded-2xl border border-[#1b2d50] bg-[#07142b] p-5"><h2 className="font-semibold">{tx.methodology}</h2><ul className="mt-3 space-y-2 text-sm text-slate-400">{(market?.avisos_metodologicos || []).map((notice,index)=><li key={`${index}-${notice}`}>• {notice}</li>)}</ul><p className="mt-4 text-xs text-slate-500">{tx.source}: {data.metadata.origem} · {tx.updated}: {formatDate(data.metadata.ultima_atualizacao,{dateStyle:"short",timeStyle:"short"})}</p></section>
    </>}
  </div></section></main>
}
