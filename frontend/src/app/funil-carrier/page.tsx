/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type LinhaFunil = {
  oportunidade_id?: string
  cliente?: string
  responsavel_id?: string
  territorio?: string
  linha_produto?: string
  equipamento?: string
  quantidade?: number
  valor_total?: number
  probabilidade?: number
  estagio?: string
  previsao_fechamento?: string
  status_item?: string
  proposta_numero?: string
  proposta_status?: string
  propostas_emitidas?: number
  pedido_gerado?: boolean
  pedido_numero?: string
  status_envio_carrier?: string
  ultima_atualizacao?: string
}

function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function data(valor?: string) { if (!valor) return "-"; const d = new Date(valor); return Number.isNaN(d.getTime()) ? valor : d.toLocaleDateString("pt-BR") }
function csvCampo(valor: unknown) { const texto = String(valor ?? ""); return `"${texto.replaceAll('"', '""')}"` }

export default function FunilCarrierPage() {
  const [dados, setDados] = useState<LinhaFunil[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [linha, setLinha] = useState("TODAS")
  const [estagio, setEstagio] = useState("TODOS")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    fetch(`${API_URL}/carrier-operacional/funil`, { cache: "no-store" })
      .then(async (response) => { const payload = await response.json().catch(() => []); if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar o Funil Carrier."); return Array.isArray(payload) ? payload : [] })
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar funil.") })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [])

  const linhasDisponiveis = useMemo(() => ["TODAS", ...new Set(dados.map((item) => item.linha_produto || "SEM LINHA"))], [dados])
  const estagiosDisponiveis = useMemo(() => ["TODOS", ...new Set(dados.map((item) => item.estagio || "SEM ESTAGIO"))], [dados])
  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return dados.filter((item) => {
      if (linha !== "TODAS" && item.linha_produto !== linha) return false
      if (estagio !== "TODOS" && item.estagio !== estagio) return false
      return !termo || JSON.stringify(item).toLocaleLowerCase("pt-BR").includes(termo)
    })
  }, [busca, dados, estagio, linha])

  const valorTotal = filtrados.reduce((total, item) => total + Number(item.valor_total || 0), 0)
  const valorPonderado = filtrados.reduce((total, item) => {
    const prob = Number(item.probabilidade || 0)
    return total + Number(item.valor_total || 0) * (prob > 1 ? prob / 100 : prob)
  }, 0)
  const comProposta = filtrados.filter((item) => Number(item.propostas_emitidas || 0) > 0).length
  const comPedido = filtrados.filter((item) => item.pedido_gerado).length

  function exportarCSV() {
    const cabecalho = ["Cliente","Territorio","Linha","Equipamento","Quantidade","Valor","Probabilidade","Estagio","Previsao","Status item","Proposta","Status proposta","Pedido","Status Carrier","Ultima atualizacao"]
    const linhasCsv = filtrados.map((item) => [
      item.cliente, item.territorio, item.linha_produto, item.equipamento, item.quantidade,
      item.valor_total, item.probabilidade, item.estagio, item.previsao_fechamento,
      item.status_item, item.proposta_numero, item.proposta_status, item.pedido_numero,
      item.status_envio_carrier, item.ultima_atualizacao,
    ].map(csvCampo).join(";"))
    const conteudo = `\uFEFF${cabecalho.map(csvCampo).join(";")}\n${linhasCsv.join("\n")}`
    const url = URL.createObjectURL(new Blob([conteudo], { type: "text/csv;charset=utf-8" }))
    const link = document.createElement("a")
    link.href = url
    link.download = `funil-carrier-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Integração comercial</p><h1 className="mt-2 text-3xl font-bold">Funil Carrier</h1><p className="mt-2 text-sm text-slate-400">Oportunidades, propostas e pedidos consolidados automaticamente a partir do CRM.</p></div>
            <div className="flex flex-wrap gap-2"><button onClick={() => window.print()} className="rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300">Imprimir / PDF</button><button onClick={exportarCSV} className="rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950">Exportar Excel (CSV)</button></div>
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi titulo="Itens no funil" valor={String(filtrados.length)} />
          <Kpi titulo="Valor total" valor={moeda(valorTotal)} />
          <Kpi titulo="Valor ponderado" valor={moeda(valorPonderado)} />
          <Kpi titulo="Propostas / Pedidos" valor={`${comProposta} / ${comPedido}`} />
        </section>

        <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 print:border-0 print:bg-white print:text-black">
          <div className="grid gap-4 md:grid-cols-3 print:hidden">
            <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, equipamento ou pedido" className="rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white" />
            <select value={linha} onChange={(e) => setLinha(e.target.value)} className="rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white">{linhasDisponiveis.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={estagio} onChange={(e) => setEstagio(e.target.value)} className="rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white">{estagiosDisponiveis.map((item) => <option key={item}>{item}</option>)}</select>
          </div>

          {erro && <div className="mt-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
          {loading ? <p className="mt-6 text-slate-400">Carregando funil...</p> : filtrados.length === 0 ? <p className="mt-6 text-slate-500">Nenhum registro encontrado.</p> : <div className="mt-6 overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead><tr className="border-b border-[#16325c] text-left text-slate-400 print:text-black"><th className="p-3">Cliente</th><th className="p-3">Linha / Equipamento</th><th className="p-3">Qtd.</th><th className="p-3">Valor</th><th className="p-3">Prob.</th><th className="p-3">Estágio</th><th className="p-3">Proposta</th><th className="p-3">Pedido</th><th className="p-3">Carrier</th><th className="p-3">Previsão</th></tr></thead>
              <tbody>{filtrados.map((item, indice) => <tr key={`${item.oportunidade_id}-${item.equipamento}-${indice}`} className="border-b border-[#13203f] align-top print:border-slate-300">
                <td className="p-3"><p className="font-semibold">{item.cliente || "Cliente"}</p><p className="mt-1 text-slate-500">{item.territorio || "-"}</p></td>
                <td className="p-3"><p>{item.equipamento || "-"}</p><p className="mt-1 text-slate-500">{item.linha_produto || "-"}</p></td>
                <td className="p-3">{item.quantidade || 0}</td>
                <td className="p-3 font-semibold text-emerald-300 print:text-black">{moeda(item.valor_total)}</td>
                <td className="p-3">{Number(item.probabilidade || 0)}%</td>
                <td className="p-3">{item.estagio || "-"}</td>
                <td className="p-3"><p>{item.proposta_numero || "-"}</p><p className="mt-1 text-slate-500">{item.proposta_status || "Sem proposta"}</p></td>
                <td className="p-3">{item.pedido_numero || "-"}</td>
                <td className="p-3">{item.status_envio_carrier || "-"}</td>
                <td className="p-3">{data(item.previsao_fechamento)}</td>
              </tr>)}</tbody>
            </table>
          </div>}
        </section>
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div> }
