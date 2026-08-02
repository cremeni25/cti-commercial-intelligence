"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type RankingItem = { nome: string; quantidade: number }
type DashboardContextual = {
  total_registros?: number
  total_clientes?: number
  total_estados?: number
  total_municipios?: number
  total_implementadoras?: number
  ticket_medio?: number
  ranking_implementadoras?: RankingItem[]
  ranking_clientes?: RankingItem[]
  metadata?: { total_registros_filtrados?: number }
}
type DashboardCRM = { oportunidades?: number; propostas?: number; pedidos?: number; atividades?: number }
type AgendaResponse = { resumo?: { atrasadas?: number; hoje?: number; futuras?: number; sem_data?: number; concluidas?: number } }
type NucleoComercial = {
  oportunidade_id: string
  etapa?: string
  valor?: number
  valor_ponderado?: number
  proposta_id?: string | null
  pedido_id?: string | null
  encerrada?: boolean
}
type PipelineCard = { etapa?: string; valor_estimado?: number; valor_ponderado?: number }
type PipelineResponse = { cards?: PipelineCard[]; resumo?: { total_oportunidades?: number; valor_total?: number; valor_ponderado?: number } }
type SerieItem = { nome: string; valor: number }
type LinhaProduto = {
  codigo: "TR" | "DT" | "DD"
  nome: string
  atual: number
  anterior: number
  variacao: number
  direcao: string
  modelos: RankingItem[]
  disponivel: boolean
}
type ProductLinesMetadata = {
  contexto?: string
  periodo_solicitado?: string
  periodo_efetivo?: string
  inicio?: string | null
  fim?: string | null
  descricao?: string
  total_registros_territorio?: number
  total_registros_periodo?: number
  registros_classificados_periodo?: number
  registros_sem_linha_classificada?: number
  cobertura_classificacao_percentual?: number
}
type ProductLinesResponse = {
  metadata?: ProductLinesMetadata
  linhas?: Omit<LinhaProduto, "disponivel">[]
}

const LINHAS = [
  { codigo: "TR" as const, nome: "Trailer" },
  { codigo: "DT" as const, nome: "Diesel Truck" },
  { codigo: "DD" as const, nome: "Direct Drive" },
]
const LINHAS_VAZIAS = LINHAS.map((linha) => ({ ...linha, atual: 0, anterior: 0, variacao: 0, direcao: "estavel", modelos: [], disponivel: false }))

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dashboard, setDashboard] = useState<DashboardContextual | null>(null)
  const [crm, setCrm] = useState<DashboardCRM | null>(null)
  const [agenda, setAgenda] = useState<AgendaResponse>({})
  const [pipeline, setPipeline] = useState<PipelineResponse>({})
  const [linhasProduto, setLinhasProduto] = useState<LinhaProduto[]>(LINHAS_VAZIAS)
  const [metadataLinhas, setMetadataLinhas] = useState<ProductLinesMetadata>({})
  const [referenciaLinhas, setReferenciaLinhas] = useState("")
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loading, setLoading] = useState(true)
  const [avisos, setAvisos] = useState<string[]>([])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      const [nucleo, dadosAgenda, dadosCrmLegado] = await Promise.all([
        tentar<NucleoComercial[]>(() => buscarJson(`${API_URL}/crm/nucleo-comercial`)),
        tentar<AgendaResponse>(() => buscarJson(`${API_URL}/crm/agenda`)),
        tentar<DashboardCRM>(() => buscarJson(`${API_URL}/crm/dashboard`)),
      ])
      if (!ativo) return

      const registros = nucleo ?? []
      const abertos = registros.filter((item) => !item.encerrada)
      setCrm({
        oportunidades: registros.length,
        propostas: registros.filter((item) => Boolean(item.proposta_id)).length,
        pedidos: registros.filter((item) => Boolean(item.pedido_id)).length,
        atividades: dadosCrmLegado?.atividades ?? 0,
      })
      setAgenda(dadosAgenda ?? {})
      setPipeline({
        cards: abertos.map((item) => ({
          etapa: item.etapa,
          valor_estimado: Number(item.valor || 0),
          valor_ponderado: Number(item.valor_ponderado || 0),
        })),
        resumo: {
          total_oportunidades: abertos.length,
          valor_total: abertos.reduce((total, item) => total + Number(item.valor || 0), 0),
          valor_ponderado: abertos.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0),
        },
      })
    })
    return () => { ativo = false }
  }, [])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      if (!ativo) return
      setLoading(true)
      setAvisos([])
      setDashboard(null)
      setLinhasProduto(LINHAS_VAZIAS)
      setMetadataLinhas({})
      setReferenciaLinhas(`${contextoAtual.label} — carregando referência temporal`)

      const historico = await tentar<DashboardContextual>(() => getDashboardExecutivoContextual(queryString), 2)
      if (!ativo) return
      if (historico) setDashboard(historico)

      const dadosLinhas = await tentar<ProductLinesResponse>(() => buscarJson(`${API_URL}/analytics/product-lines?${queryString}`), 2)
      if (!ativo) return

      const novosAvisos: string[] = []
      if (!historico) novosAvisos.push("Não foi possível atualizar a base histórica.")
      if (dadosLinhas?.linhas?.length === 3) {
        setLinhasProduto(dadosLinhas.linhas.map((linha) => ({ ...linha, disponivel: true })))
        setMetadataLinhas(dadosLinhas.metadata ?? {})
        setReferenciaLinhas(`${contextoAtual.label} — ${dadosLinhas.metadata?.descricao || "período selecionado"}`)
      } else {
        novosAvisos.push("Não foi possível atualizar os indicadores por linha.")
        setReferenciaLinhas(`${contextoAtual.label} — referência temporal indisponível`)
      }

      setAvisos(novosAvisos)
      setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
      setLoading(false)
    })
    return () => { ativo = false }
  }, [queryString, contextoAtual.label])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? dataInicio && dataFim ? `${dataInicio} até ${dataFim}` : "Personalizado sem datas — relógios usam últimos 90 dias"
      : periodo.replaceAll("_", " ").toLowerCase()

  const funilCrm = useMemo<SerieItem[]>(() => [
    { nome: "Oportunidades", valor: crm?.oportunidades ?? 0 },
    { nome: "Propostas", valor: crm?.propostas ?? 0 },
    { nome: "Pedidos", valor: crm?.pedidos ?? 0 },
  ], [crm])
  const agendaResumo = useMemo<SerieItem[]>(() => [
    { nome: "Atrasadas", valor: agenda.resumo?.atrasadas ?? 0 },
    { nome: "Hoje", valor: agenda.resumo?.hoje ?? 0 },
    { nome: "Futuras", valor: agenda.resumo?.futuras ?? 0 },
    { nome: "Sem data", valor: agenda.resumo?.sem_data ?? 0 },
  ], [agenda])
  const pipelineEtapas = useMemo<SerieItem[]>(() => {
    const contagem = new Map<string, number>()
    for (const card of pipeline.cards ?? []) {
      const etapa = card.etapa || "SEM ETAPA"
      contagem.set(etapa, (contagem.get(etapa) ?? 0) + 1)
    }
    return Array.from(contagem, ([nome, valor]) => ({ nome, valor })).sort((a, b) => b.valor - a.valor)
  }, [pipeline])
  const topClientes = useMemo<SerieItem[]>(() => (dashboard?.ranking_clientes ?? []).slice(0, 5).map((item) => ({ nome: item.nome, valor: item.quantidade })), [dashboard])
  const topImplementadoras = useMemo<SerieItem[]>(() => (dashboard?.ranking_implementadoras ?? []).slice(0, 5).map((item) => ({ nome: item.nome, valor: item.quantidade })), [dashboard])
  const conversaoProposta = percentual(crm?.pedidos, crm?.propostas)
  const conversaoOportunidade = percentual(crm?.pedidos, crm?.oportunidades)
  const totalPeriodo = metadataLinhas.total_registros_periodo ?? 0
  const totalClassificado = metadataLinhas.registros_classificados_periodo ?? linhasProduto.reduce((soma, linha) => soma + linha.atual, 0)
  const totalNaoClassificado = metadataLinhas.registros_sem_linha_classificada ?? Math.max(totalPeriodo - totalClassificado, 0)
  const cobertura = metadataLinhas.cobertura_classificacao_percentual ?? percentual(totalClassificado, totalPeriodo)

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div><h1 className="text-3xl font-bold text-white">Dashboard Executivo</h1><p className="text-gray-400 mt-2">Visão exclusivamente analítica da base histórica e dos principais resultados consolidados do CRM.</p><p className="text-cyan-300 text-sm mt-2">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p></div>
          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-sm text-gray-300"><div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"><Info titulo="Período analisado" valor={periodoExibido} /><Info titulo="Última atualização" valor={ultimaAtualizacao || "Aguardando carga dos dados."} /><Info titulo="Origem dos dados" valor="Base histórica CTI/ANFIR + núcleo comercial consolidado" /><Info titulo="Registros após filtros" valor={loading ? "..." : String(dashboard?.metadata?.total_registros_filtrados ?? 0)} /></div></section>
          {avisos.length > 0 && <div className="rounded-xl border border-amber-500/60 bg-amber-500/5 p-4 text-sm text-amber-200">Atualização incompleta: {avisos.join(" ")} Tente novamente em alguns segundos.</div>}
          <section className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4"><Kpi titulo="Clientes históricos" valor={loading ? "..." : dashboard?.total_clientes ?? 0} /><Kpi titulo="Estados atendidos" valor={loading ? "..." : dashboard?.total_estados ?? 0} /><Kpi titulo="Municípios" valor={loading ? "..." : dashboard?.total_municipios ?? 0} /><Kpi titulo="Ticket histórico" valor={loading ? "..." : moeda(dashboard?.ticket_medio)} /><Kpi titulo="Pipeline aberto" valor={moeda(pipeline.resumo?.valor_total)} /><Kpi titulo="Pipeline ponderado" valor={moeda(pipeline.resumo?.valor_ponderado)} /></section>
          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6">
            <div className="mb-5"><h2 className="text-2xl font-bold text-white">Variação da base classificada por linha de produto</h2><p className="mt-1 text-sm text-gray-400">{referenciaLinhas}.</p><p className="mt-2 text-sm font-medium text-cyan-200">Os relógios abaixo não representam o total territorial. Eles comparam somente registros com linha TR, DT ou DD identificada.</p></div>
            <div className="mb-5 grid grid-cols-2 gap-3 xl:grid-cols-4"><ResumoClassificacao titulo="Base territorial no período" valor={loading ? "..." : totalPeriodo} /><ResumoClassificacao titulo="Base classificada" valor={loading ? "..." : totalClassificado} /><ResumoClassificacao titulo="Sem classificação" valor={loading ? "..." : totalNaoClassificado} /><ResumoClassificacao titulo="Cobertura dos gráficos" valor={loading ? "..." : `${cobertura.toLocaleString("pt-BR")}%`} /></div>
            {!loading && cobertura < 100 && <div className="mb-5 rounded-xl border border-amber-500/50 bg-amber-500/5 px-4 py-3 text-sm text-amber-200">Base parcial: {totalNaoClassificado} registros do território não entram nos relógios porque não possuem linha de equipamento identificada.</div>}
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">{loading ? LINHAS.map((linha) => <div key={linha.codigo} className="h-72 animate-pulse rounded-2xl bg-[#020817]" />) : linhasProduto.map((linha) => <RelogioComercial key={linha.codigo} linha={linha} totalClassificado={totalClassificado} cobertura={cobertura} />)}</div>
          </section>
          <section className="grid grid-cols-1 xl:grid-cols-3 gap-6"><GraficoBarras titulo="Funil resumido do CRM" subtitulo="Volumes consolidados, sem funções operacionais." itens={funilCrm} /><GraficoBarras titulo="Agenda comercial" subtitulo="Resumo do estado das atividades registradas no CRM." itens={agendaResumo} /><GraficoBarras titulo="Distribuição do pipeline" subtitulo="Quantidade de oportunidades por etapa atual." itens={pipelineEtapas} /></section>
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4"><Kpi titulo="Oportunidades CRM" valor={crm?.oportunidades ?? 0} /><Kpi titulo="Propostas CRM" valor={crm?.propostas ?? 0} /><Kpi titulo="Pedidos CRM" valor={crm?.pedidos ?? 0} /><Kpi titulo="Atividades CRM" valor={crm?.atividades ?? 0} /></section>
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6"><IndicadorAnalitico titulo="Conversão proposta → pedido" valor={`${conversaoProposta}%`} descricao="Pedidos divididos pelas oportunidades com proposta vigente no núcleo comercial." /><IndicadorAnalitico titulo="Conversão oportunidade → pedido" valor={`${conversaoOportunidade}%`} descricao="Pedidos reconhecidos pelo núcleo divididos pelas oportunidades consolidadas." /></section>
          <section className="grid grid-cols-1 xl:grid-cols-2 gap-6"><GraficoBarras titulo="Top 5 clientes" subtitulo="Maiores presenças históricas; detalhes completos disponíveis em Clientes." itens={topClientes} /><GraficoBarras titulo="Top 5 implementadoras" subtitulo="Maiores origens comerciais; detalhes completos disponíveis em Implementadoras." itens={topImplementadoras} /></section>
        </div>
      </section>
    </main>
  )
}

async function buscarJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" })
  if (!response.ok) throw new Error(`${response.status} ${url}`)
  return response.json() as Promise<T>
}
async function tentar<T>(executar: () => Promise<T>, tentativas = 1): Promise<T | null> {
  for (let tentativa = 0; tentativa < tentativas; tentativa += 1) {
    try { return await executar() } catch { if (tentativa + 1 < tentativas) await new Promise((resolve) => setTimeout(resolve, 700)) }
  }
  return null
}
function percentual(parte?: number, total?: number) { if (!parte || !total) return 0; return Math.round((parte / total) * 100) }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function RelogioComercial({ linha, totalClassificado, cobertura }: { linha: LinhaProduto; totalClassificado: number; cobertura: number }) {
  const variacaoLimitada = Math.max(-50, Math.min(50, linha.variacao)); const angulo = (variacaoLimitada / 50) * 90
  const status = !linha.disponivel ? "Indisponível" : linha.direcao === "alta" ? "Crescimento" : linha.direcao === "queda" ? "Retração" : "Estabilidade"
  const participacao = totalClassificado > 0 ? (linha.atual / totalClassificado) * 100 : 0
  return <article className="rounded-2xl border border-[#13203f] bg-[#020817] p-5"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-semibold text-cyan-300">{linha.codigo}</p><h3 className="text-xl font-bold text-white">{linha.nome}</h3></div><span className="rounded-full border border-[#20345f] px-3 py-1 text-xs text-gray-300">{status}</span></div>{!linha.disponivel ? <div className="flex h-56 items-center justify-center text-center text-sm text-gray-400">Indicador temporariamente indisponível.</div> : <><div className="mt-4 rounded-lg border border-[#20345f] bg-[#071226] px-3 py-2 text-xs text-gray-300"><strong className="text-cyan-300">{linha.atual}</strong> registros classificados nesta linha · <strong className="text-cyan-300">{participacao.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</strong> da base classificada{cobertura < 100 ? " · base territorial parcial" : ""}</div><div className="relative mx-auto mt-5 h-32 w-64 overflow-hidden"><div className="absolute left-1/2 top-4 h-48 w-48 -translate-x-1/2 rounded-full border-[18px] border-[#13203f] border-b-transparent border-l-red-500/70 border-r-emerald-500/70" /><div className="absolute bottom-3 left-1/2 h-2 w-24 origin-left rounded-full bg-cyan-300 transition-transform" style={{ transform: `rotate(${angulo - 90}deg)` }} /><div className="absolute bottom-1 left-1/2 h-5 w-5 -translate-x-1/2 rounded-full border-4 border-cyan-300 bg-[#071226]" /></div><div className="text-center"><p className="text-xs uppercase tracking-widest text-gray-500">Variação da base classificada</p><p className="mt-1 text-4xl font-bold text-cyan-400">{linha.variacao > 0 ? "+" : ""}{linha.variacao.toLocaleString("pt-BR")}%</p><p className="mt-1 text-sm text-gray-400">{linha.atual} classificados no período atual · {linha.anterior} no anterior</p></div><div className="mt-5 border-t border-[#13203f] pt-4"><p className="text-xs uppercase tracking-widest text-gray-500">Modelos identificados nesta linha</p>{linha.modelos.length === 0 ? <p className="mt-2 text-sm text-gray-400">Nenhum modelo oficial identificado no período.</p> : <div className="mt-2 space-y-2">{linha.modelos.map((modelo) => <div key={modelo.nome} className="flex justify-between gap-3 text-sm"><span className="truncate text-gray-300" title={modelo.nome}>{modelo.nome}</span><strong className="text-cyan-300">{modelo.quantidade}</strong></div>)}</div>}</div></>}</article>
}
function ResumoClassificacao({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-xl border border-[#20345f] bg-[#020817] px-4 py-3"><p className="text-xs uppercase tracking-wide text-gray-500">{titulo}</p><p className="mt-1 text-xl font-bold text-cyan-300">{valor}</p></div> }
function GraficoBarras({ titulo, subtitulo, itens }: { titulo: string; subtitulo: string; itens: SerieItem[] }) { const maximo = Math.max(...itens.map((item) => item.valor), 1); return <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6"><h2 className="text-xl font-bold text-white">{titulo}</h2><p className="mt-1 text-sm text-gray-400">{subtitulo}</p><div className="mt-6 space-y-4">{itens.length === 0 ? <p className="text-gray-400">Nenhum dado disponível.</p> : itens.map((item) => <div key={item.nome}><div className="mb-2 flex justify-between gap-4 text-sm"><span className="truncate text-gray-300" title={item.nome}>{item.nome}</span><strong className="shrink-0 text-cyan-300">{item.valor}</strong></div><div className="h-3 overflow-hidden rounded-full bg-[#020817]"><div className="h-full rounded-full bg-cyan-500" style={{ width: `${Math.max((item.valor / maximo) * 100, item.valor > 0 ? 4 : 0)}%` }} /></div></div>)}</div></section> }
function IndicadorAnalitico({ titulo, valor, descricao }: { titulo: string; valor: string; descricao: string }) { return <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6"><p className="text-gray-400 text-sm">{titulo}</p><p className="mt-2 text-4xl font-bold text-cyan-400">{valor}</p><p className="mt-3 text-sm text-gray-400">{descricao}</p></section> }
function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-xl border border-[#13203f] bg-[#020817] p-4"><p className="text-cyan-300 font-semibold">{titulo}</p><p className="mt-2 text-gray-300">{valor}</p></div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5"><p className="text-gray-400 text-sm">{titulo}</p><p className="text-3xl font-bold text-cyan-400 mt-2">{valor}</p></div> }
