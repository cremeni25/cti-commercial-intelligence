"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type DashboardContextual = {
  total_registros?: number
  total_clientes?: number
  total_estados?: number
  total_municipios?: number
  total_implementadoras?: number
  ticket_medio?: number
  ranking_implementadoras?: Array<{ nome: string; quantidade: number }>
  ranking_clientes?: Array<{ nome: string; quantidade: number }>
  metadata?: { contexto?: string; periodo?: string; inicio?: string | null; fim?: string | null; total_registros_filtrados?: number }
}

type DashboardCRM = { oportunidades?: number; propostas?: number; pedidos?: number; atividades?: number }

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dashboard, setDashboard] = useState<DashboardContextual | null>(null)
  const [crm, setCrm] = useState<DashboardCRM | null>(null)
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    Promise.all([
      getDashboardExecutivoContextual(queryString),
      fetch(`${API_URL}/crm/dashboard`, { cache: "no-store" }).then((response) => response.json()),
    ])
      .then(([dadosHistoricos, dadosCrm]) => {
        if (!ativo) return
        setDashboard(dadosHistoricos)
        setCrm(dadosCrm)
        setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
      })
      .catch(() => { if (ativo) setErro("Erro ao carregar o Dashboard Executivo contextualizado.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [queryString])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? `${dataInicio || "início não definido"} até ${dataFim || "fim não definido"}`
      : periodo.replaceAll("_", " ").toLowerCase()

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard Executivo</h1>
            <p className="text-gray-400 mt-2">Indicadores históricos filtrados pelo território e período globais; CRM operacional apresentado separadamente.</p>
            <p className="text-cyan-300 text-sm mt-2">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </div>

          <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-sm text-gray-300">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Info titulo="Período analisado" valor={periodoExibido} />
              <Info titulo="Última atualização" valor={ultimaAtualizacao || "Aguardando carga dos dados."} />
              <Info titulo="Origem dos dados" valor="Base histórica CTI/ANFIR e CRM operacional" />
              <Info titulo="Registros após filtros" valor={String(dashboard?.metadata?.total_registros_filtrados ?? 0)} />
            </div>
          </section>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi titulo="Oportunidades CRM" valor={loading ? "..." : crm?.oportunidades ?? 0} />
            <Kpi titulo="Propostas CRM" valor={loading ? "..." : crm?.propostas ?? 0} />
            <Kpi titulo="Pedidos CRM" valor={loading ? "..." : crm?.pedidos ?? 0} />
            <Kpi titulo="Atividades CRM" valor={loading ? "..." : crm?.atividades ?? 0} />
            <Kpi titulo="Clientes históricos" valor={loading ? "..." : dashboard?.total_clientes ?? 0} />
            <Kpi titulo="Ticket histórico" valor={loading ? "..." : `R$ ${(dashboard?.ticket_medio ?? 0).toLocaleString("pt-BR")}`} />
          </section>

          {loading ? (
            <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-gray-300">Carregando indicadores reais...</div>
          ) : !dashboard || (dashboard.total_registros ?? 0) === 0 ? (
            <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-gray-300">Não há dados históricos com a combinação atual de território e período.</div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6"><Ranking titulo="Implementadoras" itens={dashboard.ranking_implementadoras ?? []} /><Ranking titulo="Clientes" itens={dashboard.ranking_clientes ?? []} /></div>
          )}
        </div>
      </section>
    </main>
  )
}

function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-xl border border-[#13203f] bg-[#020817] p-4"><p className="text-cyan-300 font-semibold">{titulo}</p><p className="mt-2 text-gray-300">{valor}</p></div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5"><p className="text-gray-400 text-sm">{titulo}</p><p className="text-3xl font-bold text-cyan-400 mt-2">{valor}</p></div> }
function Ranking({ titulo, itens }: { titulo: string; itens: Array<{ nome: string; quantidade: number }> }) { return <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6"><h2 className="text-xl font-bold text-white">{titulo}</h2>{itens.length === 0 ? <p className="text-gray-400 mt-4">Nenhum dado disponível.</p> : <div className="mt-4 space-y-3">{itens.slice(0, 10).map((item) => <div key={item.nome} className="flex justify-between rounded-xl bg-[#091a33] p-4 text-gray-200"><span>{item.nome}</span><strong className="text-cyan-400">{item.quantidade}</strong></div>)}</div>}</section> }
