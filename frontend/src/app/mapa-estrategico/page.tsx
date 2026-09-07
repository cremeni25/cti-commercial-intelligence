"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import { getMapaEquipeVisao, getMapaInsights, type MapaEquipeVisao, type MapaInsights } from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }
type FocoInteligencia = "geral" | "regioes" | "linhas" | "perdas"

const focos: Array<{ id: FocoInteligencia; titulo: string; apoio: string }> = [
  { id: "geral", titulo: "Visão geral", apoio: "Mercado e CRM" },
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
    Promise.all([getMapaEquipeVisao(responsavelId || null), getMapaInsights(responsavelId || null)])
      .then(([visao, leitura]) => {
        if (!ativo) return
        setDados(visao)
        setInsights(leitura)
      })
      .catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar a visão comercial.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [responsavelId])

  useEffect(() => {
    if (!dados?.pode_selecionar_responsavel) return
    let ativo = true
    void (async () => {
      try {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.auth.getSession()
        const token = data.session?.access_token
        if (error || !token) return
        const resposta = await fetch("/api/cti/analytics/anfir-workbook-2026", {
          cache: "no-store",
          headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
        })
        if (!resposta.ok) return
        const payload = await resposta.json() as { mercado_viena?: { mercado_anfir_total?: number; mercado_fora_escopo_comercial?: number; mercado_disputavel_viena?: number } }
        if (!ativo || !payload.mercado_viena) return
        setMercadoMacro({
          total: Number(payload.mercado_viena.mercado_anfir_total || 0),
          foraDisputa: Number(payload.mercado_viena.mercado_fora_escopo_comercial || 0),
          real: Number(payload.mercado_viena.mercado_disputavel_viena || 0),
        })
      } catch {
        // O consolidado é opcional; a visão individual permanece protegida por login.
      }
    })()
    return () => { ativo = false }
  }, [dados?.pode_selecionar_responsavel])

  const familiaTotal = useMemo(() => {
    if (!dados) return 0
    const f = dados.mercado.familias
    return f.trailer + f.diesel_truck + f.direct_drive
  }, [dados])

  function trocarResponsavel(novoId: string) {
    setLoading(true)
    setErro("")
    setFoco("geral")
    setResponsavelId(novoId)
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-4 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Inteligência comercial</p>
              <h1 className="mt-1 text-3xl font-bold">Mapa Comercial Estratégico</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-400">Mercado, movimento comercial e ações de 2026 para a seleção atual.</p>
            </div>
            {dados?.pode_selecionar_responsavel && (
              <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">
                Responsável comercial
                <select value={responsavelId} onChange={(e) => trocarResponsavel(e.target.value)} className="mt-2 w-full rounded-xl border border-[#214363] bg-[#071226] px-4 py-3 text-sm font-medium normal-case tracking-normal text-white outline-none focus:border-cyan-400">
                  <option value="">Toda a equipe comercial</option>
                  {dados.equipe.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}
                </select>
              </label>
            )}
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando informações comerciais...</div>}

          {!loading && dados && insights && (
            <VisaoComercial
              dados={dados}
              insights={insights}
              mercadoMacro={mercadoMacro}
              familiaTotal={familiaTotal}
              foco={foco}
              setFoco={setFoco}
            />
          )}
        </div>
      </section>
    </main>
  )
}

function VisaoComercial({ dados, insights, mercadoMacro, familiaTotal, foco, setFoco }: {
  dados: MapaEquipeVisao
  insights: MapaInsights
  mercadoMacro: MercadoMacro | null
  familiaTotal: number
  foco: FocoInteligencia
  setFoco: (foco: FocoInteligencia) => void
}) {
  const ticketPipeline = dados.evidencias.crm_ativos > 0 ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos : 0
  const consolidado = insights.escopo.consolidado

  return <>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {consolidado
        ? <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="ANFIR 2026" destaque="emerald" />
        : <Kpi titulo="Meu mercado 2026" valor={dados.mercado.mercado_real_selecao_2026} apoio={dados.selecao.nome} destaque="emerald" />}
      <Kpi titulo={consolidado ? "Mercado identificado" : "Clientes no meu mercado"} valor={consolidado ? dados.mercado.mercado_real_selecao_2026 : dados.mercado.clientes_unicos} apoio={dados.selecao.nome} destaque="cyan" />
      <Kpi titulo="Negociações em andamento" valor={dados.evidencias.crm_ativos} apoio="CRM atual" destaque="emerald" />
      <Kpi titulo="Pipeline atual" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} apoio={dados.evidencias.crm_ativos ? `ticket médio ${formatarMoeda(ticketPipeline)}` : "sem negócios ativos"} />
    </section>

    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {focos.map((item) => (
        <button key={item.id} type="button" onClick={() => setFoco(item.id)} className={`rounded-2xl border p-4 text-left transition ${foco === item.id ? "border-cyan-400 bg-cyan-500/10" : "border-[#17304d] bg-[#071226] hover:border-cyan-500/40"}`}>
          <strong className={foco === item.id ? "text-cyan-300" : "text-white"}>{item.titulo}</strong>
          <span className="mt-1 block text-xs text-slate-500">{item.apoio}</span>
        </button>
      ))}
    </section>

    {foco === "geral" && <VisaoGeral dados={dados} mercadoMacro={consolidado ? mercadoMacro : null} familiaTotal={familiaTotal} consolidado={consolidado} ticketPipeline={ticketPipeline} />}
    {foco === "regioes" && <VisaoRegioes insights={insights} />}
    {foco === "linhas" && <VisaoLinhas insights={insights} />}
    {foco === "perdas" && <VisaoPerdas insights={insights} />}

    <details className="rounded-2xl border border-slate-700/50 bg-[#061126] px-5 py-4">
      <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Dados de apoio e auditoria</summary>
      <div className="mt-4 grid gap-3 border-t border-slate-700/50 pt-4 sm:grid-cols-3">
        <MiniKpi rotulo="Registros históricos 2026" valor={dados.evidencias.historico_registros_2026} />
        <MiniKpi rotulo="Unidades históricas 2026" valor={dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} />
        <MiniKpi rotulo="Clientes históricos" valor={dados.reconciliacao.clientes_historico} />
      </div>
    </details>
  </>
}

function VisaoGeral({ dados, mercadoMacro, familiaTotal, consolidado, ticketPipeline }: { dados: MapaEquipeVisao; mercadoMacro: MercadoMacro | null; familiaTotal: number; consolidado: boolean; ticketPipeline: number }) {
  return <section className="grid gap-4 xl:grid-cols-2">
    <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
      <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Mercado 2026</p>
      <h2 className="mt-1 text-xl font-bold">Como o mercado está dividido</h2>
      {consolidado && mercadoMacro ? <div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div> : <p className="mt-4 text-sm text-slate-400">Visão individual do mercado vinculado ao login atual.</p>}
      <div className="mt-6 border-t border-slate-700/50 pt-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[.14em] text-slate-500">Composição por linha</p>
        <div className="space-y-3"><BarraComercial nome="Trailer" valor={dados.mercado.familias.trailer} total={Math.max(1, familiaTotal)} /><BarraComercial nome="Diesel Truck" valor={dados.mercado.familias.diesel_truck} total={Math.max(1, familiaTotal)} /><BarraComercial nome="Direct Drive" valor={dados.mercado.familias.direct_drive} total={Math.max(1, familiaTotal)} /></div>
      </div>
    </div>
    <div className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5">
      <div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">CRM atual</p><h2 className="mt-1 text-xl font-bold">Como estão os negócios em andamento</h2></div><strong className="text-emerald-300">{dados.evidencias.crm_ativos} ativos</strong></div>
      <div className="mt-5 space-y-3">{dados.evidencias.crm_status.length ? dados.evidencias.crm_status.map((item) => <BarraComercial key={item.nome} nome={item.nome.replaceAll("_", " ")} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />) : <p className="text-sm text-slate-500">Sem negociações ativas nesta seleção.</p>}</div>
      <div className="mt-6 grid gap-3 border-t border-slate-700/50 pt-4 sm:grid-cols-2"><MiniKpi rotulo="Pipeline" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} /><MiniKpi rotulo="Ticket médio" valor={formatarMoeda(ticketPipeline)} /></div>
    </div>
  </section>
}

function VisaoRegioes({ insights }: { insights: MapaInsights }) {
  return <section className="space-y-4">
    <div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5">
      <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Inteligência de regiões · 2026</p>
      <h2 className="mt-1 text-xl font-bold">Mercado e atuação por responsável comercial</h2>
      <p className="mt-2 text-sm text-slate-400">A atribuição é pelo responsável efetivo do cliente. Região e DDD não transferem mercado entre pessoas.</p>
    </div>
    <div className="grid gap-4 xl:grid-cols-2">
      {insights.regioes.map((item) => (
        <article key={item.id} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Responsável comercial</p><h3 className="mt-1 text-lg font-bold">{item.nome}</h3></div>
            <div className="text-right"><strong className="text-2xl text-cyan-300">{item.mercado_2026}</strong><p className="text-xs text-slate-500">mercado atribuído 2026</p></div>
          </div>
          <div className="mt-4"><GraficoLinha valores={item.mercado_mensal} meses={insights.meses} rotulo="Movimento mensal do mercado atribuído" /></div>
          <div className="mt-4 grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Clientes" valor={item.clientes_mercado} /><MiniKpi rotulo="Negócios ativos" valor={item.crm_ativos} /><MiniKpi rotulo="Pipeline" valor={formatarMoeda(item.pipeline_ativo)} /></div>
          <LeituraAcao leitura={item.leitura_comercial} acao={item.acao_recomendada} />
        </article>
      ))}
    </div>
  </section>
}

function VisaoLinhas({ insights }: { insights: MapaInsights }) {
  return <section className="space-y-4">
    <div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5">
      <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Evolução por linha · 2026</p>
      <h2 className="mt-1 text-xl font-bold">Como cada linha está se movimentando no ano</h2>
      <p className="mt-2 text-sm text-slate-400">Leitura baseada no Histórico/Funil 2026 da seleção atual. Sem comparação com anos anteriores nesta tela.</p>
    </div>
    <div className="grid gap-4 xl:grid-cols-3">
      {insights.linhas_2026.linhas.map((linha) => (
        <article key={linha.codigo} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
          <div className="flex items-end justify-between gap-3"><div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Linha de produto</p><h3 className="mt-1 text-lg font-bold">{linha.nome}</h3></div><strong className="text-2xl text-cyan-300">{linha.total_2026}</strong></div>
          <div className="mt-4"><GraficoLinha valores={linha.mensal} meses={insights.linhas_2026.meses} rotulo={`Movimento mensal de ${linha.nome}`} /></div>
          <LeituraAcao leitura={linha.leitura_comercial} acao={linha.acao_recomendada} />
        </article>
      ))}
    </div>
    {insights.linhas_2026.nao_classificado_2026 > 0 && <p className="px-1 text-xs text-amber-300">Há {insights.linhas_2026.nao_classificado_2026} unidade(s) de 2026 ainda sem linha classificada; elas não foram forçadas para Trailer, Diesel Truck ou Direct Drive.</p>}
  </section>
}

function VisaoPerdas({ insights }: { insights: MapaInsights }) {
  const totalMotivos = Math.max(1, insights.perdas.total_com_motivo)
  const totalLinhas = Math.max(1, insights.perdas.por_linha.reduce((s, item) => s + item.quantidade, 0))
  return <section className="space-y-4">
    <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Perdas comerciais · 2026</p><h2 className="mt-1 text-xl font-bold">Onde perdemos e por quê</h2></div><div className="text-right"><strong className="text-3xl text-amber-300">{insights.perdas.total_perdido}</strong><p className="text-xs text-slate-500">perdas registradas</p></div></div>
      <div className="mt-5"><GraficoLinha valores={insights.perdas.mensal} meses={insights.meses} rotulo="Evolução mensal das perdas em 2026" /></div>
      <LeituraAcao leitura={insights.perdas.leitura_comercial} acao={insights.perdas.acao_recomendada} destaque="amber" />
    </div>
    <div className="grid gap-4 xl:grid-cols-2">
      <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Por que perdemos</p><h3 className="mt-1 text-lg font-bold">Motivos registrados em 2026</h3><div className="mt-5 space-y-3">{insights.perdas.motivos.length ? insights.perdas.motivos.map((item) => <BarraComercial key={item.nome} nome={item.nome.replaceAll("_", " ")} valor={item.quantidade} total={totalMotivos} />) : <p className="text-sm text-slate-500">As perdas existem, mas ainda não há motivo estruturado suficiente para análise.</p>}</div></div>
      <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Onde perdemos</p><h3 className="mt-1 text-lg font-bold">Perdas por linha em 2026</h3><div className="mt-5 space-y-3">{insights.perdas.por_linha.length ? insights.perdas.por_linha.map((item) => <BarraComercial key={item.nome} nome={item.nome} valor={item.quantidade} total={totalLinhas} />) : <p className="text-sm text-slate-500">Não há linha classificada nas perdas deste escopo.</p>}</div></div>
    </div>
  </section>
}

function LeituraAcao({ leitura, acao, destaque = "cyan" }: { leitura: string; acao: string; destaque?: "cyan" | "amber" }) {
  const titulo = destaque === "amber" ? "text-amber-300" : "text-cyan-300"
  return <div className="mt-5 grid gap-3 border-t border-slate-700/50 pt-4 md:grid-cols-2">
    <div><p className={`text-[11px] font-semibold uppercase tracking-[.14em] ${titulo}`}>Leitura comercial</p><p className="mt-2 text-sm leading-6 text-slate-300">{leitura}</p></div>
    <div><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-emerald-300">O que fazer</p><p className="mt-2 text-sm leading-6 text-slate-300">{acao}</p></div>
  </div>
}

function GraficoLinha({ valores, meses, rotulo }: { valores: number[]; meses: string[]; rotulo: string }) {
  const serie = Array.from({ length: 12 }, (_, i) => Number(valores[i] || 0))
  const maximo = Math.max(1, ...serie)
  const largura = 720
  const altura = 180
  const margemX = 22
  const margemY = 18
  const passo = (largura - margemX * 2) / 11
  const pontos = serie.map((valor, i) => {
    const x = margemX + i * passo
    const y = altura - margemY - (valor / maximo) * (altura - margemY * 2)
    return { x, y, valor }
  })
  const caminho = pontos.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")

  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-3" aria-label={rotulo}>
    <svg viewBox={`0 0 ${largura} ${altura + 26}`} className="h-48 w-full" role="img">
      <line x1={margemX} y1={altura - margemY} x2={largura - margemX} y2={altura - margemY} stroke="currentColor" className="text-slate-700" strokeWidth="1" />
      <path d={caminho} fill="none" stroke="currentColor" className="text-cyan-400" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      {pontos.map((p, i) => <g key={i}><circle cx={p.x} cy={p.y} r="4" fill="currentColor" className="text-cyan-300" /><text x={p.x} y={Math.max(12, p.y - 9)} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-300">{p.valor || ""}</text></g>)}
      {meses.slice(0, 12).map((mes, i) => <text key={mes + i} x={margemX + i * passo} y={altura + 12} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-500">{mes}</text>)}
    </svg>
  </div>
}

function Kpi({ titulo, valor, apoio, destaque }: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald" }) {
  const cor = destaque === "emerald" ? "text-emerald-300" : destaque === "cyan" ? "text-cyan-300" : "text-white"
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><div className={`mt-2 text-2xl font-bold ${cor}`}>{valor}</div>{apoio && <p className="mt-1 text-xs text-slate-500">{apoio}</p>}</div>
}

function MiniKpi({ rotulo, valor }: { rotulo: string; valor: string | number }) {
  return <div className="rounded-xl border border-[#17304d] bg-[#09152a] p-3"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-lg text-white">{valor}</strong></div>
}

function BarraComercial({ nome, valor, total }: { nome: string; valor: number; total: number }) {
  const percentual = pct(valor, total)
  return <div><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="font-medium text-slate-300">{nome}</span><span className="font-semibold text-cyan-300">{valor} · {percentual.toFixed(0)}%</span></div><div className="h-3 overflow-hidden rounded-full bg-[#0b2040]"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(100, percentual)}%` }} /></div></div>
}

function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) {
  const foraPct = pct(fora, total)
  const realPct = pct(real, total)
  return <div><div className="grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Mercado total" valor={total} /><MiniKpi rotulo="Fora da disputa" valor={fora} /><MiniKpi rotulo="Mercado real Viena" valor={real} /></div><div className="mt-4 flex h-5 overflow-hidden rounded-full bg-slate-900" aria-label="Composição do mercado ANFIR 2026"><div className="bg-amber-500" style={{ width: `${foraPct}%` }} /><div className="bg-emerald-500" style={{ width: `${realPct}%` }} /></div><div className="mt-2 flex flex-wrap justify-end gap-4 text-xs"><span className="text-amber-300">Fora da disputa {foraPct.toFixed(1)}%</span><span className="text-emerald-300">Mercado real {realPct.toFixed(1)}%</span></div></div>
}

function pct(valor: number, total: number) { return total > 0 ? (valor / total) * 100 : 0 }
function formatarMoeda(valor: number) { return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(valor || 0) }
