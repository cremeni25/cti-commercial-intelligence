"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import { getMapaEquipeVisao, type MapaEquipeVisao } from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }

export default function Page() {
  const [responsavelId, setResponsavelId] = useState("")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
  const [mercadoMacro, setMercadoMacro] = useState<MercadoMacro | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    getMapaEquipeVisao(responsavelId || null)
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar a visão comercial regional.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [responsavelId])

  useEffect(() => {
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
        // A visão comercial segue disponível sem a leitura macro.
      }
    })()
    return () => { ativo = false }
  }, [])

  const trocarResponsavel = (novoId: string) => {
    setLoading(true)
    setErro("")
    setResponsavelId(novoId)
  }

  const familiaTotal = useMemo(() => {
    if (!dados) return 0
    const f = dados.mercado.familias
    return f.trailer + f.diesel_truck + f.direct_drive
  }, [dados])

  const gapMercado = dados ? Math.max(0, dados.mercado.mercado_real_viena_2026 - dados.mercado.mercado_real_selecao_2026) : 0
  const gapPct = dados ? Math.max(0, 100 - dados.mercado.participacao_regiao_no_mercado_real_pct) : 0
  const ticketPipeline = dados && dados.evidencias.crm_ativos > 0 ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos : 0

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
            </div>
            {dados?.pode_selecionar_responsavel && (
              <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">
                Região / responsável
                <select value={responsavelId} onChange={(e) => trocarResponsavel(e.target.value)} className="mt-2 w-full rounded-xl border border-[#214363] bg-[#071226] px-4 py-3 text-sm font-medium normal-case tracking-normal text-white outline-none focus:border-cyan-400">
                  <option value="">Toda a equipe comercial</option>
                  {dados.equipe.map((item) => <option key={item.id} value={item.id}>{item.codigo_regional ? `${item.codigo_regional} — ` : ""}{item.nome}</option>)}
                </select>
              </label>
            )}
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando informações comerciais...</div>}

          {!loading && dados && <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="100%" destaque="emerald" />
              <Kpi titulo="Ligado à análise" valor={dados.mercado.mercado_real_selecao_2026} apoio={`${dados.mercado.participacao_regiao_no_mercado_real_pct.toFixed(1)}%`} destaque="cyan" />
              <Kpi titulo="Espaço disponível" valor={gapMercado} apoio={`${gapPct.toFixed(1)}%`} destaque="amber" />
              <Kpi titulo="Negociações ativas" valor={dados.evidencias.crm_ativos} apoio={formatarMoeda(dados.evidencias.crm_valor_ativo)} />
              <Kpi titulo="Ticket médio ativo" valor={formatarMoeda(ticketPipeline)} apoio="pipeline atual" />
            </section>

            <section className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
              <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[.16em] text-slate-500">Mercado 2026</p>
                    <h2 className="mt-1 text-xl font-bold">Tamanho, disputa e espaço comercial</h2>
                  </div>
                  <span className="rounded-full border border-cyan-500/20 px-3 py-1 text-xs text-cyan-200">ANFIR 2026</span>
                </div>
                <div className="mt-5 grid gap-5 lg:grid-cols-[.8fr_1.2fr] lg:items-center">
                  <GraficoPizzaParticipacao percentual={dados.mercado.participacao_regiao_no_mercado_real_pct} selecionado={dados.mercado.mercado_real_selecao_2026} total={dados.mercado.mercado_real_viena_2026} nome={dados.selecao.nome} compacto />
                  <div className="space-y-4">
                    {mercadoMacro && <BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} />}
                    <div className="grid grid-cols-3 gap-2">
                      <MiniKpi rotulo="Trailer" valor={dados.mercado.familias.trailer} apoio={`${pct(dados.mercado.familias.trailer, familiaTotal).toFixed(1)}%`} />
                      <MiniKpi rotulo="Diesel Truck" valor={dados.mercado.familias.diesel_truck} apoio={`${pct(dados.mercado.familias.diesel_truck, familiaTotal).toFixed(1)}%`} />
                      <MiniKpi rotulo="Direct Drive" valor={dados.mercado.familias.direct_drive} apoio={`${pct(dados.mercado.familias.direct_drive, familiaTotal).toFixed(1)}%`} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-3xl border border-emerald-500/25 bg-[#061126] p-5">
                <p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">Leitura executiva</p>
                <div className="mt-4 space-y-3">
                  <Insight valor={`${gapPct.toFixed(1)}%`} texto="do Mercado Real ainda está fora da análise selecionada." />
                  <Insight valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} texto={`estão em ${dados.evidencias.crm_ativos} negociação(ões) ativa(s).`} />
                  <Insight valor={`${dados.mercado.clientes_unicos}`} texto="clientes estão identificados no mercado analisado." />
                </div>
              </div>
            </section>

            <section className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5">
                <div className="flex items-center justify-between gap-3"><h2 className="font-bold">Agora · CRM</h2><strong className="text-emerald-300">{dados.evidencias.crm_ativos} ativas</strong></div>
                <div className="mt-4 space-y-2">{dados.evidencias.crm_status.length ? dados.evidencias.crm_status.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />) : <p className="text-sm text-slate-500">Sem negociações ativas.</p>}</div>
              </div>
              <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5">
                <div className="flex items-center justify-between gap-3"><h2 className="font-bold">Histórico / Funil 2026</h2><strong className="text-amber-300">{dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} unidades</strong></div>
                <div className="mt-4 grid grid-cols-2 gap-3"><MiniKpi rotulo="Eventos" valor={dados.evidencias.historico_registros_2026} /><MiniKpi rotulo="Perdas registradas" valor={dados.evidencias.motivos_perda_historico.reduce((s, i) => s + i.quantidade, 0)} /></div>
                {dados.evidencias.motivos_perda_historico.length > 0 && <div className="mt-4 space-y-2">{dados.evidencias.motivos_perda_historico.slice(0, 3).map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.motivos_perda_historico.reduce((s, i) => s + i.quantidade, 0))} />)}</div>}
              </div>
            </section>

            <details className="group rounded-2xl border border-slate-700/60 bg-[#061126] px-5 py-4">
              <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Auditoria e origem dos dados <span className="ml-2 text-xs text-slate-500">ANFIR · Histórico/Funil · CRM</span></summary>
              <div className="mt-4 grid gap-3 border-t border-slate-700/60 pt-4 sm:grid-cols-2 xl:grid-cols-4">
                <MiniKpi rotulo="Clientes ANFIR" valor={dados.reconciliacao.clientes_anfir} apoio={`${pct(dados.reconciliacao.clientes_anfir, dados.reconciliacao.universo_clientes).toFixed(1)}%`} />
                <MiniKpi rotulo="Clientes Histórico" valor={dados.reconciliacao.clientes_historico} apoio={`${pct(dados.reconciliacao.clientes_historico, dados.reconciliacao.universo_clientes).toFixed(1)}%`} />
                <MiniKpi rotulo="Clientes CRM" valor={dados.reconciliacao.clientes_crm} apoio={`${pct(dados.reconciliacao.clientes_crm, dados.reconciliacao.universo_clientes).toFixed(1)}%`} />
                <MiniKpi rotulo="Nas 3 fontes" valor={dados.reconciliacao.nas_tres_fontes} apoio={`${pct(dados.reconciliacao.nas_tres_fontes, dados.reconciliacao.universo_clientes).toFixed(1)}%`} />
              </div>
            </details>
          </>}
        </div>
      </section>
    </main>
  )
}

function pct(parte: number, total: number) { return total > 0 ? parte / total * 100 : 0 }

function Kpi({ titulo, valor, apoio, destaque = "normal" }: { titulo: string; valor: number | string; apoio: string; destaque?: "normal" | "cyan" | "emerald" | "amber" }) {
  const cor = destaque === "cyan" ? "text-cyan-300" : destaque === "emerald" ? "text-emerald-300" : destaque === "amber" ? "text-amber-300" : "text-white"
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.12em] text-slate-500">{titulo}</p><strong className={`mt-2 block text-3xl ${cor}`}>{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong><p className="mt-1 text-xs font-semibold text-slate-400">{apoio}</p></div>
}

function MiniKpi({ rotulo, valor, apoio }: { rotulo: string; valor: number | string; apoio?: string }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#08162d] p-3"><p className="text-[10px] uppercase tracking-[.1em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-xl text-slate-100">{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong>{apoio && <p className="mt-1 text-xs font-semibold text-cyan-300">{apoio}</p>}</div>
}

function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) {
  const foraPct = pct(fora, total)
  const realPct = pct(real, total)
  return <div><div className="flex items-end justify-between gap-3"><div><p className="text-xs uppercase tracking-[.12em] text-slate-500">Mercado observado</p><strong className="text-2xl">{total.toLocaleString("pt-BR")}</strong></div><div className="text-right"><p className="text-xs text-amber-300">Fora da disputa {fora.toLocaleString("pt-BR")} · {foraPct.toFixed(1)}%</p><p className="text-xs text-emerald-300">Mercado Real {real.toLocaleString("pt-BR")} · {realPct.toFixed(1)}%</p></div></div><div className="mt-3 flex h-7 overflow-hidden rounded-full bg-slate-900"><div className="bg-amber-500/80" style={{ width: `${foraPct}%` }} /><div className="bg-emerald-400/80" style={{ width: `${realPct}%` }} /></div></div>
}

function GraficoPizzaParticipacao({ percentual, selecionado, total, nome, compacto = false }: { percentual: number; selecionado: number; total: number; nome: string; compacto?: boolean }) {
  const valorPct = Math.max(0, Math.min(100, percentual))
  const size = compacto ? "h-40 w-40" : "h-44 w-44"
  return <div className="flex flex-col items-center gap-4"><div className={`relative ${size} shrink-0 rounded-full`} style={{ background: `conic-gradient(#22d3ee 0 ${valorPct}%, #172554 ${valorPct}% 100%)` }}><div className="absolute inset-7 flex flex-col items-center justify-center rounded-full bg-[#071226]"><strong className="text-2xl text-cyan-300">{valorPct.toFixed(1)}%</strong><span className="text-[10px] text-slate-500">participação</span></div></div><div className="text-center"><strong className="text-sm">{selecionado.toLocaleString("pt-BR")} de {total.toLocaleString("pt-BR")}</strong><p className="mt-1 max-w-[260px] truncate text-xs text-slate-500">{nome}</p></div></div>
}

function Insight({ valor, texto }: { valor: string; texto: string }) { return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><strong className="text-2xl text-emerald-300">{valor}</strong><p className="mt-1 text-sm leading-snug text-slate-300">{texto}</p></div> }

function BarraStatus({ nome, valor, total }: { nome: string; valor: number; total: number }) {
  const percentual = Math.max(0, Math.min(100, pct(valor, total)))
  return <div><div className="mb-1 flex items-center justify-between text-xs"><span className="text-slate-300">{nome}</span><strong className="text-cyan-300">{valor.toLocaleString("pt-BR")} · {percentual.toFixed(0)}%</strong></div><div className="h-2 overflow-hidden rounded-full bg-[#0b1b34]"><div className="h-full rounded-full bg-cyan-400/80" style={{ width: `${percentual}%` }} /></div></div>
}

function formatarMoeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
