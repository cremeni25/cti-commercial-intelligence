"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDashboardExecutivoContextual } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type RankingItem = { nome: string; quantidade: number }
type DashboardContextual = {
  total_registros?: number
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
type CicloResumo = {
  total_pedidos?: number
  enviados_carrier?: number
  faturados?: number
  entregues?: number
  instalados?: number
  encerrados?: number
  divergencias_numero_serie?: number
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
  registros_sem_linha_classificada?: number
  cobertura_classificacao_percentual?: number
}
type ProductLinesResponse = {
  metadata?: ProductLinesMetadata
  linhas?: Omit<LinhaProduto, "disponivel">[]
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
  const [ciclo, setCiclo] = useState<CicloResumo>({})
  const [linhasProduto, setLinhasProduto] = useState<LinhaProduto[]>(LINHAS_VAZIAS)
  const [metadataLinhas, setMetadataLinhas] = useState<ProductLinesMetadata>({})
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState("")
  const [loading, setLoading] = useState(true)
  const [avisos, setAvisos] = useState<string[]>([])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      const [dadosNucleo, dadosCiclo] = await Promise.all([
        tentar<NucleoComercial[]>(() => buscarJson(`${API_URL}/crm/nucleo-comercial`)),
        tentar<CicloResumo>(() => buscarJson(`${API_URL}/carrier-operacional/ciclo-resumo`)),
      ])
      if (!ativo) return
      setNucleo(dadosNucleo ?? [])
      setCiclo(dadosCiclo ?? {})
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

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-hidden">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura temporal executiva</p>
            <h1 className="mt-2 text-3xl font-bold">Dashboard Executivo</h1>
            <p className="mt-2 max-w-4xl text-sm text-slate-400">O painel separa o que já aconteceu daquilo que ainda está em curso. O histórico respeita os filtros temporais; o CRM mostra negócios vivos e o ciclo operacional mostra o avanço real após o pedido.</p>
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
            <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Cadeia operacional atual</p>
                <h2 className="mt-1 text-2xl font-bold">Do pedido à instalação</h2>
                <p className="mt-1 text-sm text-slate-400">Entrega não encerra o ciclo. Instalação é o marco operacional; encerramento confirma a conclusão.</p>
              </div>
              {(ciclo.divergencias_numero_serie ?? 0) > 0 && <span className="w-fit rounded-full border border-amber-700 bg-amber-950/30 px-4 py-2 text-sm text-amber-200">{ciclo.divergencias_numero_serie} divergência(s) de série</span>}
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <Etapa titulo="CARRIER" valor={ciclo.enviados_carrier ?? 0} />
              <Etapa titulo="Faturados" valor={ciclo.faturados ?? 0} />
              <Etapa titulo="Entregues" valor={ciclo.entregues ?? 0} />
              <Etapa titulo="Instalados" valor={ciclo.instalados ?? 0} destaque />
              <Etapa titulo="Encerrados" valor={ciclo.encerrados ?? 0} />
            </div>
          </section>

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Histórico realizado por produto</p>
              <h2 className="mt-1 text-2xl font-bold">TR · DT · DD no período selecionado</h2>
              <p className="mt-1 text-sm text-slate-400">Comparação temporal somente sobre registros históricos classificados. Detalhes operacionais permanecem nas telas de Equipamentos.</p>
            </div>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {linhasProduto.map((linha) => <LinhaHistorica key={linha.codigo} linha={linha} totalClassificado={totalClassificado} />)}
            </div>
            <p className="mt-4 text-xs text-slate-500">Cobertura da classificação histórica no período: {loading ? "..." : `${cobertura.toLocaleString("pt-BR")}%`}. {metadataLinhas.descricao || ""}</p>
          </section>

          <section className="rounded-3xl border border-[#24466f] bg-[#07162b] p-5 sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Próxima camada: IA Comercial CTI</p>
            <h2 className="mt-1 text-xl font-bold">Interpretação, não mais poluição visual</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-400">A IA será evoluída depois da homologação desta separação temporal. Ela deverá comparar histórico realizado, negócios em curso e exceções operacionais para produzir briefing executivo, alertas e recomendações, sem reproduzir na tela os módulos que já existem no menu lateral.</p>
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
function percentual(parte?: number, total?: number) { if (!parte || !total) return 0; return Math.round((parte / total) * 100) }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: React.ReactNode }) {
  return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h2 className="mt-1 text-xl font-bold">{subtitulo}</h2></div><span className="shrink-0 rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section>
}
function Info({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{titulo}</p><p className="mt-1 text-sm font-semibold text-cyan-200">{valor}</p></div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function Etapa({ titulo, valor, destaque = false }: { titulo: string; valor: number; destaque?: boolean }) { return <div className={`rounded-2xl border p-4 ${destaque ? "border-emerald-700 bg-emerald-950/20" : "border-[#16325c] bg-[#091a33]"}`}><p className="text-sm text-slate-400">{titulo}</p><p className={`mt-2 text-3xl font-bold ${destaque ? "text-emerald-300" : "text-cyan-300"}`}>{valor}</p></div> }
function LinhaHistorica({ linha, totalClassificado }: { linha: LinhaProduto; totalClassificado: number }) {
  const participacao = totalClassificado > 0 ? (linha.atual / totalClassificado) * 100 : 0
  const direcao = linha.variacao > 0 ? "alta" : linha.variacao < 0 ? "queda" : "estável"
  return <article className="rounded-2xl border border-[#16325c] bg-[#091a33] p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold text-cyan-400">{linha.codigo}</p><h3 className="mt-1 text-lg font-bold">{linha.nome}</h3></div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{direcao}</span></div>{linha.disponivel ? <><div className="mt-5 grid grid-cols-3 gap-3 text-center"><Mini titulo="Atual" valor={linha.atual} /><Mini titulo="Anterior" valor={linha.anterior} /><Mini titulo="Variação" valor={`${linha.variacao > 0 ? "+" : ""}${linha.variacao.toLocaleString("pt-BR")}%`} /></div><p className="mt-4 text-sm text-slate-400">Participação na base histórica classificada: <strong className="text-cyan-300">{participacao.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</strong></p></> : <p className="mt-5 text-sm text-slate-500">Indicador indisponível.</p>}</article>
}
function Mini({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="rounded-xl bg-[#020817] p-3"><p className="text-xs text-slate-500">{titulo}</p><p className="mt-1 font-bold text-cyan-300">{valor}</p></div> }
