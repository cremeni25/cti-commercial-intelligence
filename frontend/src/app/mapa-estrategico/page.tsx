"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import { getMapaEquipeVisao, getMapaInsights, type MapaEquipeVisao, type MapaInsights } from "@/services/mapa-equipe-api"

type SegmentoMacro = {
  codigo: "TR" | "DT" | "DD"
  segmento: string
  mercado: number
  carrier: number
  carrier_percentual_observado: number
  tk: number
  nacional: number
  usado_concorrente: number
  usado_carrier: number
  sem_contato: number
  nao_classificado: number
}

type MercadoMacro = { total: number; foraDisputa: number; real: number; segmentos: SegmentoMacro[] }
type FocoInteligencia = "geral" | "regioes" | "linhas" | "perdas"

const focos: Array<{ id: FocoInteligencia; titulo: string; apoio: string }> = [
  { id: "geral", titulo: "Visão geral", apoio: "Mercado e caminho comercial" },
  { id: "regioes", titulo: "Inteligência de regiões", apoio: "Responsáveis, mercado e ação" },
  { id: "linhas", titulo: "Evolução por linha", apoio: "Trailer, Diesel Truck e Direct Drive" },
  { id: "perdas", titulo: "Onde perdemos e por quê", apoio: "Perdas 2026 e reversão" },
]

export default function Page() {
  const [responsavelId, setResponsavelId] = useState("")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
  const [insights, setInsights] = useState<MapaInsights | null>(null)
  const [mercadoMacro, setMercadoMacro] = useState<MercadoMacro | null>(null)
  const [foco, setFoco] = useState<FocoInteligencia>("geral")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")
    Promise.all([getMapaEquipeVisao(responsavelId || null), getMapaInsights(responsavelId || null)])
      .then(([visao, leitura]) => { if (ativo) { setDados(visao); setInsights(leitura) } })
      .catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar a visão comercial.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [responsavelId])

  useEffect(() => {
    let ativo = true
    setMercadoMacro(null)
    void (async () => {
      try {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.auth.getSession()
        const token = data.session?.access_token
        if (error || !token) return
        const qs = new URLSearchParams()
        if (responsavelId) qs.set("responsavel_id", responsavelId)
        const resposta = await fetch(`/api/cti/analytics/anfir-workbook-2026${qs.toString() ? `?${qs.toString()}` : ""}`, {
          cache: "no-store",
          headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
        })
        if (!resposta.ok) return
        const payload = await resposta.json() as {
          mercado_viena?: { mercado_anfir_total?: number; mercado_fora_escopo_comercial?: number; mercado_disputavel_viena?: number }
          inteligencia_viena?: { segmentos?: SegmentoMacro[] }
        }
        if (!ativo || !payload.mercado_viena) return
        setMercadoMacro({
          total: Number(payload.mercado_viena.mercado_anfir_total || 0),
          foraDisputa: Number(payload.mercado_viena.mercado_fora_escopo_comercial || 0),
          real: Number(payload.mercado_viena.mercado_disputavel_viena || 0),
          segmentos: Array.isArray(payload.inteligencia_viena?.segmentos) ? payload.inteligencia_viena!.segmentos! : [],
        })
      } catch {
        if (ativo) setMercadoMacro(null)
      }
    })()
    return () => { ativo = false }
  }, [responsavelId])

  const familiaTotal = useMemo(() => {
    if (!dados) return 0
    const f = dados.mercado.familias
    return f.trailer + f.diesel_truck + f.direct_drive
  }, [dados])

  function trocarResponsavel(novoId: string) {
    setFoco("geral")
    setResponsavelId(novoId)
  }

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-4 p-4 sm:p-6 lg:p-8">
        <header className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Inteligência comercial</p>
            <h1 className="mt-1 text-3xl font-bold">Mapa Comercial Estratégico</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">Mercado, evolução competitiva, acompanhamento e resultado comercial de 2026.</p>
          </div>
          {dados?.pode_selecionar_responsavel && <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">Responsável comercial<select value={responsavelId} onChange={(e) => trocarResponsavel(e.target.value)} className="mt-2 w-full rounded-xl border border-[#214363] bg-[#071226] px-4 py-3 text-sm font-medium normal-case tracking-normal text-white outline-none focus:border-cyan-400"><option value="">Toda a equipe comercial</option>{dados.equipe.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}</select></label>}
        </header>
        {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
        {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando informações comerciais...</div>}
        {!loading && dados && insights && <VisaoComercial dados={dados} insights={insights} mercadoMacro={mercadoMacro} familiaTotal={familiaTotal} foco={foco} setFoco={setFoco} responsavelId={responsavelId || undefined} />}
      </div>
    </section>
  </main>
}

function VisaoComercial({ dados, insights, mercadoMacro, familiaTotal, foco, setFoco, responsavelId }: {
  dados: MapaEquipeVisao; insights: MapaInsights; mercadoMacro: MercadoMacro | null; familiaTotal: number; foco: FocoInteligencia; setFoco: (f: FocoInteligencia) => void; responsavelId?: string
}) {
  const consolidado = insights.escopo.consolidado
  const ticketPipeline = dados.evidencias.crm_ativos ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos : 0
  const hrefAnfir = mapaDetalhe({ camada: "anfir", responsavelId, titulo: "Mercado ANFIR 2026", subtitulo: "Unidades que formam exatamente este total" })
  const hrefCrm = mapaDetalhe({ camada: "crm", responsavelId, titulo: "Negociações em andamento", subtitulo: "Negócios ativos que formam exatamente este total" })
  const valorMercado = consolidado && !responsavelId && mercadoMacro ? mercadoMacro.real : dados.mercado.mercado_real_selecao_2026
  const hrefMercado = consolidado && !responsavelId
    ? detalheGeral({ camada: "anfir", mercado: "DISPUTAVEL_VIENA", titulo: "Mercado Real Viena 2026", subtitulo: "Registros após retirada do mercado fora do escopo comercial" })
    : hrefAnfir

  return <>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Kpi href={hrefMercado} titulo={consolidado && !responsavelId ? "Mercado Real Viena" : "Meu mercado 2026"} valor={valorMercado} apoio="ANFIR 2026 · abrir unidades" destaque="emerald" />
      <Kpi href={hrefAnfir} titulo={consolidado ? "Mercado identificado" : "Registros no meu mercado"} valor={dados.mercado.mercado_real_selecao_2026} apoio={`${dados.selecao.nome} · abrir evidências`} destaque="cyan" />
      <Kpi href={hrefCrm} titulo="Negociações em andamento" valor={dados.evidencias.crm_ativos} apoio="CRM atual · abrir negócios" destaque="emerald" />
      <Kpi href={hrefCrm} titulo="Pipeline atual" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} apoio={dados.evidencias.crm_ativos ? `ticket médio ${formatarMoeda(ticketPipeline)}` : "sem negócios ativos"} />
    </section>

    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{focos.map((item) => <button key={item.id} type="button" onClick={() => setFoco(item.id)} className={`rounded-2xl border p-4 text-left transition ${foco === item.id ? "border-cyan-400 bg-cyan-500/10" : "border-[#17304d] bg-[#071226] hover:border-cyan-500/40"}`}><strong className={foco === item.id ? "text-cyan-300" : "text-white"}>{item.titulo}</strong><span className="mt-1 block text-xs text-slate-500">{item.apoio}</span></button>)}</section>

    {foco === "geral" && <VisaoGeral dados={dados} mercadoMacro={mercadoMacro} familiaTotal={familiaTotal} consolidado={consolidado} responsavelId={responsavelId} />}
    {foco === "regioes" && <VisaoRegioes insights={insights} />}
    {foco === "linhas" && <VisaoLinhas insights={insights} mercadoMacro={mercadoMacro} responsavelId={responsavelId} />}
    {foco === "perdas" && <VisaoPerdas insights={insights} responsavelId={responsavelId} />}

    <details className="rounded-2xl border border-slate-700/50 bg-[#061126] px-5 py-4"><summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Dados de apoio e auditoria</summary><div className="mt-4 grid gap-3 border-t border-slate-700/50 pt-4 sm:grid-cols-3"><MiniKpi rotulo="Registros históricos 2026" valor={dados.evidencias.historico_registros_2026} /><MiniKpi rotulo="Unidades históricas 2026" valor={dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} /><MiniKpi rotulo="Clientes históricos" valor={dados.reconciliacao.clientes_historico} /></div></details>
  </>
}

function VisaoGeral({ dados, mercadoMacro, familiaTotal, consolidado, responsavelId }: { dados: MapaEquipeVisao; mercadoMacro: MercadoMacro | null; familiaTotal: number; consolidado: boolean; responsavelId?: string }) {
  const semCrm = Math.max(0, dados.ciclo.clientes_mercado_real - dados.ciclo.crm_com_evidencia_anfir)
  return <section className="space-y-4">
    {consolidado && !responsavelId && <div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Base executiva auditável · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Mercado total → retiradas → mercado real Viena</h2><p className="mt-2 text-sm text-slate-400">Número e percentual sobre a mesma base. O mercado total e o mercado real podem ser abertos até os registros que os formam.</p>{mercadoMacro ? <div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div> : <p className="mt-4 text-sm text-slate-500">Aguardando composição auditável do mercado.</p>}</div>}

    <div className="grid gap-4 xl:grid-cols-2">
      <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Composição por linha</p><h2 className="mt-1 text-xl font-bold">Onde está o volume da seleção</h2><div className="mt-5 space-y-3"><BarraComercial href={mapaDetalhe({ camada: "anfir", responsavelId, familia: "trailer", titulo: "Trailer · ANFIR 2026", subtitulo: "Unidades que formam o total de Trailer" })} nome="Trailer" valor={dados.mercado.familias.trailer} total={Math.max(1, familiaTotal)} /><BarraComercial href={mapaDetalhe({ camada: "anfir", responsavelId, familia: "diesel-truck", titulo: "Diesel Truck · ANFIR 2026", subtitulo: "Unidades que formam o total de Diesel Truck" })} nome="Diesel Truck" valor={dados.mercado.familias.diesel_truck} total={Math.max(1, familiaTotal)} /><BarraComercial href={mapaDetalhe({ camada: "anfir", responsavelId, familia: "direct-drive", titulo: "Direct Drive · ANFIR 2026", subtitulo: "Unidades que formam o total de Direct Drive" })} nome="Direct Drive" valor={dados.mercado.familias.direct_drive} total={Math.max(1, familiaTotal)} /></div></div>
      <div className="rounded-3xl border border-violet-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-300">Caminho comercial</p><h2 className="mt-1 text-xl font-bold">Mercado → Histórico/Funil → CRM → evidência ANFIR</h2><p className="mt-2 text-sm text-slate-400">As fontes permanecem separadas; a inteligência mostra onde houve acompanhamento e onde o mercado apareceu sem evidência comercial anterior.</p><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5"><MiniKpi rotulo="Clientes no mercado" valor={dados.ciclo.clientes_mercado_real} /><MiniKpi rotulo="No Histórico/Funil" valor={dados.ciclo.clientes_historico_2026} /><MiniKpi rotulo="No CRM" valor={dados.ciclo.clientes_crm} /><MiniKpi rotulo="CRM + ANFIR" valor={dados.ciclo.crm_com_evidencia_anfir} /><MiniKpi rotulo="Mercado sem CRM" valor={semCrm} destaque="amber" /></div><div className="mt-4 flex flex-wrap gap-2 text-xs"><Link className="rounded-lg border border-cyan-700 px-3 py-2 text-cyan-200" href={mapaDetalhe({ camada: "anfir", responsavelId, titulo: "ANFIR 2026", subtitulo: "Registros do mercado observado" })}>Abrir ANFIR</Link><Link className="rounded-lg border border-violet-700 px-3 py-2 text-violet-200" href={mapaDetalhe({ camada: "historico", responsavelId, titulo: "Histórico/Funil 2026", subtitulo: "Registros históricos da seleção" })}>Abrir Histórico/Funil</Link><Link className="rounded-lg border border-emerald-700 px-3 py-2 text-emerald-200" href={mapaDetalhe({ camada: "crm", responsavelId, titulo: "CRM atual", subtitulo: "Negócios ativos da seleção" })}>Abrir CRM</Link></div></div>
    </div>
  </section>
}

function VisaoRegioes({ insights }: { insights: MapaInsights }) {
  return <section className="space-y-4"><div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Inteligência de regiões · 2026</p><h2 className="mt-1 text-xl font-bold">Mercado e atuação por responsável comercial</h2><p className="mt-2 text-sm text-slate-400">Responsabilidade comercial prevalece; DDD não redistribui mercado entre pessoas.</p></div><div className="grid gap-4 xl:grid-cols-2">{insights.regioes.map((item) => <article key={item.id} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Responsável comercial</p><h3 className="mt-1 text-lg font-bold">{item.nome}</h3></div><Link href={mapaDetalhe({ camada: "anfir", responsavelId: item.id, titulo: `Mercado 2026 · ${item.nome}`, subtitulo: "Unidades atribuídas a este responsável" })} className="text-right"><strong className="text-2xl text-cyan-300 underline decoration-cyan-500/40 underline-offset-4">{item.mercado_2026}</strong><p className="text-xs text-slate-500">abrir unidades</p></Link></div><div className="mt-4"><GraficoLinha valores={item.mercado_mensal} meses={insights.meses} rotulo="Movimento mensal" /></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Clientes" valor={item.clientes_mercado} /><MiniKpi rotulo="Negócios ativos" valor={item.crm_ativos} /><MiniKpi rotulo="Pipeline" valor={formatarMoeda(item.pipeline_ativo)} /></div><LeituraAcao leitura={item.leitura_comercial} acao={item.acao_recomendada} /></article>)}</div></section>
}

function VisaoLinhas({ insights, mercadoMacro, responsavelId }: { insights: MapaInsights; mercadoMacro: MercadoMacro | null; responsavelId?: string }) {
  return <section className="space-y-4"><div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Evolução por linha · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Como cada linha está se movimentando no ano</h2><p className="mt-2 text-sm text-slate-400">Movimento mensal ANFIR 2026 com leitura competitiva observada na mesma base.</p></div><div className="grid gap-4 xl:grid-cols-3">{insights.linhas_2026.linhas.map((linha) => { const codigo = linha.codigo === "trailer" ? "TR" : linha.codigo === "diesel_truck" ? "DT" : "DD"; const competitivo = mercadoMacro?.segmentos.find((i) => i.codigo === codigo); const concorrencia = competitivo ? competitivo.tk + competitivo.nacional + competitivo.usado_concorrente : 0; const familia = linha.codigo === "diesel_truck" ? "diesel-truck" : linha.codigo === "direct_drive" ? "direct-drive" : "trailer"; return <article key={linha.codigo} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><div className="flex items-end justify-between gap-3"><div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Linha de produto</p><h3 className="mt-1 text-lg font-bold">{linha.nome}</h3></div><Link href={mapaDetalhe({ camada: "anfir", responsavelId, familia, titulo: `${linha.nome} · ANFIR 2026`, subtitulo: "Unidades individualizadas desta linha" })} className="text-right"><strong className="text-2xl text-cyan-300 underline decoration-cyan-500/40 underline-offset-4">{linha.total_2026}</strong><span className="block text-[10px] text-slate-500">abrir unidades</span></Link></div><div className="mt-4"><GraficoLinha valores={linha.mensal} meses={insights.linhas_2026.meses} rotulo={`Movimento mensal de ${linha.nome}`} /></div>{competitivo && <div className="mt-4"><ComparativoCompetitivo mercado={competitivo.mercado} carrier={competitivo.carrier} concorrencia={concorrencia} semContato={competitivo.sem_contato} /></div>}<LeituraAcao leitura={linha.leitura_comercial} acao={linha.acao_recomendada} /></article> })}</div>{insights.linhas_2026.nao_classificado_2026 > 0 && <p className="px-1 text-xs text-amber-300">Há {insights.linhas_2026.nao_classificado_2026} unidade(s) ainda sem linha classificada; nenhuma foi forçada para uma família.</p>}</section>
}

function VisaoPerdas({ insights, responsavelId }: { insights: MapaInsights; responsavelId?: string }) {
  const totalMotivos = Math.max(1, insights.perdas.total_com_motivo)
  const totalLinhas = Math.max(1, insights.perdas.por_linha.reduce((s, i) => s + i.quantidade, 0))
  return <section className="space-y-4"><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Perdas comerciais · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Onde perdemos e por quê</h2></div><Link href={mapaDetalhe({ camada: "anfir", responsavelId, somentePerdas: true, titulo: "Perdas identificadas · ANFIR 2026", subtitulo: "Somente os registros que compõem o total de perdas" })} className="text-right"><strong className="text-3xl text-amber-300 underline decoration-amber-500/40 underline-offset-4">{insights.perdas.total_perdido}</strong><p className="text-xs text-slate-500">abrir perdas</p></Link></div><div className="mt-5"><GraficoLinha valores={insights.perdas.mensal} meses={insights.meses} rotulo="Evolução mensal das perdas" /></div><LeituraAcao leitura={insights.perdas.leitura_comercial} acao={insights.perdas.acao_recomendada} destaque="amber" /></div><div className="grid gap-4 xl:grid-cols-2"><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><h3 className="text-lg font-bold">Por que perdemos</h3><div className="mt-5 space-y-3">{insights.perdas.motivos.length ? insights.perdas.motivos.map((i) => <BarraComercial key={i.nome} nome={i.nome.replaceAll("_", " ")} valor={i.quantidade} total={totalMotivos} />) : <p className="text-sm text-slate-500">Sem motivo estruturado suficiente.</p>}</div></div><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><h3 className="text-lg font-bold">Onde perdemos</h3><div className="mt-5 space-y-3">{insights.perdas.por_linha.length ? insights.perdas.por_linha.map((i) => <BarraComercial key={i.nome} nome={i.nome} valor={i.quantidade} total={totalLinhas} />) : <p className="text-sm text-slate-500">Sem linha classificada nas perdas.</p>}</div></div></div></section>
}

function ComparativoCompetitivo({ mercado, carrier, concorrencia, semContato }: { mercado: number; carrier: number; concorrencia: number; semContato: number }) {
  const base = Math.max(1, mercado)
  return <div className="rounded-2xl border border-slate-700/50 bg-[#071226] p-3"><p className="mb-3 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">Leitura competitiva observada</p><div className="space-y-2"><BarraComercial nome="Carrier observado" valor={carrier} total={base} /><BarraComercial nome="Concorrência identificada" valor={concorrencia} total={base} /><BarraComercial nome="Sem contato" valor={semContato} total={base} /></div></div>
}

function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) {
  const foraPct = pct(fora, total), realPct = pct(real, total)
  return <div><div className="grid gap-3 sm:grid-cols-3"><Link href={detalheGeral({ camada: "anfir", titulo: "Mercado total ANFIR 2026", subtitulo: "Todos os registros da base ANFIR no recorte autorizado" })}><MiniKpi rotulo="1 · Mercado total ANFIR" valor={`${total} · 100%`} /></Link><MiniKpi rotulo="2 · Empresas retiradas" valor={`${fora} · ${foraPct.toFixed(1)}%`} destaque="amber" /><Link href={detalheGeral({ camada: "anfir", mercado: "DISPUTAVEL_VIENA", titulo: "Mercado Real Viena 2026", subtitulo: "Registros após retirada das empresas fora do escopo comercial" })}><MiniKpi rotulo="3 · Mercado Real Viena" valor={`${real} · ${realPct.toFixed(1)}%`} /></Link></div><div className="mt-4 flex h-5 overflow-hidden rounded-full bg-slate-900"><div className="bg-amber-500" style={{ width: `${foraPct}%` }} /><div className="bg-emerald-500" style={{ width: `${realPct}%` }} /></div><div className="mt-2 flex justify-end gap-4 text-xs"><span className="text-amber-300">Retirado {foraPct.toFixed(1)}%</span><span className="text-emerald-300">Mercado real {realPct.toFixed(1)}%</span></div></div>
}

function mapaDetalhe({ camada, responsavelId, familia, somentePerdas, titulo, subtitulo }: { camada: "anfir" | "historico" | "crm"; responsavelId?: string; familia?: string; somentePerdas?: boolean; titulo: string; subtitulo: string }) {
  const qs = new URLSearchParams({ origem: "mapa", camada, titulo, subtitulo })
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  if (familia) qs.set("familia", familia)
  if (somentePerdas) qs.set("somente_perdas", "true")
  return `/detalhamento?${qs.toString()}`
}

function detalheGeral({ camada, mercado, titulo, subtitulo }: { camada: "anfir" | "historico" | "crm"; mercado?: string; titulo: string; subtitulo: string }) {
  const qs = new URLSearchParams({ camada, titulo, subtitulo })
  if (camada !== "crm") { qs.set("contexto", "viena_sp"); qs.set("periodo", "ANO_ATUAL") }
  if (mercado) qs.set("mercado", mercado)
  return `/detalhamento?${qs.toString()}`
}

function Kpi({ titulo, valor, apoio, destaque, href }: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald"; href?: string }) { const cor = destaque === "emerald" ? "text-emerald-300" : destaque === "cyan" ? "text-cyan-300" : "text-white"; const corpo = <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><div className={`mt-2 text-2xl font-bold ${cor}`}>{valor}</div>{apoio && <p className="mt-1 text-xs text-slate-500">{apoio}</p>}</div>; return href ? <Link href={href} className="block transition hover:-translate-y-0.5">{corpo}</Link> : corpo }
function MiniKpi({ rotulo, valor, destaque }: { rotulo: string; valor: string | number; destaque?: "amber" }) { return <div className="rounded-xl border border-[#17304d] bg-[#09152a] p-3"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{rotulo}</p><strong className={`mt-1 block text-lg ${destaque === "amber" ? "text-amber-300" : "text-white"}`}>{valor}</strong></div> }
function BarraComercial({ nome, valor, total, href }: { nome: string; valor: number; total: number; href?: string }) { const percentual = pct(valor, total); const corpo = <><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="font-medium text-slate-300">{nome}</span><span className="font-semibold text-cyan-300">{valor} · {percentual.toFixed(0)}%</span></div><div className="h-3 overflow-hidden rounded-full bg-[#0b2040]"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(100, percentual)}%` }} /></div></>; return href ? <Link href={href} className="block rounded-lg p-1 hover:bg-cyan-500/5">{corpo}</Link> : <div>{corpo}</div> }
function LeituraAcao({ leitura, acao, destaque = "cyan" }: { leitura: string; acao: string; destaque?: "cyan" | "amber" }) { return <div className="mt-5 grid gap-3 border-t border-slate-700/50 pt-4 md:grid-cols-2"><div><p className={`text-[11px] font-semibold uppercase tracking-[.14em] ${destaque === "amber" ? "text-amber-300" : "text-cyan-300"}`}>Leitura comercial</p><p className="mt-2 text-sm leading-6 text-slate-300">{leitura}</p></div><div><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-emerald-300">O que fazer</p><p className="mt-2 text-sm leading-6 text-slate-300">{acao}</p></div></div> }
function GraficoLinha({ valores, meses, rotulo }: { valores: number[]; meses: string[]; rotulo: string }) { const serie = Array.from({ length: 12 }, (_, i) => Number(valores[i] || 0)); const max = Math.max(1, ...serie), w = 720, h = 180, mx = 22, my = 18, passo = (w - mx * 2) / 11; const pts = serie.map((valor, i) => ({ x: mx + i * passo, y: h - my - (valor / max) * (h - my * 2), valor })); const path = pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "); return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-3" aria-label={rotulo}><svg viewBox={`0 0 ${w} ${h + 26}`} className="h-48 w-full"><line x1={mx} y1={h-my} x2={w-mx} y2={h-my} stroke="currentColor" className="text-slate-700"/><path d={path} fill="none" stroke="currentColor" className="text-cyan-400" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>{pts.map((p,i)=><g key={i}><circle cx={p.x} cy={p.y} r="4" fill="currentColor" className="text-cyan-300"/><text x={p.x} y={Math.max(12,p.y-9)} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-300">{p.valor||""}</text></g>)}{meses.slice(0,12).map((m,i)=><text key={m+i} x={mx+i*passo} y={h+12} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-500">{m}</text>)}</svg></div> }
function pct(valor: number, total: number) { return total > 0 ? valor / total * 100 : 0 }
function formatarMoeda(valor: number) { return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(valor || 0) }
