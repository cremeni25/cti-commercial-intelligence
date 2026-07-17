"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getImplementadorasContextuais } from "@/services/cti-api"

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

function normalizarBusca(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}

export default function ImplementadorasPage() {
  const { contexto, contextoAtual } = useOperationalContext()
  const [implementadoras, setImplementadoras] = useState<ImplementadoraResumo[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")

  useEffect(() => {
    let ativo = true

    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")

      getImplementadorasContextuais(contexto)
      .then((dados) => {
        if (ativo) setImplementadoras(dados)
      })
      .catch(() => {
        if (ativo) setErro("Erro ao carregar implementadoras do contexto operacional ativo.")
      })
      .finally(() => {
        if (ativo) setLoading(false)
      })
    })

    return () => {
      ativo = false
    }
  }, [contexto])

  const lista = useMemo(() => {
    return implementadoras.filter((item) =>
      normalizarBusca([item.nome, ...(item.aliases ?? [])].join(" ")).includes(normalizarBusca(busca))
    )
  }, [implementadoras, busca])

  const valorTotal = implementadoras.reduce((total, item) => total + (item.valor_total ?? 0), 0)

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0">
        <Topbar />
        <div className="p-8 space-y-8 text-white">
          <div>
            <h1 className="text-3xl font-bold">Implementadoras</h1>
            <p className="text-gray-400 mt-2">
              Listagem operacional conforme o Contexto Operacional Global.
            </p>
            <p className="text-cyan-300 text-sm mt-2">
              Contexto ativo: {contextoAtual.label} — {contextoAtual.description}
            </p>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Kpi titulo="Implementadoras" valor={loading ? "..." : implementadoras.length} />
            <Kpi titulo="Registros" valor={loading ? "..." : implementadoras.reduce((total, item) => total + (item.quantidade_registros ?? 0), 0)} />
            <Kpi titulo="Valor total" valor={loading ? "..." : `R$ ${valorTotal.toLocaleString("pt-BR")}`} />
          </section>

          <section className="rounded-2xl bg-[#071226] border border-[#13203f] p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-2xl font-bold">Dados operacionais</h2>
                <p className="text-gray-400">Implementadoras carregadas a partir dos endpoints já existentes de Brasil e Viena SP.</p>
              </div>
              <input
                value={busca}
                onChange={(event) => setBusca(event.target.value)}
                placeholder="Buscar implementadora"
                className="rounded-xl bg-[#0b1730] border border-[#13203f] px-4 py-3 text-white"
              />
            </div>

            {loading ? (
              <p className="text-gray-400 mt-8">Carregando implementadoras...</p>
            ) : lista.length === 0 ? (
              <p className="text-gray-400 mt-8">Nenhuma implementadora encontrada para o contexto ou filtro atual.</p>
            ) : (
              <div className="mt-6 space-y-3">
                {lista.map((item) => (
                  <div key={item.nome} className="rounded-xl border border-[#13203f] bg-[#091a33] p-4">
                    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="font-bold text-white">{item.nome}</p>
                        <p className="text-gray-400 text-sm">{item.aliases?.slice(0, 3).join(", ") || "Sem aliases operacionais"}</p>
                      </div>
                      <p className="text-cyan-400 font-semibold">{item.quantidade_registros ?? 0} registros</p>
                    </div>
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-gray-300">
                      <p>Valor: R$ {(item.valor_total ?? 0).toLocaleString("pt-BR")}</p>
                      <p>Estados: {item.estados?.join(", ") || "-"}</p>
                      <p>Linhas: {item.linhas_produto?.join(", ") || "-"}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) {
  return (
    <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5">
      <p className="text-gray-400 text-sm">{titulo}</p>
      <p className="text-3xl font-bold text-cyan-400 mt-2">{valor}</p>
    </div>
  )
}
