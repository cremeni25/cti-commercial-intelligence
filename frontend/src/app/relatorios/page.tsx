/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Registro = Record<string, unknown>
type Venda = Registro & { valor?: number; cliente_nome?: string; equipamento_nome?: string; equipamento_codigo?: string; data_venda?: string }

type DadosRelatorio = {
  oportunidades: Registro[]
  propostas: Registro[]
  pedidos: Registro[]
  vendas: Venda[]
}

function numero(valor: unknown) {
  const convertido = Number(valor || 0)
  return Number.isFinite(convertido) ? convertido : 0
}

function moeda(valor: unknown) {
  return numero(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function texto(valor: unknown, padrao = "-") {
  const resultado = String(valor ?? "").trim()
  return resultado || padrao
}

async function carregarLista(url: string) {
  const resposta = await fetch(url, { cache: "no-store" })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new Error(payload?.detail || `Falha ao consultar ${url}.`)
  if (!Array.isArray(payload)) throw new Error(`Resposta inesperada em ${url}.`)
  return payload as Registro[]
}

export default function RelatoriosPage() {
  const [dados, setDados] = useState<DadosRelatorio>({ oportunidades: [], propostas: [], pedidos: [], vendas: [] })
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    setLoading(true)
    setErro("")

    Promise.all([
      carregarLista(`${API_URL}/crm-visao/oportunidades`),
      carregarLista(`${API_URL}/crm-documentos/propostas`),
      carregarLista(`${API_URL}/crm-documentos/pedidos`),
      carregarLista(`${API_URL}/vendas`),
    ])
      .then(([oportunidades, propostas, pedidos, vendas]) => {
        if (!ativo) return
        setDados({ oportunidades, propostas, pedidos, vendas: vendas as Venda[] })
      })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao consolidar relatório comercial.") })
      .finally(() => { if (ativo) setLoading(false) })

    return () => { ativo = false }
  }, [])

  const resumo = useMemo(() => {
    const valorOportunidades = dados.oportunidades.reduce((total, item) => total + numero(item.valor_estimado), 0)
    const valorPropostas = dados.propostas.reduce((total, item) => total + numero(item.valor_total ?? item.valor), 0)
    const valorPedidos = dados.pedidos.reduce((total, item) => total + numero(item.valor), 0)
    const valorVendas = dados.vendas.reduce((total, item) => total + numero(item.valor), 0)
    const conversaoPedidoVenda = dados.pedidos.length ? (dados.vendas.length / dados.pedidos.length) * 100 : 0
    const conversaoOportunidadeVenda = dados.oportunidades.length ? (dados.vendas.length / dados.oportunidades.length) * 100 : 0
    return { valorOportunidades, valorPropostas, valorPedidos, valorVendas, conversaoPedidoVenda, conversaoOportunidadeVenda }
  }, [dados])

  const ranking = useMemo(() => {
    const acumulado = new Map<string, { cliente: string; vendas: number; valor: number }>()
    for (const venda of dados.vendas) {
      const cliente = texto(venda.cliente_nome, "Cliente não identificado")
      const atual = acumulado.get(cliente) || { cliente, vendas: 0, valor: 0 }
      atual.vendas += 1
      atual.valor += numero(venda.valor)
      acumulado.set(cliente, atual)
    }
    return Array.from(acumulado.values()).sort((a, b) => b.valor - a.valor).slice(0, 5)
  }, [dados.vendas])

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1">
      <Topbar />
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Gestão comercial</p>
          <h1 className="mt-2 text-3xl font-bold">Relatórios</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">Consolidação gerencial do fluxo real do CRM: oportunidade → proposta → pedido → venda.</p>
        </header>

        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
        {loading ? <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-400">Consolidando dados comerciais...</div> : <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi titulo="Oportunidades" valor={String(dados.oportunidades.length)} detalhe={moeda(resumo.valorOportunidades)} />
            <Kpi titulo="Propostas" valor={String(dados.propostas.length)} detalhe={moeda(resumo.valorPropostas)} />
            <Kpi titulo="Pedidos" valor={String(dados.pedidos.length)} detalhe={moeda(resumo.valorPedidos)} />
            <Kpi titulo="Vendas" valor={String(dados.vendas.length)} detalhe={moeda(resumo.valorVendas)} destaque />
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Conversão comercial</h2>
              <p className="mt-1 text-sm text-slate-400">Leitura direta dos registros existentes no CRM e no painel de vendas.</p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <Indicador titulo="Pedido → Venda" valor={`${resumo.conversaoPedidoVenda.toFixed(1)}%`} />
                <Indicador titulo="Oportunidade → Venda" valor={`${resumo.conversaoOportunidadeVenda.toFixed(1)}%`} />
              </div>
              <div className="mt-5 space-y-3">
                <Etapa nome="Oportunidades" quantidade={dados.oportunidades.length} />
                <Etapa nome="Propostas" quantidade={dados.propostas.length} />
                <Etapa nome="Pedidos" quantidade={dados.pedidos.length} />
                <Etapa nome="Vendas" quantidade={dados.vendas.length} />
              </div>
            </div>

            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
              <h2 className="text-xl font-bold">Top clientes por vendas</h2>
              <p className="mt-1 text-sm text-slate-400">Ranking financeiro da base de vendas registrada.</p>
              <div className="mt-5 space-y-3">
                {ranking.length === 0 ? <p className="rounded-2xl border border-dashed border-[#24466f] p-6 text-center text-sm text-slate-400">Nenhuma venda disponível para ranking.</p> : ranking.map((item, index) => <div key={item.cliente} className="flex items-center justify-between gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-4">
                  <div><p className="text-xs text-slate-500">#{index + 1} · {item.vendas} venda{item.vendas === 1 ? "" : "s"}</p><p className="mt-1 font-semibold">{item.cliente}</p></div>
                  <strong className="text-emerald-300">{moeda(item.valor)}</strong>
                </div>)}
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
            <h2 className="text-xl font-bold">Últimas vendas</h2>
            <p className="mt-1 text-sm text-slate-400">Fechamentos mais recentes refletidos no CTI.</p>
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead><tr className="border-b border-[#16325c] text-left text-slate-400"><th className="p-3">Cliente</th><th className="p-3">Equipamento</th><th className="p-3">Data</th><th className="p-3">Valor</th></tr></thead>
                <tbody>{dados.vendas.slice(0, 10).map((venda, index) => <tr key={String(venda.id || index)} className="border-b border-[#13203f]"><td className="p-3 font-semibold">{texto(venda.cliente_nome)}</td><td className="p-3">{texto(venda.equipamento_nome || venda.equipamento_codigo)}</td><td className="p-3">{texto(venda.data_venda)}</td><td className="p-3 font-semibold text-emerald-300">{moeda(venda.valor)}</td></tr>)}</tbody>
              </table>
            </div>
          </section>
        </>}
      </div>
    </section>
  </main>
}

function Kpi({ titulo, valor, detalhe, destaque = false }: { titulo: string; valor: string; detalhe: string; destaque?: boolean }) {
  return <div className={`rounded-2xl border p-5 ${destaque ? "border-emerald-800 bg-emerald-950/20" : "border-[#13203f] bg-[#091a33]"}`}><p className="text-sm text-slate-400">{titulo}</p><p className={`mt-2 text-3xl font-bold ${destaque ? "text-emerald-300" : "text-cyan-300"}`}>{valor}</p><p className="mt-1 text-sm text-slate-300">{detalhe}</p></div>
}

function Indicador({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-2xl font-bold text-cyan-300">{valor}</p></div>
}

function Etapa({ nome, quantidade }: { nome: string; quantidade: number }) {
  return <div className="flex items-center justify-between rounded-xl border border-[#16325c] px-4 py-3"><span className="text-slate-300">{nome}</span><strong>{quantidade}</strong></div>
}
