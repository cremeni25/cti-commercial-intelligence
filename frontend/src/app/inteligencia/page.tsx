"use client"

import { useEffect, useState } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://cti-backend-5ugf.onrender.com"
const segmentos = ["GERAL", "TR", "DT", "DD", "UNKNOWN"] as const
const contextos = [
  ["brasil", "Brasil"],
  ["viena-sp", "VIENA SP"],
  ["outros-dealers", "Outros Dealers"],
] as const

type Intelligence = {
  metadata: {
    contexto_operacional: string
    segmento: string
    periodo_analisado: { inicio: string | null; fim: string | null }
    ultima_atualizacao: string
    origem: string
    criterio_calculo: string
  }
  resumo: {
    total_registros: number
    valor_total: number
    clientes_unicos: number
    implementadoras_unicas: number
  }
  segmentos: Record<string, number>
  market_share: Array<{ fabricante: string; quantidade: number; participacao_percentual: number }>
  implementadoras: Array<{ nome: string; quantidade: number }>
  crescimento_regional: Array<{ estado: string; quantidade: number; valor: number }>
  clientes: Array<{ nome: string; quantidade: number }>
  tendencias: { segmento_lider: string | null; implementadora_lider: string | null; estado_lider: string | null }
  empty_state: string | null
}

function Card({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  )
}

export default function InteligenciaPage() {
  const [contexto, setContexto] = useState("brasil")
  const [segmento, setSegmento] = useState("GERAL")
  const [dados, setDados] = useState<Intelligence | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    fetch(
      `${API_URL}/analytics/intelligence?contexto=${encodeURIComponent(contexto)}&segmento=${encodeURIComponent(segmento)}`,
      { cache: "no-store", signal: controller.signal }
    )
      .then((response) => {
        if (!response.ok) throw new Error(`Backend respondeu ${response.status}`)
        return response.json() as Promise<Intelligence>
      })
      .then((payload) => {
        setDados(payload)
        setErro(null)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return
        setDados(null)
        setErro(error instanceof Error ? error.message : "Falha ao carregar a inteligência comercial")
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [contexto, segmento, reloadKey])

  function selecionarContexto(value: string) {
    if (value === contexto) return
    setLoading(true)
    setErro(null)
    setContexto(value)
  }

  function selecionarSegmento(value: string) {
    if (value === segmento) return
    setLoading(true)
    setErro(null)
    setSegmento(value)
  }

  function recarregar() {
    setLoading(true)
    setErro(null)
    setReloadKey((current) => current + 1)
  }

  return (
    <main className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header>
          <p className="text-sm font-medium uppercase tracking-wide text-blue-700">CTI Commercial Intelligence</p>
          <h1 className="text-3xl font-bold text-slate-950">Inteligência Comercial</h1>
          <p className="mt-2 text-slate-600">Leitura histórica e analítica, sem criação automática de oportunidades no CRM.</p>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap gap-2">
            {contextos.map(([value, label]) => (
              <button key={value} onClick={() => selecionarContexto(value)} className={`rounded-lg px-4 py-2 text-sm font-medium ${contexto === value ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}>{label}</button>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {segmentos.map((value) => (
              <button key={value} onClick={() => selecionarSegmento(value)} className={`rounded-lg px-4 py-2 text-sm font-medium ${segmento === value ? "bg-blue-700 text-white" : "bg-blue-50 text-blue-800"}`}>{value}</button>
            ))}
          </div>
        </section>

        {loading && <div className="rounded-xl border bg-white p-10 text-center text-slate-600">Carregando inteligência comercial...</div>}

        {erro && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <p className="font-semibold text-red-800">Não foi possível carregar os dados.</p>
            <p className="mt-1 text-sm text-red-700">{erro}</p>
            <button onClick={recarregar} className="mt-4 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white">Recarregar</button>
          </div>
        )}

        {!loading && dados?.empty_state && <div className="rounded-xl border bg-white p-10 text-center text-slate-600">{dados.empty_state}</div>}

        {!loading && dados && !dados.empty_state && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card title="Registros analisados" value={dados.resumo.total_registros} />
              <Card title="Clientes únicos" value={dados.resumo.clientes_unicos} />
              <Card title="Implementadoras" value={dados.resumo.implementadoras_unicas} />
              <Card title="Valor total" value={dados.resumo.valor_total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold">Market share</h2>
                <div className="mt-4 space-y-3">{dados.market_share.map((item) => <div key={item.fabricante} className="flex justify-between border-b pb-2 text-sm"><span>{item.fabricante}</span><strong>{item.participacao_percentual}% ({item.quantidade})</strong></div>)}</div>
              </div>
              <div className="rounded-xl border bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold">Ranking de implementadoras</h2>
                <div className="mt-4 space-y-3">{dados.implementadoras.map((item, index) => <div key={item.nome} className="flex justify-between border-b pb-2 text-sm"><span>{index + 1}. {item.nome}</span><strong>{item.quantidade}</strong></div>)}</div>
              </div>
              <div className="rounded-xl border bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold">Crescimento regional</h2>
                <div className="mt-4 space-y-3">{dados.crescimento_regional.slice(0, 10).map((item) => <div key={item.estado} className="flex justify-between border-b pb-2 text-sm"><span>{item.estado}</span><strong>{item.quantidade}</strong></div>)}</div>
              </div>
              <div className="rounded-xl border bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold">Clientes em destaque</h2>
                <div className="mt-4 space-y-3">{dados.clientes.map((item) => <div key={item.nome} className="flex justify-between border-b pb-2 text-sm"><span>{item.nome}</span><strong>{item.quantidade}</strong></div>)}</div>
              </div>
            </section>

            <section className="rounded-xl border bg-white p-5 text-sm text-slate-600 shadow-sm">
              <h2 className="font-semibold text-slate-900">Contexto analítico</h2>
              <p className="mt-2">Origem: {dados.metadata.origem} · Contexto: {dados.metadata.contexto_operacional} · Segmento: {dados.metadata.segmento}</p>
              <p>Período: {dados.metadata.periodo_analisado.inicio || "não identificado"} a {dados.metadata.periodo_analisado.fim || "não identificado"}</p>
              <p>Critério: {dados.metadata.criterio_calculo}</p>
              <p>Atualização: {new Date(dados.metadata.ultima_atualizacao).toLocaleString("pt-BR")}</p>
            </section>
          </>
        )}
      </div>
    </main>
  )
}
