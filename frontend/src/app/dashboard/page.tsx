"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type DashboardContextual = {
  total_clientes?: number
  total_estados?: number
  total_municipios?: number
  ticket_medio?: number
  metadata?: { total_registros_filtrados?: number }
}
type NucleoComercial = {
  oportunidade_id: string
  responsavel_id?: string | null
  valor?: number
  proposta_id?: string | null
  pedido_id?: string | null
  encerrada?: boolean
}
type OportunidadeCRM = {
  id: string
  linha_equipamentos?: string | null
  equipamento?: string | null
  descricao?: string | null
}
type LinhaProduto = {
  codigo: "TR" | "DT" | "DD"
  nome: string
  atual: number
  anterior: number
  variacao: number
  disponivel: boolean
}
type ProductLinesMetadata = {
  descricao?: string
  total_registros_periodo?: number
  registros_classificados_periodo?: number
  cobertura_classificacao_percentual?: number
}
type ProductLinesResponse = {
  metadata?: ProductLinesMetadata
  linhas?: Array<{ codigo: "TR" | "DT" | "DD"; nome: string; atual: number; anterior: number; variacao: number }>
}
type LinhaEmCurso = {
  codigo: "TR" | "DT" | "DD"
  nome: string
  negociacoes: number
  valor: number
}

const LINHAS = [
  { codigo: "TR" as const, nome: "Trailer" },
  { codigo: "DT" as const, nome: "Diesel Truck" },
  { codigo: "DD" as const, nome: "Direct Drive" },
]
const RETRY_MS = 5_000
const REFRESH_MS = 60_000

export default function DashboardHub() {
  const { usuario } = useAuth()
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [historico, setHistorico] = useState<DashboardContextual | null>(null)
  const [nucleo, setNucleo] = useState<NucleoComercial[] | null>(null)
  const [oportunidadesCrm, setOportunidadesCrm] = useState<OportunidadeCRM[] | null>(null)
  const [linhasProduto, setLinhasProduto] = useState<LinhaProduto[] | null>(null)
  const [metadataLinhas, setMetadataLinhas] = useState<ProductLinesMetadata>({})
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loadingHistorico, setLoadingHistorico] = useState(true)
  const [loadingOperacional, setLoadingOperacional] = useState(true)
  const [falhaHistorico, setFalhaHistorico] = useState(false)
  const [falhaLinhas, setFalhaLinhas] = useState(false)
  const [falhaNucleo, setFalhaNucleo] = useState(false)
  const [falhaOportunidades, setFalhaOportunidades] = useState(false)

  const carregarOperacional = useCallback(async () => {
    const [dadosNucleo, dadosOportunidades] = await Promise.all([
      tentar<NucleoComercial[]>(() => buscarJson(`${API_URL}/crm/nucleo-comercial`), 2),
      tentar<OportunidadeCRM[]>(() => buscarJson(`${API_URL}/crm/oportunidades`), 2),
    ])
    const nucleoOk = dadosNucleo !== null
    const oportunidadesOk = dadosOportunidades !== null
    if (nucleoOk) setNucleo(dadosNucleo)
    if (oportunidadesOk) setOportunidadesCrm(dadosOportunidades)
    setFalhaNucleo(!nucleoOk)
    setFalhaOportunidades(!oportunidadesOk)
    setLoadingOperacional(false)
    if (nucleoOk || oportunidadesOk) setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
    return nucleoOk && oportunidadesOk
  }, [])

  const carregarHistorico = useCallback(async () => {
    const [dadosHistoricos, dadosLinhas] = await Promise.all([
      tentar<DashboardContextual>(() => getDashboardExecutivoContextual(queryString), 2),
      tentar<ProductLinesResponse>(() => buscarJson(`${API_URL}/analytics/product-lines?${queryString}`), 2),
    ])
    const historicoOk = dadosHistoricos !== null
    const linhasOk = Boolean(dadosLinhas?.linhas?.length === 3)
    if (historicoOk) setHistorico(dadosHistoricos)
    if (linhasOk && dadosLinhas) {
      setLinhasProduto((dadosLinhas.linhas ?? []).map((linha) => ({ ...linha, disponivel: true })))
      setMetadataLinhas(dadosLinhas.metadata ?? {})
    }
    setFalhaHistorico(!historicoOk)
    setFalhaLinhas(!linhasOk)
    setLoadingHistorico(false)
    if (historicoOk || linhasOk) setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
    return historicoOk && linhasOk
  }, [queryString])

  useEffect(() => {
    let ativo = true
    let timer: number | undefined
    const executar = async () => {
      const ok = await carregarOperacional()
      if (!ativo) return
      timer = window.setTimeout(() => void executar(), ok ? REFRESH_MS : RETRY_MS)
    }
    queueMicrotask(() => {
      if (!ativo) return
      setLoadingOperacional(true)
      void executar()
    })
    const aoReconectar = () => void carregarOperacional()
    window.addEventListener("online", aoReconectar)
    return () => {
      ativo = false
      if (timer) window.clearTimeout(timer)
      window.removeEventListener("online", aoReconectar)
    }
  }, [carregarOperacional])

  useEffect(() => {
    let ativo = true
    let timer: number | undefined
    const executar = async () => {
      const ok = await carregarHistorico()
      if (!ativo) return
      timer = window.setTimeout(() => void executar(), ok ? REFRESH_MS : RETRY_MS)
    }
    queueMicrotask(() => {
      if (!ativo) return
      setHistorico(null)
      setLinhasProduto(null)
      setMetadataLinhas({})
      setLoadingHistorico(true)
      void executar()
    })
    const aoReconectar = () => void carregarHistorico()
    window.addEventListener("online", aoReconectar)
    return () => {
      ativo = false
      if (timer) window.clearTimeout(timer)
      window.removeEventListener("online", aoReconectar)
    }
  }, [carregarHistorico])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? dataInicio && dataFim ? `${dataInicio} até ${dataFim}` : "Período personalizado"
      : periodo.replaceAll("_", " ").toLowerCase()

  const historicoDisponivel = historico !== null
  const linhasDisponiveis = linhasProduto !== null
  const nucleoDisponivel = nucleo !== null
  const oportunidadesDisponiveis = oportunidadesCrm !== null
  const operacionalDisponivel = nucleoDisponivel && oportunidadesDisponiveis
  const abertos = (nucleo ?? []).filter((item) => !item.encerrada && pertenceAoEscopoDoUsuario(item.responsavel_id, usuario))
  const pipelineAberto = abertos.reduce((total, item) => total + Number(item.valor || 0), 0)
  const propostasAbertas = abertos.filter((item) => Boolean(item.proposta_id)).length
  const pedidosAbertos = abertos.filter((item) => Boolean(item.pedido_id)).length
  const totalPeriodo = metadataLinhas.total_registros_periodo ?? 0
  const totalClassificado = metadataLinhas.registros_classificados_periodo ?? (linhasProduto ?? []).reduce((soma, linha) => soma + linha.atual, 0)
  const cobertura = totalPeriodo > 0 ? (totalClassificado / totalPeriodo) * 100 : 0

  const oportunidadePorId = new Map((oportunidadesCrm ?? []).map((item) => [String(item.id), item]))
  const linhasEmCurso: LinhaEmCurso[] = LINHAS.map((linha) => {
    const itens = abertos.filter((item) => classificarLinha(oportunidadePorId.get(String(item.oportunidade_id))) === linha.codigo)
    return {
      codigo: linha.codigo,
      nome: linha.nome,
      negociacoes: itens.length,
      valor: itens.reduce((total, item) => total + Number(item.valor || 0), 0),
    }
  })
  const classificadosEmCurso = linhasEmCurso.reduce((total, item) => total + item.negociacoes, 0)
  const semLinhaEmCurso = Math.max(abertos.length - classificadosEmCurso, 0)

  const graficoHistorico = LINHAS.map((definicao) => {
    const linha = (linhasProduto ?? []).find((item) => item.codigo === definicao.codigo)
    return { linha: definicao.codigo, nome: definicao.nome, atual: linha?.atual ?? 0, anterior: linha?.anterior ?? 0 }
  })
  const graficoPipeline = linhasEmCurso.map((linha) => ({ linha: linha.codigo, nome: linha.nome, valor: linha.valor, negociacoes: linha.negociacoes }))
  const falhaTemporaria = falhaHistorico || falhaLinhas || falhaNucleo || falhaOportunidades
  const registrosHistoricosHref = drilldown("anfir", "Dashboard Executivo · Registros históricos filtrados", queryString)
  const negociosEmCursoHref = drilldown("crm", "Dashboard Executivo · Negócios em curso")

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-hidden">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura temporal executiva</p>
            <h1 className="mt-2 text-3xl font-bold">Dashboard Executivo</h1>
            <p className="mt-2 max-w-4xl text-sm text-slate-400">Passado consolidado e negócios atuais, separados para leitura imediata.</p>
            <p className="mt-2 text-sm text-cyan-300">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </header>

          <section className="grid gap-3 md:grid-cols-3">
            <Info titulo="Período histórico" valor={periodoExibido} />
            <Info titulo="Última atualização" valor={ultimaAtualizacao || "Carregando dados"} />
            <Info titulo="Registros históricos filtrados" valor={loadingHistorico ? "..." : historicoDisponivel ? String(historico.metadata?.total_registros_filtrados ?? 0) : "—"} href={historicoDisponivel ? registrosHistoricosHref : undefined} />
          </section>

          {falhaTemporaria && <div className="rounded-2xl border border-amber-700 bg-amber-950/20 p-4 text-sm text-amber-200">Conexão temporariamente indisponível. Reconexão automática em andamento; nenhum indicador indisponível será mostrado como zero.</div>}

          <section className="grid gap-5 xl:grid-cols-2">
            <PainelTempo titulo="REALIZADO" subtitulo="O que já aconteceu." destaque="Histórico confirmado">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Clientes históricos" valor={loadingHistorico ? "..." : historicoDisponivel ? historico.total_clientes ?? 0 : "—"} />
                <Kpi titulo="Ticket histórico" valor={loadingHistorico ? "..." : historicoDisponivel ? moeda(historico.ticket_medio) : "—"} />
                <Kpi titulo="Estados atendidos" valor={loadingHistorico ? "..." : historicoDisponivel ? historico.total_estados ?? 0 : "—"} />
                <Kpi titulo="Municípios" valor={loadingHistorico ? "..." : historicoDisponivel ? historico.total_municipios ?? 0 : "—"} />
              </div>
            </PainelTempo>

            <PainelTempo titulo="EM CURSO" subtitulo="O que está acontecendo agora." destaque="Negócios vivos">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Pipeline aberto" valor={loadingOperacional ? "..." : nucleoDisponivel ? moeda(pipelineAberto) : "—"} href={nucleoDisponivel ? negociosEmCursoHref : undefined} />
                <Kpi titulo="Negociações ativas" valor={loadingOperacional ? "..." : nucleoDisponivel ? abertos.length : "—"} href={nucleoDisponivel ? negociosEmCursoHref : undefined} />
                <Kpi titulo="Propostas vigentes" valor={loadingOperacional ? "..." : nucleoDisponivel ? propostasAbertas : "—"} />
                <Kpi titulo="Pedidos em curso" valor={loadingOperacional ? "..." : nucleoDisponivel ? pedidosAbertos : "—"} />
              </div>
            </PainelTempo>
          </section>

          <section className="grid gap-5 2xl:grid-cols-2">
            <GraficoPainel titulo="REALIZADO" subtitulo="Volume por linha — período atual × anterior">
              {linhasDisponiveis ? <ResponsiveContainer width="100%" height="100%">
                <BarChart data={graficoHistorico} margin={{ top: 30, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false} />
                  <XAxis dataKey="linha" stroke="#8294ad" />
                  <YAxis stroke="#8294ad" />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(label) => nomeLinha(String(label))} />
                  <Legend />
                  <Bar dataKey="anterior" name="Período anterior" fill="#52657d" radius={[7, 7, 0, 0]}>
                    <LabelList dataKey="anterior" position="top" fill="#94a3b8" fontSize={12} />
                  </Bar>
                  <Bar dataKey="atual" name="Período selecionado" fill="#22d3ee" radius={[7, 7, 0, 0]}>
                    <LabelList dataKey="atual" position="top" fill="#67e8f9" fontSize={12} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer> : <GraficoIndisponivel />}
            </GraficoPainel>

            <GraficoPainel titulo="EM CURSO" subtitulo="Pipeline atual por linha de equipamento">
              {operacionalDisponivel ? <>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={graficoPipeline} margin={{ top: 34, right: 16, left: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false} />
                    <XAxis dataKey="linha" stroke="#8294ad" />
                    <YAxis stroke="#8294ad" tickFormatter={(valor) => abreviarMoeda(Number(valor))} />
                    <Tooltip contentStyle={tooltipStyle} labelFormatter={(label) => nomeLinha(String(label))} formatter={(valor, nome) => nome === "Pipeline" ? [moeda(Number(valor)), nome] : [valor, nome]} />
                    <Legend />
                    <Bar dataKey="valor" name="Pipeline" fill="#34d399" radius={[7, 7, 0, 0]}>
                      <LabelList dataKey="valor" position="top" fill="#6ee7b7" fontSize={12} formatter={(valor) => abreviarMoeda(Number(valor))} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  {linhasEmCurso.map((linha) => <Mini key={linha.codigo} titulo={linha.codigo} valor={`${linha.negociacoes} negócio(s) · ${abreviarMoeda(linha.valor)}`} />)}
                </div>
              </> : <GraficoIndisponivel />}
            </GraficoPainel>
          </section>

          <section className="flex flex-col gap-2 rounded-2xl border border-[#13203f] bg-[#071226] px-5 py-4 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
            <span>Cobertura da classificação histórica: {loadingHistorico ? "..." : linhasDisponiveis ? `${cobertura.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%` : "—"}.</span>
            {operacionalDisponivel ? (semLinhaEmCurso > 0 ? <span className="text-amber-300">{semLinhaEmCurso} negócio(s) em curso sem classificação recuperável.</span> : <span className="text-emerald-300">Todos os negócios em curso estão classificados por linha.</span>) : <span className="text-amber-300">Dados em curso reconectando.</span>}
          </section>
        </div>
      </section>
    </main>
  )
}

const tooltipStyle = { backgroundColor: "#061126", border: "1px solid #24507a", borderRadius: "14px", color: "#fff" }
async function buscarJson<T>(url: string): Promise<T> { const response = await fetch(url, { cache: "no-store" }); if (!response.ok) throw new Error(`${response.status} ${url}`); return response.json() as Promise<T> }
async function tentar<T>(executar: () => Promise<T>, tentativas = 1): Promise<T | null> { for (let tentativa = 0; tentativa < tentativas; tentativa += 1) { try { return await executar() } catch { if (tentativa + 1 < tentativas) await new Promise((resolve) => setTimeout(resolve, 700)) } } return null }
function normalizar(valor?: string | null) { return String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[-_/]+/g, " ").replace(/\s+/g, " ").trim() }
function valorContexto(descricao: string | null | undefined, chave: string) {
  const texto = String(descricao || "")
  const match = texto.match(new RegExp(`(?:^|\\n)${chave}\\s*:\\s*([^\\n]+)`, "i"))
  return match?.[1]?.trim() || ""
}
function classificarLinha(item?: OportunidadeCRM) {
  if (!item) return null
  const linhaEstruturada = normalizar(item.linha_equipamentos)
  const linhaContexto = normalizar(valorContexto(item.descricao, "linhas?"))
  const linha = linhaEstruturada || linhaContexto
  if (["TR", "TRAILER", "LINHA TRAILER"].includes(linha)) return "TR"
  if (["DT", "DIESEL TRUCK", "LINHA DIESEL TRUCK"].includes(linha)) return "DT"
  if (["DD", "DIRECT DRIVE", "LINHA DIRECT DRIVE"].includes(linha)) return "DD"

  const equipamentoEstruturado = normalizar(item.equipamento)
  const equipamentoContexto = normalizar(valorContexto(item.descricao, "equipamentos?"))
  const equipamento = equipamentoEstruturado || equipamentoContexto
  if (/\b(X4 7500|X4 7700|VECTOR 8500|VECTOR HE19|HE19)\b/.test(equipamento)) return "TR"
  if (/\b(SUPRA 750|SUPRA 850|SUPRA 1150|A500)\b/.test(equipamento)) return "DT"
  if (/\b(CM 280|CM280|CM 400|CM400|CM 500|CM500|CM 600|CM600|D6|D7|S8|S9|XARIOS 350|XARIOS 600)\b/.test(equipamento)) return "DD"
  return null
}
function drilldown(camada: "anfir" | "crm", titulo: string, queryString = "") {
  const query = new URLSearchParams(queryString)
  query.set("camada", camada)
  query.set("titulo", titulo)
  query.set("subtitulo", camada === "anfir" ? "Registros individualizados do realizado no contexto selecionado" : "Oportunidades abertas que formam o indicador operacional")
  return `/detalhamento?${query.toString()}`
}
function nomeLinha(codigo: string) { return LINHAS.find((linha) => linha.codigo === codigo)?.nome ?? codigo }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function abreviarMoeda(valor: number) { if (Math.abs(valor) >= 1000000) return `R$ ${(valor / 1000000).toFixed(1)}M`; if (Math.abs(valor) >= 1000) return `R$ ${(valor / 1000).toFixed(0)}k`; return `R$ ${valor}` }
function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: React.ReactNode }) { return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2></div><span className="shrink-0 rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section> }
function Info({ titulo, valor, href }: { titulo: string; valor: string; href?: string }) { const body = <><p className="text-xs uppercase tracking-wide text-slate-500">{titulo}</p><p className="mt-1 text-sm font-semibold text-cyan-200">{valor}</p>{href && <p className="mt-2 text-[11px] text-cyan-400">Clique para detalhar</p>}</>; return href ? <Link href={href} className="rounded-2xl border border-[#13203f] bg-[#071226] p-4 transition hover:border-cyan-500/70 hover:bg-[#0a1a31]">{body}</Link> : <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-4">{body}</div> }
function Kpi({ titulo, valor, href }: { titulo: string; valor: string | number; href?: string }) { const body = <><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p>{href && <p className="mt-2 text-[11px] text-cyan-400">Clique para detalhar</p>}</>; return href ? <Link href={href} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4 transition hover:border-cyan-500/70 hover:bg-[#0b1d38]">{body}</Link> : <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4">{body}</div> }
function GraficoPainel({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: React.ReactNode }) { return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2><div className="mt-5 h-[300px]">{children}</div></section> }
function GraficoIndisponivel() { return <div className="grid h-full place-items-center rounded-2xl border border-dashed border-amber-700/60 bg-amber-950/10 px-6 text-center text-sm text-amber-200">Dados temporariamente indisponíveis. Reconexão automática em andamento.</div> }
function Mini({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-xl border border-[#16325c] bg-[#091a33] p-3"><p className="text-xs font-bold text-cyan-300">{titulo}</p><p className="mt-1 text-xs text-slate-400">{valor}</p></div> }
