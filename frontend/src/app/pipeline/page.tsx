/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type CardPipeline = { id: string; oportunidade_id: string; titulo: string; cliente_nome: string; etapa: string; valor_estimado: number; probabilidade: number; valor_ponderado: number; equipamento?: string; data_fechamento_prevista?: string; ultima_movimentacao?: string }
type QuadroPipeline = { etapas: string[]; cards: CardPipeline[]; resumo: { total_oportunidades: number; valor_total: number; valor_ponderado: number; por_etapa: Record<string, number> } }
const vazio: QuadroPipeline = { etapas: ["OPORTUNIDADE", "ATIVIDADES", "PROPOSTA", "NEGOCIACAO", "PEDIDO", "GANHO", "PERDIDO"], cards: [], resumo: { total_oportunidades: 0, valor_total: 0, valor_ponderado: 0, por_etapa: {} } }
function moeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function percentual(valor: number) { return `${Math.round((valor <= 1 ? valor : valor / 100) * 100)}%` }
function inicioMesAtual() { const agora = new Date(); return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, "0")}-01` }
function fimMesAtual() { const agora = new Date(); return new Date(agora.getFullYear(), agora.getMonth() + 1, 0).toISOString().slice(0, 10) }

export default function PipelinePage() {
  const [quadro, setQuadro] = useState<QuadroPipeline>(vazio)
  const [inicio, setInicio] = useState(inicioMesAtual)
  const [fim, setFim] = useState(fimMesAtual)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    fetch(`${API_URL}/crm-visao/pipeline?inicio=${inicio}&fim=${fim}`, { cache: "no-store" })
      .then(async (response) => { if (!response.ok) throw new Error("Falha ao carregar pipeline"); return response.json() as Promise<QuadroPipeline> })
      .then((dados) => { if (ativo) setQuadro(dados) })
      .catch(() => { if (ativo) setErro("Não foi possível carregar o quadro operacional do pipeline.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [inicio, fim])

  const etapas = useMemo(() => quadro.etapas.filter((etapa) => !["GANHO", "PERDIDO"].includes(etapa)), [quadro.etapas])

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><h1 className="text-3xl font-bold sm:text-4xl">CRM • Pipeline Comercial</h1><p className="mt-2 text-gray-400">Visão por estágio, com uma ficha compacta para cada negociação.</p></div><Link href="/oportunidades?novo=1" className="rounded-xl bg-cyan-500 px-5 py-3 text-center font-semibold text-slate-950">Nova oportunidade</Link></div>
    <section className="grid gap-4 rounded-2xl border border-[#13203f] bg-[#071226] p-5 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto]"><CampoData label="Início" value={inicio} onChange={setInicio} /><CampoData label="Fim" value={fim} onChange={setFim} /><button type="button" onClick={() => { setInicio(inicioMesAtual()); setFim(fimMesAtual()) }} className="self-end rounded-xl border border-cyan-700 px-4 py-3 text-cyan-300">Mês atual</button></section>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
    <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Oportunidades no período" valor={quadro.resumo.total_oportunidades.toLocaleString("pt-BR")} /><Kpi titulo="Pipeline total" valor={moeda(quadro.resumo.valor_total)} /><Kpi titulo="Pipeline ponderado" valor={moeda(quadro.resumo.valor_ponderado)} /></section>
    {loading ? <Aviso>Carregando pipeline...</Aviso> : quadro.cards.length === 0 ? <Aviso>Nenhuma oportunidade encontrada no período.</Aviso> : <div className="overflow-x-auto pb-4"><div className="grid min-w-[1450px] grid-cols-5 gap-4">{etapas.map((etapa) => { const cards = quadro.cards.filter((card) => card.etapa === etapa); return <section key={etapa} className="min-h-[460px] rounded-2xl border border-[#13203f] bg-[#071028]"><header className="flex items-center justify-between border-b border-[#13203f] p-4"><h2 className="font-bold text-cyan-300">{etapa.replaceAll("_", " ")}</h2><span className="rounded-full bg-cyan-500/10 px-2 py-1 text-xs text-cyan-300">{cards.length}</span></header><div className="space-y-3 p-3">{cards.map((card) => <Card key={card.id} card={card} />)}</div></section> })}</div></div>}
  </div></section></main>
}

function Card({ card }: { card: CardPipeline }) { return <article className="rounded-xl border border-[#13203f] bg-[#091a33] p-4"><p className="text-sm font-semibold text-cyan-300">{card.cliente_nome}</p><h3 className="mt-1 font-semibold text-white">{card.titulo}</h3><div className="mt-3 space-y-1 text-xs text-gray-400"><p>{moeda(card.valor_estimado)} • {percentual(card.probabilidade)}</p>{card.equipamento && <p>{card.equipamento}</p>}{card.data_fechamento_prevista && <p>Previsão: {new Date(`${card.data_fechamento_prevista}T12:00:00`).toLocaleDateString("pt-BR")}</p>}</div><Link href={`/oportunidades/${card.oportunidade_id}`} className="mt-4 inline-flex rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Ver detalhes</Link></article> }
function CampoData({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="text-sm text-slate-300">{label}<input type="date" value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" /></label> }
function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-400">{valor}</p></div> }
function Aviso({ children }: { children: React.ReactNode }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-10 text-gray-300">{children}</div> }