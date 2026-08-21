"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getMapaEstrategico, type MapaEstrategicoResumo, type RankingItem } from "@/services/modulos-api"

export default function Page() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dados, setDados] = useState<MapaEstrategicoResumo | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")
      getMapaEstrategico(queryString)
        .then((resultado) => { if (ativo) setDados(resultado) })
        .catch(() => { if (ativo) setErro("Não foi possível carregar a inteligência territorial do CTI.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [queryString])

  const periodoExibido = periodo === "TODO_HISTORICO" ? "Todo o histórico" : periodo === "PERSONALIZADO" ? `${dataInicio || "?"} a ${dataFim || "?"}` : periodo.replaceAll("_", " ")

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-7 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">CTI operacional</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Mapa Estratégico</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">Leitura territorial e comercial do mercado refrigerado, cruzando realizado ANFIR, histórico comercial e negociações em curso sem fundir as fontes.</p>
            <p className="mt-2 text-sm text-cyan-300">Contexto: {contextoAtual.label} • Período: {periodoExibido}</p>
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando inteligência territorial...</div>}

          {!loading && dados && <>
            <section className="grid gap-4 md:grid-cols-3">
              <Kpi titulo="ANFIR · realizado" valor={numero(dados.realizado.total_registros)} apoio={moeda(dados.realizado.valor_total)} tom="cyan" />
              <Kpi titulo="Histórico comercial" valor={numero(dados.historico_comercial.total_registros)} apoio={`${numero(dados.historico_comercial.total_unidades)} unidades nominais`} tom="amber" />
              <Kpi titulo="CRM · em curso" valor={numero(dados.em_curso.total_registros)} apoio={moeda(dados.em_curso.valor_pipeline)} tom="emerald" />
            </section>

            <section className="grid gap-5 xl:grid-cols-3">
              <Ranking titulo="Cobertura por estado · ANFIR" itens={dados.realizado.estados} vazio="Nenhum estado classificado no contexto selecionado." />
              <Ranking titulo="Cobertura por município · ANFIR" itens={dados.realizado.municipios} vazio="Nenhum município classificado no contexto selecionado." />
              <Ranking titulo="Cobertura por DDD · ANFIR" itens={dados.realizado.ddds} vazio="Nenhum DDD classificado no contexto selecionado." />
            </section>

            <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Cruzamento por família</p><h2 className="mt-1 text-lg font-semibold">TR · DT · DD nas três camadas</h2></div>
                <p className="text-xs text-slate-500">Comparação visual; totais não são somados.</p>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                {familias(dados).map((item) => <div key={item.nome} className="rounded-xl border border-[#13203f] bg-[#08162d] p-4"><h3 className="font-semibold">{item.nome}</h3><div className="mt-3 space-y-2 text-sm"><Linha rotulo="ANFIR realizado" valor={item.realizado} cor="text-cyan-300"/><Linha rotulo="Histórico comercial" valor={item.historico} cor="text-amber-300"/><Linha rotulo="CRM em curso" valor={item.emCurso} cor="text-emerald-300"/></div></div>)}
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-3">
              <Ranking titulo="Empresas · realizado ANFIR" itens={dados.realizado.empresas} vazio="Nenhuma empresa classificada no realizado." />
              <Ranking titulo="Equipamentos · histórico comercial" itens={dados.historico_comercial.equipamentos} vazio="Nenhum equipamento no histórico para este período." />
              <Ranking titulo="Equipamentos · CRM em curso" itens={dados.em_curso.equipamentos} vazio="Nenhuma negociação ativa classificada por equipamento." />
            </section>

            <section className="grid gap-5 xl:grid-cols-2">
              <Ranking titulo="Implementadoras · realizado ANFIR" itens={dados.realizado.implementadoras} vazio="Nenhuma implementadora classificada." />
              <Ranking titulo="Implementadoras · histórico comercial" itens={dados.historico_comercial.implementadoras} vazio="Nenhuma implementadora identificada no histórico." />
            </section>

            <div className="rounded-xl border border-cyan-500/25 bg-cyan-950/10 p-4 text-sm leading-6 text-cyan-100/80">
              O território é apresentado apenas quando a própria fonte possui geografia. O Histórico Comercial preserva cliente, equipamento e implementadora, mas não recebe estado/DDD artificialmente. A correlação é estratégica, não uma fusão de registros.
            </div>
          </>}
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor, apoio, tom }: { titulo: string; valor: string; apoio: string; tom: "cyan" | "amber" | "emerald" }) {
  const cor = tom === "amber" ? "text-amber-300" : tom === "emerald" ? "text-emerald-300" : "text-cyan-300"
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><p className={`text-xs font-semibold uppercase tracking-[.14em] ${cor}`}>{titulo}</p><strong className="mt-2 block text-3xl">{valor}</strong><p className="mt-1 text-sm text-slate-400">{apoio}</p></div>
}

function Ranking({ titulo, itens, vazio }: { titulo: string; itens: RankingItem[]; vazio: string }) {
  return <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.slice(0, 12).map((item) => <div key={item.nome} className="flex items-center justify-between gap-4 rounded-xl bg-[#08162d] px-3 py-2.5 text-sm"><span className="min-w-0 truncate text-slate-300">{item.nome}</span><strong className="shrink-0 text-cyan-300">{numero(item.quantidade_registros)}</strong></div>)}</div>}</section>
}

function Linha({ rotulo, valor, cor }: { rotulo: string; valor: number; cor: string }) { return <div className="flex items-center justify-between gap-3"><span className="text-slate-400">{rotulo}</span><strong className={cor}>{numero(valor)}</strong></div> }

function familias(dados: MapaEstrategicoResumo) {
  const nomes = ["TR • Trailer", "DT • Diesel Truck", "DD • Direct Drive"]
  const procurar = (itens: RankingItem[] | undefined, nome: string) => itens?.find((item) => item.nome === nome)?.quantidade_registros ?? 0
  return nomes.map((nome) => ({
    nome,
    realizado: procurar(dados.realizado.familias, nome),
    historico: procurar(dados.historico_comercial.familias, nome),
    emCurso: procurar(dados.em_curso.familias, nome),
  }))
}

function numero(valor: number) { return Number(valor || 0).toLocaleString("pt-BR") }
function moeda(valor: number) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
