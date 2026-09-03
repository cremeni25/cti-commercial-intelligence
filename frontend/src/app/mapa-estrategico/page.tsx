"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getMapaEquipeVisao, type MapaEquipeVisao } from "@/services/mapa-equipe-api"

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
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Gestão comercial regional</p>
              <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Mapa Comercial Estratégico</h1>
              <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
                Mercado Real Viena 2026 por região e responsável, com ANFIR como mercado, Histórico/Funil como evidência comercial e CRM como operação atual.
              </p>
            </div>
            {dados?.pode_selecionar_responsavel && (
              <label className="min-w-[320px] text-xs font-semibold uppercase tracking-[.12em] text-slate-400">
                Região / responsável
                <select
                  value={responsavelId}
                  onChange={(e) => trocarResponsavel(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-[#214363] bg-[#071226] px-4 py-3 text-sm font-medium normal-case tracking-normal text-white outline-none focus:border-cyan-400"
                >
                  <option value="">Toda a equipe comercial</option>
                  {dados.equipe.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.codigo_regional ? `${item.codigo_regional} — ` : ""}{item.nome}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando leitura regional...</div>}

          {!loading && dados && (
            <>
              <section className="rounded-2xl border border-cyan-500/30 bg-[#071226] p-5">
                <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Recorte ativo</p>
                    <h2 className="mt-1 text-2xl font-semibold">{dados.selecao.nome}</h2>
                    <p className="mt-2 text-sm text-slate-400">
                      {dados.selecao.codigo_regional || "Consolidado Viena SP"}
                      {dados.selecao.ddds.length ? ` · DDDs ${dados.selecao.ddds.join(", ")}` : ""}
                    </p>
                  </div>
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/10 px-4 py-3 text-sm text-cyan-100/80">
                    Base oficial: Mercado Real Viena 2026. Fibra West, High Flex e Planalto já estão fora do mercado funcional.
                  </div>
                </div>
              </section>

              <section className="grid gap-4 xl:grid-cols-3">
                <Kpi titulo="Mercado Real Viena 2026" valor={dados.mercado.mercado_real_viena_2026} apoio="Base total efetivamente disputável" />
                <Kpi titulo="Mercado da região / carteira" valor={dados.mercado.mercado_real_selecao_2026} apoio={`${dados.mercado.participacao_regiao_no_mercado_real_pct.toFixed(1)}% do Mercado Real Viena`} />
                <Kpi titulo="Clientes únicos no mercado real" valor={dados.mercado.clientes_unicos} apoio="Clientes observados no recorte ANFIR da seleção" />
              </section>

              <section className="grid gap-5 xl:grid-cols-2">
                <GraficoPizzaParticipacao
                  percentual={dados.mercado.participacao_regiao_no_mercado_real_pct}
                  selecionado={dados.mercado.mercado_real_selecao_2026}
                  total={dados.mercado.mercado_real_viena_2026}
                  titulo="Peso da região no Mercado Real Viena"
                />
                <GraficoPizzaFamilias familias={dados.mercado.familias} total={familiaTotal} />
              </section>

              <section className="grid gap-4 xl:grid-cols-2">
                <div className="rounded-2xl border border-amber-500/20 bg-[#071226] p-5">
                  <p className="text-xs font-semibold uppercase tracking-[.14em] text-amber-300">Evidência comercial preservada</p>
                  <h2 className="mt-1 text-xl font-semibold">Histórico / Funil 2026</h2>
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <MiniKpi rotulo="Registros" valor={dados.evidencias.historico_registros_2026} />
                    <MiniKpi rotulo="Unidades nominais" valor={dados.evidencias.historico_unidades_2026} />
                  </div>
                  <p className="mt-4 text-xs leading-5 text-slate-500">Estes números são evidências de registros comerciais de 2026. Não representam tamanho de mercado nem share.</p>
                </div>

                <div className="rounded-2xl border border-emerald-500/20 bg-[#071226] p-5">
                  <p className="text-xs font-semibold uppercase tracking-[.14em] text-emerald-300">Operação atual</p>
                  <h2 className="mt-1 text-xl font-semibold">CRM desde a implantação</h2>
                  <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <MiniKpi rotulo="Registros CRM" valor={dados.evidencias.crm_registros} />
                    <MiniKpi rotulo="Ativos" valor={dados.evidencias.crm_ativos} />
                    <MiniKpi rotulo="Pipeline ativo" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} />
                  </div>
                  {dados.evidencias.crm_status.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {dados.evidencias.crm_status.map((item) => <Badge key={item.nome}>{item.nome}: {item.quantidade}</Badge>)}
                    </div>
                  )}
                </div>
              </section>

              <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Rastreabilidade do ciclo</p>
                  <h2 className="mt-1 text-xl font-semibold">Cliente a cliente · evidências encontradas</h2>
                  <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">O CTI cruza nomes de clientes entre as três fontes para encontrar continuidade. A diferença entre os totais nunca é tratada como conversão ou falha da equipe.</p>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                  <MiniKpi rotulo="Mercado real" valor={dados.ciclo.clientes_mercado_real} />
                  <MiniKpi rotulo="Histórico 2026" valor={dados.ciclo.clientes_historico_2026} />
                  <MiniKpi rotulo="CRM" valor={dados.ciclo.clientes_crm} />
                  <MiniKpi rotulo="CRM + Histórico" valor={dados.ciclo.crm_com_evidencia_historico} />
                  <MiniKpi rotulo="CRM + ANFIR" valor={dados.ciclo.crm_com_evidencia_anfir} />
                  <MiniKpi rotulo="3 fontes" valor={dados.ciclo.clientes_com_evidencia_nas_tres_fontes} />
                </div>
                <div className="mt-4 rounded-xl border border-cyan-500/20 bg-cyan-950/10 p-4 text-xs leading-5 text-cyan-100/70">{dados.ciclo.nota}</div>
              </section>

              <section className="grid gap-5 xl:grid-cols-2">
                <Lista titulo="Status atuais do CRM" itens={dados.evidencias.crm_status} vazio="Ainda não há status CRM registrados neste recorte." />
                <Lista titulo="Motivos de perda registrados no Histórico/Funil 2026" itens={dados.evidencias.motivos_perda_historico} vazio="Não há motivos de perda registrados neste recorte." />
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor, apoio }: { titulo: string; valor: number; apoio: string }) {
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><p className="text-xs font-semibold uppercase tracking-[.13em] text-cyan-300">{titulo}</p><strong className="mt-2 block text-3xl">{valor.toLocaleString("pt-BR")}</strong><p className="mt-2 text-xs text-slate-500">{apoio}</p></div>
}

function MiniKpi({ rotulo, valor }: { rotulo: string; valor: number | string }) {
  return <div className="rounded-xl border border-[#13203f] bg-[#08162d] p-3"><p className="text-[11px] uppercase tracking-[.1em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-xl text-slate-100">{typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}</strong></div>
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300">{children}</span>
}

function GraficoPizzaParticipacao({ percentual, selecionado, total, titulo }: { percentual: number; selecionado: number; total: number; titulo: string }) {
  const pct = Math.max(0, Math.min(100, percentual))
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2><div className="mt-5 flex flex-col items-center gap-5 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${pct}%, #172554 ${pct}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-2xl">{pct.toFixed(1)}%</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`Região / carteira: ${selecionado.toLocaleString("pt-BR")}`} /><Legenda cor="bg-blue-950" texto={`Demais regiões: ${Math.max(0, total - selecionado).toLocaleString("pt-BR")}`} /><p className="pt-2 text-xs leading-5 text-slate-500">A pizza mede somente a participação territorial dentro do Mercado Real Viena 2026.</p></div></div></div>
}

function GraficoPizzaFamilias({ familias, total }: { familias: { trailer: number; diesel_truck: number; direct_drive: number }; total: number }) {
  const tr = total ? familias.trailer / total * 100 : 0
  const dt = total ? familias.diesel_truck / total * 100 : 0
  const ddFim = Math.min(100, tr + dt + (total ? familias.direct_drive / total * 100 : 0))
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">Composição do mercado real da região</h2><div className="mt-5 flex flex-col items-center gap-5 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(#22d3ee 0 ${tr}%, #f59e0b ${tr}% ${tr + dt}%, #34d399 ${tr + dt}% ${ddFim}%, #172554 ${ddFim}% 100%)` }}><div className="absolute inset-7 flex items-center justify-center rounded-full bg-[#071226]"><strong className="text-xl">{total.toLocaleString("pt-BR")}</strong></div></div><div className="space-y-3 text-sm"><Legenda cor="bg-cyan-400" texto={`Trailer: ${familias.trailer.toLocaleString("pt-BR")}`} /><Legenda cor="bg-amber-500" texto={`Diesel Truck: ${familias.diesel_truck.toLocaleString("pt-BR")}`} /><Legenda cor="bg-emerald-400" texto={`Direct Drive: ${familias.direct_drive.toLocaleString("pt-BR")}`} /><p className="pt-2 text-xs leading-5 text-slate-500">Distribuição interna do Mercado Real ANFIR 2026 no recorte selecionado.</p></div></div></div>
}

function Legenda({ cor, texto }: { cor: string; texto: string }) {
  return <div className="flex items-center gap-2 text-slate-300"><span className={`h-3 w-3 rounded-sm ${cor}`} />{texto}</div>
}

function Lista({ titulo, itens, vazio }: { titulo: string; itens: Array<{ nome: string; quantidade: number }>; vazio: string }) {
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="font-semibold">{titulo}</h2>{itens.length === 0 ? <p className="mt-4 text-sm text-slate-500">{vazio}</p> : <div className="mt-4 space-y-2">{itens.map((item) => <div key={item.nome} className="flex items-center justify-between rounded-xl bg-[#08162d] px-3 py-2.5 text-sm"><span className="text-slate-300">{item.nome}</span><strong className="text-cyan-300">{item.quantidade.toLocaleString("pt-BR")}</strong></div>)}</div>}</div>
}

function formatarMoeda(valor: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(valor || 0)
}
