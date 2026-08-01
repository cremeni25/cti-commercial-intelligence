/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type LinhaFunil = {
  oportunidade_id: string
  cliente_nome: string
  titulo: string
  responsavel_id?: string | null
  etapa: string
  valor: number
  valor_ponderado: number
  probabilidade: number
  competencia: string
  data_fechamento_prevista?: string | null
  proposta_numero?: string | null
  status_proposta?: string | null
  pedido_numero?: string | null
  status_pedido?: string | null
  quantidade_itens: number
  encerrada: boolean
}

function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function data(valor?: string | null) { if (!valor) return "-"; const d = new Date(`${valor.slice(0, 10)}T12:00:00`); return Number.isNaN(d.getTime()) ? valor : d.toLocaleDateString("pt-BR") }
function csvCampo(valor: unknown) { const texto = String(valor ?? ""); return `"${texto.replaceAll('"', '""')}"` }

export default function FunilCarrierPage() {
  const [dados, setDados] = useState<LinhaFunil[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [etapa, setEtapa] = useState("TODAS")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    fetch(`${API_URL}/crm/nucleo-comercial`, { cache: "no-store" })
      .then(async (response) => { const payload = await response.json().catch(() => []); if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar o Funil Carrier."); return Array.isArray(payload) ? payload : [] })
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar funil.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  const etapasDisponiveis = useMemo(() => ["TODAS", ...new Set(dados.map((item) => item.etapa || "SEM_ETAPA"))], [dados])
  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return dados.filter((item) => {
      if (etapa !== "TODAS" && item.etapa !== etapa) return false
      return !termo || JSON.stringify(item).toLocaleLowerCase("pt-BR").includes(termo)
    })
  }, [busca, dados, etapa])

  const valorTotal = filtrados.reduce((total, item) => total + Number(item.valor || 0), 0)
  const valorPonderado = filtrados.reduce((total, item) => total + Number(item.valor_ponderado || 0), 0)
  const comProposta = filtrados.filter((item) => item.proposta_numero).length
  const comPedido = filtrados.filter((item) => item.pedido_numero).length

  function exportarCSV() {
    const cabecalho = ["Cliente","Oportunidade","Etapa","Itens","Valor","Valor ponderado","Probabilidade","Proposta","Status proposta","Pedido","Status pedido","Previsão"]
    const linhasCsv = filtrados.map((item) => [
      item.cliente_nome, item.titulo, item.etapa, item.quantidade_itens, item.valor,
      item.valor_ponderado, item.probabilidade, item.proposta_numero, item.status_proposta,
      item.pedido_numero, item.status_pedido, item.data_fechamento_prevista,
    ].map(csvCampo).join(";"))
    const conteudo = `\uFEFF${cabecalho.map(csvCampo).join(";")}\n${linhasCsv.join("\n")}`
    const url = URL.createObjectURL(new Blob([conteudo], { type: "text/csv;charset=utf-8" }))
    const link = document.createElement("a")
    link.href = url
    link.download = `funil-carrier-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6"><div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Integração comercial</p><h1 className="mt-2 text-3xl font-bold">Funil Carrier</h1><p className="mt-2 text-sm text-slate-400">Oportunidades, propostas e pedidos lidos diretamente do núcleo único do CRM.</p></div><div className="flex flex-wrap gap-2"><button onClick={() => window.print()} className="rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300">Imprimir / PDF</button><button onClick={exportarCSV} className="rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950">Exportar Excel (CSV)</button></div></div></header>

    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi titulo="Negociações no funil" valor={String(filtrados.length)} /><Kpi titulo="Valor total" valor={moeda(valorTotal)} /><Kpi titulo="Valor ponderado" valor={moeda(valorPonderado)} /><Kpi titulo="Propostas / Pedidos" valor={`${comProposta} / ${comPedido}`} /></section>

    <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:border-0 print:bg-white print:text-black"><div className="grid gap-4 md:grid-cols-2 print:hidden"><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, oportunidade, proposta ou pedido" className="rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white" /><select value={etapa} onChange={(e) => setEtapa(e.target.value)} className="rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white">{etapasDisponiveis.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></div>
      {erro && <div className="mt-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
      {loading ? <p className="mt-6 text-slate-400">Carregando funil...</p> : filtrados.length === 0 ? <p className="mt-6 text-slate-500">Nenhum registro encontrado.</p> : <div className="mt-6 overflow-x-auto"><table className="min-w-full text-xs"><thead><tr className="border-b border-[#16325c] text-left text-slate-400 print:text-black"><Th>Cliente</Th><Th>Oportunidade</Th><Th>Itens</Th><Th>Valor</Th><Th>Prob.</Th><Th>Etapa</Th><Th>Proposta</Th><Th>Pedido</Th><Th>Previsão</Th></tr></thead><tbody>{filtrados.map((item) => <tr key={item.oportunidade_id} className="border-b border-[#13203f] align-top print:border-slate-300"><Td><p className="font-semibold">{item.cliente_nome}</p></Td><Td>{item.titulo}</Td><Td>{item.quantidade_itens}</Td><td className="p-3 font-semibold text-emerald-300 print:text-black">{moeda(item.valor)}</td><Td>{Math.round(Number(item.probabilidade || 0) * 100)}%</Td><Td>{item.etapa.replaceAll("_", " ")}</Td><Td><p>{item.proposta_numero || "-"}</p><p className="mt-1 text-slate-500">{item.status_proposta || "Sem proposta"}</p></Td><Td><p>{item.pedido_numero || "-"}</p><p className="mt-1 text-slate-500">{item.status_pedido || "Sem pedido"}</p></Td><Td>{data(item.data_fechamento_prevista)}</Td></tr>)}</tbody></table></div>}
    </section>
  </div></section></main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
function Th({ children }: { children: React.ReactNode }) { return <th className="p-3">{children}</th> }
function Td({ children }: { children: React.ReactNode }) { return <td className="p-3">{children}</td> }
