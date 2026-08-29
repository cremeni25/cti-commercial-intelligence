"use client"

import { useEffect, useMemo, useState } from "react"
import { useOperationalContext } from "@/context/OperationalContext"
import { useI18n } from "@/core/i18n"

type SegmentCode = "TR" | "DT" | "DD"
type CompetitiveItem = { categoria: string; quantidade: number; participacao_mercado_percentual: number }
type CauseItem = { causa: string; quantidade: number; participacao_percentual: number }
type ThemeItem = { tema: string; ocorrencias: number; clientes_distintos: number }
type PriorityItem = { cliente: string; score_prioridade: number; volume: number; categorias_competitivas: { nome: string; quantidade: number }[]; causas: { nome: string; quantidade: number }[]; implementadoras: { nome: string; quantidade: number }[] }
type RecordItem = { status?: string | null; motivo?: string | null; ocorrencia?: string | null; cliente?: string | null; empresa?: string | null; implementadora?: string | null; produto?: string | null; linha?: string | null }
type Intel = {
  mercado: { volume: number; comparacao?: { atual: number; anterior: number; percentual: number; direcao: string; periodo_atual?: string; periodo_anterior?: string } }
  competitividade: { distribuicao: CompetitiveItem[]; carrier_observado: { quantidade: number; participacao_observada_percentual: number } }
  causas_estrategicas: CauseItem[]
  cobertura_comercial: { nao_participamos_proposta: number; sem_contato: number; percentual_nao_participacao: number }
  inteligencia_observacoes: { temas: ThemeItem[] }
  prioridades_recuperacao: PriorityItem[]
}
type ResponseData = { inteligencia_mercado?: Intel; registros?: RecordItem[] }

type ModelSignal = { nome: string; ocorrencias: number; classe: "carrier" | "concorrente" }

const SEGMENT_BY_SLUG: Record<string, SegmentCode> = { trailer: "TR", "diesel-truck": "DT", "direct-drive": "DD" }
const SEGMENT_NAME: Record<SegmentCode, string> = { TR: "Trailer", DT: "Diesel Truck", DD: "Direct Drive" }

const labels = {
  "pt-BR": {
    eyebrow: "LEITURA COMPETITIVA ANFIR 2026", title: "O que esta linha está dizendo comercialmente", source: "Fotografia Carrier/JOV 2026 · território ativo do CTI", loading: "Interpretando a fotografia ANFIR 2026...", error: "A leitura competitiva 2026 está temporariamente indisponível.",
    market: "Mercado real 2026", carrier: "Carrier observada", outside: "Fora da Carrier observada", destination: "Para onde foi o mercado", why: "Por que estamos perdendo", signals: "O que as observações revelam", models: "Modelos e marcas citados nas observações", act: "O que fazer agora", accounts: "Contas para atacar primeiro", note: "Presença Carrier observada na ANFIR; não é market share contábil reconciliado.",
    noParticipation: "não participamos", noContact: "sem contato", records: "unid.", carrierModels: "Carrier", competitorModels: "Concorrentes", noSignal: "Sem evidência textual suficiente para modelo/marca.",
  },
  en: {
    eyebrow: "ANFIR 2026 COMPETITIVE READING", title: "What this product line is saying commercially", source: "Carrier/JOV 2026 snapshot · active CTI territory", loading: "Interpreting the ANFIR 2026 snapshot...", error: "The 2026 competitive reading is temporarily unavailable.",
    market: "2026 realized market", carrier: "Observed Carrier", outside: "Outside observed Carrier", destination: "Where the market went", why: "Why we are losing", signals: "What notes reveal", models: "Models and brands mentioned in notes", act: "What to do now", accounts: "Accounts to attack first", note: "Observed Carrier presence in ANFIR; not reconciled accounting market share.",
    noParticipation: "no participation", noContact: "no contact", records: "units", carrierModels: "Carrier", competitorModels: "Competitors", noSignal: "Not enough textual evidence for model/brand.",
  },
  es: {
    eyebrow: "LECTURA COMPETITIVA ANFIR 2026", title: "Lo que esta línea está diciendo comercialmente", source: "Fotografía Carrier/JOV 2026 · territorio activo de CTI", loading: "Interpretando la fotografía ANFIR 2026...", error: "La lectura competitiva 2026 no está disponible temporalmente.",
    market: "Mercado real 2026", carrier: "Carrier observada", outside: "Fuera de Carrier observada", destination: "A dónde fue el mercado", why: "Por qué estamos perdiendo", signals: "Lo que revelan las observaciones", models: "Modelos y marcas citados en observaciones", act: "Qué hacer ahora", accounts: "Cuentas para atacar primero", note: "Presencia Carrier observada en ANFIR; no es market share contable reconciliado.",
    noParticipation: "sin participación", noContact: "sin contacto", records: "unid.", carrierModels: "Carrier", competitorModels: "Competidores", noSignal: "Sin evidencia textual suficiente para modelo/marca.",
  },
} as const

const categoryLabel: Record<string, string> = { TK: "Thermo King", NACIONAL: "Nacionais", USADO_CONCORRENTE: "Usado concorrente", USADO_CARRIER: "Usado Carrier", SEM_CONTATO: "Sem contato", NAO_CLASSIFICADO: "A qualificar", OUTROS: "Outros" }
const causeLabel: Record<string, string> = { COBERTURA_COMERCIAL: "Cobertura / não participação", SEM_CONTATO: "Sem contato", PRECO_VALOR: "Preço / valor", RELACIONAMENTO: "Relacionamento", TECNICO_PRODUTO: "Produto / técnico", USADO_REAPROVEITAMENTO: "Usado / renovação", CONDICAO_FINANCEIRA: "Condição comercial", SEM_CAUSA_ESTRUTURADA: "Sem causa estruturada", OUTRA_CAUSA_ESTRUTURADA: "Outros fatores" }
const themeLabel: Record<string, string> = { CONCORRENTE_TK: "TK/modelos concorrentes", CONCORRENTE_NACIONAL: "Fabricantes nacionais", IMPLEMENTADORA_INTEGRADA: "Implementadora influencia a solução", PRECO_VALOR: "Preço / valor", RELACIONAMENTO: "Relacionamento / visita", TECNICO_PRODUTO: "Produto / solução técnica", USADO_REAPROVEITAMENTO: "Usado / reaproveitamento", POS_VENDA_MANUTENCAO: "Pós-venda / manutenção", TESTE_DEMO: "Teste / demonstração", CONTEXTO_LIVRE: "Contexto adicional" }

const MODEL_RULES: { nome: string; classe: "carrier" | "concorrente"; re: RegExp }[] = [
  { nome: "X4 7500", classe: "carrier", re: /\bX\s*4[- ]?7500\b/i },
  { nome: "X4 7700", classe: "carrier", re: /\bX\s*4[- ]?7700\b/i },
  { nome: "Vector HE19", classe: "carrier", re: /\b(?:VECTOR\s*)?HE\s*19\b/i },
  { nome: "Vector 8500", classe: "carrier", re: /\bVECTOR\s*8500\b/i },
  { nome: "Supra 1150", classe: "carrier", re: /\bSUPRA\s*1150\b/i },
  { nome: "Supra 850", classe: "carrier", re: /\bSUPRA\s*850\b/i },
  { nome: "Supra 750", classe: "carrier", re: /\bSUPRA\s*750\b/i },
  { nome: "Citimax/CM 600", classe: "carrier", re: /\b(?:CITIMAX|CM)\s*600\b/i },
  { nome: "Citimax/CM 500", classe: "carrier", re: /\b(?:CITIMAX|CM)\s*500\b/i },
  { nome: "Citimax/CM 400", classe: "carrier", re: /\b(?:CITIMAX|CM)\s*400\b/i },
  { nome: "Citimax/CM 280", classe: "carrier", re: /\b(?:CITIMAX|CM)\s*280\b/i },
  { nome: "Xarios 600", classe: "carrier", re: /\bXARIOS\s*600\b/i },
  { nome: "Xarios 350", classe: "carrier", re: /\bXARIOS\s*350\b/i },
  { nome: "A500", classe: "concorrente", re: /\bA\s*500\b/i },
  { nome: "SLXi 400", classe: "concorrente", re: /\bSLX[I1]?\s*400\b/i },
  { nome: "SLXi", classe: "concorrente", re: /\bSLX[I1]\b/i },
  { nome: "Frigoking", classe: "concorrente", re: /\bFRIGOKING\b/i },
  { nome: "Rodofrio", classe: "concorrente", re: /\bRODOFRIO\b/i },
  { nome: "Thermoflex", classe: "concorrente", re: /\bTHERMOFLEX\b/i },
  { nome: "Thermostar", classe: "concorrente", re: /\bTHERMOSTAR\b/i },
  { nome: "Titon", classe: "concorrente", re: /\bTITON\b/i },
]

function modelSignals(records: RecordItem[]): ModelSignal[] {
  const counts = new Map<string, ModelSignal>()
  for (const record of records) {
    const text = `${record.ocorrencia || ""} ${record.motivo || ""}`
    for (const rule of MODEL_RULES) if (rule.re.test(text)) {
      const current = counts.get(rule.nome)
      counts.set(rule.nome, { nome: rule.nome, classe: rule.classe, ocorrencias: (current?.ocorrencias || 0) + 1 })
    }
  }
  return [...counts.values()].sort((a, b) => b.ocorrencias - a.ocorrencias)
}

function recommendedActions(intel: Intel): string[] {
  const total = Math.max(1, intel.mercado.volume)
  const dist = Object.fromEntries(intel.competitividade.distribuicao.map(item => [item.categoria, item.quantidade])) as Record<string, number>
  const causes = Object.fromEntries(intel.causas_estrategicas.map(item => [item.causa, item.quantidade])) as Record<string, number>
  const themes = Object.fromEntries(intel.inteligencia_observacoes.temas.map(item => [item.tema, item.ocorrencias])) as Record<string, number>
  const actions: { score: number; text: string }[] = []
  const noPart = intel.cobertura_comercial.nao_participamos_proposta
  if (noPart) actions.push({ score: noPart / total, text: `Recuperar cobertura antes da próxima compra: ${noPart} ocorrências indicam ausência na proposta.` })
  if (dist.NACIONAL) actions.push({ score: dist.NACIONAL / total, text: `Separar estratégia contra fabricantes nacionais: ${dist.NACIONAL} unidades observadas exigem argumento próprio, não a mesma abordagem usada contra TK.` })
  if (dist.TK) actions.push({ score: dist.TK / total, text: `Atacar contas hoje vinculadas à Thermo King com comparação por modelo, TCO, manutenção e condição comercial.` })
  if (intel.cobertura_comercial.sem_contato) actions.push({ score: intel.cobertura_comercial.sem_contato / total, text: `Criar fila de contato para ${intel.cobertura_comercial.sem_contato} ocorrências sem cobertura comercial registrada.` })
  if (themes.IMPLEMENTADORA_INTEGRADA) actions.push({ score: themes.IMPLEMENTADORA_INTEGRADA / total + 0.05, text: `Antecipar a abordagem nas implementadoras: há ${themes.IMPLEMENTADORA_INTEGRADA} sinais de decisão influenciada ou fechada antes do contato da Viena.` })
  if (causes.PRECO_VALOR || themes.PRECO_VALOR) actions.push({ score: Math.max(causes.PRECO_VALOR || 0, themes.PRECO_VALOR || 0) / total, text: "Tratar preço como valor total da solução: comparar equipamento, instalação, manutenção, pós-venda e vida útil; não responder apenas com desconto." })
  if (causes.TECNICO_PRODUTO || themes.TECNICO_PRODUTO) actions.push({ score: Math.max(causes.TECNICO_PRODUTO || 0, themes.TECNICO_PRODUTO || 0) / total, text: "Separar objeções técnicas das comerciais e validar aderência de produto antes de classificar a perda como preço." })
  if (causes.USADO_REAPROVEITAMENTO || dist.USADO_CONCORRENTE || dist.USADO_CARRIER) actions.push({ score: ((causes.USADO_REAPROVEITAMENTO || 0) + (dist.USADO_CONCORRENTE || 0)) / total, text: "Transformar usados/reaproveitamento em radar de renovação: nem toda ocorrência é perda de venda nova; parte é ciclo futuro de substituição." })
  return actions.sort((a, b) => b.score - a.score).slice(0, 4).map(item => item.text)
}

function pct(value: number) { return `${Number(value || 0).toFixed(1)}%` }

export default function AnfirCompetitiveDecision({ slug }: { slug: string }) {
  const code = SEGMENT_BY_SLUG[slug]
  const { queryString } = useOperationalContext()
  const { locale, formatNumber } = useI18n()
  const tx = labels[locale]
  const [data, setData] = useState<ResponseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const request = useMemo(() => {
    if (!code) return ""
    const params = new URLSearchParams(queryString)
    params.set("periodo", "ANO_ATUAL")
    params.set("segmento", code)
    params.set("comparacao", "PERIODO_ANTERIOR")
    return `/api/cti/analytics/intelligence?${params.toString()}`
  }, [code, queryString])

  useEffect(() => {
    if (!request) return
    let active = true
    queueMicrotask(() => {
      if (!active) return
      setLoading(true); setError(false)
      fetch(request, { cache: "no-store" }).then(async response => {
        if (!response.ok) throw new Error(String(response.status))
        return response.json() as Promise<ResponseData>
      }).then(payload => { if (active) setData(payload) }).catch(() => { if (active) setError(true) }).finally(() => { if (active) setLoading(false) })
    })
    return () => { active = false }
  }, [request])

  if (!code) return null
  if (loading) return <section className="rounded-2xl border border-cyan-800/40 bg-cyan-950/10 p-5 text-sm text-slate-400">{tx.loading}</section>
  if (error || !data?.inteligencia_mercado) return <section className="rounded-2xl border border-amber-800/50 bg-amber-950/10 p-5 text-sm text-amber-200">{tx.error}</section>

  const intel = data.inteligencia_mercado
  const total = intel.mercado.volume
  const carrier = intel.competitividade.carrier_observado.quantidade
  const outside = Math.max(0, total - carrier)
  const destinations = intel.competitividade.distribuicao.filter(item => item.categoria !== "CARRIER" && item.quantidade > 0).sort((a, b) => b.quantidade - a.quantidade)
  const causes = intel.causas_estrategicas.filter(item => item.quantidade > 0).slice(0, 6)
  const themes = intel.inteligencia_observacoes.temas.filter(item => item.ocorrencias > 0 && item.tema !== "CONTEXTO_LIVRE").slice(0, 6)
  const models = modelSignals(data.registros || []).slice(0, 10)
  const actions = recommendedActions(intel)
  const priorities = intel.prioridades_recuperacao.slice(0, 6)

  return <section className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-[#071a31] to-[#061126] p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-xs font-semibold tracking-[.18em] text-cyan-400">{tx.eyebrow} · {SEGMENT_NAME[code]}</p><h2 className="mt-2 text-2xl font-bold">{tx.title}</h2><p className="mt-2 text-xs text-slate-500">{tx.source}</p></div>
      <p className="max-w-xl rounded-xl border border-cyan-900 bg-cyan-950/20 px-3 py-2 text-xs text-cyan-100/80">{tx.note}</p>
    </div>

    <div className="mt-6 grid gap-3 md:grid-cols-3">
      <Metric title={tx.market} value={formatNumber(total)} detail={intel.mercado.comparacao ? `${intel.mercado.comparacao.periodo_atual || "Q2"} × ${intel.mercado.comparacao.periodo_anterior || "Q1"}: ${intel.mercado.comparacao.percentual > 0 ? "+" : ""}${pct(intel.mercado.comparacao.percentual)}` : undefined}/>
      <Metric title={tx.carrier} value={`${formatNumber(carrier)} · ${pct(intel.competitividade.carrier_observado.participacao_observada_percentual)}`} detail={tx.note}/>
      <Metric title={tx.outside} value={formatNumber(outside)} detail={`${formatNumber(intel.cobertura_comercial.nao_participamos_proposta)} ${tx.noParticipation} · ${formatNumber(intel.cobertura_comercial.sem_contato)} ${tx.noContact}`}/>
    </div>

    <div className="mt-6 grid gap-5 xl:grid-cols-3">
      <DecisionPanel title={tx.destination}>{destinations.slice(0, 6).map(item => <Row key={item.categoria} label={categoryLabel[item.categoria] || item.categoria} value={`${formatNumber(item.quantidade)} · ${pct(item.participacao_mercado_percentual)}`}/>)}</DecisionPanel>
      <DecisionPanel title={tx.why}>{causes.map(item => <Row key={item.causa} label={causeLabel[item.causa] || item.causa} value={formatNumber(item.quantidade)}/>)}</DecisionPanel>
      <DecisionPanel title={tx.signals}>{themes.map(item => <Row key={item.tema} label={themeLabel[item.tema] || item.tema} value={`${formatNumber(item.ocorrencias)} · ${formatNumber(item.clientes_distintos)} clientes`}/>)}</DecisionPanel>
    </div>

    <div className="mt-5 grid gap-5 xl:grid-cols-2">
      <DecisionPanel title={tx.models}>{models.length ? <div className="grid gap-2 sm:grid-cols-2">{models.map(item => <div key={`${item.classe}-${item.nome}`} className="rounded-xl bg-[#08162d] p-3"><p className={`text-[10px] font-semibold uppercase tracking-wider ${item.classe === "carrier" ? "text-cyan-300" : "text-amber-300"}`}>{item.classe === "carrier" ? tx.carrierModels : tx.competitorModels}</p><div className="mt-1 flex items-center justify-between gap-3"><strong>{item.nome}</strong><span className="text-slate-400">{formatNumber(item.ocorrencias)}</span></div></div>)}</div> : <p className="text-sm text-slate-500">{tx.noSignal}</p>}</DecisionPanel>
      <DecisionPanel title={tx.act}><ol className="space-y-3">{actions.map((action, index) => <li key={action} className="flex gap-3 text-sm leading-6 text-slate-300"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-500/15 text-xs font-bold text-cyan-300">{index + 1}</span><span>{action}</span></li>)}</ol></DecisionPanel>
    </div>

    <DecisionPanel title={tx.accounts} extra="mt-5"><div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">{priorities.map(item => <div key={item.cliente} className="rounded-xl border border-[#193354] bg-[#08162d] p-3"><div className="flex items-start justify-between gap-3"><strong className="text-sm leading-5">{item.cliente}</strong><span className="rounded-lg bg-cyan-500/10 px-2 py-1 text-xs font-bold text-cyan-300">{item.score_prioridade}</span></div><p className="mt-2 text-xs text-slate-400">{formatNumber(item.volume)} {tx.records} · {categoryLabel[item.categorias_competitivas[0]?.nome] || item.categorias_competitivas[0]?.nome || "—"}</p><p className="mt-1 text-xs text-slate-500">{causeLabel[item.causas[0]?.nome] || item.causas[0]?.nome || "—"}{item.implementadoras[0]?.nome ? ` · ${item.implementadoras[0].nome}` : ""}</p></div>)}</div></DecisionPanel>
  </section>
}

function Metric({ title, value, detail }: { title: string; value: string; detail?: string }) { return <div className="rounded-xl border border-[#193354] bg-[#08162d] p-4"><p className="text-[11px] uppercase tracking-wider text-slate-500">{title}</p><p className="mt-2 text-2xl font-bold text-white">{value}</p>{detail && <p className="mt-2 text-xs leading-5 text-slate-400">{detail}</p>}</div> }
function DecisionPanel({ title, children, extra = "" }: { title: string; children: React.ReactNode; extra?: string }) { return <div className={`${extra} rounded-xl border border-[#193354] bg-[#07142b] p-4`}><h3 className="font-semibold text-white">{title}</h3><div className="mt-3 space-y-2">{children}</div></div> }
function Row({ label, value }: { label: string; value: string }) { return <div className="flex items-center justify-between gap-4 border-b border-[#162842] py-2 text-sm last:border-0"><span className="text-slate-300">{label}</span><strong className="shrink-0 text-white">{value}</strong></div> }
