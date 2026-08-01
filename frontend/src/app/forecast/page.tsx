"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type LinhaNucleo = {
  oportunidade_id: string
  titulo: string
  cliente_nome: string
  responsavel_id?: string | null
  competencia: string
  etapa: string
  valor: number
  valor_ponderado: number
  probabilidade: number
  encerrada: boolean
}

function mesAtual() {
  return new Date().toISOString().slice(0, 7)
}

export default function ForecastPage() {
  const [linhas, setLinhas] = useState<LinhaNucleo[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [competencia, setCompetencia] = useState(mesAtual())
  const [etapa, setEtapa] = useState("TODAS")

  useEffect(() => {
    void (async () => {
      try {
        const resposta = await fetch(`${API_URL}/crm/nucleo-comercial`, { cache: "no-store" })
        const payload = await resposta.json().catch(() => [])
        if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível carregar o núcleo comercial.")
        setLinhas(Array.isArray(payload) ? payload : [])
      } catch (falha) {
        setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o Forecast.")
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const abertas = useMemo(() => linhas.filter((item) => !item.encerrada), [linhas])
  const competencias = useMemo(() => Array.from(new Set(abertas.map((item) => item.competencia).filter(Boolean))).sort(), [abertas])
  const etapas = useMemo(() => Array.from(new Set(abertas.map((item) => item.etapa))).sort(), [abertas])
  const filtradas = useMemo(
    () => abertas.filter((item) => (!competencia || item.competencia === competencia) && (etapa === "TODAS" || item.etapa === etapa)),
    [abertas, competencia, etapa],
  )

  const pipelineTotal = filtradas.reduce((total, item) => total + Number(item.valor || 0), 0)
  const pipelinePonderado = filtradas.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0)

  return <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="flex-1"><Topbar /><div className="space-y-6 p-8">
    <div><h1 className="text-4xl font-bold text-white">CRM • Forecast Comercial</h1><p className="mt-2 text-gray-400">Forecast derivado da projeção única do núcleo CRM. Esta tela não recalcula status, valor nem probabilidade.</p></div>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

    <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-5"><div className="flex flex-col gap-4 lg:flex-row lg:items-end"><div><h2 className="font-semibold text-white">Filtros do Forecast</h2><p className="mt-1 text-sm text-gray-400">Os filtros apenas selecionam registros já consolidados pelo núcleo comercial.</p></div><label className="text-sm text-gray-300">Competência<select value={competencia} onChange={(evento) => setCompetencia(evento.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="">Todas</option>{competencias.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label className="text-sm text-gray-300">Etapa<select value={etapa} onChange={(evento) => setEtapa(evento.target.value)} className="ml-3 rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white"><option value="TODAS">Todas</option>{etapas.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label></div></section>

    <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Pipeline da competência" valor={`R$ ${pipelineTotal.toLocaleString("pt-BR")}`} /><Kpi titulo="Pipeline ponderado" valor={`R$ ${pipelinePonderado.toLocaleString("pt-BR")}`} destaque="verde" /><Kpi titulo="Oportunidades consideradas" valor={filtradas.length} /></section>

    <div className="overflow-hidden rounded-2xl border border-[#13203f] bg-[#091a33]"><div className="border-b border-[#13203f] p-6"><h2 className="text-xl font-semibold text-white">Forecast Comercial</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : filtradas.length === 0 ? <div className="p-10 text-gray-400">Nenhuma oportunidade aberta na competência e etapa selecionadas.</div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-[#13203f]"><Th>Cliente</Th><Th>Oportunidade</Th><Th>Competência</Th><Th>Etapa</Th><Th>Pipeline</Th><Th>Probabilidade</Th><Th>Ponderado</Th></tr></thead><tbody>{filtradas.map((item) => <tr key={item.oportunidade_id} className="border-b border-[#13203f]"><Td>{item.cliente_nome}</Td><Td>{item.titulo}</Td><Td>{item.competencia || "Não definida"}</Td><td className="p-4 text-cyan-400">{item.etapa.replaceAll("_", " ")}</td><td className="p-4 text-cyan-400">R$ {Number(item.valor || 0).toLocaleString("pt-BR")}</td><Td>{Math.round(Number(item.probabilidade || 0) * 100)}%</Td><td className="p-4 text-green-400">R$ {Number(item.valor_ponderado || 0).toLocaleString("pt-BR")}</td></tr>)}</tbody></table></div>}</div>
  </div></section></main>
}

function Kpi({ titulo, valor, destaque = "ciano" }: { titulo: string; valor: string | number; destaque?: "ciano" | "verde" }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><h2 className={`mt-2 text-3xl font-bold ${destaque === "verde" ? "text-green-400" : "text-cyan-400"}`}>{valor}</h2></div> }
function Th({ children }: { children: React.ReactNode }) { return <th className="p-4 text-left text-gray-400">{children}</th> }
function Td({ children }: { children: React.ReactNode }) { return <td className="p-4 text-white">{children}</td> }
