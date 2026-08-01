"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Oportunidade = {
  id: string
  titulo?: string
  responsavel_id?: string
  valor_estimado?: number
  probabilidade?: number
  status?: string
  data_fechamento_prevista?: string
  created_at?: string
}

type Proposta = {
  id: string
  oportunidade_id?: string
  item_oportunidade_id?: string
  valor?: number
  versao?: number
  status?: string
  status_documento?: string
  created_at?: string
}

type LinhaForecast = {
  id: string
  oportunidade: string
  responsavel: string
  competencia: string
  fase: string
  pipelineTotal: number
  pipelinePonderado: number
  probabilidade: number
}

const STATUS_FECHADOS = new Set(["GANHO", "PERDIDO", "CANCELADO", "CONCLUIDO"])

function fatorProbabilidade(valor: unknown) {
  const numero = Number(valor || 0)
  if (!Number.isFinite(numero) || numero <= 0) return 0
  return numero <= 1 ? numero : numero / 100
}

function prioridadeProposta(item: Proposta) {
  const status = String(item.status_documento || item.status || "").toUpperCase()
  if (status === "CONVERTIDA_PEDIDO") return 60
  if (status === "ACEITA" || status === "APROVADA") return 50
  if (["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)) return 40
  if (["APROVADA_INTERNA", "EM_REVISAO"].includes(status)) return 30
  if (["RASCUNHO", "ELABORACAO"].includes(status)) return 20
  return 10
}

function mesAtual() {
  return new Date().toISOString().slice(0, 7)
}

export default function ForecastPage() {
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [propostas, setPropostas] = useState<Proposta[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [competencia, setCompetencia] = useState(mesAtual())
  const [fase, setFase] = useState("TODAS")

  useEffect(() => {
    queueMicrotask(async () => {
      try {
        const [resOportunidades, resPropostas] = await Promise.all([
          fetch(`${API_URL}/crm/oportunidades`, { cache: "no-store" }),
          fetch(`${API_URL}/crm/propostas`, { cache: "no-store" }),
        ])
        const [jsonOportunidades, jsonPropostas] = await Promise.all([
          resOportunidades.json().catch(() => []),
          resPropostas.json().catch(() => []),
        ])
        if (!resOportunidades.ok) throw new Error(jsonOportunidades?.detail || "Não foi possível carregar oportunidades.")
        if (!resPropostas.ok) throw new Error(jsonPropostas?.detail || "Não foi possível carregar propostas.")
        setOportunidades(Array.isArray(jsonOportunidades) ? jsonOportunidades : [])
        setPropostas(Array.isArray(jsonPropostas) ? jsonPropostas : [])
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Não foi possível consolidar o Forecast.")
      } finally {
        setLoading(false)
      }
    })
  }, [])

  const propostaVigentePorOportunidade = useMemo(() => {
    const mapa = new Map<string, Proposta>()
    for (const proposta of propostas) {
      if (!proposta.oportunidade_id) continue
      const atual = mapa.get(proposta.oportunidade_id)
      if (!atual) {
        mapa.set(proposta.oportunidade_id, proposta)
        continue
      }
      const diferenca = prioridadeProposta(proposta) - prioridadeProposta(atual)
      if (diferenca > 0 || (diferenca === 0 && Number(proposta.versao || 0) > Number(atual.versao || 0))) mapa.set(proposta.oportunidade_id, proposta)
    }
    return mapa
  }, [propostas])

  const linhas = useMemo<LinhaForecast[]>(() => oportunidades.map((item) => {
    const proposta = propostaVigentePorOportunidade.get(item.id)
    const valorComercial = Number(proposta?.valor ?? item.valor_estimado ?? 0)
    const probabilidade = fatorProbabilidade(item.probabilidade)
    const competenciaItem = String(item.data_fechamento_prevista || item.created_at || "").slice(0, 7)
    return {
      id: item.id,
      oportunidade: item.titulo || "Oportunidade sem título",
      responsavel: item.responsavel_id ? "Responsável comercial vinculado" : "Responsável não definido",
      competencia: competenciaItem,
      fase: String(item.status || "OPORTUNIDADE").replaceAll("_", " "),
      pipelineTotal: valorComercial,
      pipelinePonderado: valorComercial * probabilidade,
      probabilidade,
    }
  }).filter((item) => !STATUS_FECHADOS.has(item.fase.replaceAll(" ", "_").toUpperCase())), [oportunidades, propostaVigentePorOportunidade])

  const competencias = useMemo(() => Array.from(new Set(linhas.map((item) => item.competencia).filter(Boolean))).sort(), [linhas])
  const fases = useMemo(() => Array.from(new Set(linhas.map((item) => item.fase))).sort(), [linhas])
  const filtradas = useMemo(() => linhas.filter((item) => (!competencia || item.competencia === competencia) && (fase === "TODAS" || item.fase === fase)), [linhas, competencia, fase])

  const pipelineTotal = filtradas.reduce((acc, item) => acc + item.pipelineTotal, 0)
  const pipelinePonderado = filtradas.reduce((acc, item) => acc + item.pipelinePonderado, 0)

  return <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="flex-1"><Topbar /><div className="space-y-6 p-8">
    <div><h1 className="text-4xl font-bold text-white">CRM • Forecast Comercial</h1><p className="mt-2 text-gray-400">Previsão própria do CRM, calculada pela competência de fechamento e pelo valor vigente da negociação.</p></div>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

    <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-5"><div className="flex flex-col gap-4 lg:flex-row lg:items-end"><div><h2 className="font-semibold text-white">Filtros do Forecast</h2><p className="mt-1 text-sm text-gray-400">Atuam somente nesta tela e não reutilizam o período do Dashboard Executivo.</p></div><label className="text-sm text-gray-300">Competência<select value={competencia} onChange={(evento) => setCompetencia(evento.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="">Todas</option>{competencias.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label className="text-sm text-gray-300">Fase<select value={fase} onChange={(evento) => setFase(evento.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="TODAS">Todas</option>{fases.map((item) => <option key={item} value={item}>{item}</option>)}</select></label></div></section>

    <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Pipeline da competência" valor={`R$ ${pipelineTotal.toLocaleString("pt-BR")}`} /><Kpi titulo="Pipeline ponderado" valor={`R$ ${pipelinePonderado.toLocaleString("pt-BR")}`} destaque="verde" /><Kpi titulo="Oportunidades consideradas" valor={filtradas.length} /></section>

    <div className="overflow-hidden rounded-2xl border border-[#13203f] bg-[#091a33]"><div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-semibold text-white">Forecast Comercial</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : filtradas.length === 0 ? <div className="p-10 text-gray-400">Nenhuma oportunidade aberta na competência e fase selecionadas.</div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-[#13203f]"><th className="p-4 text-left text-gray-400">Oportunidade</th><th className="p-4 text-left text-gray-400">Responsável</th><th className="p-4 text-left text-gray-400">Competência</th><th className="p-4 text-left text-gray-400">Fase</th><th className="p-4 text-left text-gray-400">Pipeline</th><th className="p-4 text-left text-gray-400">Probabilidade</th><th className="p-4 text-left text-gray-400">Ponderado</th></tr></thead><tbody>{filtradas.map((item) => <tr key={item.id} className="border-b border-[#13203f]"><td className="p-4 text-white">{item.oportunidade}</td><td className="p-4 text-gray-300">{item.responsavel}</td><td className="p-4 text-white">{item.competencia || "Não definida"}</td><td className="p-4 text-cyan-400">{item.fase}</td><td className="p-4 text-cyan-400">R$ {item.pipelineTotal.toLocaleString("pt-BR")}</td><td className="p-4 text-white">{Math.round(item.probabilidade * 100)}%</td><td className="p-4 text-green-400">R$ {item.pipelinePonderado.toLocaleString("pt-BR")}</td></tr>)}</tbody></table></div>}</div>
  </div></section></main>
}

function Kpi({ titulo, valor, destaque = "ciano" }: { titulo: string; valor: string | number; destaque?: "ciano" | "verde" }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><h2 className={`mt-2 text-3xl font-bold ${destaque === "verde" ? "text-green-400" : "text-cyan-400"}`}>{valor}</h2></div> }
