"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"
import {
  getMapaEquipeInteligencia,
  getMapaEquipeVisao,
  type MapaEquipeVisao,
} from "@/services/mapa-equipe-api"

type MercadoMacro = { total: number; foraDisputa: number; real: number }
type Visao = "executiva" | "crm" | "historico"

const visoes: Array<{ id: Visao; label: string }> = [
  { id: "executiva", label: "Visão executiva" },
  { id: "crm", label: "CRM atual" },
  { id: "historico", label: "Histórico" },
]

export default function Page() {
  const [responsavelId, setResponsavelId] = useState("")
  const [visao, setVisao] = useState<Visao>("executiva")
  const [dados, setDados] = useState<MapaEquipeVisao | null>(null)
  const [mercadoMacro, setMercadoMacro] = useState<MercadoMacro | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [analiseIa, setAnaliseIa] = useState("")
  const [loadingIa, setLoadingIa] = useState(true)
  const [erroIa, setErroIa] = useState("")

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
      .then((resposta) => { if (ativo) setAnaliseIa(resposta.analise || "") })
      .catch((e) => { if (ativo) setErroIa(e instanceof Error ? e.message : "A IA Comercial não concluiu a leitura.") })
      .finally(() => { if (ativo) setLoadingIa(false) })
    return () => { ativo = false }
  }, [responsavelId])

  async function carregarInteligencia(id = responsavelId) {
    setLoadingIa(true)
    setErroIa("")
    try {
      const resposta = await getMapaEquipeInteligencia(id || null)
      setAnaliseIa(resposta.analise || "")
    } catch (e) {
      setAnaliseIa("")
      setErroIa(e instanceof Error ? e.message : "A IA Comercial não concluiu a leitura.")
    } finally {
      setLoadingIa(false)
    }
  }

  const familiaTotal = useMemo(() => {
    if (!dados) return 0
    const f = dados.mercado.familias
    return f.trailer + f.diesel_truck + f.direct_drive
  }, [dados])

  const ticketPipeline = dados && dados.evidencias.crm_ativos > 0
    ? dados.evidencias.crm_valor_ativo / dados.evidencias.crm_ativos
    : 0
  const perdasHistorico = dados
    ? dados.evidencias.motivos_perda_historico.reduce((s, i) => s + i.quantidade, 0)
    : 0

  function trocarResponsavel(novoId: string) {
    setLoading(true)
    setErro("")
    setLoadingIa(true)
    setErroIa("")
    setAnaliseIa("")
    setResponsavelId(novoId)
    setVisao("executiva")
  }

  function aprofundarNaIa() {
    const nome = dados?.selecao.nome || "a seleção atual"
    const prompt = `Aprofunde a análise comercial de ${nome}. Investigue os dados internos relevantes do CTI e explique em linguagem natural o que merece atenção, por quê e quais movimentos comerciais os dados sustentam.`
    window.location.href = `/ia-comercial?prompt=${encodeURIComponent(prompt)}`
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

          <nav className="flex flex-wrap gap-2" aria-label="Visões da Inteligência Comercial">
            {visoes.map((item) => (
              <button key={item.id} type="button" onClick={() => setVisao(item.id)} className={`rounded-xl border px-4 py-2.5 text-sm font-semibold transition ${visao === item.id ? "border-cyan-400 bg-cyan-400 text-slate-950" : "border-[#214363] bg-[#071226] text-slate-300 hover:border-cyan-500/60 hover:text-white"}`}>
                {item.label}
              </button>
            ))}
          </nav>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/20 p-4 text-red-200">{erro}</div>}
          {loading && <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-6 text-slate-400">Carregando informações comerciais...</div>}

          {!loading && dados && visao === "executiva" && (
            <VisaoExecutiva dados={dados} mercadoMacro={mercadoMacro} familiaTotal={familiaTotal} analiseIa={analiseIa} loadingIa={loadingIa} erroIa={erroIa} atualizarIa={() => void carregarInteligencia()} aprofundarNaIa={aprofundarNaIa} irPara={setVisao} />
          )}
          {!loading && dados && visao === "crm" && <VisaoCrm dados={dados} ticketPipeline={ticketPipeline} />}
          {!loading && dados && visao === "historico" && <VisaoHistorico dados={dados} perdasHistorico={perdasHistorico} />}

          {!loading && dados && (
            <details className="group rounded-2xl border border-slate-700/60 bg-[#061126] px-5 py-4">
              <summary className="cursor-pointer list-none text-sm font-semibold text-slate-300">Auditoria e origem dos dados <span className="ml-2 text-xs text-slate-500">ANFIR · Histórico/Funil · CRM</span></summary>
              <div className="mt-4 grid gap-3 border-t border-slate-700/60 pt-4 sm:grid-cols-2 xl:grid-cols-4">
                <MiniKpi rotulo="Clientes ANFIR" valor={dados.reconciliacao.clientes_anfir} />
                <MiniKpi rotulo="Clientes Histórico" valor={dados.reconciliacao.clientes_historico} />
                <MiniKpi rotulo="Clientes CRM" valor={dados.reconciliacao.clientes_crm} />
                <MiniKpi rotulo="Presentes nas 3 fontes" valor={dados.reconciliacao.nas_tres_fontes} />
              </div>
            </details>
          )}
        </div>
      </section>
    </main>
  )
}

function VisaoExecutiva({ dados, mercadoMacro, familiaTotal, analiseIa, loadingIa, erroIa, atualizarIa, aprofundarNaIa, irPara }: { dados: MapaEquipeVisao; mercadoMacro: MercadoMacro | null; familiaTotal: number; analiseIa: string; loadingIa: boolean; erroIa: string; atualizarIa: () => void; aprofundarNaIa: () => void; irPara: (visao: Visao) => void }) {
  return <>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <Kpi titulo="Mercado Real Viena" valor={dados.mercado.mercado_real_viena_2026} apoio="ANFIR 2026" destaque="emerald" />
      <Kpi titulo="ANFIR com vínculo seguro" valor={dados.mercado.mercado_real_selecao_2026} apoio={dados.selecao.nome} destaque="cyan" />
      <Kpi titulo="Clientes ANFIR identificados" valor={dados.mercado.clientes_unicos} apoio="seleção atual" />
      <Kpi titulo="Negociações CRM ativas" valor={dados.evidencias.crm_ativos} apoio="autoria operacional" destaque="emerald" onClick={() => irPara("crm")} />
      <Kpi titulo="Pipeline ativo" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} apoio="CRM atual" onClick={() => irPara("crm")} />
    </section>

    <section className="grid gap-4 xl:grid-cols-[.9fr_1.1fr]">
      <div className="rounded-3xl border border-[#17304d] bg-[#061126] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-slate-500">Base comercial 2026</p><h2 className="mt-1 text-xl font-bold">Tamanho e composição</h2></div><span className="rounded-full border border-cyan-500/20 px-3 py-1 text-xs text-cyan-200">ANFIR 2026</span></div>
        {mercadoMacro && <div className="mt-5"><BarraMercado total={mercadoMacro.total} fora={mercadoMacro.foraDisputa} real={mercadoMacro.real} /></div>}
        <div className="mt-4 grid gap-2 sm:grid-cols-3">
          <MiniKpi rotulo="Trailer" valor={dados.mercado.familias.trailer} apoio={`${pct(dados.mercado.familias.trailer, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
          <MiniKpi rotulo="Diesel Truck" valor={dados.mercado.familias.diesel_truck} apoio={`${pct(dados.mercado.familias.diesel_truck, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
          <MiniKpi rotulo="Direct Drive" valor={dados.mercado.familias.direct_drive} apoio={`${pct(dados.mercado.familias.direct_drive, familiaTotal).toFixed(1)}% dos vínculos seguros`} />
        </div>
      </div>

      <div className="rounded-3xl border border-violet-500/30 bg-[#081126] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-300">IA Comercial CTI</p><h2 className="mt-1 text-xl font-bold">O que os dados estão mostrando</h2></div>
          <div className="flex gap-2"><button type="button" onClick={atualizarIa} disabled={loadingIa} className="rounded-xl border border-violet-400/30 px-3 py-2 text-xs font-semibold text-violet-200 disabled:opacity-50">Atualizar leitura</button><button type="button" onClick={aprofundarNaIa} className="rounded-xl bg-violet-400 px-3 py-2 text-xs font-bold text-slate-950">Aprofundar na IA</button></div>
        </div>
        {loadingIa && <p className="mt-5 text-sm text-slate-400">A IA está cruzando as fontes autorizadas desta seleção...</p>}
        {!loadingIa && erroIa && <p className="mt-5 rounded-xl border border-amber-500/30 bg-amber-950/10 p-3 text-sm text-amber-200">{erroIa}</p>}
        {!loadingIa && !erroIa && analiseIa && <div className="mt-5 whitespace-pre-wrap text-[15px] leading-7 text-slate-200">{analiseIa}</div>}
      </div>
    </section>

    <section className="grid gap-4 xl:grid-cols-2">
      <button type="button" onClick={() => irPara("crm")} className="rounded-3xl border border-emerald-500/20 bg-[#061126] p-5 text-left transition hover:border-emerald-400/60"><div className="flex items-center justify-between gap-3"><h2 className="font-bold">CRM atual</h2><strong className="text-emerald-300">{dados.evidencias.crm_ativos} ativas</strong></div><div className="mt-4 space-y-2">{dados.evidencias.crm_status.length ? dados.evidencias.crm_status.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />) : <p className="text-sm text-slate-500">Sem negociações ativas nesta seleção.</p>}</div></button>
      <button type="button" onClick={() => irPara("historico")} className="rounded-3xl border border-amber-500/20 bg-[#061126] p-5 text-left transition hover:border-amber-400/60"><div className="flex items-center justify-between gap-3"><h2 className="font-bold">Histórico / Funil 2026</h2><strong className="text-amber-300">{dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} unidades</strong></div><div className="mt-4 grid grid-cols-2 gap-3"><MiniKpi rotulo="Eventos" valor={dados.evidencias.historico_registros_2026} /><MiniKpi rotulo="Perdas com motivo" valor={dados.evidencias.motivos_perda_historico.reduce((s, i) => s + i.quantidade, 0)} /></div></button>
    </section>
  </>
}

function VisaoCrm({ dados, ticketPipeline }: { dados: MapaEquipeVisao; ticketPipeline: number }) {
  return <section className="space-y-5 rounded-3xl border border-emerald-500/20 bg-[#061126] p-5"><div><p className="text-xs uppercase tracking-[.16em] text-emerald-300">CRM atual</p><h2 className="mt-1 text-2xl font-bold">O que está em andamento em {dados.selecao.nome}</h2></div><div className="grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Negociações ativas" valor={dados.evidencias.crm_ativos} /><MiniKpi rotulo="Pipeline ativo" valor={formatarMoeda(dados.evidencias.crm_valor_ativo)} /><MiniKpi rotulo="Ticket médio" valor={formatarMoeda(ticketPipeline)} /></div><div className="space-y-3">{dados.evidencias.crm_status.length ? dados.evidencias.crm_status.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, dados.evidencias.crm_registros)} />) : <p className="text-sm text-slate-500">Sem registros operacionais nesta seleção.</p>}</div></section>
}

function VisaoHistorico({ dados, perdasHistorico }: { dados: MapaEquipeVisao; perdasHistorico: number }) {
  return <section className="space-y-5 rounded-3xl border border-amber-500/20 bg-[#061126] p-5"><div><p className="text-xs uppercase tracking-[.16em] text-amber-300">Histórico / Funil 2026</p><h2 className="mt-1 text-2xl font-bold">O que ficou registrado antes para {dados.selecao.nome}</h2></div><div className="grid gap-3 sm:grid-cols-3"><MiniKpi rotulo="Eventos" valor={dados.evidencias.historico_registros_2026} /><MiniKpi rotulo="Unidades" valor={dados.evidencias.historico_unidades_2026.toLocaleString("pt-BR")} /><MiniKpi rotulo="Perdas com motivo" valor={perdasHistorico} /></div><div className="space-y-3">{dados.evidencias.motivos_perda_historico.length ? dados.evidencias.motivos_perda_historico.map((item) => <BarraStatus key={item.nome} nome={item.nome} valor={item.quantidade} total={Math.max(1, perdasHistorico)} />) : <p className="text-sm text-slate-500">Não há motivo de perda estruturado suficiente nesta seleção.</p>}</div></section>
}

function Kpi({ titulo, valor, apoio, destaque, onClick }: { titulo: string; valor: string | number; apoio?: string; destaque?: "cyan" | "emerald"; onClick?: () => void }) {
  const cor = destaque === "emerald" ? "text-emerald-300" : destaque === "cyan" ? "text-cyan-300" : "text-white"
  const conteudo = <><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{titulo}</p><div className={`mt-2 text-2xl font-bold ${cor}`}>{valor}</div>{apoio && <p className="mt-1 text-xs text-slate-500">{apoio}</p>}</>
  if (onClick) return <button type="button" onClick={onClick} className="rounded-2xl border border-[#17304d] bg-[#071226] p-4 text-left transition hover:border-cyan-500/50">{conteudo}</button>
  return <div className="rounded-2xl border border-[#17304d] bg-[#071226] p-4">{conteudo}</div>
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
