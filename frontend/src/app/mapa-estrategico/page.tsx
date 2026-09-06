"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getMapaEquipeVisao, type MapaEquipeVisao, type ParticipacaoEquipe } from "@/services/mapa-equipe-api"

export default function Page() {
  const [responsavelId, setResponsavelId] = useState<string>("")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
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
              <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Gestão comercial regional</p>
              <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Mapa Comercial Estratégico</h1>
              <p className="mt-2 text-sm text-slate-400">Mercado Real Viena 2026 por região e responsável.</p>
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
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando leitura regional...</div>}

          {!loading && dados && <>
            <section className="flex flex-col gap-3 rounded-2xl border border-cyan-500/30 bg-[#071226] p-5 lg:flex-row lg:items-center lg:justify-between">
              <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Responsável analisado</p><h2 className="mt-1 text-2xl font-semibold">{dados.selecao.nome}</h2>{(dados.selecao.codigo_regional || dados.selecao.ddds.length > 0) && <p className="mt-1 text-sm text-slate-400">{dados.selecao.codigo_regional || "Viena SP"}{dados.selecao.ddds.length ? ` · DDDs ${dados.selecao.ddds.join(", ")}` : ""}</p>}</div>
              <span className="rounded-full border border-cyan-500/20 bg-cyan-950/10 px-4 py-2 text-xs font-semibold text-cyan-200">Base: Mercado Real Viena 2026</span>
            </section>

            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="100,0% da base comercial" />
              <Kpi titulo="Mercado da carteira" valor={dados.mercado.mercado_real_selecao_2026} apoio="Unidades no recorte selecionado" />
              <Kpi titulo="Participação no mercado real" valor={`${dados.mercado.participacao_regiao_no_mercado_real_pct.toFixed(1)}%`} apoio={`${dados.mercado.mercado_real_selecao_2026.toLocaleString("pt-BR")} de ${dados.mercado.mercado_real_viena_2026.toLocaleString("pt-BR")}`} destaque />
              <Kpi titulo="Clientes únicos" valor={dados.mercado.clientes_unicos} apoio="Clientes ANFIR no recorte" />
            </section>

            <section className="grid gap-5 xl:grid-cols-2">
              <GraficoPizzaParticipacao percentual={dados.mercado.participacao_regiao_no_mercado_real_pct} selecionado={dados.mercado.mercado_real_selecao_2026} total={dados.mercado.mercado_real_viena_2026} nome={dados.selecao.nome} />
              <GraficoPizzaFamilias familias={dados.mercado.familias} total={familiaTotal} />
            </section>

            {dados.selecao.modo === "TODA_EQUIPE" && (
              <FechamentoEquipe
                participacoes={dados.mercado.participacoes_equipe}
                totalViena={dados.mercado.mercado_real_viena_2026}
                totalEquipe={dados.mercado.mercado_real_selecao_2026}
                somaIndividual={dados.mercado.soma_mercado_individual}
                sobreposicoes={dados.mercado.sobreposicoes_entre_carteiras}
                semCarteira={dados.mercado.mercado_real_sem_carteira}
              />
            )}

            <section className="rounded-2xl border border-emerald-500/30 bg-[#071226] p-5">
              <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
                <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">Conciliação das três fontes</p><h2 className="mt-1 text-xl font-semibold">Mesmo cliente · mesmo responsável · mesmo recorte</h2></div>
                <span className="text-xs text-slate-400">Universo reconciliado: {dados.reconciliacao.universo_clientes.toLocaleString("pt-BR")} clientes</span>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MiniKpi rotulo="Clientes ANFIR" valor={dados.reconciliacao.clientes_anfir} />
                <MiniKpi rotulo="Clientes Histórico/Funil" valor={dados.reconciliacao.clientes_historico} />
                <MiniKpi rotulo="Clientes CRM" valor={dados.reconciliacao.clientes_crm} />
                <MiniKpi rotulo="Presentes nas 3 fontes" valor={dados.reconciliacao.nas_tres_fontes} />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <MiniKpi rotulo="ANFIR + Histórico" valor={dados.reconciliacao.anfir_historico} />
                <MiniKpi rotulo="ANFIR + CRM" valor={dados.reconciliacao.anfir_crm} />
                <MiniKpi rotulo="Histórico + CRM" valor={dados.reconciliacao.historico_crm} />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <MiniKpi rotulo="Somente ANFIR" valor={dados.reconciliacao.somente_anfir} />
                <MiniKpi rotulo="Somente Histórico" valor={dados.reconciliacao.somente_historico} />
                <MiniKpi rotulo="Somente CRM" valor={dados.reconciliacao.somente_crm} />
              </div>
              <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-950/10 px-4 py-3 text-xs text-slate-300">Fora do Mercado Real deste recorte: Histórico/Funil {dados.reconciliacao.historico_fora_mercado_real.toLocaleString("pt-BR")} cliente(s) · CRM {dados.reconciliacao.crm_fora_mercado_real.toLocaleString("pt-BR")} cliente(s). Estes registros permanecem auditáveis, mas não entram no denominador de mercado.</div>
            </section>

            <section>
              <div className="mb-3"><p className="text-xs font-semibold uppercase tracking-[.16em] text-slate-500">Eventos comerciais do mesmo recorte</p></div>
              <div className="grid gap-4 xl:grid-cols-2">
                <div className="rounded-2xl border border-amber-500/20 bg-[#071226] p-5"><p className="text-xs font-semibold uppercase tracking-[.14em] text-amber-300">Histórico / Funil 2026</p><div className="mt-4 grid grid-cols-2 gap-3"><MiniKpi rotulo="Eventos registrados" valor={dados.evidencias.historico_registros_2026} /><MiniKpi rotulo="Unidades registradas" valor={dados.evidencias.historico_unidades_2026} /></div></div>
                <div className="rounded-2xl border border-emerald-500/20 bg-[#071226] p-5"><p className="text-xs font-semibold uppercase tracking-[.14em] text-emerald-300">CRM em operação</p><div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3"><MiniKpi rotulo="Eventos CRM" valor={dados.evidencias.crm_registros} /><MiniKpi rotulo="Ativos" valor={dados.evidencias.crm_ativos} /><MiniKpi rotulo="Pipeline ativo" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} /></div></div>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-2">
              <Lista titulo="Status atuais do CRM" itens={dados.evidencias.crm_status} vazio="Sem status CRM neste recorte." />
              <Lista titulo="Motivos de perda · Histórico/Funil 2026" itens={dados.evidencias.motivos_perda_historico} vazio="Sem motivos de perda registrados neste recorte." />
            </section>
          </>}
        </div>
      </section>
    </main>
  )
}

function FechamentoEquipe({ participacoes, totalViena, totalEquipe, somaIndividual, sobreposicoes, semCarteira }: { participacoes: ParticipacaoEquipe[]; totalViena: number; totalEquipe: number; somaIndividual: number; sobreposicoes: number; semCarteira: number }) {
  const pctEquipe = totalViena ? totalEquipe / totalViena * 100 : 0
  return <section className="rounded-2xl border border-violet-500/30 bg-[#071226] p-5">
    <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
      <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-300">Fechamento macro = micro</p><h2 className="mt-1 text-xl font-semibold">Participação real da equipe no Mercado Real Viena</h2></div>
      <strong className="text-2xl text-violet-200">{totalEquipe.toLocaleString("pt-BR")} de {totalViena.toLocaleString("pt-BR")} · {pctEquipe.toFixed(1)}%</strong>
    </div>
    <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {participacoes.map((item) => <MiniKpi key={item.id} rotulo={item.nome} valor={`${item.mercado.toLocaleString("pt-BR")} · ${item.participacao_pct.toFixed(1)}%`} />)}
    </div>
    <div className="mt-4 grid gap-3 sm:grid-cols-3">
      <MiniKpi rotulo="Soma das carteiras individuais" valor={somaIndividual} />
      <MiniKpi rotulo="Sobreposição entre carteiras" valor={sobreposicoes} />
      <MiniKpi rotulo="Mercado real ainda sem carteira" valor={semCarteira} />
    </div>
    <p className="mt-4 text-xs text-slate-400">Fechamento obrigatório: soma individual − sobreposições = carteira consolidada da equipe. Carteira consolidada + mercado sem carteira = Mercado Real Viena.</p>
  </section>
}

function Kpi({ titulo, valor, apoio, destaque = false }: { titulo: string; valor: number | string; apoio: string; destaque?: boolean }) {
  return <div className={`rounded-2xl border bg-[#071226] p-5 ${destaque ? "border-cyan-400/50" : "border-[#17304d]"}`}><p className="text-xs font-semibold uppercase tracking-[.13em] text-cyan-300">{titulo}</p><strong className={`mt-2 block text-3xl ${destaque ? "text-cyan-300" : "text-white"}`}>{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong><p className="mt-2 text-xs text-slate-500">{apoio}</p></div>
}

function MiniKpi({ rotulo, valor }: { rotulo: string; valor: number | string }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#08162d] p-3"><p className="text-[11px] uppercase tracking-[.1em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-xl text-slate-100">{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong></div>
}

function GraficoPizzaParticipacao({ percentual, selecionado, total, nome }: { percentual: number; selecionado: number; total: number; nome: string }) {
  const pct = Math.max(0, Math.min(100, percentual))
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">Participação no Mercado Real Viena</h2><div className="mt-5 flex flex-col items-center gap-6 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${pct}%, #172554 ${pct}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-2xl text-cyan-300">{pct.toFixed(1)}%</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`${nome}: ${selecionado.toLocaleString("pt-BR")}`} /><Legenda cor="bg-blue-950" texto={`Fora do recorte: ${Math.max(0, total - selecionado).toLocaleString("pt-BR")}`} /><div className="pt-2 text-xs font-semibold text-slate-400">{selecionado.toLocaleString("pt-BR")} de {total.toLocaleString("pt-BR")}</div></div></div></div>
}

function GraficoPizzaFamilias({ familias, total }: { familias: { trailer: number; diesel_truck: number; direct_drive: number }; total: number }) {
  const tr = total ? familias.trailer / total * 100 : 0
  const dt = total ? familias.diesel_truck / total * 100 : 0
  const dd = total ? familias.direct_drive / total * 100 : 0
  const ddFim = Math.min(100, tr + dt + dd)
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">Composição da carteira por linha</h2><div className="mt-5 flex flex-col items-center gap-6 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${tr}%, #f59e0b ${tr}% ${tr + dt}%, #34d399 ${tr + dt}% ${ddFim}%, #172554 ${ddFim}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-xl">{total.toLocaleString("pt-BR")}</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`Trailer: ${familias.trailer.toLocaleString("pt-BR")} · ${tr.toFixed(1)}%`} /><Legenda cor="bg-amber-500" texto={`Diesel Truck: ${familias.diesel_truck.toLocaleString("pt-BR")} · ${dt.toFixed(1)}%`} /><Legenda cor="bg-emerald-400" texto={`Direct Drive: ${familias.direct_drive.toLocaleString("pt-BR")} · ${dd.toFixed(1)}%`} /></div></div></div>
}

function Legenda({ cor, texto }: { cor: string; texto: string }) { return <div className="flex items-center gap-2 text-slate-300"><span className={`h-3 w-3 rounded-sm ${cor}`} />{texto}</div> }
function Lista({ titulo, itens, vazio }: { titulo: string; itens: Array<{ nome: string; quantidade: number }>; vazio: string }) { return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.map((item) => <div key={item.nome} className="flex items-center justify-between rounded-xl bg-[#08162d] px-3 py-2.5 text-sm"><span className="text-slate-300">{item.nome}</span><strong className="text-cyan-300">{item.quantidade.toLocaleString("pt-BR")}</strong></div>)}</div>}</div> }
function formatarMoeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
