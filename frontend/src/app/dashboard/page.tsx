"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type DashboardContextual = {
  total_registros?: number
  total_clientes?: number
  ticket_medio?: number
  ranking_implementadoras?: Array<{ nome: string; quantidade: number }>
  ranking_clientes?: Array<{ nome: string; quantidade: number }>
  metadata?: { total_registros_filtrados?: number }
}

type DashboardCRM = { oportunidades?: number; propostas?: number; pedidos?: number; atividades?: number }
type AgendaItem = { id?: string; cliente_id?: string; oportunidade_id?: string; oportunidade_titulo?: string; titulo?: string; descricao?: string; data?: string; horario?: string; situacao?: string; responsavel_id?: string }
type AgendaResponse = { itens?: AgendaItem[]; resumo?: { atrasadas?: number; hoje?: number; futuras?: number; sem_data?: number } }
type PipelineCard = { id?: string; titulo?: string; cliente_id?: string; etapa?: string; valor_estimado?: number; valor_ponderado?: number; data_fechamento_prevista?: string; ultima_movimentacao?: string; responsavel_id?: string; equipamento?: string }
type PipelineResponse = { cards?: PipelineCard[]; resumo?: { total_oportunidades?: number; valor_total?: number; valor_ponderado?: number } }

type Prioridade = {
  chave: string
  nivel: "ALTA" | "MEDIA" | "BAIXA"
  cliente: string
  titulo: string
  motivo: string
  proximaAcao: string
  data?: string
  valor?: number
  href: string
}

const etapasEncerradas = new Set(["GANHO", "PERDIDO"])

function diasSemMovimento(valor: string | undefined, agoraMs: number) {
  if (!valor || agoraMs <= 0) return 999
  const data = new Date(valor)
  if (Number.isNaN(data.getTime())) return 999
  return Math.max(0, Math.floor((agoraMs - data.getTime()) / 86400000))
}

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dashboard, setDashboard] = useState<DashboardContextual | null>(null)
  const [crm, setCrm] = useState<DashboardCRM | null>(null)
  const [agenda, setAgenda] = useState<AgendaResponse>({})
  const [pipeline, setPipeline] = useState<PipelineResponse>({})
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [agoraMs, setAgoraMs] = useState(0)
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
        fetch(`${API_URL}/crm/dashboard`, { cache: "no-store" }).then((response) => {
          if (!response.ok) throw new Error("dashboard CRM indisponível")
          return response.json()
        }),
        fetch(`${API_URL}/crm/agenda`, { cache: "no-store" }).then((response) => {
          if (!response.ok) throw new Error("agenda indisponível")
          return response.json()
        }),
        fetch(`${API_URL}/crm/pipeline/quadro`, { cache: "no-store" }).then((response) => {
          if (!response.ok) throw new Error("pipeline indisponível")
          return response.json()
        }),
      ])
        .then(([dadosHistoricos, dadosCrm, dadosAgenda, dadosPipeline]) => {
          if (!ativo) return
          const referenciaTemporal = Date.now()
          setDashboard(dadosHistoricos)
          setCrm(dadosCrm)
          setAgenda(dadosAgenda)
          setPipeline(dadosPipeline)
          setAgoraMs(referenciaTemporal)
          setUltimaAtualizacao(new Date(referenciaTemporal).toLocaleString("pt-BR"))
        })
        .catch(() => { if (ativo) setErro("Erro ao carregar a Central de Prioridades Comerciais.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [queryString])

  const prioridades = useMemo<Prioridade[]>(() => {
    const itens: Prioridade[] = []
    const agendaItens = agenda.itens ?? []
    const cards = pipeline.cards ?? []

    agendaItens.filter((item) => item.situacao === "ATRASADA").forEach((item, index) => {
      itens.push({
        chave: `atividade-atrasada-${item.id ?? index}`,
        nivel: "ALTA",
        cliente: item.cliente_id || "Cliente não identificado",
        titulo: item.titulo || item.descricao || "Follow-up atrasado",
        motivo: "Atividade comercial vencida sem conclusão.",
        proximaAcao: "Executar contato e registrar resultado.",
        data: item.data,
        href: "/atividades",
      })
    })

    cards.filter((card) => !etapasEncerradas.has(card.etapa || "")).forEach((card, index) => {
      const temAgenda = agendaItens.some((item) => item.oportunidade_id === card.id && ["ATRASADA", "HOJE", "FUTURA"].includes(item.situacao || ""))
      const semMovimento = diasSemMovimento(card.ultima_movimentacao, agoraMs)
      const fechamento = card.data_fechamento_prevista ? new Date(`${card.data_fechamento_prevista}T00:00:00`) : null
      const fechamentoVencido = Boolean(fechamento && agoraMs > 0 && !Number.isNaN(fechamento.getTime()) && fechamento.getTime() < agoraMs)

      if (!temAgenda) {
        itens.push({
          chave: `sem-acao-${card.id ?? index}`,
          nivel: semMovimento >= 15 ? "ALTA" : "MEDIA",
          cliente: card.cliente_id || "Cliente não identificado",
          titulo: card.titulo || "Oportunidade sem título",
          motivo: semMovimento >= 15 ? `Oportunidade sem movimentação há ${semMovimento} dias e sem próxima ação.` : "Oportunidade aberta sem próxima ação programada.",
          proximaAcao: "Agendar follow-up comercial.",
          data: card.data_fechamento_prevista,
          valor: card.valor_estimado,
          href: "/pipeline",
        })
      } else if (fechamentoVencido) {
        itens.push({
          chave: `fechamento-vencido-${card.id ?? index}`,
          nivel: "ALTA",
          cliente: card.cliente_id || "Cliente não identificado",
          titulo: card.titulo || "Oportunidade sem título",
          motivo: "Data prevista de fechamento vencida.",
          proximaAcao: "Requalificar previsão e atualizar etapa.",
          data: card.data_fechamento_prevista,
          valor: card.valor_estimado,
          href: "/pipeline",
        })
      }
    })

    const peso = { ALTA: 0, MEDIA: 1, BAIXA: 2 }
    return itens.sort((a, b) => peso[a.nivel] - peso[b.nivel] || (b.valor ?? 0) - (a.valor ?? 0))
  }, [agenda, pipeline, agoraMs])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? `${dataInicio || "início não definido"} até ${dataFim || "fim não definido"}`
      : periodo.replaceAll("_", " ").toLowerCase()

  const altas = prioridades.filter((item) => item.nivel === "ALTA").length
  const semAcao = prioridades.filter((item) => item.proximaAcao.includes("Agendar")).length

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <p className="text-cyan-300 text-sm font-semibold">Etapa 17.5</p>
            <h1 className="text-3xl font-bold text-white">Central de Prioridades Comerciais</h1>
            <p className="text-gray-400 mt-2">Onde atuar agora, quais clientes exigem atenção e qual é a próxima ação comercial.</p>
            <p className="text-cyan-300 text-sm mt-2">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </div>

          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-sm text-gray-300">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Info titulo="Período analisado" valor={periodoExibido} />
              <Info titulo="Última atualização" valor={ultimaAtualizacao || "Aguardando carga dos dados."} />
              <Info titulo="Origem dos dados" valor="Base histórica, pipeline e agenda existentes" />
              <Info titulo="Registros após filtros" valor={String(dashboard?.metadata?.total_registros_filtrados ?? 0)} />
            </div>
          </section>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi titulo="Prioridades altas" valor={loading ? "..." : altas} destaque />
            <Kpi titulo="Atividades atrasadas" valor={loading ? "..." : agenda.resumo?.atrasadas ?? 0} destaque />
            <Kpi titulo="Oportunidades sem ação" valor={loading ? "..." : semAcao} />
            <Kpi titulo="Pipeline aberto" valor={loading ? "..." : `R$ ${(pipeline.resumo?.valor_total ?? 0).toLocaleString("pt-BR")}`} />
            <Kpi titulo="Pipeline ponderado" valor={loading ? "..." : `R$ ${(pipeline.resumo?.valor_ponderado ?? 0).toLocaleString("pt-BR")}`} />
            <Kpi titulo="Clientes históricos" valor={loading ? "..." : dashboard?.total_clientes ?? 0} />
          </section>

          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div><h2 className="text-2xl font-bold text-white">Fila de atuação comercial</h2><p className="text-gray-400 mt-1">Ordenada por urgência e potencial financeiro.</p></div>
              <div className="flex gap-3"><Link href="/atividades" className="rounded-xl border border-cyan-500 px-4 py-2 text-cyan-300 hover:bg-cyan-500/10">Abrir agenda</Link><Link href="/pipeline" className="rounded-xl bg-cyan-500 px-4 py-2 font-semibold text-[#020817] hover:bg-cyan-400">Abrir pipeline</Link></div>
            </div>

            {loading ? <p className="mt-6 text-gray-400">Consolidando prioridades reais...</p> : prioridades.length === 0 ? <p className="mt-6 text-green-300">Nenhuma prioridade crítica encontrada. Agenda e pipeline estão cobertos.</p> : (
              <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
                {prioridades.slice(0, 12).map((item) => <PrioridadeCard key={item.chave} item={item} />)}
              </div>
            )}
          </section>

          {!loading && dashboard && (dashboard.total_registros ?? 0) > 0 && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6"><Ranking titulo="Onde vender: clientes com maior presença histórica" itens={dashboard.ranking_clientes ?? []} /><Ranking titulo="Origem comercial: implementadoras mais presentes" itens={dashboard.ranking_implementadoras ?? []} /></div>
          )}

          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Kpi titulo="Oportunidades CRM" valor={loading ? "..." : crm?.oportunidades ?? 0} />
            <Kpi titulo="Propostas CRM" valor={loading ? "..." : crm?.propostas ?? 0} />
            <Kpi titulo="Pedidos CRM" valor={loading ? "..." : crm?.pedidos ?? 0} />
            <Kpi titulo="Ticket histórico" valor={loading ? "..." : `R$ ${(dashboard?.ticket_medio ?? 0).toLocaleString("pt-BR")}`} />
          </section>
        </div>
      </section>
    </main>
  )
}

function PrioridadeCard({ item }: { item: Prioridade }) {
  const classe = item.nivel === "ALTA" ? "border-red-500/60" : item.nivel === "MEDIA" ? "border-amber-500/50" : "border-cyan-500/40"
  return <article className={`rounded-2xl border ${classe} bg-[#091a33] p-5`}><div className="flex items-start justify-between gap-4"><div><span className="text-xs font-bold tracking-widest text-cyan-300">{item.nivel}</span><h3 className="mt-2 text-lg font-bold text-white">{item.titulo}</h3><p className="mt-1 text-sm text-gray-400">{item.cliente}</p></div>{item.valor !== undefined && <strong className="text-cyan-300">R$ {item.valor.toLocaleString("pt-BR")}</strong>}</div><p className="mt-4 text-gray-300">{item.motivo}</p><div className="mt-4 rounded-xl bg-[#020817] p-4"><p className="text-xs uppercase tracking-widest text-gray-500">Próxima ação</p><p className="mt-1 font-semibold text-white">{item.proximaAcao}</p>{item.data && <p className="mt-1 text-sm text-gray-400">Referência: {item.data}</p>}</div><Link href={item.href} className="mt-4 inline-flex text-sm font-semibold text-cyan-300 hover:text-cyan-200">Executar agora →</Link></article>
}

function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-xl border border-[#13203f] bg-[#020817] p-4"><p className="text-cyan-300 font-semibold">{titulo}</p><p className="mt-2 text-gray-300">{valor}</p></div> }
function Kpi({ titulo, valor, destaque = false }: { titulo: string; valor: string | number; destaque?: boolean }) { return <div className={`rounded-2xl bg-[#071226] border p-5 ${destaque ? "border-red-500/50" : "border-[#13203f]"}`}><p className="text-gray-400 text-sm">{titulo}</p><p className={`text-3xl font-bold mt-2 ${destaque ? "text-red-300" : "text-cyan-400"}`}>{valor}</p></div> }
function Ranking({ titulo, itens }: { titulo: string; itens: Array<{ nome: string; quantidade: number }> }) { return <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6"><h2 className="text-xl font-bold text-white">{titulo}</h2>{itens.length === 0 ? <p className="text-gray-400 mt-4">Nenhum dado disponível.</p> : <div className="mt-4 space-y-3">{itens.slice(0, 10).map((item) => <div key={item.nome} className="flex justify-between rounded-xl bg-[#091a33] p-4 text-gray-200"><span>{item.nome}</span><strong className="text-cyan-400">{item.quantidade}</strong></div>)}</div>}</section> }
