"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import type { EmpresaResumoItem } from "@/services/modulos-api"

function normalizar(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}

export default function ModuloListaPage({
  titulo,
  subtitulo,
  carregar,
}: {
  titulo: string
  subtitulo: string
  carregar: (query: string) => Promise<EmpresaResumoItem[]>
}) {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dados, setDados] = useState<EmpresaResumoItem[]>([])
  const [busca, setBusca] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")
      carregar(queryString)
        .then((resultado) => { if (ativo) setDados(resultado) })
        .catch(() => { if (ativo) setErro("Erro ao carregar dados reais do módulo.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [carregar, queryString])

  const lista = useMemo(() => dados.filter((item) => normalizar(item.nome).includes(normalizar(busca))), [dados, busca])
  const valorTotal = dados.reduce((total, item) => total + (item.valor_total ?? 0), 0)
  const estados = new Set(dados.flatMap((item) => item.estados ?? []))
  const periodoExibido = periodo === "TODO_HISTORICO" ? "Todo o histórico" : periodo === "PERSONALIZADO" ? `${dataInicio || "?"} a ${dataFim || "?"}` : periodo.replaceAll("_", " ")

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-4xl font-bold text-white">{titulo}</h1>
            <p className="text-gray-400 mt-2">{subtitulo}</p>
            <p className="text-cyan-300 text-sm mt-2">Contexto: {contextoAtual.label} • Período: {periodoExibido}</p>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Kpi titulo="Registros" valor={dados.reduce((total, item) => total + item.quantidade_registros, 0).toLocaleString("pt-BR")} />
            <Kpi titulo="Entidades" valor={dados.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Valor total" valor={`R$ ${valorTotal.toLocaleString("pt-BR")}`} />
          </div>

          <section className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div><h2 className="text-2xl font-bold text-white">Dados operacionais</h2><p className="text-gray-400">{estados.size} estados encontrados após os filtros globais.</p></div>
              <input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Buscar empresa" className="rounded-xl bg-[#071028] border border-[#13203f] px-4 py-3 text-white" />
            </div>

            {loading ? <p className="text-gray-400 mt-8">Carregando dados reais...</p> : lista.length === 0 ? <p className="text-gray-400 mt-8">Nenhuma empresa encontrada para o território e período selecionados.</p> : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-left">
                  <thead><tr className="border-b border-[#13203f] text-gray-400"><th className="p-3">Nome</th><th className="p-3">Registros</th><th className="p-3">Valor</th><th className="p-3">Estados</th><th className="p-3">Linhas</th></tr></thead>
                  <tbody>{lista.map((item) => <tr key={item.nome} className="border-b border-[#13203f] text-gray-200"><td className="p-3 font-semibold">{item.nome}</td><td className="p-3">{item.quantidade_registros}</td><td className="p-3">R$ {(item.valor_total ?? 0).toLocaleString("pt-BR")}</td><td className="p-3">{item.estados?.join(", ") || "-"}</td><td className="p-3">{item.linhas?.join(", ") || "-"}</td></tr>)}</tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6"><p className="text-gray-400 text-sm">{titulo}</p><p className="text-3xl text-cyan-400 font-bold mt-2">{valor}</p></div> }
