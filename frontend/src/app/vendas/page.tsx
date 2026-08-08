/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Venda = {
  id?: string
  cliente_id?: string
  cliente_nome?: string
  equipamento_id?: string
  equipamento_codigo?: string
  equipamento_nome?: string
  implementador_id?: string
  implementadora_id?: string
  implementadora_nome?: string
  pedido_id?: string
  pedido_numero?: string
  tipo_venda?: string
  valor?: number
  data_venda?: string
  observacao?: string
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function dataBr(valor?: string) {
  if (!valor) return "-"
  const data = new Date(`${valor}T12:00:00`)
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleDateString("pt-BR")
}

export default function VendasPage() {
  const [dados, setDados] = useState<Venda[]>([])
  const [busca, setBusca] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")

    fetch(`${API_URL}/vendas`, { cache: "no-store" })
      .then(async (response) => {
        const payload = await response.json().catch(() => null)
        if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar as vendas.")
        if (!Array.isArray(payload)) throw new Error("A API de vendas retornou um formato inesperado.")
        return payload as Venda[]
      })
      .then((payload) => { if (ativo) setDados(payload) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar vendas.") })
      .finally(() => { if (ativo) setLoading(false) })

    return () => { ativo = false }
  }, [])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return dados
    return dados.filter((item) => JSON.stringify(item).toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, dados])

  const valorTotal = dados.reduce((total, item) => total + Number(item.valor || 0), 0)
  const ticketMedio = dados.length ? valorTotal / dados.length : 0
  const tipos = new Set(dados.map((item) => String(item.tipo_venda || "").trim()).filter(Boolean)).size

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Operação comercial</p>
          <h1 className="mt-2 text-3xl font-bold">Vendas</h1>
          <p className="mt-2 text-sm text-slate-400">Consolidação das vendas registradas pela equipe comercial no CRM.</p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi titulo="Vendas registradas" valor={String(dados.length)} />
          <Kpi titulo="Valor vendido" valor={moeda(valorTotal)} />
          <Kpi titulo="Ticket médio" valor={moeda(ticketMedio)} />
          <Kpi titulo="Tipos de venda" valor={String(tipos)} />
        </section>

        <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-xl font-bold">Histórico de vendas</h2>
              <p className="mt-1 text-sm text-slate-400">Espelho gerencial das vendas registradas no CRM.</p>
            </div>
            <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, equipamento, pedido, tipo ou observação" className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white md:max-w-md" />
          </div>

          {erro && <div className="mt-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
          {loading ? <p className="mt-6 text-slate-400">Carregando vendas...</p> : filtrados.length === 0 ? <div className="mt-6 rounded-2xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhuma venda registrada na base atual.</div> : <div className="mt-6 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead><tr className="border-b border-[#16325c] text-left text-slate-400"><th className="p-3">Data</th><th className="p-3">Cliente</th><th className="p-3">Pedido</th><th className="p-3">Equipamento</th><th className="p-3">Implementadora</th><th className="p-3">Tipo</th><th className="p-3">Valor</th></tr></thead>
              <tbody>{filtrados.map((item, index) => <tr key={item.id || `${item.cliente_id}-${item.data_venda}-${index}`} className="border-b border-[#13203f] align-top">
                <td className="p-3">{dataBr(item.data_venda)}</td>
                <td className="p-3 font-semibold text-white">{item.cliente_nome || item.cliente_id || "-"}</td>
                <td className="p-3 text-cyan-300">{item.pedido_numero || "-"}</td>
                <td className="p-3">{item.equipamento_nome || item.equipamento_codigo || item.equipamento_id || "-"}</td>
                <td className="p-3">{item.implementadora_nome || "-"}</td>
                <td className="p-3"><span className="rounded-full border border-cyan-800 px-3 py-1 text-xs text-cyan-200">{item.tipo_venda || "VENDA"}</span></td>
                <td className="p-3 font-semibold text-emerald-300">{moeda(item.valor)}</td>
              </tr>)}</tbody>
            </table>
          </div>}
        </section>
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div>
}
