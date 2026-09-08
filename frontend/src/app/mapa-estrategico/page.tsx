"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import { getMapaEquipeVisao, getMapaInsights, type MapaEquipeVisao, type MapaInsights } from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }
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
    if (!dados?.pode_selecionar_responsavel) return
    let ativo = true
    void (async () => {
      try {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.auth.getSession()
        const token = data.session?.access_token
        if (error || !token) return
        const resposta = await fetch("/api/cti/analytics/anfir-workbook-2026", { cache: "no-store", headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } })
        if (!resposta.ok) return
        const payload = await resposta.json() as { mercado_viena?: { mercado_anfir_total?: number; mercado_fora_escopo_comercial?: number; mercado_disputavel_viena?: number } }
        if (!ativo || !payload.mercado_viena) return
        setMercadoMacro({
          total: Number(payload.mercado_viena.mercado_anfir_total || 0),
          foraDisputa: Number(payload.mercado_viena.mercado_fora_escopo_comercial || 0),
          real: Number(payload.mercado_viena.mercado_disputavel_viena || 0),
        })
      } catch { /* consolidado opcional */ }
    })()
    return () => { ativo = false }
  }, [dados?.pode_selecionar_responsavel])

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
            <p className="mt-2 max-w-3xl text-sm text-slate-400">Leitura rápida do mercado 2026, do acompanhamento comercial e do resultado observado.</p>
          </div>
          {dados?.pode_selecionar_responsavel && <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">Responsável comercial<select value={responsavelId} onChange={(e) => trocarResponsavel(e.target.value)} className="mt-2 w-full rounded-xl border border-[#214363] bg-[#071226] px-4 py-3 text-sm font-medium normal-case tracking-normal text-white outline-none focus:border-cyan-400"><option value="">Toda a equipe comercial</option>{dados.equipe.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}</select></label>}
        </header>
        {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
        {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando informações comerciais...</div>}
        {!loading && dados && insights && <VisaoComercial dados={dados} insights={insights} mercadoMacro={mercadoMacro} familiaTotal={familiaTotal} foco={foco} setFoco={setFoco} />}
      </div>
    </section>
  </main>
}

function VisaoComercial({ dados, insights, mercadoMacro, familiaTotal, foco, setFoco }: { dados: MapaEquipeVisao; insights: MapaInsights; mercadoMacro: MercadoMacro | null; familiaTotal: number; foco: FocoInteligencia; setFoco: (f: FocoInteligencia) => void }) {
  const consolidado = insights.escopo.consolidado
  const rid = dados.selecao.id || undefined
  const ticket = dados.evidencias.crm_ativos ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos : 0
  return <>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <KpiLink titulo={consolidado && mercadoMacro ? "Mercado Real Viena" : "Meu mercado 2026"} valor={consolidado && mercadoMacro ? mercadoMacro.real : dados.mercado.mercado_real_selecao_2026} apoio="ANFIR 2026 · abrir unidades" destaque="emerald" href={detalheHref("anfir", rid, "Unidades do mercado 2026")} />
      <KpiLink titulo="Clientes no mercado" valor={dados.mercado.clientes_unicos} apoio="abrir carteira / empresas" destaque="cyan" href="/empresas" />
      <KpiLink titulo="Negociações em andamento" valor={dados.evidencias.crm_ativos} apoio="CRM atual · abrir negócios" destaque="emerald" href={detalheHref("crm", rid, "Negociações em andamento")} />
      <Kpi titulo="Pipeline atual" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} apoio={dados.evidencias.crm_ativos ? `ticket médio ${formatarMoeda(ticket)}` : "sem negócios ativos"} />
    </section>

    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{focos.map((item) => <button key={item.id} type="button" onClick={() => setFoco(item.id)} className={`rounded-2xl border p-4 text-left transition ${foco === item.id ? "border-cyan-400 bg-cyan-500/10" : "border-[#17304d] bg-[#071226] hover:border-cyan-500/40"}`}><strong className={foco === item.id ? "text-cyan-300" : "text-white"}>{item.titulo}</strong><span className="mt-1 block text-xs text-slate-500">{item.apoio}</span></button>)}</section>

    {foco === "geral" && <VisaoGeral dados={dados} mercadoMacro={consolidado ? mercadoMacro : null} familiaTotal={familiaTotal} consolidado={consolidado} rid={rid} />}
    {foco === "regioes" && <VisaoRegioes insights={insights} />}
    {foco === "linhas" && <VisaoLinhas insights={insights} rid={rid} />}
    {foco === "perdas" && <VisaoPerdas insights={insights} />}
  </>
}

function VisaoGeral({ dados, mercadoMacro, familiaTotal, consolidado, rid }: { dados: MapaEquipeVisao; mercadoMacro: MercadoMacro | null; familiaTotal: number; consolidado: boolean; rid?: string }) {
  const c = dados.ciclo
  return <section className="space-y-4">
    {consolidado && mercadoMacro && <div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Base executiva auditável · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Mercado total → empresas retiradas → mercado real Viena</h2><p className="mt-2 text-sm text-slate-400">Número e percentual sobre a mesma base. O mercado real abre os registros que formam o saldo comercial.</p><div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div></div>}

    <div className="grid gap-4 xl:grid-cols-2">
      <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Composição do mercado 2026</p><h2 className="mt-1 text-xl font-bold">Onde está o volume</h2><div className="mt-5 space-y-3"><BarraLink nome="Trailer" valor={dados.mercado.familias.trailer} total={Math.max(1, familiaTotal)} href={detalheHref("anfir", rid, "Unidades Trailer 2026", { familia: "trailer" })} /><BarraLink nome="Diesel Truck" valor={dados.mercado.familias.diesel_truck} total={Math.max(1, familiaTotal)} href={detalheHref("anfir", rid, "Unidades Diesel Truck 2026", { familia: "diesel_truck" })} /><BarraLink nome="Direct Drive" valor={dados.mercado.familias.direct_drive} total={Math.max(1, familiaTotal)} href={detalheHref("anfir", rid, "Unidades Direct Drive 2026", { familia: "direct_drive" })} /></div></div>
      <div className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">Caminho comercial</p><h2 className="mt-1 text-xl font-bold">Mercado → acompanhamento → resultado</h2><div className="mt-5 grid gap-3 sm:grid-cols-2"><MiniLink rotulo="Clientes no mercado" valor={c.clientes_mercado_real} href="/empresas" /><MiniLink rotulo="Clientes com CRM" valor={c.clientes_crm} href={detalheHref("crm", rid, "Clientes acompanhados no CRM")} /><MiniLink rotulo="CRM + histórico" valor={c.crm_com_evidencia_historico} href={detalheHref("historico", rid, "Histórico/Funil dos clientes acompanhados")} /><MiniKpi rotulo="Nas 3 fontes" valor={c.clientes_com_evidencia_nas_tres_fontes} /></div><p className="mt-4 text-sm leading-6 text-slate-400">A leitura cruza as mesmas carteiras entre ANFIR, Histórico/Funil e CRM sem somar fontes diferentes como se fossem o mesmo evento.</p></div>
    </div>
  </section>
}

function VisaoRegioes({ insights }: { insights: MapaInsights }) {
  return <section className="space-y-4"><div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Inteligência de regiões · 2026</p><h2 className="mt-1 text-xl font-bold">Mercado e atuação por responsável comercial</h2></div><div className="grid gap-4 xl:grid-cols-2">{insights.regioes.map((item) => <article key={item.id} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Responsável comercial</p><h3 className="mt-1 text-lg font-bold">{item.nome}</h3></div><Link href={detalheHref("anfir", item.id, `Mercado 2026 · ${item.nome}`)} className="text-right"><strong className="text-2xl text-cyan-300 underline decoration-cyan-500/40 underline-offset-4">{item.mercado_2026}</strong><p className="text-xs text-slate-500">abrir unidades</p></Link></div><div className="mt-4"><GraficoLinha valores={item.mercado_mensal} meses={insights.meses} rotulo="Movimento mensal" /></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Clientes" valor={item.clientes_mercado} /><MiniLink rotulo="Negócios ativos" valor={item.crm_ativos} href={detalheHref("crm", item.id, `CRM ativo · ${item.nome}`)} /><MiniKpi rotulo="Pipeline" valor={formatarMoeda(item.pipeline_ativo)} /></div><LeituraAcao leitura={item.leitura_comercial} acao={item.acao_recomendada} /></article>)}</div></section>
}

function VisaoLinhas({ insights, rid }: { insights: MapaInsights; rid?: string }) {
  return <section className="space-y-4"><div className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Evolução por linha · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Como cada linha está se movimentando no ano</h2></div><div className="grid gap-4 xl:grid-cols-3">{insights.linhas_2026.linhas.map((linha) => <article key={linha.codigo} className="rounded-3xl border border-[#17304d] bg-[#061126] p-5"><div className="flex items-end justify-between gap-3"><div><p className="text-xs uppercase tracking-[.14em] text-slate-500">Linha de produto</p><h3 className="mt-1 text-lg font-bold">{linha.nome}</h3></div><Link href={detalheHref("anfir", rid, `${linha.nome} · 2026`, { familia: linha.codigo })} className="text-right"><strong className="text-2xl text-cyan-300 underline decoration-cyan-500/40 underline-offset-4">{linha.total_2026}</strong><span className="block text-[10px] text-slate-500">abrir unidades</span></Link></div><div className="mt-4"><GraficoLinha valores={linha.mensal} meses={insights.linhas_2026.meses} rotulo={`Movimento mensal de ${linha.nome}`} /></div><LeituraAcao leitura={linha.leitura_comercial} acao={linha.acao_recomendada} /></article>)}</div></section>
}

function VisaoPerdas({ insights }: { insights: MapaInsights }) {
  const totalMotivos = Math.max(1, insights.perdas.total_com_motivo)
  const totalLinhas = Math.max(1, insights.perdas.por_linha.reduce((s, i) => s + i.quantidade, 0))
  return <section className="space-y-4"><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Perdas comerciais · ANFIR 2026</p><h2 className="mt-1 text-xl font-bold">Onde perdemos e por quê</h2></div><strong className="text-3xl text-amber-300">{insights.perdas.total_perdido}</strong></div><div className="mt-5"><GraficoLinha valores={insights.perdas.mensal} meses={insights.meses} rotulo="Evolução mensal das perdas" /></div><LeituraAcao leitura={insights.perdas.leitura_comercial} acao={insights.perdas.acao_recomendada} destaque="amber" /></div><div className="grid gap-4 xl:grid-cols-2"><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><h3 className="text-lg font-bold">Por que perdemos</h3><div className="mt-5 space-y-3">{insights.perdas.motivos.map((i) => <BarraComercial key={i.nome} nome={i.nome.replaceAll("_", " ")} valor={i.quantidade} total={totalMotivos} />)}</div></div><div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><h3 className="text-lg font-bold">Onde perdemos</h3><div className="mt-5 space-y-3">{insights.perdas.por_linha.map((i) => <BarraComercial key={i.nome} nome={i.nome} valor={i.quantidade} total={totalLinhas} />)}</div></div></div></section>
}

function detalheHref(camada: "anfir" | "historico" | "crm", responsavelId: string | undefined, titulo: string, extras: Record<string, string> = {}) {
  const q = new URLSearchParams({ origem: "mapa", camada, titulo, subtitulo: "Registros que formam exatamente o indicador selecionado" })
  if (responsavelId) q.set("responsavel_id", responsavelId)
  Object.entries(extras).forEach(([k, v]) => q.set(k, v))
  return `/detalhamento?${q.toString()}`
}

function Kpi({ titulo, valor, apoio, destaque }: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald" }) { const cor = destaque === "emerald" ? "text-emerald-300" : destaque === "cyan" ? "text-cyan-300" : "text-white"; return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><div className={`mt-2 text-2xl font-bold ${cor}`}>{valor}</div>{apoio && <p className="mt-1 text-xs text-slate-500">{apoio}</p>}</div> }
function KpiLink(props: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald"; href: string }) { return <Link href={props.href} className="block rounded-2xl outline-none ring-cyan-400 focus:ring-2"><Kpi titulo={props.titulo} valor={props.valor} apoio={props.apoio} destaque={props.destaque} /></Link> }
function MiniKpi({ rotulo, valor }: { rotulo: string; valor: string | number }) { return <div className="rounded-xl border border-[#17304d] bg-[#09152a] p-3"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-lg text-white">{valor}</strong></div> }
function MiniLink({ rotulo, valor, href }: { rotulo: string; valor: string | number; href: string }) { return <Link href={href} className="rounded-xl border border-[#17304d] bg-[#09152a] p-3 transition hover:border-cyan-500/50"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-lg text-cyan-300 underline decoration-cyan-500/40 underline-offset-4">{valor}</strong></Link> }
function BarraComercial({ nome, valor, total }: { nome: string; valor: number; total: number }) { const percentual = pct(valor, total); return <div><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="font-medium text-slate-300">{nome}</span><span className="font-semibold text-cyan-300">{valor} · {percentual.toFixed(0)}%</span></div><div className="h-3 overflow-hidden rounded-full bg-[#0b2040]"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(100, percentual)}%` }} /></div></div> }
function BarraLink({ nome, valor, total, href }: { nome: string; valor: number; total: number; href: string }) { return <Link href={href} className="block rounded-lg p-1 transition hover:bg-cyan-500/5"><BarraComercial nome={nome} valor={valor} total={total} /></Link> }
function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) { const f = pct(fora, total), r = pct(real, total); return <div><div className="grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Mercado total ANFIR" valor={`${total} · 100%`} /><MiniKpi rotulo="Empresas retiradas" valor={`${fora} · ${f.toFixed(1)}%`} /><MiniKpi rotulo="Mercado real Viena" valor={`${real} · ${r.toFixed(1)}%`} /></div><div className="mt-4 flex h-5 overflow-hidden rounded-full bg-slate-900"><div className="bg-amber-500" style={{ width: `${f}%` }} /><div className="bg-emerald-500" style={{ width: `${r}%` }} /></div></div> }
function LeituraAcao({ leitura, acao, destaque = "cyan" }: { leitura: string; acao: string; destaque?: "cyan" | "amber" }) { return <div className="mt-5 grid gap-3 border-t border-slate-700/50 pt-4 md:grid-cols-2"><div><p className={`text-[11px] font-semibold uppercase tracking-[.14em] ${destaque === "amber" ? "text-amber-300" : "text-cyan-300"}`}>Leitura comercial</p><p className="mt-2 text-sm leading-6 text-slate-300">{leitura}</p></div><div><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-emerald-300">O que fazer</p><p className="mt-2 text-sm leading-6 text-slate-300">{acao}</p></div></div> }
function GraficoLinha({ valores, meses, rotulo }: { valores: number[]; meses: string[]; rotulo: string }) { const serie = Array.from({ length: 12 }, (_, i) => Number(valores[i] || 0)); const max = Math.max(1, ...serie), w = 720, h = 180, mx = 22, my = 18, passo = (w - mx * 2) / 11; const pts = serie.map((valor, i) => ({ x: mx + i * passo, y: h - my - (valor / max) * (h - my * 2), valor })); const path = pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "); return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-3" aria-label={rotulo}><svg viewBox={`0 0 ${w} ${h + 26}`} className="h-48 w-full"><line x1={mx} y1={h-my} x2={w-mx} y2={h-my} stroke="currentColor" className="text-slate-700"/><path d={path} fill="none" stroke="currentColor" className="text-cyan-400" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>{pts.map((p,i)=><g key={i}><circle cx={p.x} cy={p.y} r="4" fill="currentColor" className="text-cyan-300"/><text x={p.x} y={Math.max(12,p.y-9)} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-300">{p.valor||""}</text></g>)}{meses.slice(0,12).map((m,i)=><text key={m+i} x={mx+i*passo} y={h+12} textAnchor="middle" fontSize="10" fill="currentColor" className="text-slate-500">{m}</text>)}</svg></div> }
function pct(valor: number, total: number) { return total > 0 ? valor / total * 100 : 0 }
function formatarMoeda(valor: number) { return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(valor || 0) }
