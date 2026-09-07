"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import {
  getMapaEquipeInteligencia,
  getMapaEquipeVisao,
  perguntarMapaEquipeInteligencia,
  type FonteContextual,
  type MapaEquipeVisao,
  type TurnoContextual,
} from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }

export default function Page() {
  const [responsavelId, setResponsavelId] = useState("")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
  const [mercadoMacro, setMercadoMacro] = useState<MercadoMacro | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [analiseIa, setAnaliseIa] = useState("")
  const [fontesContextuais, setFontesContextuais] = useState<FonteContextual[]>([])
  const [loadingIa, setLoadingIa] = useState(true)
  const [erroIa, setErroIa] = useState("")
  const [perguntaContextual, setPerguntaContextual] = useState("")
  const [historicoContextual, setHistoricoContextual] = useState<TurnoContextual[]>([])
  const [perguntando, setPerguntando] = useState(false)

  useEffect(() => {
    let ativo = true
    getMapaEquipeVisao(responsavelId || null)
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar a visão comercial.") })
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
        // A visão principal permanece disponível mesmo se esta leitura auxiliar falhar.
      }
    })()
    return () => { ativo = false }
  }, [])

  useEffect(() => {
    let ativo = true
    getMapaEquipeInteligencia(responsavelId || null)
      .then((resposta) => {
        if (!ativo) return
        setAnaliseIa(resposta.analise || "")
        setFontesContextuais(resposta.fontes_contextuais || [])
      })
      .catch((e) => { if (ativo) setErroIa(e instanceof Error ? e.message : "A leitura inteligente não foi concluída.") })
      .finally(() => { if (ativo) setLoadingIa(false) })
    return () => { ativo = false }
  }, [responsavelId])

  async function carregarInteligencia(id = responsavelId) {
    setLoadingIa(true)
    setErroIa("")
    try {
      const resposta = await getMapaEquipeInteligencia(id || null)
      setAnaliseIa(resposta.analise || "")
      setFontesContextuais(resposta.fontes_contextuais || [])
      setHistoricoContextual([])
    } catch (e) {
      setAnaliseIa("")
      setFontesContextuais([])
      setErroIa(e instanceof Error ? e.message : "A leitura inteligente não foi concluída.")
    } finally {
      setLoadingIa(false)
    }
  }

  async function perguntarContexto() {
    const pergunta = perguntaContextual.trim()
    if (!pergunta || perguntando) return
    setPerguntando(true)
    setErroIa("")
    try {
      const resposta = await perguntarMapaEquipeInteligencia(pergunta, historicoContextual, responsavelId || null)
      const novosTurnos: TurnoContextual[] = [
        { role: "user", content: pergunta },
        { role: "assistant", content: resposta.analise || "" },
      ]
      setHistoricoContextual((atual) => [...atual, ...novosTurnos].slice(-8))
      setFontesContextuais(resposta.fontes_contextuais || [])
      setPerguntaContextual("")
    } catch (e) {
      setErroIa(e instanceof Error ? e.message : "Não foi possível aprofundar esta leitura.")
    } finally {
      setPerguntando(false)
    }
  }

  const familiaTotal = useMemo(() => {
    if (!dados) return 0
    const f = dados.mercado.familias
    return f.trailer + f.diesel_truck + f.direct_drive
  }, [dados])

  function trocarResponsavel(novoId: string) {
    setLoading(true)
    setErro("")
    setLoadingIa(true)
    setErroIa("")
    setAnaliseIa("")
    setFontesContextuais([])
    setHistoricoContextual([])
    setPerguntaContextual("")
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
              <p className="mt-2 max-w-3xl text-sm text-slate-400">Mercado, cobertura comercial, continuidade entre bases e negócios em andamento na seleção atual.</p>
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

          {!loading && dados && (
            <VisaoExecutiva
              dados={dados}
              mercadoMacro={mercadoMacro}
              familiaTotal={familiaTotal}
              analiseIa={analiseIa}
              fontesContextuais={fontesContextuais}
              loadingIa={loadingIa}
              erroIa={erroIa}
              atualizarIa={() => void carregarInteligencia()}
              perguntaContextual={perguntaContextual}
              setPerguntaContextual={setPerguntaContextual}
              historicoContextual={historicoContextual}
              perguntando={perguntando}
              perguntarContexto={() => void perguntarContexto()}
            />
          )}
        </div>
      </section>
    </main>
  )
}

function VisaoExecutiva({
  dados,
  mercadoMacro,
  familiaTotal,
  analiseIa,
  fontesContextuais,
  loadingIa,
  erroIa,
  atualizarIa,
  perguntaContextual,
  setPerguntaContextual,
  historicoContextual,
  perguntando,
  perguntarContexto,
}: {
  dados: MapaEquipeVisao
  mercadoMacro: MercadoMacro | null
  familiaTotal: number
  analiseIa: string
  fontesContextuais: FonteContextual[]
  loadingIa: boolean
  erroIa: string
  atualizarIa: () => void
  perguntaContextual: string
  setPerguntaContextual: (valor: string) => void
  historicoContextual: TurnoContextual[]
  perguntando: boolean
  perguntarContexto: () => void
}) {
  const ticketPipeline = dados.evidencias.crm_ativos > 0
    ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos
    : 0
  const coberturaVinculo = pct(dados.mercado.mercado_real_selecao_2026, dados.mercado.mercado_real_viena_2026)
  const crmComHistorico = pct(dados.ciclo.crm_com_evidencia_historico, dados.ciclo.clientes_crm)
  const crmComAnfir = pct(dados.ciclo.crm_com_evidencia_anfir, dados.ciclo.clientes_crm)
  const crmNasTres = pct(dados.ciclo.clientes_com_evidencia_nas_tres_fontes, dados.ciclo.clientes_crm)

  return <>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="ANFIR 2026" destaque="emerald" />
      <Kpi titulo="Vínculos ANFIR seguros" valor={dados.mercado.mercado_real_selecao_2026} apoio={`${coberturaVinculo.toFixed(1)}% do mercado real`} destaque="cyan" />
      <Kpi titulo="Clientes ANFIR identificados" valor={dados.mercado.clientes_unicos} apoio={dados.selecao.nome} />
      <Kpi titulo="Negociações CRM ativas" valor={dados.evidencias.crm_ativos} apoio="autoria operacional" destaque="emerald" />
      <Kpi titulo="Pipeline ativo" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} apoio={dados.evidencias.crm_ativos ? `ticket médio ${formatarMoeda(ticketPipeline)}` : "sem negociações ativas"} />
    </section>

    <section className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Sinais de decisão</p>
        <h2 className="mt-1 text-xl font-bold">Onde a seleção pede atenção</h2>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Sinal
          titulo="Cobertura do mercado"
          valor={`${coberturaVinculo.toFixed(1)}%`}
          texto={`${dados.mercado.mercado_real_selecao_2026} vínculos ANFIR seguros sobre ${dados.mercado.mercado_real_viena_2026} do mercado real Viena.`}
        />
        <Sinal
          titulo="Continuidade CRM ↔ Histórico"
          valor={`${crmComHistorico.toFixed(0)}%`}
          texto={`${dados.ciclo.crm_com_evidencia_historico} de ${dados.ciclo.clientes_crm} clientes do CRM possuem evidência histórica.`}
        />
        <Sinal
          titulo="Continuidade CRM ↔ ANFIR"
          valor={`${crmComAnfir.toFixed(0)}%`}
          texto={`${dados.ciclo.crm_com_evidencia_anfir} de ${dados.ciclo.clientes_crm} clientes do CRM possuem evidência ANFIR.`}
        />
        <Sinal
          titulo="Continuidade completa"
          valor={`${crmNasTres.toFixed(0)}%`}
          texto={`${dados.ciclo.clientes_com_evidencia_nas_tres_fontes} cliente(s) do CRM aparecem simultaneamente em ANFIR e Histórico.`}
        />
      </div>
      {(dados.reconciliacao.somente_anfir > 0 || dados.reconciliacao.crm_fora_mercado_real > 0) && (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {dados.reconciliacao.somente_anfir > 0 && (
            <Alerta
              titulo="Lacuna de conhecimento comercial"
              texto={`${dados.reconciliacao.somente_anfir} cliente(s) aparecem apenas na ANFIR, sem evidência correspondente em Histórico ou CRM. Isso é lacuna de cobertura de dados, não oportunidade automática.`}
            />
          )}
          {dados.reconciliacao.crm_fora_mercado_real > 0 && (
            <Alerta
              titulo="CRM fora do mercado real atual"
              texto={`${dados.reconciliacao.crm_fora_mercado_real} cliente(s) do CRM não estão reconciliados com o mercado real ANFIR desta seleção e exigem conferência de contexto, não exclusão automática.`}
            />
          )}
        </div>
      )}
    </section>

    <section className="grid gap-4 xl:grid-cols-[.9fr_1.1fr]">
      <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-slate-500">Mercado 2026</p><h2 className="mt-1 text-xl font-bold">Tamanho e composição</h2></div>
          <span className="rounded-full border border-cyan-500/20 px-3 py-1 text-xs text-cyan-200">ANFIR 2026</span>
        </div>
        {mercadoMacro && <div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div>}
        <div className="mt-4 grid gap-2 sm:grid-cols-3">
          <MiniKpi rotulo="Trailer" valor={dados.mercado.familias.trailer} apoio={`${pct(dados.mercado.familias.trailer, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
          <MiniKpi rotulo="Diesel Truck" valor={dados.mercado.familias.diesel_truck} apoio={`${pct(dados.mercado.familias.diesel_truck, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
          <MiniKpi rotulo="Direct Drive" valor={dados.mercado.familias.direct_drive} apoio={`${pct(dados.mercado.familias.direct_drive, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
        </div>
      </div>

      <div className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5">
        <div className="flex items-center justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">CRM atual</p><h2 className="mt-1 text-xl font-bold">Negócios em andamento</h2></div>
          <strong className="text-emerald-300">{dados.evidencias.crm_ativos} ativas</strong>
        </div>
        <div className="mt-4 space-y-2">
          {dados.evidencias.crm_status.length
            ? dados.evidencias.crm_status.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />)
            : <p className="text-sm text-slate-500">Sem negociações ativas nesta seleção.</p>}
        </div>
      </div>
    </section>

    {(analiseIa || erroIa || loadingIa) && (
      <section className="rounded-3xl border border-violet-500/30 bg-[#081126] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-300">Interpretação contextual</p><h2 className="mt-1 text-xl font-bold">Leitura da seleção atual</h2></div>
          {!loadingIa && <button type="button" onClick={atualizarIa} disabled={perguntando} className="rounded-xl border border-violet-400/30 px-3 py-2 text-xs font-semibold text-violet-200 disabled:opacity-50">Atualizar</button>}
        </div>
        {loadingIa && <p className="mt-4 text-sm text-slate-500">Interpretação em processamento. Os sinais objetivos acima permanecem disponíveis.</p>}
        {!loadingIa && erroIa && <p className="mt-4 text-sm text-amber-200">Interpretação indisponível nesta tentativa. Os indicadores objetivos acima continuam válidos.</p>}
        {!loadingIa && analiseIa && <div className="mt-5 whitespace-pre-wrap text-[15px] leading-7 text-slate-200">{analiseIa}</div>}

        {!loadingIa && analiseIa && historicoContextual.length > 0 && (
          <div className="mt-5 space-y-3 border-t border-violet-400/15 pt-4">
            {historicoContextual.slice(-4).map((turno, index) => (
              <div key={`${turno.role}-${index}`} className={turno.role === "user" ? "rounded-xl bg-violet-500/10 px-3 py-2 text-sm text-violet-100" : "whitespace-pre-wrap text-sm leading-6 text-slate-300"}>
                {turno.role === "user" && <span className="mr-2 text-[10px] font-semibold uppercase tracking-[.12em] text-violet-300">Pergunta</span>}
                {turno.content}
              </div>
            ))}
          </div>
        )}

        {!loadingIa && analiseIa && (
          <div className="mt-5 border-t border-violet-400/15 pt-4">
            <div className="flex gap-2">
              <input
                value={perguntaContextual}
                onChange={(e) => setPerguntaContextual(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); perguntarContexto() } }}
                disabled={perguntando}
                placeholder="Pergunte sobre a leitura desta seleção..."
                className="min-w-0 flex-1 rounded-xl border border-violet-400/20 bg-[#060d1d] px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 focus:border-violet-400/50 disabled:opacity-60"
              />
              <button type="button" onClick={perguntarContexto} disabled={perguntando || !perguntaContextual.trim()} className="rounded-xl border border-violet-400/30 px-4 py-2.5 text-sm font-semibold text-violet-100 disabled:opacity-40">
                {perguntando ? "Analisando..." : "Perguntar"}
              </button>
            </div>
          </div>
        )}

        {!loadingIa && analiseIa && fontesContextuais.length > 0 && (
          <details className="mt-4 border-t border-violet-400/10 pt-3 text-xs text-slate-500">
            <summary className="cursor-pointer list-none font-semibold text-slate-400">Contexto utilizado</summary>
            <div className="mt-3 space-y-2">
              {fontesContextuais.map((fonte) => (
                <div key={fonte.codigo}><strong className="text-slate-400">{fonte.nome}: </strong><span>{fonte.evidencia}</span></div>
              ))}
            </div>
          </details>
        )}
      </section>
    )}

    <details className="rounded-2xl border border-amber-500/15 bg-[#061126] px-5 py-4">
      <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">
        Evidências históricas <span className="ml-2 text-xs font-normal text-slate-500">apoio à interpretação, não leitura principal</span>
      </summary>
      <div className="mt-4 grid gap-3 border-t border-slate-700/60 pt-4 sm:grid-cols-3">
        <MiniKpi rotulo="Registros 2026" valor={dados.evidencias.historico_registros_2026} />
        <MiniKpi rotulo="Unidades registradas" valor={dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} />
        <MiniKpi rotulo="Clientes com histórico" valor={dados.reconciliacao.clientes_historico} />
      </div>
      {dados.evidencias.motivos_perda_historico.length > 0 && (
        <div className="mt-4 space-y-2">
          {dados.evidencias.motivos_perda_historico.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.motivos_perda_historico.reduce((s, i) => s + i.quantidade, 0))} />)}
        </div>
      )}
    </details>

    <details className="rounded-2xl border border-slate-700/60 bg-[#061126] px-5 py-4">
      <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Auditoria e origem dos dados</summary>
      <div className="mt-4 space-y-2 border-t border-slate-700/60 pt-4 text-sm text-slate-400">
        <p>ANFIR: {dados.reconciliacao.clientes_anfir} clientes · Histórico: {dados.reconciliacao.clientes_historico} · CRM: {dados.reconciliacao.clientes_crm}</p>
        <p>Interseções: ANFIR + Histórico {dados.reconciliacao.anfir_historico} · ANFIR + CRM {dados.reconciliacao.anfir_crm} · Histórico + CRM {dados.reconciliacao.historico_crm} · 3 fontes {dados.reconciliacao.nas_tres_fontes}</p>
      </div>
    </details>
  </>
}

function Kpi({ titulo, valor, apoio, destaque }: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald" }) {
  const cor = destaque === "emerald" ? "text-emerald-300" : destaque === "cyan" ? "text-cyan-300" : "text-white"
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><div className={`mt-2 text-2xl font-bold ${cor}`}>{valor}</div>{apoio && <p className="mt-1 text-xs text-slate-500">{apoio}</p>}</div>
}

function Sinal({ titulo, valor, texto }: { titulo: string; valor: string; texto: string }) {
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><strong className="mt-2 block text-2xl text-cyan-300">{valor}</strong><p className="mt-2 text-sm leading-5 text-slate-400">{texto}</p></div>
}

function Alerta({ titulo, texto }: { titulo: string; texto: string }) {
  return <div className="rounded-2xl border border-amber-500/25 bg-amber-950/10 p-4"><p className="text-sm font-semibold text-amber-200">{titulo}</p><p className="mt-1 text-sm leading-5 text-slate-400">{texto}</p></div>
}

function MiniKpi({ rotulo, valor, apoio }: { rotulo: string; valor: string | number; apoio?: string }) {
  return <div className="rounded-xl border border-[#17304d] bg-[#09152a] p-3"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{rotulo}</p><strong className="mt-1 block text-lg text-white">{valor}</strong>{apoio && <span className="text-[11px] text-cyan-300">{apoio}</span>}</div>
}

function BarraStatus({ nome, valor, total }: { nome: string; valor: number; total: number }) {
  const percentual = pct(valor, total)
  return <div><div className="mb-1 flex justify-between gap-3 text-xs"><span>{nome.replaceAll("_", " ")}</span><span className="font-semibold text-cyan-300">{valor} · {percentual.toFixed(0)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-[#0b2040]"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(100, percentual)}%` }} /></div></div>
}

function BarraMercado({ total, fora, real }: { total: number; fora: number; real: number }) {
  const foraPct = pct(fora, total)
  const realPct = pct(real, total)
  return <div><div className="mb-2 flex flex-wrap justify-between gap-2 text-xs"><span className="text-slate-400">Mercado territorial observado: <strong className="text-white">{total}</strong></span><span><span className="text-amber-300">Fora da disputa {fora} · {foraPct.toFixed(1)}%</span><span className="ml-3 text-emerald-300">Mercado Real {real} · {realPct.toFixed(1)}%</span></span></div><div className="flex h-4 overflow-hidden rounded-full bg-slate-900"><div className="bg-amber-500" style={{ width: `${foraPct}%` }} /><div className="bg-emerald-500" style={{ width: `${realPct}%` }} /></div></div>
}

function pct(valor: number, total: number) { return total > 0 ? (valor / total) * 100 : 0 }
function formatarMoeda(valor: number) { return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(valor || 0) }
