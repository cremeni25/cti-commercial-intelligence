"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import { getMapaEquipeVisao, type MapaEquipeVisao } from "@/services/mapa-equipe-api"

type MercadoMacro = {
  total: number
  foraDisputa: number
  real: number
}

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
    const carregar = async () => {
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
        const payload = await resposta.json() as {
          mercado_viena?: {
            mercado_anfir_total?: number
            mercado_fora_escopo_comercial?: number
            mercado_disputavel_viena?: number
          }
        }
        if (!ativo || !payload.mercado_viena) return
        setMercadoMacro({
          total: Number(payload.mercado_viena.mercado_anfir_total || 0),
          foraDisputa: Number(payload.mercado_viena.mercado_fora_escopo_comercial || 0),
          real: Number(payload.mercado_viena.mercado_disputavel_viena || 0),
        })
      } catch {
        // A visão regional continua utilizável mesmo se a leitura macro falhar.
      }
    }
    void carregar()
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

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-5 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Inteligência comercial territorial</p>
              <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Mapa Comercial Estratégico</h1>
              <p className="mt-2 max-w-4xl text-sm text-slate-400">Primeiro entenda o mercado disponível para a Viena. Depois veja quanto está ligado à equipe ou ao responsável, o que aconteceu antes e o que está acontecendo agora.</p>
            </div>
            {dados?.pode_selecionar_responsavel && (
              <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">
                Quem você quer analisar?
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
            <section className="flex flex-col gap-3 rounded-2xl border border-cyan-500/30 bg-[#071226] p-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Análise exibida para</p>
                <h2 className="mt-1 text-2xl font-semibold">{dados.selecao.nome}</h2>
                {(dados.selecao.codigo_regional || dados.selecao.ddds.length > 0) && <p className="mt-1 text-sm text-slate-400">{dados.selecao.codigo_regional || "Viena SP"}{dados.selecao.ddds.length ? ` · DDDs ${dados.selecao.ddds.join(", ")}` : ""}</p>}
              </div>
              <span className="rounded-full border border-cyan-500/20 bg-cyan-950/10 px-4 py-2 text-xs font-semibold text-cyan-200">Fonte de mercado: ANFIR 2026</span>
            </section>

            <section className="rounded-3xl border border-cyan-500/30 bg-[#061126] p-5 sm:p-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">1 · Qual é o mercado disponível para a Viena?</p>
                <h2 className="mt-2 text-2xl font-bold">Do mercado observado ao mercado que realmente pode ser disputado</h2>
                <p className="mt-2 max-w-4xl text-sm text-slate-400">A ANFIR mostra o mercado observado no território. Uma parte fica fora da disputa comercial da Viena. O que sobra é o Mercado Real Viena, usado como base para participação e cobertura comercial.</p>
              </div>

              {mercadoMacro ? <>
                <div className="mt-5 grid gap-4 md:grid-cols-3">
                  <MercadoCard titulo="Mercado total observado" valor={mercadoMacro.total} percentual={100} apoio="Tudo o que foi observado na base territorial ANFIR 2026." />
                  <MercadoCard titulo="Fora da disputa Viena" valor={mercadoMacro.foraDisputa} percentual={pct(mercadoMacro.foraDisputa, mercadoMacro.total)} apoio="Existe no território, mas não entra na base usada para medir a equipe Viena." tom="amber" />
                  <MercadoCard titulo="Mercado Real Viena" valor={mercadoMacro.real} percentual={pct(mercadoMacro.real, mercadoMacro.total)} apoio="É o mercado efetivamente disponível para disputa comercial da Viena." tom="emerald" />
                </div>
                <BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} />
                <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 px-4 py-3 text-sm text-slate-300">
                  <strong className="text-emerald-200">Como interpretar:</strong> {mercadoMacro.total.toLocaleString("pt-BR")} unidades observadas − {mercadoMacro.foraDisputa.toLocaleString("pt-BR")} fora da disputa = <strong>{mercadoMacro.real.toLocaleString("pt-BR")} unidades de Mercado Real Viena</strong>. A parte fora da disputa não aumenta nem reduz a participação da equipe, porque fica fora do denominador comercial.
                </div>
              </> : <div className="mt-5 rounded-xl border border-[#17304d] bg-[#071427] p-4 text-sm text-slate-400">Carregando composição do mercado ANFIR...</div>}
            </section>

            <section className="rounded-3xl border border-[#17304d] bg-[#061126] p-5 sm:p-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">2 · Quanto deste mercado está ligado à equipe ou responsável?</p>
                <h2 className="mt-2 text-2xl font-bold">Participação dentro do Mercado Real Viena</h2>
                <p className="mt-2 max-w-4xl text-sm text-slate-400">A partir daqui a comparação usa somente o Mercado Real Viena. O mercado fora da disputa já foi retirado e não interfere nos percentuais abaixo.</p>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="100% da base comercial disponível para a Viena." />
                <Kpi titulo="Ligado à análise selecionada" valor={dados.mercado.mercado_real_selecao_2026} apoio={`${dados.mercado.participacao_regiao_no_mercado_real_pct.toFixed(1)}% do Mercado Real Viena.`} />
                <Kpi titulo="Demais unidades do Mercado Real" valor={Math.max(0, dados.mercado.mercado_real_viena_2026 - dados.mercado.mercado_real_selecao_2026)} apoio={`${Math.max(0, 100 - dados.mercado.participacao_regiao_no_mercado_real_pct).toFixed(1)}% do Mercado Real Viena.`} />
                <Kpi titulo="Clientes identificados" valor={dados.mercado.clientes_unicos} apoio="Clientes encontrados na ANFIR para a análise selecionada." />
              </div>

              <div className="mt-5 grid gap-5 xl:grid-cols-2">
                <GraficoPizzaParticipacao percentual={dados.mercado.participacao_regiao_no_mercado_real_pct} selecionado={dados.mercado.mercado_real_selecao_2026} total={dados.mercado.mercado_real_viena_2026} nome={dados.selecao.nome} />
                <GraficoPizzaFamilias familias={dados.mercado.familias} total={familiaTotal} />
              </div>
            </section>

            <section className="rounded-3xl border border-[#17304d] bg-[#061126] p-5 sm:p-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">3 · O que aconteceu antes e o que está acontecendo agora?</p>
                <h2 className="mt-2 text-2xl font-bold">Histórico comercial e operação atual</h2>
                <p className="mt-2 max-w-4xl text-sm text-slate-400">Histórico/Funil e CRM não são somados ao mercado ANFIR. Eles explicam o movimento comercial relacionado aos clientes desta análise.</p>
              </div>
              <div className="mt-5 grid gap-4 xl:grid-cols-2">
                <div className="rounded-2xl border border-amber-500/20 bg-[#071226] p-5">
                  <p className="text-xs font-semibold uppercase tracking-[.14em] text-amber-300">Histórico / Funil 2026</p>
                  <p className="mt-2 text-sm text-slate-400">Mostra negociações e movimentos comerciais que passaram pelo funil durante 2026.</p>
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <MiniKpi rotulo="Eventos registrados" valor={dados.evidencias.historico_registros_2026} />
                    <MiniKpi rotulo="Unidades registradas" valor={dados.evidencias.historico_unidades_2026} />
                  </div>
                </div>
                <div className="rounded-2xl border border-emerald-500/20 bg-[#071226] p-5">
                  <p className="text-xs font-semibold uppercase tracking-[.14em] text-emerald-300">CRM em operação</p>
                  <p className="mt-2 text-sm text-slate-400">Mostra as negociações que a equipe comercial está conduzindo neste momento.</p>
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <MiniKpi rotulo="Registros no CRM" valor={dados.evidencias.crm_registros} />
                    <MiniKpi rotulo="Negociações ativas" valor={dados.evidencias.crm_ativos} />
                    <MiniKpi rotulo="Valor ativo no pipeline" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} />
                  </div>
                </div>
              </div>
              <div className="mt-5 grid gap-5 xl:grid-cols-2">
                <Lista titulo="Situação das negociações atuais no CRM" itens={dados.evidencias.crm_status} vazio="Sem negociações CRM para a equipe ou responsável selecionado." />
                <Lista titulo="Motivos registrados nas perdas do Histórico/Funil 2026" itens={dados.evidencias.motivos_perda_historico} vazio="Sem motivos de perda registrados no Histórico/Funil para esta análise." />
              </div>
            </section>

            <details className="group rounded-3xl border border-slate-700/60 bg-[#061126] p-5 sm:p-6">
              <summary className="cursor-pointer list-none">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[.18em] text-slate-500">4 · Origem e conferência dos dados</p>
                    <h2 className="mt-2 text-xl font-bold">Abrir somente quando precisar auditar ou entender o cruzamento das fontes</h2>
                    <p className="mt-2 text-sm text-slate-400">ANFIR = mercado realizado · Histórico/Funil = movimentos do período · CRM = operação atual.</p>
                  </div>
                  <span className="shrink-0 rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300 group-open:hidden">Abrir detalhes</span>
                  <span className="hidden shrink-0 rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300 group-open:inline">Fechar detalhes</span>
                </div>
              </summary>

              <div className="mt-5 border-t border-slate-700/60 pt-5">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <MiniKpiPercent rotulo="Clientes encontrados na ANFIR" valor={dados.reconciliacao.clientes_anfir} base={dados.reconciliacao.universo_clientes} />
                  <MiniKpiPercent rotulo="Clientes no Histórico/Funil" valor={dados.reconciliacao.clientes_historico} base={dados.reconciliacao.universo_clientes} />
                  <MiniKpiPercent rotulo="Clientes no CRM atual" valor={dados.reconciliacao.clientes_crm} base={dados.reconciliacao.universo_clientes} />
                  <MiniKpiPercent rotulo="Presentes nas 3 fontes" valor={dados.reconciliacao.nas_tres_fontes} base={dados.reconciliacao.universo_clientes} />
                </div>
                <div className="mt-4 rounded-xl border border-slate-700 bg-[#071226] px-4 py-3 text-xs leading-relaxed text-slate-400">
                  Existem registros históricos ou atuais que não pertencem ao Mercado Real Viena usado no cálculo de participação. Eles ficam disponíveis aqui somente para rastreabilidade e auditoria e não alteram o total do mercado.
                </div>
              </div>
            </details>
          </>}
        </div>
      </section>
    </main>
  )
}

function pct(parte: number, total: number) { return total > 0 ? parte / total * 100 : 0 }

function MercadoCard({ titulo, valor, percentual, apoio, tom = "cyan" }: { titulo: string; valor: number; percentual: number; apoio: string; tom?: "cyan" | "amber" | "emerald" }) {
  const cor = tom === "amber" ? "text-amber-300" : tom === "emerald" ? "text-emerald-300" : "text-cyan-300"
  const borda = tom === "amber" ? "border-amber-500/30" : tom === "emerald" ? "border-emerald-500/30" : "border-cyan-500/30"
  return <div className={`rounded-2xl border ${borda} bg-[#071226] p-5`}><p className="text-xs font-semibold uppercase tracking-[.13em] text-slate-400">{titulo}</p><div className="mt-2 flex items-end gap-3"><strong className={`text-3xl ${cor}`}>{valor.toLocaleString("pt-BR")}</strong><span className={`pb-1 text-lg font-bold ${cor}`}>{percentual.toFixed(1)}%</span></div><p className="mt-2 text-xs leading-relaxed text-slate-500">{apoio}</p></div>
}

function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) {
  const foraPct = pct(fora, total)
  const realPct = pct(real, total)
  return <div className="mt-5 rounded-2xl border border-[#17304d] bg-[#071226] p-5"><div className="flex items-center justify-between gap-4"><div><h3 className="font-semibold">Como o mercado total se transforma em Mercado Real Viena</h3><p className="mt-1 text-xs text-slate-500">A barra representa 100% do mercado territorial observado.</p></div><strong className="text-sm text-slate-300">{total.toLocaleString("pt-BR")} = 100%</strong></div><div className="mt-4 flex h-8 w-full overflow-hidden rounded-full bg-slate-900"><div className="flex items-center justify-center bg-amber-500/80 text-[11px] font-bold text-black" style={{ width: `${foraPct}%` }}>{foraPct >= 12 ? `${foraPct.toFixed(1)}%` : ""}</div><div className="flex items-center justify-center bg-emerald-400/80 text-[11px] font-bold text-black" style={{ width: `${realPct}%` }}>{realPct >= 12 ? `${realPct.toFixed(1)}%` : ""}</div></div><div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs"><span className="text-amber-300">● Fora da disputa Viena: {fora.toLocaleString("pt-BR")} · {foraPct.toFixed(1)}%</span><span className="text-emerald-300">● Mercado Real Viena: {real.toLocaleString("pt-BR")} · {realPct.toFixed(1)}%</span></div></div>
}

function Kpi({ titulo, valor, apoio }: { titulo: string; valor: number | string; apoio: string }) {
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><p className="text-xs font-semibold uppercase tracking-[.13em] text-cyan-300">{titulo}</p><strong className="mt-2 block text-3xl text-white">{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong><p className="mt-2 text-xs leading-relaxed text-slate-500">{apoio}</p></div>
}

function MiniKpi({ rotulo, valor }: { rotulo: string; valor: number | string }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#08162d] p-3"><p className="text-[11px] uppercase tracking-[.1em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-xl text-slate-100">{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong></div>
}

function MiniKpiPercent({ rotulo, valor, base }: { rotulo: string; valor: number; base: number }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#08162d] p-3"><p className="text-[11px] uppercase tracking-[.1em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-xl text-slate-100">{valor.toLocaleString("pt-BR")}</strong><p className="mt-1 text-xs text-cyan-300">{pct(valor, base).toFixed(1)}% dos {base.toLocaleString("pt-BR")} clientes unidos</p></div>
}

function GraficoPizzaParticipacao({ percentual, selecionado, total, nome }: { percentual: number; selecionado: number; total: number; nome: string }) {
  const valorPct = Math.max(0, Math.min(100, percentual))
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">Quanto esta análise representa do Mercado Real Viena</h2><p className="mt-2 text-sm text-slate-400">Fonte: ANFIR 2026. Aqui o denominador já é somente o mercado disponível para a Viena.</p><div className="mt-5 flex flex-col items-center gap-6 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${valorPct}%, #172554 ${valorPct}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-2xl text-cyan-300">{valorPct.toFixed(1)}%</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`${nome}: ${selecionado.toLocaleString("pt-BR")} · ${valorPct.toFixed(1)}%`} /><Legenda cor="bg-blue-950" texto={`Demais unidades: ${Math.max(0, total - selecionado).toLocaleString("pt-BR")} · ${Math.max(0, 100 - valorPct).toFixed(1)}%`} /><div className="pt-2 text-xs font-semibold text-slate-400">{selecionado.toLocaleString("pt-BR")} de {total.toLocaleString("pt-BR")} unidades</div></div></div></div>
}

function GraficoPizzaFamilias({ familias, total }: { familias: { trailer: number; diesel_truck: number; direct_drive: number }; total: number }) {
  const tr = pct(familias.trailer, total)
  const dt = pct(familias.diesel_truck, total)
  const dd = pct(familias.direct_drive, total)
  const ddFim = Math.min(100, tr + dt + dd)
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">Como as unidades se dividem por linha</h2><p className="mt-2 text-sm text-slate-400">Fonte: ANFIR 2026. Distribuição das unidades ligadas à análise selecionada.</p><div className="mt-5 flex flex-col items-center gap-6 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${tr}%, #f59e0b ${tr}% ${tr + dt}%, #34d399 ${tr + dt}% ${ddFim}%, #172554 ${ddFim}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-xl">{total.toLocaleString("pt-BR")}</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`Trailer: ${familias.trailer.toLocaleString("pt-BR")} · ${tr.toFixed(1)}%`} /><Legenda cor="bg-amber-500" texto={`Diesel Truck: ${familias.diesel_truck.toLocaleString("pt-BR")} · ${dt.toFixed(1)}%`} /><Legenda cor="bg-emerald-400" texto={`Direct Drive: ${familias.direct_drive.toLocaleString("pt-BR")} · ${dd.toFixed(1)}%`} /></div></div></div>
}

function Legenda({ cor, texto }: { cor: string; texto: string }) { return <div className="flex items-center gap-2 text-slate-300"><span className={`h-3 w-3 rounded-sm ${cor}`} />{texto}</div> }
function Lista({ titulo, itens, vazio }: { titulo: string; itens: Array<{ nome: string; quantidade: number }>; vazio: string }) { return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.map((item) => <div key={item.nome} className="flex items-center justify-between rounded-xl bg-[#08162d] px-3 py-2.5 text-sm"><span className="text-slate-300">{item.nome}</span><strong className="text-cyan-300">{item.quantidade.toLocaleString("pt-BR")}</strong></div>)}</div>}</div> }
function formatarMoeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
