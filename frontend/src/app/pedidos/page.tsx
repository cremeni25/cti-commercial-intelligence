/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type RegistroNucleo = {
  oportunidade_id: string
  cliente_nome?: string
  etapa?: string
  valor?: number
  proposta_numero?: string
  pedido_id?: string
  pedido_numero?: string
  status_pedido?: string
}

type PedidoOperacional = {
  id: string
  numero?: string
  cliente_nome?: string
  valor?: number
  status?: string
  data_pedido?: string
  linha_produto?: string
  equipamento?: string
  quantidade?: number
  proposta_numero?: string
  status_envio_carrier?: string
  aceite?: { nome_signatario?: string; metodo?: string; aceito_em?: string; status?: string }
}

type Pedido = PedidoOperacional & {
  oportunidade_id?: string
  etapa_comercial?: string
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function data(valor?: string) {
  if (!valor) return "-"
  const d = new Date(valor)
  return Number.isNaN(d.getTime()) ? valor : d.toLocaleDateString("pt-BR")
}

async function buscarJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" })
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar os pedidos.")
  return payload as T
}

export default function PedidosPage() {
  const [dados, setDados] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")

    Promise.all([
      buscarJson<RegistroNucleo[]>(`${API_URL}/crm/nucleo-comercial`),
      buscarJson<PedidoOperacional[]>(`${API_URL}/carrier-operacional/pedidos`).catch(() => []),
    ])
      .then(([nucleo, operacionais]) => {
        if (!ativo) return
        const operacionalPorId = new Map(operacionais.map((item) => [String(item.id), item]))
        const pedidos = nucleo
          .filter((item) => Boolean(item.pedido_id))
          .map((item) => {
            const operacional = operacionalPorId.get(String(item.pedido_id))
            return {
              ...(operacional || { id: String(item.pedido_id) }),
              id: String(item.pedido_id),
              numero: item.pedido_numero || operacional?.numero,
              cliente_nome: item.cliente_nome || operacional?.cliente_nome,
              valor: Number(item.valor || 0),
              status: item.status_pedido || operacional?.status,
              proposta_numero: item.proposta_numero || operacional?.proposta_numero,
              oportunidade_id: item.oportunidade_id,
              etapa_comercial: item.etapa,
            }
          })
        setDados(pedidos)
      })
      .catch((falha) => {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar pedidos.")
      })
      .finally(() => { if (ativo) setLoading(false) })

    return () => { ativo = false }
  }, [])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return dados
    return dados.filter((item) => JSON.stringify(item).toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, dados])

  const valorTotal = dados.reduce((total, item) => total + Number(item.valor || 0), 0)
  const enviados = dados.filter((item) => ["ENVIADO", "REENVIADO", "CONFIRMADO", "ENVIADO_CARRIER", "APROVADO_CARRIER"].includes(String(item.status_envio_carrier || item.status))).length
  const preparando = dados.filter((item) => String(item.status_envio_carrier) === "PREPARANDO" || item.etapa_comercial === "DOSSIÊ").length

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Operação comercial</p>
              <h1 className="mt-2 text-3xl font-bold">Pedidos e dossiês Carrier</h1>
              <p className="mt-2 text-sm text-slate-400">Pedidos reconhecidos pelo núcleo comercial e complementados pelos dados operacionais do dossiê.</p>
            </div>
            <Link href="/funil-carrier" className="rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300">Abrir Funil Carrier</Link>
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi titulo="Pedidos" valor={String(dados.length)} />
          <Kpi titulo="Valor total" valor={moeda(valorTotal)} />
          <Kpi titulo="Dossiês em preparação" valor={String(preparando)} />
          <Kpi titulo="Enviados à Carrier" valor={String(enviados)} />
        </section>

        <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div><h2 className="text-xl font-bold">Gestão de pedidos</h2><p className="mt-1 text-sm text-slate-400">Proposta, aceite, pedido e encaminhamento em uma única trilha.</p></div>
            <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, pedido ou equipamento" className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-sm text-white md:max-w-md" />
          </div>

          {erro && <div className="mt-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
          {loading ? <p className="mt-6 text-slate-400">Carregando pedidos...</p> : filtrados.length === 0 ? <p className="mt-6 text-slate-500">Nenhum pedido encontrado.</p> : <div className="mt-6 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead><tr className="border-b border-[#16325c] text-left text-slate-400"><th className="p-3">Cliente</th><th className="p-3">Pedido</th><th className="p-3">Equipamento</th><th className="p-3">Valor</th><th className="p-3">Aceite</th><th className="p-3">Carrier</th><th className="p-3">Ação</th></tr></thead>
              <tbody>{filtrados.map((item) => <tr key={item.id} className="border-b border-[#13203f] align-top">
                <td className="p-3"><p className="font-semibold text-white">{item.cliente_nome || "Cliente não identificado"}</p><p className="mt-1 text-xs text-slate-500">{data(item.data_pedido)}</p></td>
                <td className="p-3"><p className="text-cyan-300">{item.numero || "Pedido"}</p><p className="mt-1 text-xs text-slate-500">Proposta {item.proposta_numero || "-"}</p></td>
                <td className="p-3"><p>{item.equipamento || "-"}</p><p className="mt-1 text-xs text-slate-500">{item.linha_produto || "-"} • {item.quantidade || 1} un.</p></td>
                <td className="p-3 font-semibold text-emerald-300">{moeda(item.valor)}</td>
                <td className="p-3"><p>{item.aceite?.nome_signatario || "Registrado"}</p><p className="mt-1 text-xs text-slate-500">{item.aceite?.metodo || "-"}</p></td>
                <td className="p-3"><span className="rounded-full border border-cyan-800 px-3 py-1 text-xs text-cyan-200">{item.status_envio_carrier || item.etapa_comercial || "PEDIDO"}</span></td>
                <td className="p-3"><Link href={`/pedidos/${item.id}`} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Abrir dossiê</Link></td>
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
