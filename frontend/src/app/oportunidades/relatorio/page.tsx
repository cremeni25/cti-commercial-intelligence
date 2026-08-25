/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { API_URL } from "@/lib/api"
import { lerContextoOportunidade } from "@/lib/crm-opportunity"

type Oportunidade = {
  id: string
  titulo: string
  cliente_nome: string
  status: string
  valor_estimado: number
  probabilidade: number
  data_fechamento_prevista?: string
  equipamento?: string
  linha_equipamentos?: string
  responsavel_id?: string
}

type Recorte = "TODAS" | "ABERTAS" | "GANHAS" | "PERDIDAS"

function moeda(valor: number) { return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function percentual(valor?: number) { const numero = Number(valor || 0); return Math.round(numero <= 1 ? numero * 100 : numero) }
function dataBr(valor?: string) { return valor ? new Date(`${valor.slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR") : "—" }
function escaparCsv(valor: unknown) { return `"${String(valor ?? "").replaceAll('"', '""')}"` }

export default function RelatorioOportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [inicio, setInicio] = useState("")
  const [fim, setFim] = useState("")
  const [busca, setBusca] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [recorte, setRecorte] = useState<Recorte>("TODAS")

  useEffect(() => {
    const parametros = new URLSearchParams(window.location.search)
    const inicioParametro = parametros.get("inicio") || ""
    const fimParametro = parametros.get("fim") || ""
    const buscaParametro = parametros.get("busca") || ""
    setInicio(inicioParametro)
    setFim(fimParametro)
    setBusca(buscaParametro)
    fetch(`${API_URL}/crm-visao/oportunidades?inicio=${encodeURIComponent(inicioParametro)}&fim=${encodeURIComponent(fimParametro)}`, { cache: "no-store" })
      .then(async (response) => { if (!response.ok) throw new Error("Falha ao gerar relatório"); return response.json() as Promise<Oportunidade[]> })
      .then((registros) => setDados(Array.isArray(registros) ? registros : []))
      .catch(() => setErro("Não foi possível gerar o relatório de oportunidades."))
      .finally(() => setLoading(false))
  }, [])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return dados
    return dados.filter((item) => `${item.cliente_nome} ${item.titulo} ${item.status} ${item.equipamento || ""} ${item.linha_equipamentos || ""}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, dados])

  const abertas = filtrados.filter((item) => !["GANHO", "PERDIDO", "CANCELADO"].includes(String(item.status || "").toUpperCase()))
  const ganhas = filtrados.filter((item) => String(item.status || "").toUpperCase() === "GANHO")
  const perdidas = filtrados.filter((item) => String(item.status || "").toUpperCase() === "PERDIDO")
  const valorTotal = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0), 0)
  const valorPonderado = abertas.reduce((total, item) => total + Number(item.valor_estimado || 0) * percentual(item.probabilidade) / 100, 0)
  const porEtapa = filtrados.reduce<Record<string, number>>((acc, item) => { const etapa = item.status || "SEM ETAPA"; acc[etapa] = (acc[etapa] || 0) + 1; return acc }, {})
  const detalhados = recorte === "ABERTAS" ? abertas : recorte === "GANHAS" ? ganhas : recorte === "PERDIDAS" ? perdidas : filtrados

  function abrirRecorte(novoRecorte: Recorte) {
    setRecorte(novoRecorte)
    requestAnimationFrame(() => document.getElementById("composicao-relatorio-oportunidades")?.scrollIntoView({ behavior: "smooth", block: "start" }))
  }

  function exportarCsv() {
    const cabecalho = ["Empresa", "Oportunidade", "Produto", "Valor", "Probabilidade", "Etapa", "Responsável", "Previsão"]
    const linhas = filtrados.map((item) => {
      const contexto = lerContextoOportunidade(item)
      return [item.cliente_nome, item.titulo, contexto.equipamentos.join(", ") || item.equipamento || item.linha_equipamentos || "A definir", Number(item.valor_estimado || 0).toFixed(2), `${percentual(item.probabilidade)}%`, item.status, item.responsavel_id || "", item.data_fechamento_prevista || ""]
    })
    const csv = `\uFEFF${[cabecalho, ...linhas].map((linha) => linha.map(escaparCsv).join(";")).join("\n")}`
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
    const link = document.createElement("a")
    link.href = url
    link.download = `relatorio-oportunidades-${inicio || "inicio"}-${fim || "fim"}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return <main className="min-h-screen bg-slate-100 p-4 text-slate-950 sm:p-8">
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="rounded-2xl bg-white p-6 shadow-sm print:shadow-none">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div><p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-700">CTI Inteligência Comercial</p><h1 className="mt-2 text-3xl font-bold">Relatório de oportunidades</h1><p className="mt-2 text-sm text-slate-600">Período: {dataBr(inicio)} a {dataBr(fim)}{busca ? ` • Filtro: ${busca}` : ""}</p><p className="mt-1 text-xs text-slate-500">Gerado em {new Date().toLocaleString("pt-BR")}</p></div>
          <div className="flex flex-wrap gap-2 print:hidden"><Link href={`/oportunidades?inicio=${inicio}&fim=${fim}`} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold">Voltar</Link><button type="button" onClick={exportarCsv} className="rounded-lg border border-cyan-700 px-4 py-2 text-sm font-semibold text-cyan-800">Exportar Excel/CSV</button><button type="button" onClick={() => window.print()} className="rounded-lg bg-cyan-700 px-4 py-2 text-sm font-semibold text-white">Imprimir / PDF</button></div>
        </div>
      </header>

      {loading && <div className="rounded-2xl bg-white p-8">Gerando relatório...</div>}
      {erro && <div className="rounded-2xl border border-red-300 bg-red-50 p-5 text-red-800">{erro}</div>}

      {!loading && !erro && <>
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
          <Kpi titulo="Total" valor={String(filtrados.length)} onClick={() => abrirRecorte("TODAS")} /><Kpi titulo="Abertas" valor={String(abertas.length)} onClick={() => abrirRecorte("ABERTAS")} /><Kpi titulo="Ganhas" valor={String(ganhas.length)} onClick={() => abrirRecorte("GANHAS")} /><Kpi titulo="Perdidas" valor={String(perdidas.length)} onClick={() => abrirRecorte("PERDIDAS")} /><Kpi titulo="Pipeline" valor={moeda(valorTotal)} onClick={() => abrirRecorte("ABERTAS")} /><Kpi titulo="Ponderado" valor={moeda(valorPonderado)} onClick={() => abrirRecorte("ABERTAS")} />
        </section>
        <section className="rounded-2xl bg-white p-6 shadow-sm print:shadow-none"><h2 className="text-lg font-bold">Distribuição por etapa</h2><div className="mt-4 flex flex-wrap gap-3">{Object.entries(porEtapa).map(([etapa, quantidade]) => <div key={etapa} className="rounded-xl border border-slate-200 px-4 py-3"><span className="text-xs uppercase text-slate-500">{etapa}</span><strong className="ml-3 text-lg">{quantidade}</strong></div>)}</div></section>
        <section id="composicao-relatorio-oportunidades" className="scroll-mt-6 overflow-x-auto rounded-2xl bg-white shadow-sm print:shadow-none"><div className="border-b border-slate-200 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Composição do indicador</p><p className="mt-1 text-sm text-slate-600">Recorte atual: {recorte} • {detalhados.length} registro(s). Pipeline e Ponderado usam o mesmo conjunto de oportunidades abertas.</p></div><table className="min-w-[1050px] w-full text-left text-sm"><thead className="bg-slate-100 text-xs uppercase text-slate-500"><tr><th className="p-4">Empresa</th><th className="p-4">Oportunidade</th><th className="p-4">Produto</th><th className="p-4">Valor</th><th className="p-4">Chance</th><th className="p-4">Etapa</th><th className="p-4">Responsável</th><th className="p-4">Previsão</th></tr></thead><tbody className="divide-y divide-slate-200">{detalhados.map((item) => { const contexto = lerContextoOportunidade(item); return <tr key={item.id}><td className="p-4 font-semibold">{item.cliente_nome}</td><td className="p-4">{item.titulo}</td><td className="p-4">{contexto.equipamentos.join(", ") || item.equipamento || item.linha_equipamentos || "A definir"}</td><td className="p-4">{moeda(Number(item.valor_estimado || 0))}</td><td className="p-4">{percentual(item.probabilidade)}%</td><td className="p-4">{item.status}</td><td className="p-4">{item.responsavel_id || "—"}</td><td className="p-4">{dataBr(item.data_fechamento_prevista)}</td></tr> })}</tbody></table></section>
      </>}
    </div>
  </main>
}

function Kpi({ titulo, valor, onClick }: { titulo: string; valor: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="rounded-2xl bg-white p-5 text-left shadow-sm transition hover:ring-2 hover:ring-cyan-600/30 print:border print:border-slate-200 print:shadow-none"><p className="text-xs font-semibold uppercase text-slate-500">{titulo}</p><p className="mt-2 text-2xl font-bold">{valor}</p><p className="mt-2 text-[11px] text-cyan-700 print:hidden">Clique para detalhar</p></button> }
