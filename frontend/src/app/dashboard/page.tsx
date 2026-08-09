"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type RankingItem = { nome: string; quantidade: number }
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
  valor_ponderado?: number
  proposta_id?: string | null
  pedido_id?: string | null
  encerrada?: boolean
}
type OportunidadeCRM = {
  id: string
  linha_equipamentos?: string | null
  equipamento?: string | null
  status?: string | null
}
type LinhaProduto = {
  codigo: "TR" | "DT" | "DD"
  nome: string
  atual: number
  anterior: number
  variacao: number
  direcao: string
  modelos: RankingItem[]
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
  linhas?: Omit<LinhaProduto, "disponivel">[]
}
type LinhaEmCurso = {
  codigo: "TR" | "DT" | "DD"
  negociacoes: number
  valor: number
  ponderado: number
}

const LINHAS = [
  { codigo: "TR" as const, nome: "Trailer" },
  { codigo: "DT" as const, nome: "Diesel Truck" },
  { codigo: "DD" as const, nome: "Direct Drive" },
]
const LINHAS_VAZIAS = LINHAS.map((linha) => ({ ...linha, atual: 0, anterior: 0, variacao: 0, direcao: "estavel", modelos: [], disponivel: false }))

export default function DashboardHub() {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [historico, setHistorico] = useState<DashboardContextual | null>(null)
  const [nucleo, setNucleo] = useState<NucleoComercial[]>([])
  const [oportunidadesCrm, setOportunidadesCrm] = useState<OportunidadeCRM[]>([])
  const [linhasProduto, setLinhasProduto] = useState<LinhaProduto[]>(LINHAS_VAZIAS)
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
        setLinhasProduto(LINHAS_VAZIAS)
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
  const oportunidades = nucleo.length
  const propostas = nucleo.filter((item) => Boolean(item.proposta_id)).length
  const pedidos = nucleo.filter((item) => Boolean(item.pedido_id)).length
  const pipelineAberto = abertos.reduce((total, item) => total + Number(item.valor || 0), 0)
  const pipelinePonderado = abertos.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0)
  const totalPeriodo = metadataLinhas.total_registros_periodo ?? 0
  const totalClassificado = metadataLinhas.registros_classificados_periodo ?? linhasProduto.reduce((soma, linha) => soma + linha.atual, 0)
  const cobertura = metadataLinhas.cobertura_classificacao_percentual ?? percentual(totalClassificado, totalPeriodo)

  const oportunidadePorId = new Map(oportunidadesCrm.map((item) => [String(item.id), item]))
  const linhasEmCurso: LinhaEmCurso[] = LINHAS.map((linha) => {
    const itens = abertos.filter((item) => classificarLinha(oportunidadePorId.get(String(item.oportunidade_id))) === linha.codigo)
    return {
      codigo: linha.codigo,
      negociacoes: itens.length,
      valor: itens.reduce((total, item) => total + Number(item.valor || 0), 0),
      ponderado: itens.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0),
    }
  })
  const classificadosEmCurso = linhasEmCurso.reduce((total, item) => total + item.negociacoes, 0)
  const semLinhaEmCurso = Math.max(abertos.length - classificadosEmCurso, 0)

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-hidden">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura temporal executiva</p>
            <h1 className="mt-2 text-3xl font-bold">Dashboard Executivo</h1>
            <p className="mt-2 max-w-4xl text-sm text-slate-400">O painel compara o que já foi consolidado nas bases históricas com o que está sendo construído agora pelo CRM.</p>
            <p className="mt-2 text-sm text-cyan-300">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </header>

          <section className="grid gap-3 md:grid-cols-3">
            <Info titulo="Período histórico" valor={periodoExibido} />
            <Info titulo="Última atualização" valor={ultimaAtualizacao || "Carregando dados"} />
            <Info titulo="Registros históricos filtrados" valor={loading ? "..." : String(historico?.metadata?.total_registros_filtrados ?? 0)} />
          </section>

          {avisos.length > 0 && <div className="rounded-2xl border border-amber-700 bg-amber-950/20 p-4 text-sm text-amber-200">{avisos.join(" ")}</div>}

          <section className="grid gap-5 xl:grid-cols-2">
            <PainelTempo titulo="REALIZADO" subtitulo="O que já foi concluído e consolidado nas bases históricas." destaque="Histórico confirmado">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Clientes históricos" valor={loading ? "..." : historico?.total_clientes ?? 0} />
                <Kpi titulo="Ticket histórico" valor={loading ? "..." : moeda(historico?.ticket_medio)} />
                <Kpi titulo="Estados atendidos" valor={loading ? "..." : historico?.total_estados ?? 0} />
                <Kpi titulo="Municípios" valor={loading ? "..." : historico?.total_municipios ?? 0} />
              </div>
            </PainelTempo>

            <PainelTempo titulo="EM CURSO" subtitulo="O que está acontecendo agora no CRM e ainda pode mudar." destaque="Negócios vivos">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Pipeline aberto" valor={moeda(pipelineAberto)} />
                <Kpi titulo="Pipeline ponderado" valor={moeda(pipelinePonderado)} />
                <Kpi titulo="Oportunidades" valor={oportunidades} />
                <Kpi titulo="Propostas / Pedidos" valor={`${propostas} / ${pedidos}`} />
              </div>
            </PainelTempo>
          </section>

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Comparativo temporal por equipamento</p>
              <h2 className="mt-1 text-2xl font-bold">REALIZADO × EM CURSO</h2>
              <p className="mt-1 text-sm text-slate-400">Cada linha confronta sua presença histórica no período selecionado com as negociações abertas no CRM.</p>
            </div>
            <div className="mt-5 grid gap-4 xl:grid-cols-3">
              {LINHAS.map((definicao) => {
                const realizado = linhasProduto.find((linha) => linha.codigo === definicao.codigo) ?? { ...definicao, atual: 0, anterior: 0, variacao: 0, direcao: "estavel", modelos: [], disponivel: false }
                const emCurso = linhasEmCurso.find((linha) => linha.codigo === definicao.codigo) ?? { codigo: definicao.codigo, negociacoes: 0, valor: 0, ponderado: 0 }
                return <ComparativoLinha key={definicao.codigo} linha={realizado} emCurso={emCurso} totalHistorico={totalClassificado} totalPipeline={pipelineAberto} loading={loading} />
              })}
            </div>
            <div className="mt-4 flex flex-col gap-1 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
              <span>Cobertura da classificação histórica: {loading ? "..." : `${cobertura.toLocaleString("pt-BR")}%`}. {metadataLinhas.descricao || ""}</span>
              {semLinhaEmCurso > 0 && <span className="text-amber-300">{semLinhaEmCurso} negócio(s) em curso ainda sem linha de equipamento classificada.</span>}
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}

async function buscarJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" })
  if (!response.ok) throw new Error(`${response.status} ${url}`)
  return response.json() as Promise<T>
}
async function tentar<T>(executar: () => Promise<T>, tentativas = 1): Promise<T | null> {
  for (let tentativa = 0; tentativa < tentativas; tentativa += 1) {
    try { return await executar() } catch { if (tentativa + 1 < tentativas) await new Promise((resolve) => setTimeout(resolve, 700)) }
  }
  return null
}
function normalizar(valor?: string | null) { return String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[-_/]+/g, " ").replace(/\s+/g, " ").trim() }
function classificarLinha(item?: OportunidadeCRM) {
  if (!item) return null
  const linha = normalizar(item.linha_equipamentos)
  if (["TR", "TRAILER", "LINHA TRAILER"].includes(linha)) return "TR"
  if (["DT", "DIESEL TRUCK", "LINHA DIESEL TRUCK"].includes(linha)) return "DT"
  if (["DD", "DIRECT DRIVE", "LINHA DIRECT DRIVE"].includes(linha)) return "DD"
  const equipamento = normalizar(item.equipamento)
  if (/\b(X4 7500|X4 7700|VECTOR HE19|HE19)\b/.test(equipamento)) return "TR"
  if (/\b(SUPRA 750|SUPRA 850|SUPRA 1150)\b/.test(equipamento)) return "DT"
  if (/\b(CM 280|CM280|CM 400|CM400|CM 500|CM500|D6|D7|XARIOS 350|XARIOS 600)\b/.test(equipamento)) return "DD"
  return null
}
function percentual(parte?: number, total?: number) { if (!parte || !total) return 0; return Math.round((parte / total) * 100) }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: React.ReactNode }) {
  return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2></div><span className="shrink-0 rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section>
}
function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{titulo}</p><p className="mt-1 text-sm font-semibold text-cyan-200">{valor}</p></div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function ComparativoLinha({ linha, emCurso, totalHistorico, totalPipeline, loading }: { linha: LinhaProduto; emCurso: LinhaEmCurso; totalHistorico: number; totalPipeline: number; loading: boolean }) {
  const participacaoHistorica = totalHistorico > 0 ? (linha.atual / totalHistorico) * 100 : 0
  const participacaoPipeline = totalPipeline > 0 ? (emCurso.valor / totalPipeline) * 100 : 0
  const sinal = linha.variacao > 0 ? "+" : ""
  return <article className="overflow-hidden rounded-2xl border border-[#16325c] bg-[#091a33]">
    <header className="border-b border-[#16325c] p-4"><p className="text-xs font-semibold text-cyan-400">{linha.codigo}</p><h3 className="mt-1 text-xl font-bold">{linha.nome}</h3></header>
    <div className="grid sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
      <div className="border-b border-[#16325c] p-4 sm:border-b-0 sm:border-r xl:border-b xl:border-r-0 2xl:border-b-0 2xl:border-r"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Realizado</p><p className="mt-3 text-3xl font-bold text-cyan-300">{loading ? "..." : linha.atual}</p><p className="mt-2 text-sm text-slate-400">{participacaoHistorica.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% da base classificada</p><p className="mt-1 text-xs text-slate-500">Anterior: {linha.anterior} · Variação: {sinal}{linha.variacao.toLocaleString("pt-BR")}%</p></div>
      <div className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">Em curso</p><p className="mt-3 text-3xl font-bold text-emerald-300">{emCurso.negociacoes}</p><p className="mt-2 text-sm text-slate-300">{moeda(emCurso.valor)} em pipeline</p><p className="mt-1 text-xs text-slate-500">{participacaoPipeline.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% do pipeline · ponderado {moeda(emCurso.ponderado)}</p></div>
    </div>
  </article>
}
