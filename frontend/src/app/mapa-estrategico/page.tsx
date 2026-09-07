"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import {
  getMapaEquipeInteligencia,
  getMapaEquipeVisao,
  getMapaInsights,
  perguntarMapaEquipeInteligencia,
  type FonteContextual,
  type MapaEquipeVisao,
  type MapaInsights,
  type TurnoContextual,
} from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }
type FocoInteligencia = "geral" | "regioes" | "linhas" | "perdas"

const focos: Array<{ id: FocoInteligencia; titulo: string; apoio: string }> = [
  { id: "geral", titulo: "Visão geral", apoio: "Mercado e CRM" },
  { id: "regioes", titulo: "Inteligência de regiões", apoio: "Território, carteira e negócios" },
  { id: "linhas", titulo: "Evolução por linha", apoio: "Trailer, Diesel Truck e Direct Drive" },
  { id: "perdas", titulo: "Onde perdemos e por quê", apoio: "Linhas e motivos registrados" },
]

export default function Page() {
  const [responsavelId, setResponsavelId] = useState("")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
  const [insights, setInsights] = useState<MapaInsights | null>(null)
  const [mercadoMacro, setMercadoMacro] = useState<MercadoMacro | null>(null)
  const [foco, setFoco] = useState<FocoInteligencia>("geral")
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
    setLoading(true)
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
    if (!dados?.pode_selecionar_responsavel) {
      setMercadoMacro(null)
      return
    }
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
        // A visão individual permanece disponível sem expor o consolidado.
      }
    })()
    return () => { ativo = false }
  }, [dados?.pode_selecionar_responsavel])

  useEffect(() => {
    let ativo = true
    setLoadingIa(true)
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
    setErro("")
    setLoadingIa(true)
    setErroIa("")
    setAnaliseIa("")
    setFontesContextuais([])
    setHistoricoContextual([])
    setPerguntaContextual("")
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
              <p className="mt-2 max-w-3xl text-sm text-slate-400">Mercado real, composição, negócios atuais e caminhos de inteligência da seleção.</p>
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

          {!loading && dados && insights && (
            <VisaoComercial
              dados={dados}
              insights={insights}
              mercadoMacro={mercadoMacro}
              familiaTotal={familiaTotal}
              foco={foco}
              setFoco={setFoco}
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

function VisaoComercial({
  dados,
  insights,
  mercadoMacro,
  familiaTotal,
  foco,
  setFoco,
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
  insights: MapaInsights
  mercadoMacro: MercadoMacro | null
  familiaTotal: number
  foco: FocoInteligencia
  setFoco: (foco: FocoInteligencia) => void
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

    {!loadingIa && (analiseIa || erroIa) && (
      <section className="rounded-3xl border border-violet-500/25 bg-[#081126] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-300">Interpretação comercial</p>
            <h2 className="mt-1 text-xl font-bold">O que merece atenção nesta seleção</h2>
          </div>
          <button type="button" onClick={atualizarIa} disabled={perguntando} className="rounded-xl border border-violet-400/30 px-3 py-2 text-xs font-semibold text-violet-200 disabled:opacity-50">Atualizar leitura</button>
        </div>
        {erroIa && <p className="mt-4 text-sm text-amber-200">A interpretação contextual não foi concluída nesta tentativa.</p>}
        {analiseIa && <div className="mt-5 whitespace-pre-wrap text-[15px] leading-7 text-slate-200">{analiseIa}</div>}
        {analiseIa && historicoContextual.length > 0 && (
          <div className="mt-5 space-y-3 border-t border-violet-400/15 pt-4">
            {historicoContextual.slice(-4).map((turno, index) => (
              <div key={`${turno.role}-${index}`} className={turno.role === "user" ? "rounded-xl bg-violet-500/10 px-3 py-2 text-sm text-violet-100" : "whitespace-pre-wrap text-sm leading-6 text-slate-300"}>{turno.content}</div>
            ))}
          </div>
        )}
        {analiseIa && (
          <div className="mt-5 border-t border-violet-400/15 pt-4">
            <div className="flex gap-2">
              <input value={perguntaContextual} onChange={(e) => setPerguntaContextual(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); perguntarContexto() } }} disabled={perguntando} placeholder="Pergunte sobre esta seleção..." className="min-w-0 flex-1 rounded-xl border border-violet-400/20 bg-[#060d1d] px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 focus:border-violet-400/50 disabled:opacity-60" />
              <button type="button" onClick={perguntarContexto} disabled={perguntando || !perguntaContextual.trim()} className="rounded-xl border border-violet-400/30 px-4 py-2.5 text-sm font-semibold text-violet-100 disabled:opacity-40">{perguntando ? "Analisando..." : "Perguntar"}</button>
            </div>
          </div>
        )}
        {analiseIa && fontesContextuais.length > 0 && (
          <details className="mt-4 border-t border-violet-400/10 pt-3 text-xs text-slate-500">
            <summary className="cursor-pointer list-none font-semibold text-slate-400">Contexto utilizado</summary>
            <div className="mt-3 space-y-2">{fontesContextuais.map((fonte) => <div key={fonte.codigo}><strong className="text-slate-400">{fonte.nome}: </strong><span>{fonte.evidencia}</span></div>)}</div>
          </details>
        )}
      </section>
    )}

    {loadingIa && <p className="px-1 text-xs text-slate-600">A interpretação comercial está sendo preparada sem bloquear a leitura dos gráficos.</p>}

    <details className="rounded-2xl border border-slate-700/50 bg-[#061126] px-5 py-4">
      <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Dados de apoio e auditoria</summary>
      <div className="mt-4 space-y-5 border-t border-slate-700/50 pt-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <MiniKpi rotulo="Registros históricos 2026" valor={dados.evidencias.historico_registros_2026} />
          <MiniKpi rotulo="Unidades históricas 2026" valor={dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} />
          <MiniKpi rotulo="Clientes históricos" valor={dados.reconciliacao.clientes_historico} />
        </div>
      </div>
    </details>
  </>
}

function VisaoGeral({ dados, mercadoMacro, familiaTotal, consolidado, ticketPipeline }: { dados: MapaEquipeVisao; mercadoMacro: MercadoMacro | null; familiaTotal: number; consolidado: boolean; ticketPipeline: number }) {
  return <section className="grid gap-4 xl:grid-cols-2">
    <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
      <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Mercado 2026</p><h2 className="mt-1 text-xl font-bold">Como o mercado está dividido</h2></div>
      {consolidado && mercadoMacro ? <div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div> : <p className="mt-4 text-sm text-slate-400">Visão individual do mercado vinculado ao login atual.</p>}
      <div className="mt-6 border-t border-slate-700/50 pt-4"><p className="mb-3 text-xs font-semibold uppercase tracking-[.14em] text-slate-500">Composição por linha</p><div className="space-y-3"><BarraComercial nome="Trailer" valor={dados.mercado.familias.trailer} total={Math.max(1, familiaTotal)} /><BarraComercial nome="Diesel Truck" valor={dados.mercado.familias.diesel_truck} total={Math.max(1, familiaTotal)} /><BarraComercial nome="Direct Drive" valor={dados.mercado.familias.direct_drive} total={Math.max(1, familiaTotal)} /></div></div>
    </div>
    <div className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5">
      <div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">CRM atual</p><h2 className="mt-1 text-xl font-bold">Como estão os negócios em andamento</h2></div><strong className="text-emerald-300">{dados.evidencias.crm_ativos} ativos</strong></div>
      <div className="mt-5 space-y-3">{dados.evidencias.crm_status.length ? dados.evidencias.crm_status.map((item) => <BarraComercial key={item.nome} nome={item.nome.replaceAll("_", " ")} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />) : <p className="text-sm text-slate-500">Sem negociações ativas nesta seleção.</p>}</div>
      <div className="mt-6 grid gap-3 border-t border-slate-700/50 pt-4 sm:grid-cols-2"><MiniKpi rotulo="Pipeline" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} /><MiniKpi rotulo="Ticket médio" valor={formatarMoeda(ticketPipeline)} /></div>
    </div>
  </section>
}

function VisaoRegioes({ insights }: { insights: MapaInsights }) {
  const max = Math.max(1, ...insights.regioes.map((item) => item.mercado_2026))
  return <section className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5">
    <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Inteligência de regiões</p>
    <h2 className="mt-1 text-xl font-bold">Território, mercado e negócios por responsável</h2>
    <div className="mt-5 space-y-4">{insights.regioes.map((item) => <div key={item.id} className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><strong>{item.codigo_regional ? `${item.codigo_regional} — ` : ""}{item.nome}</strong><p className="mt-1 text-xs text-slate-500">DDD {item.ddds.join(", ") || "não informado"}</p></div><div className="text-right text-xs text-slate-400"><div>{item.crm_ativos} negócio(s) ativo(s)</div><strong className="text-emerald-300">{formatarMoeda(item.pipeline_ativo)}</strong></div></div><div className="mt-3"><BarraComercial nome="Mercado 2026" valor={item.mercado_2026} total={max} /></div></div>)}</div>
  </section>
}

function VisaoLinhas({ insights }: { insights: MapaInsights }) {
  const max = Math.max(1, ...insights.evolucao_linhas.flatMap((item) => [item.trailer, item.diesel_truck, item.direct_drive]))
  return <section className="rounded-3xl border border-cyan-500/20 bg-[#061126] p-5">
    <p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Evolução por linha</p>
    <h2 className="mt-1 text-xl font-bold">Histórico comercial 2023–2026</h2>
    <div className="mt-5 grid gap-4 xl:grid-cols-4">{insights.evolucao_linhas.map((item) => <div key={item.ano} className="rounded-2xl border border-[#17304d] bg-[#071226] p-4"><strong className="text-lg">{item.ano}</strong><div className="mt-4 space-y-3"><BarraComercial nome="Trailer" valor={item.trailer} total={max} /><BarraComercial nome="Diesel Truck" valor={item.diesel_truck} total={max} /><BarraComercial nome="Direct Drive" valor={item.direct_drive} total={max} /></div></div>)}</div>
  </section>
}

function VisaoPerdas({ insights }: { insights: MapaInsights }) {
  const totalMotivos = Math.max(1, insights.perdas.motivos.reduce((s, item) => s + item.quantidade, 0))
  const totalLinhas = Math.max(1, insights.perdas.por_linha.reduce((s, item) => s + item.quantidade, 0))
  return <section className="grid gap-4 xl:grid-cols-2">
    <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Por que perdemos</p><h2 className="mt-1 text-xl font-bold">Motivos registrados</h2><div className="mt-5 space-y-3">{insights.perdas.motivos.length ? insights.perdas.motivos.map((item) => <BarraComercial key={item.nome} nome={item.nome.replaceAll("_", " ")} valor={item.quantidade} total={totalMotivos} />) : <p className="text-sm text-slate-500">Não há motivo de perda estruturado suficiente neste escopo.</p>}</div></div>
    <div className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Onde perdemos</p><h2 className="mt-1 text-xl font-bold">Perdas por linha de equipamento</h2><div className="mt-5 space-y-3">{insights.perdas.por_linha.length ? insights.perdas.por_linha.map((item) => <BarraComercial key={item.nome} nome={item.nome} valor={item.quantidade} total={totalLinhas} />) : <p className="text-sm text-slate-500">Não há perda estruturada suficiente neste escopo.</p>}</div></div>
  </section>
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
