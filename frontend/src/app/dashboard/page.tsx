"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"

type DashboardContextual = {
  total_registros?: number
  total_clientes?: number
  total_estados?: number
  total_municipios?: number
  total_implementadoras?: number
  faturamento_total?: number
  ticket_medio?: number
  ranking_implementadoras?: Array<{ nome: string; quantidade: number }>
  ranking_clientes?: Array<{ nome: string; quantidade: number }>
}

export default function DashboardHub() {
  const { contexto, contextoAtual } = useOperationalContext()
  const [dashboard, setDashboard] = useState<DashboardContextual | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true

    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")

      getDashboardExecutivoContextual(contexto)
      .then((dados) => {
        if (ativo) setDashboard(dados)
      })
      .catch(() => {
        if (ativo) setErro("Erro ao carregar o Dashboard Executivo contextualizado.")
      })
      .finally(() => {
        if (ativo) setLoading(false)
      })
    })

    return () => {
      ativo = false
    }
  }, [contexto])

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-white">
              Dashboard Executivo
            </h1>
            <p className="text-gray-400 mt-2">
              Indicadores reais carregados conforme o Contexto Operacional Global.
            </p>
            <p className="text-cyan-300 text-sm mt-2">
              Contexto ativo: {contextoAtual.label} — {contextoAtual.description}
            </p>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi titulo="Registros" valor={loading ? "..." : dashboard?.total_registros ?? 0} />
            <Kpi titulo="Clientes" valor={loading ? "..." : dashboard?.total_clientes ?? 0} />
            <Kpi titulo="Estados" valor={loading ? "..." : dashboard?.total_estados ?? 0} />
            <Kpi titulo="Municípios" valor={loading ? "..." : dashboard?.total_municipios ?? 0} />
            <Kpi titulo="Implementadoras" valor={loading ? "..." : dashboard?.total_implementadoras ?? 0} />
            <Kpi titulo="Ticket médio" valor={loading ? "..." : `R$ ${(dashboard?.ticket_medio ?? 0).toLocaleString("pt-BR")}`} />
          </section>

          {loading ? (
            <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-gray-300">
              Carregando indicadores reais...
            </div>
          ) : !dashboard || (dashboard.total_registros ?? 0) === 0 ? (
            <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-6 text-gray-300">
              Nenhum registro encontrado para o contexto operacional ativo.
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <Ranking titulo="Implementadoras" itens={dashboard.ranking_implementadoras ?? []} />
              <Ranking titulo="Clientes" itens={dashboard.ranking_clientes ?? []} />
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) {
  return (
    <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5">
      <p className="text-gray-400 text-sm">{titulo}</p>
      <p className="text-3xl font-bold text-cyan-400 mt-2">{valor}</p>
    </div>
  )
}

function Ranking({ titulo, itens }: { titulo: string; itens: Array<{ nome: string; quantidade: number }> }) {
  return (
    <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6">
      <h2 className="text-xl font-bold text-white">{titulo}</h2>
      {itens.length === 0 ? (
        <p className="text-gray-400 mt-4">Nenhum dado disponível.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {itens.slice(0, 10).map((item) => (
            <div key={item.nome} className="flex justify-between rounded-xl bg-[#091a33] p-4 text-gray-200">
              <span>{item.nome}</span>
              <strong className="text-cyan-400">{item.quantidade}</strong>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
