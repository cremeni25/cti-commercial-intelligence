"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
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
  valor?: number
  proposta_id?: string | null
  pedido_id?: string | null
  encerrada?: boolean
}
type OportunidadeCRM = {
  id: string
  linha_equipamentos?: string | null
  equipamento?: string | null
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

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [historico, setHistorico] = useState<DashboardContextual | null>(null)
  const [nucleo, setNucleo] = useState<NucleoComercial[]>([])
  const [oportunidadesCrm, setOportunidadesCrm] = useState<OportunidadeCRM[]>([])
  const [linhasProduto, setLinhasProduto] = useState<LinhaProduto[]>([])
  const [metadataLinhas, setMetadataLinhas] = useState<ProductLinesMetadata>({})
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loading, setLoading] = useState(true)
  const [avisos, setAvisos] = useState<string[]>([])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      const [dadosNucleo, dadosOportunidades] = await Promise.all([
        tentar<NucleoComercial[]>(() => buscarJson(`${API_URL}/crm/nucleo-comercial`)),
        tentar<OportunidadeCRM[]>(() => buscarJson(`${API_URL}/crm/oportunidades`)),
      ])
      if (!ativo) return
      setNucleo(dadosNucleo ?? [])
      setOportunidadesCrm(dadosOportunidades ?? [])
    })
    return () => { ativo = false }
  }, [])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      setLoading(true)
      setAvisos([])
      const [dadosHistoricos, dadosLinhas] = await Promise.all([
        tentar<DashboardContextual>(() => getDashboardExecutivoContextual(queryString), 2),
        tentar<ProductLinesResponse>(() => buscarJson(`${API_URL}/analytics/product-lines?${queryString}`), 2),
      ])
      if (!ativo) return
      const novosAvisos: string[] = []
      if (dadosHistoricos) setHistorico(dadosHistoricos)
      else novosAvisos.push("Base histórica indisponível.")
      if (dadosLinhas?.linhas?.length === 3) {
        setLinhasProduto(dadosLinhas.linhas.map((linha) => ({ ...linha, disponivel: true })))
        setMetadataLinhas(dadosLinhas.metadata ?? {})
      } else {
        setLinhasProduto([])
        novosAvisos.push("Indicadores históricos por linha indisponíveis.")
      }
      setAvisos(novosAvisos)
      setUltimaAtualizacao(new Date().toLocaleString("pt-BR"))
      setLoading(false)
    })
    return () => { ativo = false }
  }, [queryString])

  const periodoExibido = periodo === "TODO_HISTORICO"
    ? "Todo o histórico disponível"
    : periodo === "PERSONALIZADO"
      ? dataInicio && dataFim ? `${dataInicio} até ${dataFim}` : "Período personalizado"
      : periodo.replaceAll("_", " ").toLowerCase()

  const abertos = nucleo.filter((item) => !item.encerrada)
  const pipelineAberto = abertos.reduce((total, item) => total + Number(item.valor || 0), 0)
  const propostasAbertas = abertos.filter((item) => Boolean(item.proposta_id)).length
  const pedidosAbertos = abertos.filter((item) => Boolean(item.pedido_id)).length
  const totalPeriodo = metadataLinhas.total_registros_periodo ?? 0
  const totalClassificado = metadataLinhas.registros_classificados_periodo ?? linhasProduto.reduce((soma, linha) => soma + linha.atual, 0)
  const cobertura = totalPeriodo > 0 ? (totalClassificado / totalPeriodo) * 100 : 0

  const oportunidadePorId = new Map(oportunidadesCrm.map((item) => [String(item.id), item]))
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
    const linha = linhasProduto.find((item) => item.codigo === definicao.codigo)
    return { linha: definicao.codigo, nome: definicao.nome, atual: linha?.atual ?? 0, anterior: linha?.anterior ?? 0 }
  })
  const graficoPipeline = linhasEmCurso.map((linha) => ({ linha: linha.codigo, nome: linha.nome, valor: linha.valor, negociacoes: linha.negociacoes }))

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
            <Info titulo="Registros históricos filtrados" valor={loading ? "..." : String(historico?.metadata?.total_registros_filtrados ?? 0)} />
          </section>

          {avisos.length > 0 && <div className="rounded-2xl border border-amber-700 bg-amber-950/20 p-4 text-sm text-amber-200">{avisos.join(" ")}</div>}

          <section className="grid gap-5 xl:grid-cols-2">
            <PainelTempo titulo="REALIZADO" subtitulo="O que já aconteceu." destaque="Histórico confirmado">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Clientes históricos" valor={loading ? "..." : historico?.total_clientes ?? 0} />
                <Kpi titulo="Ticket histórico" valor={loading ? "..." : moeda(historico?.ticket_medio)} />
                <Kpi titulo="Estados atendidos" valor={loading ? "..." : historico?.total_estados ?? 0} />
                <Kpi titulo="Municípios" valor={loading ? "..." : historico?.total_municipios ?? 0} />
              </div>
            </PainelTempo>

            <PainelTempo titulo="EM CURSO" subtitulo="O que está acontecendo agora." destaque="Negócios vivos">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Pipeline aberto" valor={moeda(pipelineAberto)} />
                <Kpi titulo="Negociações ativas" valor={abertos.length} />
                <Kpi titulo="Propostas vigentes" valor={propostasAbertas} />
                <Kpi titulo="Pedidos em curso" valor={pedidosAbertos} />
              </div>
            </PainelTempo>
          </section>

          <section className="grid gap-5 2xl:grid-cols-2">
            <GraficoPainel titulo="REALIZADO" subtitulo="Volume por linha — período atual × anterior">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={graficoHistorico} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false} />
                  <XAxis dataKey="linha" stroke="#8294ad" />
                  <YAxis stroke="#8294ad" />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(label) => nomeLinha(String(label))} />
                  <Legend />
                  <Bar dataKey="anterior" name="Período anterior" fill="#52657d" radius={[7, 7, 0, 0]} />
                  <Bar dataKey="atual" name="Período selecionado" fill="#22d3ee" radius={[7, 7, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </GraficoPainel>

            <GraficoPainel titulo="EM CURSO" subtitulo="Pipeline atual por linha de equipamento">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={graficoPipeline} margin={{ top: 12, right: 16, left: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#17304d" strokeDasharray="3 5" vertical={false} />
                  <XAxis dataKey="linha" stroke="#8294ad" />
                  <YAxis stroke="#8294ad" tickFormatter={(valor) => abreviarMoeda(Number(valor))} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(label) => nomeLinha(String(label))} formatter={(valor, nome) => nome === "Pipeline" ? [moeda(Number(valor)), nome] : [valor, nome]} />
                  <Legend />
                  <Bar dataKey="valor" name="Pipeline" fill="#34d399" radius={[7, 7, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-3 grid grid-cols-3 gap-2">
                {linhasEmCurso.map((linha) => <Mini key={linha.codigo} titulo={linha.codigo} valor={`${linha.negociacoes} negócio(s)`} />)}
              </div>
            </GraficoPainel>
          </section>

          <section className="flex flex-col gap-2 rounded-2xl border border-[#13203f] bg-[#071226] px-5 py-4 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
            <span>Cobertura da classificação histórica: {loading ? "..." : `${cobertura.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`}.</span>
            {semLinhaEmCurso > 0 ? <span className="text-amber-300">{semLinhaEmCurso} negócio(s) em curso ainda sem linha de equipamento classificada.</span> : <span>Todos os negócios em curso estão classificados por linha.</span>}
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
function classificarLinha(item?: OportunidadeCRM) { if (!item) return null; const linha = normalizar(item.linha_equipamentos); if (["TR", "TRAILER", "LINHA TRAILER"].includes(linha)) return "TR"; if (["DT", "DIESEL TRUCK", "LINHA DIESEL TRUCK"].includes(linha)) return "DT"; if (["DD", "DIRECT DRIVE", "LINHA DIRECT DRIVE"].includes(linha)) return "DD"; const equipamento = normalizar(item.equipamento); if (/\b(X4 7500|X4 7700|VECTOR HE19|HE19)\b/.test(equipamento)) return "TR"; if (/\b(SUPRA 750|SUPRA 850|SUPRA 1150)\b/.test(equipamento)) return "DT"; if (/\b(CM 280|CM280|CM 400|CM400|CM 500|CM500|D6|D7|XARIOS 350|XARIOS 600)\b/.test(equipamento)) return "DD"; return null }
function nomeLinha(codigo: string) { return LINHAS.find((linha) => linha.codigo === codigo)?.nome ?? codigo }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function abreviarMoeda(valor: number) { if (Math.abs(valor) >= 1000000) return `R$ ${(valor / 1000000).toFixed(1)}M`; if (Math.abs(valor) >= 1000) return `R$ ${(valor / 1000).toFixed(0)}k`; return `R$ ${valor}` }
function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: React.ReactNode }) { return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2></div><span className="shrink-0 rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section> }
function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{titulo}</p><p className="mt-1 text-sm font-semibold text-cyan-200">{valor}</p></div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function GraficoPainel({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: React.ReactNode }) { return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2><div className="mt-5 h-[300px]">{children}</div></section> }
function Mini({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-xl border border-[#16325c] bg-[#091a33] p-3"><p className="text-xs font-bold text-cyan-300">{titulo}</p><p className="mt-1 text-xs text-slate-400">{valor}</p></div> }
