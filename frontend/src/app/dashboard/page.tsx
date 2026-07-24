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
type PipelineCard = { etapa?: string; valor_estimado?: number; valor_ponderado?: number }
type PipelineResponse = { cards?: PipelineCard[]; resumo?: { total_oportunidades?: number; valor_total?: number; valor_ponderado?: number } }

type SerieItem = { nome: string; valor: number }

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dashboard, setDashboard] = useState<DashboardContextual | null>(null)
  const [crm, setCrm] = useState<DashboardCRM | null>(null)
  const [agenda, setAgenda] = useState<AgendaResponse>({})
  const [pipeline, setPipeline] = useState<PipelineResponse>({})
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")
      Promise.all([
        getDashboardExecutivoContextual(queryString),
        fetch(`${API_URL}/crm/dashboard`, { cache: "no-store" }).then(validarResposta),
        fetch(`${API_URL}/crm/agenda`, { cache: "no-store" }).then(validarResposta),
        fetch(`${API_URL}/crm/pipeline/quadro`, { cache: "no-store" }).then(validarResposta),
      ])
        .then(([dadosHistoricos, dadosCrm, dadosAgenda, dadosPipeline]) => {
          if (!ativo) return
          setDashboard(dadosHistoricos)
          setCrm(dadosCrm)
          setAgenda(dadosAgenda)
          setPipeline(dadosPipeline)
          setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
        })
        .catch(() => { if (ativo) setErro("Erro ao carregar os indicadores analíticos do Dashboard.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [queryString])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? `${dataInicio || "início não definido"} até ${dataFim || "fim não definido"}`
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

  const conversaoProposta = percentual(crm?.pedidos, crm?.propostas)
  const conversaoOportunidade = percentual(crm?.pedidos, crm?.oportunidades)

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard Executivo</h1>
            <p className="text-gray-400 mt-2">Visão exclusivamente analítica da base histórica e dos principais resultados consolidados do CRM.</p>
            <p className="text-cyan-300 text-sm mt-2">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </div>

          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-sm text-gray-300">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Info titulo="Período analisado" valor={periodoExibido} />
              <Info titulo="Última atualização" valor={ultimaAtualizacao || "Aguardando carga dos dados."} />
              <Info titulo="Origem dos dados" valor="Base histórica CTI/ANFIR + resumo consolidado do CRM" />
              <Info titulo="Registros após filtros" valor={String(dashboard?.metadata?.total_registros_filtrados ?? 0)} />
            </div>
          </section>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi titulo="Clientes históricos" valor={loading ? "..." : dashboard?.total_clientes ?? 0} />
            <Kpi titulo="Estados atendidos" valor={loading ? "..." : dashboard?.total_estados ?? 0} />
            <Kpi titulo="Municípios" valor={loading ? "..." : dashboard?.total_municipios ?? 0} />
            <Kpi titulo="Ticket histórico" valor={loading ? "..." : moeda(dashboard?.ticket_medio)} />
            <Kpi titulo="Pipeline aberto" valor={loading ? "..." : moeda(pipeline.resumo?.valor_total)} />
            <Kpi titulo="Pipeline ponderado" valor={loading ? "..." : moeda(pipeline.resumo?.valor_ponderado)} />
          </section>

          <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <GraficoBarras titulo="Funil resumido do CRM" subtitulo="Volumes consolidados, sem funções operacionais." itens={funilCrm} />
            <GraficoBarras titulo="Agenda comercial" subtitulo="Resumo do estado das atividades registradas no CRM." itens={agendaResumo} />
            <GraficoBarras titulo="Distribuição do pipeline" subtitulo="Quantidade de oportunidades por etapa atual." itens={pipelineEtapas} />
          </section>

          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Kpi titulo="Oportunidades CRM" valor={loading ? "..." : crm?.oportunidades ?? 0} />
            <Kpi titulo="Propostas CRM" valor={loading ? "..." : crm?.propostas ?? 0} />
            <Kpi titulo="Pedidos CRM" valor={loading ? "..." : crm?.pedidos ?? 0} />
            <Kpi titulo="Atividades CRM" valor={loading ? "..." : crm?.atividades ?? 0} />
          </section>

          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <IndicadorAnalitico titulo="Conversão proposta → pedido" valor={`${conversaoProposta}%`} descricao="Pedidos divididos pelas propostas cadastradas no CRM." />
            <IndicadorAnalitico titulo="Conversão oportunidade → pedido" valor={`${conversaoOportunidade}%`} descricao="Pedidos divididos pelas oportunidades cadastradas no CRM." />
          </section>

          {!loading && dashboard && (dashboard.total_registros ?? 0) > 0 && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <Ranking titulo="Onde vender: clientes com maior presença histórica" itens={dashboard.ranking_clientes ?? []} />
              <Ranking titulo="Origem comercial: implementadoras mais presentes" itens={dashboard.ranking_implementadoras ?? []} />
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

async function validarResposta(response: Response) {
  if (!response.ok) throw new Error("Serviço indisponível")
  return response.json()
}

function percentual(parte?: number, total?: number) {
  if (!parte || !total) return 0
  return Math.round((parte / total) * 100)
}

function moeda(valor?: number) {
  return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}`
}

function GraficoBarras({ titulo, subtitulo, itens }: { titulo: string; subtitulo: string; itens: SerieItem[] }) {
  const maximo = Math.max(...itens.map((item) => item.valor), 1)
  return (
    <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6">
      <h2 className="text-xl font-bold text-white">{titulo}</h2>
      <p className="mt-1 text-sm text-gray-400">{subtitulo}</p>
      <div className="mt-6 space-y-4">
        {itens.length === 0 ? <p className="text-gray-400">Nenhum dado disponível.</p> : itens.map((item) => (
          <div key={item.nome}>
            <div className="mb-2 flex justify-between gap-4 text-sm"><span className="text-gray-300">{item.nome}</span><strong className="text-cyan-300">{item.valor}</strong></div>
            <div className="h-3 overflow-hidden rounded-full bg-[#020817]"><div className="h-full rounded-full bg-cyan-500" style={{ width: `${Math.max((item.valor / maximo) * 100, item.valor > 0 ? 4 : 0)}%` }} /></div>
          </div>
        ))}
      </div>
    </section>
  )
}

function IndicadorAnalitico({ titulo, valor, descricao }: { titulo: string; valor: string; descricao: string }) {
  return <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6"><p className="text-gray-400 text-sm">{titulo}</p><p className="mt-2 text-4xl font-bold text-cyan-400">{valor}</p><p className="mt-3 text-sm text-gray-400">{descricao}</p></section>
}

function Info({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#020817] p-4"><p className="text-cyan-300 font-semibold">{titulo}</p><p className="mt-2 text-gray-300">{valor}</p></div>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) {
  return <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5"><p className="text-gray-400 text-sm">{titulo}</p><p className="text-3xl font-bold text-cyan-400 mt-2">{valor}</p></div>
}

function Ranking({ titulo, itens }: { titulo: string; itens: RankingItem[] }) {
  return <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6"><h2 className="text-xl font-bold text-white">{titulo}</h2>{itens.length === 0 ? <p className="text-gray-400 mt-4">Nenhum dado disponível.</p> : <div className="mt-4 space-y-3">{itens.slice(0, 10).map((item) => <div key={item.nome} className="flex justify-between rounded-xl bg-[#091a33] p-4 text-gray-200"><span>{item.nome}</span><strong className="text-cyan-400">{item.quantidade}</strong></div>)}</div>}</section>
}
