"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type CardPipeline = {
  id: string
  oportunidade_id: string
  titulo: string
  cliente_id?: string
  responsavel_id?: string
  etapa: string
  valor_estimado: number
  probabilidade: number
  valor_ponderado: number
  equipamento?: string
  implementadora?: string
  municipio?: string
  estado?: string
  data_fechamento_prevista?: string
  ultima_movimentacao?: string
}

type QuadroPipeline = {
  etapas: string[]
  cards: CardPipeline[]
  resumo: {
    total_oportunidades: number
    valor_total: number
    valor_ponderado: number
    por_etapa: Record<string, number>
  }
}

const vazio: QuadroPipeline = {
  etapas: ["OPORTUNIDADE", "ATIVIDADES", "PROPOSTA", "NEGOCIACAO", "PEDIDO", "GANHO", "PERDIDO"],
  cards: [],
  resumo: { total_oportunidades: 0, valor_total: 0, valor_ponderado: 0, por_etapa: {} },
}

function moeda(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function percentual(valor: number) {
  return `${Math.round((valor <= 1 ? valor : valor / 100) * 100)}%`
}

export default function PipelinePage() {
  const [quadro, setQuadro] = useState<QuadroPipeline>(vazio)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    fetch(`${API_URL}/crm/pipeline/quadro`)
      .then(async (response) => {
        if (!response.ok) throw new Error("Falha ao carregar pipeline")
        return response.json() as Promise<QuadroPipeline>
      })
      .then((dados) => { if (ativo) setQuadro(dados) })
      .catch(() => { if (ativo) setErro("Não foi possível carregar o quadro operacional do pipeline.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white">CRM • Pipeline Comercial</h1>
              <p className="mt-2 text-gray-400">Fotografia atual de cada oportunidade, sem duplicar o histórico de movimentações.</p>
            </div>
            <Link href="/oportunidades?novo=1" className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova oportunidade</Link>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Kpi titulo="Oportunidades atuais" valor={quadro.resumo.total_oportunidades.toLocaleString("pt-BR")} />
            <Kpi titulo="Pipeline total" valor={moeda(quadro.resumo.valor_total)} />
            <Kpi titulo="Pipeline ponderado" valor={moeda(quadro.resumo.valor_ponderado)} />
          </section>

          <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-5 text-sm text-gray-300">
            <h2 className="mb-2 font-semibold text-white">Integração com a base existente</h2>
            <p>As oportunidades são vinculadas aos clientes já identificados no Cadastro Mestre. Equipamento, implementadora, território, valor e probabilidade permanecem associados à oportunidade comercial, enquanto o histórico de movimentações continua preservado separadamente.</p>
          </div>

          {loading ? <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-10 text-gray-400">Carregando pipeline...</div> : quadro.cards.length === 0 ? (
            <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-10 text-gray-300">
              <p>Nenhuma oportunidade operacional cadastrada.</p>
              <Link href="/oportunidades?novo=1" className="mt-4 inline-block rounded-xl bg-cyan-500 px-4 py-2 font-semibold text-slate-950">Cadastrar primeira oportunidade</Link>
            </div>
          ) : (
            <div className="overflow-x-auto pb-4">
              <div className="grid min-w-[1750px] grid-cols-7 gap-4">
                {quadro.etapas.map((etapa) => {
                  const cards = quadro.cards.filter((card) => card.etapa === etapa)
                  return (
                    <section key={etapa} className="min-h-[520px] rounded-2xl border border-[#13203f] bg-[#071028]">
                      <header className="flex items-center justify-between border-b border-[#13203f] p-4">
                        <h2 className="font-bold text-cyan-300">{etapa.replaceAll("_", " ")}</h2>
                        <span className="rounded-full bg-cyan-500/10 px-2 py-1 text-xs text-cyan-300">{cards.length}</span>
                      </header>
                      <div className="space-y-3 p-3">
                        {cards.map((card) => <Card key={card.id} card={card} />)}
                      </div>
                    </section>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

function Card({ card }: { card: CardPipeline }) {
  return (
    <article className="rounded-xl border border-[#13203f] bg-[#091a33] p-4">
      <h3 className="font-semibold text-white">{card.titulo}</h3>
      <p className="mt-1 text-sm text-cyan-300">{card.cliente_id || "Cliente não informado"}</p>
      <div className="mt-3 space-y-1 text-xs text-gray-400">
        <p>{moeda(card.valor_estimado)} • {percentual(card.probabilidade)}</p>
        <p>Ponderado: {moeda(card.valor_ponderado)}</p>
        {card.equipamento && <p>Equipamento: {card.equipamento}</p>}
        {card.implementadora && <p>Implementadora: {card.implementadora}</p>}
        {(card.municipio || card.estado) && <p>Território: {[card.municipio, card.estado].filter(Boolean).join(" / ")}</p>}
      </div>
    </article>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-400">{valor}</p></div>
}
