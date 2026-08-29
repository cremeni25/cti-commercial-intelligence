"use client"

import { useEffect, useMemo, useState } from "react"
import { useI18n } from "@/core/i18n/I18nContext"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://cti-backend-5ugf.onrender.com"
const dims = ["regiao", "uf", "dealer", "implementadora", "cliente", "linha", "familia", "produto"] as const
type Dim = (typeof dims)[number]
type Filters = Record<Dim, string> & { contexto: string; segmento: string; periodo: string; comparacao: string; inicio: string; fim: string }
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
  segmentos: Array<{ nome: string; quantidade: number }>
  categorias_competitivas: Array<{ nome: string; quantidade: number }>
  causas: Array<{ nome: string; quantidade: number }>
  implementadoras: Array<{ nome: string; quantidade: number }>
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
  metadata: { contexto_operacional: string; segmento: string; ultima_atualizacao: string; origem: string; natureza_dados?: string; motor_mercado?: string }
  kpis: { volume: number; valor: number; ticket_medio: number; comparacoes: Record<string, { percentual: number; direcao: string }> }
  resumo?: { clientes_unicos?: number }
  rankings: Record<string, Rank[]>
  serie_temporal: Serie[]
  clientes_sem_registro_recente?: Array<{ nome: string; dias_sem_registro: number | null }>
  heatmap: Array<{ regiao: string; uf: string }>
  drilldown: Record<string, Rank[]>
  empty_state: string | null
  inteligencia_mercado?: MarketIntel
}
type SegmentCode = "TR" | "DT" | "DD"

const initial: Filters = { contexto: "viena-sp", segmento: "GERAL", periodo: "ANO_ATUAL", comparacao: "PERIODO_ANTERIOR", inicio: "", fim: "", regiao: "", uf: "", dealer: "", implementadora: "", cliente: "", linha: "", familia: "", produto: "" }
const periodValues = ["HOJE", "ULTIMOS_7_DIAS", "ULTIMOS_30_DIAS", "ULTIMOS_90_DIAS", "MES_ATUAL", "TRIMESTRE_ATUAL", "ANO_ATUAL", "PERSONALIZADO"]

const ui = {
  "pt-BR": {
    eyebrow: "CTI · inteligência ANFIR", title: "Inteligência de Mercado", intro: "Leitura executiva do mercado realizado ANFIR, separada do Funil e do CRM operacional.",
    separation: "ANFIR = mercado realizado. CRM = operação comercial. Funil = oportunidades. A análise correlaciona as camadas sem fundir registros.",
    context: "Contexto", segment: "Segmento", period: "Período", comparison: "Comparação", start: "Início", end: "Fim", all: "Todos",
    apply: "Aplicar filtros", clear: "Limpar", exportCsv: "Exportar CSV", exportXlsx: "Exportar XLSX", loading: "Carregando inteligência de mercado...", loadError: "Falha ao carregar",
    brazil: "Brasil", vienna: "VIENA SP", others: "Outros Dealers", noComparison: "Sem comparação", previousPeriod: "Período anterior", previousYear: "Ano anterior",
    periods: ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Mês atual", "Trimestre atual", "Ano atual", "Personalizado"],
    executive: "Leitura executiva", marketVolume: "Mercado no período", trend: "Tendência de mercado", carrierPresence: "Presença Carrier observada", classificationCoverage: "Cobertura da classificação",
    growth: "crescimento", decline: "retração", stable: "estável", versus: "vs. período comparado", records: "registros", classified: "classificados",
    segmentsTitle: "Os três segmentos", segmentsHelp: "Comparação simultânea de Trailer, Diesel Truck e Direct Drive no mesmo contexto e período.",
    market: "Mercado", carrier: "Carrier observada", directCompetition: "Concorrência direta", noParticipation: "Não participamos", noContact: "Sem contato",
    competitive: "Panorama competitivo observado", competitiveHelp: "Distribuição dos fatos ANFIR classificados. Não representa market share contábil reconciliado.",
    causes: "Por que estamos perdendo espaço", causesHelp: "Causas estratégicas derivadas dos motivos e observações originais, sem substituir o texto fonte.",
    originalReasons: "Motivos originais Carrier", observations: "Sinais das observações", opportunities: "Onde agir primeiro", opportunitiesHelp: "Prioridades de recuperação calculadas por volume, categoria competitiva e causa estratégica.",
    client: "Cliente", score: "Prioridade", occurrences: "Ocorrências", mainCause: "Causa principal", competitor: "Cenário", implementer: "Implementadora", months: "meses",
    evolution: "Evolução mensal do mercado", implementers: "Implementadoras com maior volume", clients: "Clientes com maior volume", methodological: "Critérios metodológicos",
    source: "Origem", nature: "Natureza", updated: "Atualização", backend: "Backend respondeu", recordsLabel: "Registros realizados", customersHistorical: "Clientes observados",
    currencyRecorded: "Valor registrado", avgTicket: "Ticket médio histórico", unknown: "Não classificado", notAvailable: "Sem dados", evidence: "Evidência ANFIR realizada",
  },
  en: {
    eyebrow: "CTI · ANFIR intelligence", title: "Market Intelligence", intro: "Executive reading of realized ANFIR market facts, separated from Funnel and operational CRM.",
    separation: "ANFIR = realized market. CRM = commercial operations. Funnel = opportunities. Analysis correlates layers without merging records.",
    context: "Context", segment: "Segment", period: "Period", comparison: "Comparison", start: "Start", end: "End", all: "All",
    apply: "Apply filters", clear: "Clear", exportCsv: "Export CSV", exportXlsx: "Export XLSX", loading: "Loading market intelligence...", loadError: "Failed to load",
    brazil: "Brazil", vienna: "VIENA SP", others: "Other Dealers", noComparison: "No comparison", previousPeriod: "Previous period", previousYear: "Previous year",
    periods: ["Today", "Last 7 days", "Last 30 days", "Last 90 days", "Current month", "Current quarter", "Current year", "Custom"],
    executive: "Executive reading", marketVolume: "Market in period", trend: "Market trend", carrierPresence: "Observed Carrier presence", classificationCoverage: "Classification coverage",
    growth: "growth", decline: "decline", stable: "stable", versus: "vs. comparison period", records: "records", classified: "classified",
    segmentsTitle: "Three segments", segmentsHelp: "Side-by-side view of Trailer, Diesel Truck and Direct Drive in the same context and period.",
    market: "Market", carrier: "Observed Carrier", directCompetition: "Direct competition", noParticipation: "No participation", noContact: "No contact",
    competitive: "Observed competitive landscape", competitiveHelp: "Distribution of classified ANFIR facts. This is not reconciled accounting market share.",
    causes: "Why we are losing space", causesHelp: "Strategic causes derived from original reasons and notes without replacing source text.",
    originalReasons: "Original Carrier reasons", observations: "Signals from notes", opportunities: "Where to act first", opportunitiesHelp: "Recovery priorities calculated from volume, competitive category and strategic cause.",
    client: "Account", score: "Priority", occurrences: "Occurrences", mainCause: "Main cause", competitor: "Scenario", implementer: "Body Builder", months: "months",
    evolution: "Monthly market evolution", implementers: "Body Builders with highest volume", clients: "Accounts with highest volume", methodological: "Methodological criteria",
    source: "Source", nature: "Nature", updated: "Updated", backend: "Backend returned", recordsLabel: "Realized records", customersHistorical: "Observed accounts",
    currencyRecorded: "Recorded value", avgTicket: "Historical average ticket", unknown: "Unclassified", notAvailable: "No data", evidence: "Realized ANFIR evidence",
  },
  es: {
    eyebrow: "CTI · inteligencia ANFIR", title: "Inteligencia de Mercado", intro: "Lectura ejecutiva del mercado realizado ANFIR, separada del Embudo y del CRM operativo.",
    separation: "ANFIR = mercado realizado. CRM = operación comercial. Embudo = oportunidades. El análisis correlaciona las capas sin fusionar registros.",
    context: "Contexto", segment: "Segmento", period: "Período", comparison: "Comparación", start: "Inicio", end: "Fin", all: "Todos",
    apply: "Aplicar filtros", clear: "Limpiar", exportCsv: "Exportar CSV", exportXlsx: "Exportar XLSX", loading: "Cargando inteligencia de mercado...", loadError: "Error al cargar",
    brazil: "Brasil", vienna: "VIENA SP", others: "Otros Dealers", noComparison: "Sin comparación", previousPeriod: "Período anterior", previousYear: "Año anterior",
    periods: ["Hoy", "Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Mes actual", "Trimestre actual", "Año actual", "Personalizado"],
    executive: "Lectura ejecutiva", marketVolume: "Mercado en el período", trend: "Tendencia de mercado", carrierPresence: "Presencia Carrier observada", classificationCoverage: "Cobertura de clasificación",
    growth: "crecimiento", decline: "retracción", stable: "estable", versus: "vs. período comparado", records: "registros", classified: "clasificados",
    segmentsTitle: "Los tres segmentos", segmentsHelp: "Comparación simultánea de Trailer, Diesel Truck y Direct Drive en el mismo contexto y período.",
    market: "Mercado", carrier: "Carrier observada", directCompetition: "Competencia directa", noParticipation: "No participamos", noContact: "Sin contacto",
    competitive: "Panorama competitivo observado", competitiveHelp: "Distribución de hechos ANFIR clasificados. No representa market share contable reconciliado.",
    causes: "Por qué estamos perdiendo espacio", causesHelp: "Causas estratégicas derivadas de motivos y observaciones originales, sin sustituir el texto fuente.",
    originalReasons: "Motivos originales Carrier", observations: "Señales de observaciones", opportunities: "Dónde actuar primero", opportunitiesHelp: "Prioridades de recuperación calculadas por volumen, categoría competitiva y causa estratégica.",
    client: "Cliente", score: "Prioridad", occurrences: "Ocurrencias", mainCause: "Causa principal", competitor: "Escenario", implementer: "Carrocero", months: "meses",
    evolution: "Evolución mensual del mercado", implementers: "Carroceros con mayor volumen", clients: "Clientes con mayor volumen", methodological: "Criterios metodológicos",
    source: "Origen", nature: "Naturaleza", updated: "Actualización", backend: "Backend respondió", recordsLabel: "Registros realizados", customersHistorical: "Clientes observados",
    currencyRecorded: "Valor registrado", avgTicket: "Ticket medio histórico", unknown: "No clasificado", notAvailable: "Sin datos", evidence: "Evidencia ANFIR realizada",
  },
} as const

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
const segmentNames: Record<SegmentCode, string> = { TR: "Trailer", DT: "Diesel Truck", DD: "Direct Drive" }

function qs(filters: Filters, extra: Record<string, string> = {}) {
  const p = new URLSearchParams()
  Object.entries({ ...filters, ...extra }).forEach(([key, value]) => { if (value) p.set(key, value) })
  return p.toString()
}
function pct(value: number) { return `${value > 0 ? "+" : ""}${Number(value || 0).toFixed(1)}%` }
function trendLabel(direction: string, c: typeof ui["pt-BR"]) { return direction === "alta" ? c.growth : direction === "queda" ? c.decline : c.stable }
function barWidth(value: number, max: number) { return `${Math.max(value > 0 ? 4 : 0, max ? value / max * 100 : 0)}%` }

function MetricCard({ title, value, detail }: { title: string; value: string; detail?: string }) {
  return <div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{title}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>{detail && <p className="mt-2 text-xs text-slate-500">{detail}</p>}</div>
}
function MiniBar({ label, value, max, suffix = "" }: { label: string; value: number; max: number; suffix?: string }) {
  return <div><div className="flex items-center justify-between gap-3 text-sm"><span className="truncate">{label}</span><strong>{value}{suffix}</strong></div><div className="mt-1 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-blue-600" style={{ width: barWidth(value, max) }} /></div></div>
}

export default function InteligenciaPage() {
  const { locale, formatCurrency, formatDate, formatNumber } = useI18n()
  const lang = locale === "pt-BR" ? "pt-BR" : locale === "en" ? "en" : "es"
  const c = ui[lang]
  const [edit, setEdit] = useState<Filters>(initial)
  const [filters, setFilters] = useState<Filters>(initial)
  const [data, setData] = useState<Data | null>(null)
  const [segments, setSegments] = useState<Record<SegmentCode, Data | null>>({ TR: null, DT: null, DD: null })
  const [options, setOptions] = useState<Record<string, Option[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const query = useMemo(() => qs(filters), [filters])

  useEffect(() => {
    const controller = new AbortController()
    const base = { cache: "no-store" as RequestCache, signal: controller.signal }
    const intelligence = (segmento: string) => fetch(`${API_URL}/analytics/intelligence?${qs({ ...filters, segmento })}`, base)
    Promise.all([
      intelligence(filters.segmento),
      fetch(`${API_URL}/analytics/intelligence/filter-options?${query}`, base),
      intelligence("TR"), intelligence("DT"), intelligence("DD"),
    ]).then(async ([main, opts, tr, dt, dd]) => {
      if (![main, opts, tr, dt, dd].every(response => response.ok)) throw new Error(`${c.backend} ${[main, opts, tr, dt, dd].map(r => r.status).join("/")}`)
      const [mainData, optionData, trData, dtData, ddData] = await Promise.all([main.json(), opts.json(), tr.json(), dt.json(), dd.json()])
      setData(mainData)
      setOptions(optionData.opcoes || {})
      setSegments({ TR: trData, DT: dtData, DD: ddData })
      setError(null)
    }).catch((err: unknown) => {
      if (err instanceof DOMException && err.name === "AbortError") return
      setError(err instanceof Error ? err.message : c.loadError)
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [c.backend, c.loadError, filters, query])

  function change(key: keyof Filters, value: string) {
    const next = { ...edit, [key]: value }
    if (key === "linha") { next.familia = ""; next.produto = "" }
    if (key === "familia") next.produto = ""
    setEdit(next)
  }
  function apply() { setLoading(true); setFilters(edit) }
  function clear() { setLoading(true); setEdit(initial); setFilters(initial) }
  function exportFile(format: "csv" | "xlsx") { window.open(`${API_URL}/analytics/intelligence/export?${qs(filters, { formato: format })}`, "_blank") }

  const market = data?.inteligencia_mercado
  const comparison = market?.mercado.comparacao
  const competitiveMax = Math.max(1, ...(market?.competitividade.distribuicao || []).map(item => item.quantidade))
  const causesMax = Math.max(1, ...(market?.causas_estrategicas || []).map(item => item.quantidade))
  const reasonsMax = Math.max(1, ...(market?.motivos_originais || []).map(item => item.quantidade))
  const themesMax = Math.max(1, ...(market?.inteligencia_observacoes.temas || []).map(item => item.ocorrencias))

  return <main className="min-h-screen bg-slate-50 p-4 md:p-8"><div className="mx-auto max-w-7xl space-y-6">
    <header><p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">{c.eyebrow}</p><h1 className="mt-1 text-3xl font-bold text-slate-950">{c.title}</h1><p className="mt-2 max-w-4xl text-slate-600">{c.intro}</p></header>
    <section className="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-950"><strong>{c.evidence}:</strong> {c.separation}</section>

    <section className="rounded-2xl border bg-white p-5 shadow-sm"><div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <label className="text-sm">{c.context}<select className="mt-1 w-full rounded-lg border p-2" value={edit.contexto} onChange={e => change("contexto", e.target.value)}><option value="brasil">{c.brazil}</option><option value="viena-sp">{c.vienna}</option><option value="outros-dealers">{c.others}</option></select></label>
      <label className="text-sm">{c.segment}<select className="mt-1 w-full rounded-lg border p-2" value={edit.segmento} onChange={e => change("segmento", e.target.value)}><option value="GERAL">GERAL</option><option value="TR">Trailer</option><option value="DT">Diesel Truck</option><option value="DD">Direct Drive</option><option value="UNKNOWN">{c.unknown}</option></select></label>
      <label className="text-sm">{c.period}<select className="mt-1 w-full rounded-lg border p-2" value={edit.periodo} onChange={e => change("periodo", e.target.value)}>{periodValues.map((value, index) => <option value={value} key={value}>{c.periods[index]}</option>)}</select></label>
      <label className="text-sm">{c.comparison}<select className="mt-1 w-full rounded-lg border p-2" value={edit.comparacao} onChange={e => change("comparacao", e.target.value)}><option value="SEM_COMPARACAO">{c.noComparison}</option><option value="PERIODO_ANTERIOR">{c.previousPeriod}</option><option value="ANO_ANTERIOR">{c.previousYear}</option></select></label>
      {edit.periodo === "PERSONALIZADO" && <><label className="text-sm">{c.start}<input type="date" className="mt-1 w-full rounded-lg border p-2" value={edit.inicio} onChange={e => change("inicio", e.target.value)} /></label><label className="text-sm">{c.end}<input type="date" className="mt-1 w-full rounded-lg border p-2" value={edit.fim} onChange={e => change("fim", e.target.value)} /></label></>}
      {dims.map(dim => <label className="text-sm capitalize" key={dim}>{dim}<select className="mt-1 w-full rounded-lg border p-2" value={edit[dim]} onChange={e => change(dim, e.target.value)}><option value="">{c.all}</option>{(options[dim] || []).map(option => <option key={option.valor} value={option.valor}>{option.valor} ({option.contagem})</option>)}</select></label>)}
    </div><div className="mt-4 flex flex-wrap gap-2"><button onClick={apply} className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-medium text-white">{c.apply}</button><button onClick={clear} className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-medium">{c.clear}</button><button onClick={() => exportFile("csv")} className="rounded-lg border px-4 py-2 text-sm">{c.exportCsv}</button><button onClick={() => exportFile("xlsx")} className="rounded-lg border px-4 py-2 text-sm">{c.exportXlsx}</button></div></section>

    {loading && <div className="rounded-2xl border bg-white p-10 text-center">{c.loading}</div>}
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800">{error}</div>}
    {!loading && data?.empty_state && <div className="rounded-2xl border bg-white p-10 text-center">{data.empty_state}</div>}

    {!loading && data && !data.empty_state && <>
      <section><div className="mb-3"><h2 className="text-xl font-semibold">{c.executive}</h2></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title={c.marketVolume} value={`${formatNumber(market?.mercado.volume ?? data.kpis.volume)} ${c.records}`} detail={comparison ? `${pct(comparison.percentual)} ${c.versus}` : undefined} />
        <MetricCard title={c.trend} value={comparison ? trendLabel(comparison.direcao, c) : c.notAvailable} detail={comparison ? `${formatNumber(comparison.atual)} × ${formatNumber(comparison.anterior)} ${c.records}` : undefined} />
        <MetricCard title={c.carrierPresence} value={`${market?.competitividade.carrier_observado.participacao_observada_percentual.toFixed(1) ?? "0.0"}%`} detail={`${formatNumber(market?.competitividade.carrier_observado.quantidade ?? 0)} ${c.records}`} />
        <MetricCard title={c.classificationCoverage} value={`${market?.competitividade.cobertura_classificacao_percentual.toFixed(1) ?? "0.0"}%`} detail={`${formatNumber(market?.competitividade.registros_classificados ?? 0)} ${c.classified}`} />
      </div></section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm"><h2 className="text-xl font-semibold">{c.segmentsTitle}</h2><p className="mt-1 text-sm text-slate-500">{c.segmentsHelp}</p><div className="mt-5 grid gap-4 lg:grid-cols-3">{(["TR", "DT", "DD"] as SegmentCode[]).map(code => {
        const item = segments[code]?.inteligencia_mercado
        const comp = item?.mercado.comparacao
        return <div key={code} className="rounded-xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{code}</p><h3 className="text-lg font-semibold">{segmentNames[code]}</h3></div><span className={`rounded-full px-2 py-1 text-xs font-medium ${comp?.direcao === "alta" ? "bg-emerald-50 text-emerald-700" : comp?.direcao === "queda" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-600"}`}>{comp ? `${pct(comp.percentual)} · ${trendLabel(comp.direcao, c)}` : c.notAvailable}</span></div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><p className="text-slate-500">{c.market}</p><strong>{formatNumber(item?.mercado.volume ?? 0)}</strong></div><div><p className="text-slate-500">{c.carrier}</p><strong>{(item?.competitividade.carrier_observado.participacao_observada_percentual ?? 0).toFixed(1)}%</strong></div><div><p className="text-slate-500">{c.directCompetition}</p><strong>{formatNumber(item?.cobertura_comercial.concorrencia_direta_observada ?? 0)}</strong></div><div><p className="text-slate-500">{c.noParticipation}</p><strong>{formatNumber(item?.cobertura_comercial.nao_participamos_proposta ?? 0)}</strong></div></div>
        </div>
      })}</div></section>

      <section className="grid gap-6 lg:grid-cols-2"><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.competitive}</h2><p className="mt-1 text-sm text-slate-500">{c.competitiveHelp}</p><div className="mt-5 space-y-4">{(market?.competitividade.distribuicao || []).filter(item => item.quantidade > 0).map(item => <MiniBar key={item.categoria} label={categoryNames[lang][item.categoria] || item.categoria} value={item.quantidade} max={competitiveMax} />)}</div></div>
        <div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.causes}</h2><p className="mt-1 text-sm text-slate-500">{c.causesHelp}</p><div className="mt-5 space-y-4">{(market?.causas_estrategicas || []).slice(0, 9).map(item => <MiniBar key={item.causa} label={causeNames[lang][item.causa] || item.causa} value={item.quantidade} max={causesMax} />)}</div></div></section>

      <section className="grid gap-6 lg:grid-cols-3"><MetricCard title={c.noParticipation} value={formatNumber(market?.cobertura_comercial.nao_participamos_proposta ?? 0)} detail={`${(market?.cobertura_comercial.percentual_nao_participacao ?? 0).toFixed(1)}%`} /><MetricCard title={c.noContact} value={formatNumber(market?.cobertura_comercial.sem_contato ?? 0)} /><MetricCard title={c.directCompetition} value={formatNumber(market?.cobertura_comercial.concorrencia_direta_observada ?? 0)} /></section>

      <section className="grid gap-6 lg:grid-cols-2"><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.originalReasons}</h2><div className="mt-5 space-y-4">{(market?.motivos_originais || []).slice(0, 10).map(item => <MiniBar key={item.motivo} label={item.motivo} value={item.quantidade} max={reasonsMax} />)}</div></div><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.observations}</h2><div className="mt-5 space-y-4">{(market?.inteligencia_observacoes.temas || []).slice(0, 10).map(item => <MiniBar key={item.tema} label={`${themeNames[lang][item.tema] || item.tema} · ${item.clientes_distintos} ${c.client.toLowerCase()}`} value={item.ocorrencias} max={themesMax} />)}</div></div></section>

      <section className="rounded-2xl border bg-white p-5"><h2 className="text-xl font-semibold">{c.opportunities}</h2><p className="mt-1 text-sm text-slate-500">{c.opportunitiesHelp}</p><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead><tr className="border-b text-xs uppercase tracking-wide text-slate-500"><th className="py-3 pr-4">{c.client}</th><th className="py-3 pr-4">{c.score}</th><th className="py-3 pr-4">{c.occurrences}</th><th className="py-3 pr-4">{c.competitor}</th><th className="py-3 pr-4">{c.mainCause}</th><th className="py-3">{c.implementer}</th></tr></thead><tbody>{(market?.prioridades_recuperacao || []).slice(0, 15).map(item => <tr key={item.cliente} className="border-b align-top"><td className="py-3 pr-4 font-medium">{item.cliente}</td><td className="py-3 pr-4"><span className="rounded-full bg-amber-50 px-2 py-1 font-semibold text-amber-800">{item.score_prioridade}</span></td><td className="py-3 pr-4">{item.volume} · {item.meses_com_ocorrencia} {c.months}</td><td className="py-3 pr-4">{categoryNames[lang][item.categorias_competitivas[0]?.nome] || item.categorias_competitivas[0]?.nome || c.notAvailable}</td><td className="py-3 pr-4">{causeNames[lang][item.causas[0]?.nome] || item.causas[0]?.nome || c.notAvailable}</td><td className="py-3">{item.implementadoras[0]?.nome || c.notAvailable}</td></tr>)}</tbody></table></div></section>

      <section className="grid gap-6 lg:grid-cols-3"><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.evolution}</h2><div className="mt-4 space-y-2 text-sm">{data.serie_temporal.slice(-12).map(item => <div key={item.periodo} className="flex justify-between gap-4 border-b py-2"><span>{item.periodo}</span><strong>{formatNumber(item.volume)} {c.records}</strong></div>)}</div></div><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.implementers}</h2><div className="mt-4 space-y-3">{(data.rankings.implementadora || []).slice(0, 10).map(item => <MiniBar key={item.nome} label={item.nome} value={item.quantidade} max={Math.max(1, ...(data.rankings.implementadora || []).map(x => x.quantidade))} />)}</div></div><div className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.clients}</h2><div className="mt-4 space-y-3">{(data.rankings.cliente || []).slice(0, 10).map(item => <MiniBar key={item.nome} label={item.nome} value={item.quantidade} max={Math.max(1, ...(data.rankings.cliente || []).map(x => x.quantidade))} />)}</div></div></section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><MetricCard title={c.recordsLabel} value={formatNumber(data.kpis.volume)} /><MetricCard title={c.currencyRecorded} value={formatCurrency(data.kpis.valor, "BRL")} /><MetricCard title={c.avgTicket} value={formatCurrency(data.kpis.ticket_medio, "BRL")} /><MetricCard title={c.customersHistorical} value={formatNumber(data.resumo?.clientes_unicos ?? 0)} /></section>

      <section className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">{c.methodological}</h2><ul className="mt-3 space-y-2 text-sm text-slate-600">{(market?.avisos_metodologicos || []).map((notice, index) => <li key={`${notice}-${index}`} className="flex gap-2"><span>•</span><span>{notice}</span></li>)}</ul></section>
      <section className="rounded-2xl border bg-white p-4 text-sm text-slate-600">{c.source}: {data.metadata.origem} · {c.nature}: {data.metadata.natureza_dados || "FATO_MERCADO_REALIZADO"} · {c.context}: {data.metadata.contexto_operacional} · {c.updated}: {formatDate(data.metadata.ultima_atualizacao, { dateStyle: "short", timeStyle: "short" })}</section>
    </>}
  </div></main>
}
