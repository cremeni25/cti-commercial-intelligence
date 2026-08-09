"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getImplementadorasContextuais } from "@/services/cti-api"
import { API_URL } from "@/lib/api"

type ImplementadoraResumo = {
  nome: string
  aliases?: string[]
  quantidade_registros?: number
  valor_total?: number
  estados?: string[]
  municipios?: string[]
  clientes?: number
  linhas_produto?: string[]
}

type Venda = {
  id?: string
  pedido_id?: string
  pedido_numero?: string
  implementadora_id?: string | number
  implementadora_nome?: string
  equipamento_codigo?: string
  equipamento_nome?: string
  valor?: number
}

type Pedido = {
  id?: string
  numero?: string
  status?: string
  status_ciclo?: string
  valor?: number
}

function normalizar(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim()
}

function moeda(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

async function buscarJson<T>(endpoint: string): Promise<T> {
  const resposta = await fetch(`${API_URL}${endpoint}`, { cache: "no-store" })
  if (!resposta.ok) throw new Error(`${resposta.status}`)
  return resposta.json() as Promise<T>
}

export default function ImplementadorasPage() {
  const { contexto, contextoAtual } = useOperationalContext()
  const [implementadoras, setImplementadoras] = useState<ImplementadoraResumo[]>([])
  const [vendas, setVendas] = useState<Venda[]>([])
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      setLoading(true)
      setErro("")
      try {
        const [historico, vendasAtuais, pedidosAtuais] = await Promise.all([
          getImplementadorasContextuais(contexto),
          buscarJson<Venda[]>("/vendas"),
          buscarJson<Pedido[]>("/crm/pedidos"),
        ])
        if (!ativo) return
        setImplementadoras(historico)
        setVendas(Array.isArray(vendasAtuais) ? vendasAtuais : [])
        setPedidos(Array.isArray(pedidosAtuais) ? pedidosAtuais : [])
      } catch {
        if (ativo) setErro("Erro ao carregar a leitura temporal de implementadoras.")
      } finally {
        if (ativo) setLoading(false)
      }
    })
    return () => { ativo = false }
  }, [contexto])

  const pedidosPorId = useMemo(() => new Map(pedidos.map((item) => [String(item.id || ""), item])), [pedidos])

  const ciclosEmCurso = useMemo(() => vendas.filter((venda) => {
    if (!venda.pedido_id) return false
    const pedido = pedidosPorId.get(String(venda.pedido_id))
    if (!pedido) return false
    return String(pedido.status_ciclo || pedido.status || "").toUpperCase() !== "ENCERRADO"
  }), [pedidosPorId, vendas])

  const emCursoPorImplementadora = useMemo(() => {
    const mapa = new Map<string, { quantidade: number; valor: number; equipamentos: string[] }>()
    ciclosEmCurso.forEach((venda) => {
      if (!venda.implementadora_nome) return
      const chave = normalizar(venda.implementadora_nome)
      const atual = mapa.get(chave) || { quantidade: 0, valor: 0, equipamentos: [] }
      atual.quantidade += 1
      atual.valor += Number(venda.valor || 0)
      const equipamento = venda.equipamento_nome || venda.equipamento_codigo
      if (equipamento && !atual.equipamentos.includes(equipamento)) atual.equipamentos.push(equipamento)
      mapa.set(chave, atual)
    })
    return mapa
  }, [ciclosEmCurso])

  const semImplementadora = useMemo(() => ciclosEmCurso.filter((item) => !item.implementadora_nome), [ciclosEmCurso])
  const valorSemImplementadora = semImplementadora.reduce((total, item) => total + Number(item.valor || 0), 0)
  const valorHistorico = implementadoras.reduce((total, item) => total + Number(item.valor_total || 0), 0)
  const registrosHistoricos = implementadoras.reduce((total, item) => total + Number(item.quantidade_registros || 0), 0)
  const implementadorasComCiclo = new Set(ciclosEmCurso.map((item) => item.implementadora_nome).filter(Boolean)).size

  const lista = useMemo(() => implementadoras.filter((item) =>
    normalizar([item.nome, ...(item.aliases ?? []), ...(item.estados ?? []), ...(item.linhas_produto ?? [])].join(" ")).includes(normalizar(busca))
  ), [busca, implementadoras])

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura temporal por implementadora</p>
            <h1 className="mt-2 text-3xl font-bold">Implementadoras</h1>
            <p className="mt-2 text-sm text-slate-400">Histórico confirmado e vínculos reais do ciclo comercial atual, sem atribuições presumidas.</p>
            <p className="mt-2 text-sm text-cyan-300">Contexto ativo: {contextoAtual.label} — {contextoAtual.description}</p>
          </header>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid gap-5 xl:grid-cols-2">
            <PainelTempo titulo="REALIZADO" subtitulo="O que as implementadoras já representaram." destaque="Histórico confirmado">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Implementadoras históricas" valor={loading ? "..." : implementadoras.length.toLocaleString("pt-BR")} />
                <Kpi titulo="Registros históricos" valor={loading ? "..." : registrosHistoricos.toLocaleString("pt-BR")} />
                <Kpi titulo="Clientes relacionados" valor={loading ? "..." : implementadoras.reduce((s, i) => s + Number(i.clientes || 0), 0).toLocaleString("pt-BR")} />
                <Kpi titulo="Valor registrado na base" valor={loading ? "..." : moeda(valorHistorico)} />
              </div>
            </PainelTempo>

            <PainelTempo titulo="EM CURSO" subtitulo="O que está operacionalmente vinculado agora." destaque="Ciclo atual">
              <div className="grid gap-3 sm:grid-cols-2">
                <Kpi titulo="Implementadoras definidas" valor={loading ? "..." : implementadorasComCiclo.toLocaleString("pt-BR")} />
                <Kpi titulo="Pedidos/ciclos em curso" valor={loading ? "..." : ciclosEmCurso.length.toLocaleString("pt-BR")} />
                <Kpi titulo="Aguardando implementadora" valor={loading ? "..." : semImplementadora.length.toLocaleString("pt-BR")} />
                <Kpi titulo="Valor aguardando definição" valor={loading ? "..." : moeda(valorSemImplementadora)} />
              </div>
              {!loading && semImplementadora.length > 0 && (
                <div className="mt-4 rounded-xl border border-amber-700/70 bg-amber-950/20 p-4 text-sm text-amber-200">
                  Existem {semImplementadora.length} ciclo(s) comercial(is), totalizando {moeda(valorSemImplementadora)}, ainda sem implementadora vinculada no dado canônico. O CTI sinaliza a pendência; não atribui uma empresa por inferência.
                </div>
              )}
            </PainelTempo>
          </section>

          <section className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5 sm:p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-xl font-bold">Implementadoras — histórico e situação atual</h2>
                <p className="mt-1 text-sm text-slate-400">Cada linha confronta presença histórica com vínculos operacionais realmente existentes hoje.</p>
              </div>
              <input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Buscar implementadora, estado ou linha" className="rounded-xl border border-[#13203f] bg-[#071028] px-4 py-3 text-white" />
            </div>

            {loading ? <p className="mt-8 text-slate-400">Carregando dados reais...</p> : lista.length === 0 ? <p className="mt-8 text-slate-400">Nenhuma implementadora encontrada.</p> : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead><tr className="border-b border-[#13203f] text-slate-400"><th className="p-3">Implementadora</th><th className="p-3">REALIZADO</th><th className="p-3">EM CURSO</th><th className="p-3">Linhas</th></tr></thead>
                  <tbody>{lista.map((item) => {
                    const atual = emCursoPorImplementadora.get(normalizar(item.nome))
                    return <tr key={item.nome} className="border-b border-[#13203f] align-top text-slate-200 hover:bg-cyan-500/5">
                      <td className="p-3"><p className="font-semibold text-white">{item.nome}</p><p className="text-xs text-slate-500">{item.aliases?.slice(0, 3).join(", ") || "Sem aliases operacionais"}</p></td>
                      <td className="p-3"><p>{item.quantidade_registros ?? 0} registros</p><p className="text-xs text-slate-500">{moeda(Number(item.valor_total || 0))} na base • {item.estados?.join(", ") || "-"}</p></td>
                      <td className="p-3">{atual ? <><p>{atual.quantidade} ciclo(s)</p><p className="text-xs text-emerald-300">{moeda(atual.valor)} • {atual.equipamentos.join(", ") || "Equipamento não identificado"}</p></> : <><p>0 ciclos vinculados</p><p className="text-xs text-slate-500">Sem vínculo operacional atual</p></>}</td>
                      <td className="p-3">{item.linhas_produto?.join(", ") || "-"}</td>
                    </tr>
                  })}</tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}

function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: React.ReactNode }) {
  return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h3 className="mt-1 text-xl font-bold text-white">{subtitulo}</h3></div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-xl font-bold text-cyan-300">{valor}</p></div>
}
