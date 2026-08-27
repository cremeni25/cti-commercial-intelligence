"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { useOperationalContext } from "@/context/OperationalContext"
import { getMapaEstrategico, type MapaEstrategicoResumo, type RankingItem } from "@/services/modulos-api"

export default function Page() {
  const { usuario } = useAuth()
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
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const escopoExibido = adminMaster ? "Consolidado do contexto selecionado" : `Contexto permitido para ${usuario?.nome || "usuário autenticado"}`

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-7 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">CTI operacional</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Mapa Estratégico</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">Leitura territorial e comercial do mercado refrigerado. Clique em qualquer total individualizável para abrir os registros que o compõem.</p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full border border-cyan-700/70 bg-cyan-950/30 px-3 py-1.5 text-cyan-200">Escopo comercial: {escopoExibido}</span>
              <span className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-slate-300">Sessão: {usuario?.nome || "Usuário autenticado"}</span>
              <span className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-slate-300">Contexto: {contextoAtual.label}</span>
              <span className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-slate-300">Período: {periodoExibido}</span>
            </div>
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando inteligência territorial...</div>}

          {!loading && dados && <>
            <section className="grid gap-4 md:grid-cols-3">
              <Kpi titulo="ANFIR · realizado" valor={numero(dados.realizado.total_registros)} apoio={moeda(dados.realizado.valor_total)} tom="cyan" href={hrefDrill("anfir", undefined, undefined, "ANFIR · realizado", queryString)} />
              <Kpi titulo="Histórico comercial" valor={numero(dados.historico_comercial.total_registros)} apoio={`${numero(dados.historico_comercial.total_unidades)} unidades nominais`} tom="amber" href={hrefDrill("historico", undefined, undefined, "Histórico comercial", queryString)} />
              <Kpi titulo="CRM · em curso" valor={numero(dados.em_curso.total_registros)} apoio={moeda(dados.em_curso.valor_pipeline)} tom="emerald" href={hrefDrill("crm", undefined, undefined, "CRM · negociações em curso", queryString)} />
            </section>

            <section className="grid gap-5 xl:grid-cols-3">
              <Ranking titulo="Cobertura por estado · ANFIR" itens={dados.realizado.estados} vazio="Nenhum estado classificado no contexto selecionado." camada="anfir" campo="estado" queryString={queryString} />
              <Ranking titulo="Cobertura por município · ANFIR" itens={dados.realizado.municipios} vazio="Nenhum município classificado no contexto selecionado." camada="anfir" campo="municipio" queryString={queryString} />
              <Ranking titulo="Cobertura por DDD · ANFIR" itens={dados.realizado.ddds} vazio="Nenhum DDD classificado no contexto selecionado." camada="anfir" campo="ddd" queryString={queryString} />
            </section>

            <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Cruzamento por família</p><h2 className="mt-1 text-lg font-semibold">TR · DT · DD nas três camadas</h2></div><p className="text-xs text-slate-500">Comparação visual; totais não são somados.</p></div>
              <div className="grid gap-3 md:grid-cols-3">
                {familias(dados).map((item) => <div key={item.nome} className="rounded-xl border border-[#13203f] bg-[#08162d] p-4"><h3 className="font-semibold">{item.nome}</h3><div className="mt-3 space-y-2 text-sm"><Linha rotulo="ANFIR realizado" valor={item.realizado} cor="text-cyan-300" href={hrefDrill("anfir", "familia", item.slug, `${item.nome} · ANFIR realizado`, queryString)} /><Linha rotulo="Histórico comercial" valor={item.historico} cor="text-amber-300" href={hrefDrill("historico", "familia", item.slug, `${item.nome} · Histórico comercial`, queryString)} /><Linha rotulo="CRM em curso" valor={item.emCurso} cor="text-emerald-300" href={hrefDrill("crm", "familia", item.slug, `${item.nome} · CRM em curso`, queryString)} /></div></div>)}
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-3">
              <Ranking titulo="Empresas · realizado ANFIR" itens={dados.realizado.empresas} vazio="Nenhuma empresa classificada no realizado." camada="anfir" campo="empresa" queryString={queryString} />
              <Ranking titulo="Equipamentos · histórico comercial" itens={dados.historico_comercial.equipamentos} vazio="Nenhum equipamento no histórico para este período." camada="historico" campo="equipamento" queryString={queryString} />
              <Ranking titulo="Equipamentos · CRM em curso" itens={dados.em_curso.equipamentos} vazio="Nenhuma negociação ativa classificada por equipamento." camada="crm" campo="equipamento" queryString={queryString} />
            </section>

            <section className="grid gap-5 xl:grid-cols-2">
              <Ranking titulo="Implementadoras · realizado ANFIR" itens={dados.realizado.implementadoras} vazio="Nenhuma implementadora classificada." camada="anfir" campo="implementadora" queryString={queryString} />
              <Ranking titulo="Implementadoras · histórico comercial" itens={dados.historico_comercial.implementadoras} vazio="Nenhuma implementadora identificada no histórico." camada="historico" campo="implementadora" queryString={queryString} />
            </section>

            <div className="rounded-xl border border-cyan-500/25 bg-cyan-950/10 p-4 text-sm leading-6 text-cyan-100/80">O detalhamento preserva a origem de cada camada. ANFIR, Histórico Comercial e CRM continuam separados; o drill-down apenas individualiza os registros por trás do total selecionado. A correlação é estratégica, não uma fusão de registros.</div>
          </>}
        </div>
      </section>
    </main>
  )
}

function hrefDrill(camada: "anfir" | "historico" | "crm", campo: string | undefined, valor: string | undefined, titulo: string, base: string) {
  const query = new URLSearchParams(base || "")
  query.set("camada", camada)
  query.set("titulo", titulo)
  query.set("subtitulo", "Registros individualizados que compõem o indicador selecionado")
  if (campo) query.set("campo", campo)
  if (valor) query.set("valor", valor)
  return `/detalhamento?${query.toString()}`
}

function Kpi({ titulo, valor, apoio, tom, href }: { titulo: string; valor: string; apoio: string; tom: "cyan" | "amber" | "emerald"; href: string }) {
  const cor = tom === "amber" ? "text-amber-300" : tom === "emerald" ? "text-emerald-300" : "text-cyan-300"
  return <Link href={href} className="rounded-2xl border border-[#17304d] bg-[#071226] p-5 transition hover:border-cyan-500/70 hover:bg-[#0a1a31]"><p className={`text-xs font-semibold uppercase tracking-[.14em] ${cor}`}>{titulo}</p><strong className="mt-2 block text-3xl">{valor}</strong><p className="mt-1 text-sm text-slate-400">{apoio}</p><p className="mt-3 text-[11px] text-slate-500">Clique para detalhar</p></Link>
}

function Ranking({ titulo, itens, vazio, camada, campo, queryString }: { titulo: string; itens: RankingItem[]; vazio: string; camada: "anfir" | "historico" | "crm"; campo: string; queryString: string }) {
  return <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.slice(0, 12).map((item) => <Link href={hrefDrill(camada, campo, item.nome, `${titulo} · ${item.nome}`, queryString)} key={item.nome} className="flex items-center justify-between gap-4 rounded-xl bg-[#08162d] px-3 py-2.5 text-sm transition hover:bg-[#0b1d38] hover:ring-1 hover:ring-cyan-500/50"><span className="min-w-0 truncate text-slate-300">{item.nome}</span><strong className="shrink-0 text-cyan-300">{numero(item.quantidade_registros)}</strong></Link>)}</div>}</section>
}

function Linha({ rotulo, valor, cor, href }: { rotulo: string; valor: number; cor: string; href: string }) { return <Link href={href} className="flex items-center justify-between gap-3 rounded-lg px-2 py-1 transition hover:bg-[#0b1d38]"><span className="text-slate-400">{rotulo}</span><strong className={cor}>{numero(valor)}</strong></Link> }

function familias(dados: MapaEstrategicoResumo) {
  const itens = [{ nome: "TR • Trailer", slug: "trailer" }, { nome: "DT • Diesel Truck", slug: "diesel-truck" }, { nome: "DD • Direct Drive", slug: "direct-drive" }]
  const procurar = (lista: RankingItem[] | undefined, nome: string) => lista?.find((item) => item.nome === nome)?.quantidade_registros ?? 0
  return itens.map((item) => ({ ...item, realizado: procurar(dados.realizado.familias, item.nome), historico: procurar(dados.historico_comercial.familias, item.nome), emCurso: procurar(dados.em_curso.familias, item.nome) }))
}

function numero(valor: number) { return Number(valor || 0).toLocaleString("pt-BR") }
function moeda(valor: number) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
