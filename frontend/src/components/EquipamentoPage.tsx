"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getEquipamento, type EquipamentoResumo, type RankingItem } from "@/services/modulos-api"

export default function EquipamentoPage({ slug, fallbackTitulo }: { slug: string; fallbackTitulo: string }) {
  const [dados, setDados] = useState<EquipamentoResumo | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true

    getEquipamento(slug)
      .then((resultado) => {
        if (ativo) setDados(resultado)
      })
      .catch(() => {
        if (ativo) setErro("Erro ao carregar dados reais do equipamento.")
      })
      .finally(() => {
        if (ativo) setLoading(false)
      })

    return () => {
      ativo = false
    }
  }, [slug])

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-4xl font-bold text-white">{dados?.nome ?? fallbackTitulo}</h1>
            <p className="text-gray-400 mt-2">Visão operacional baseada nos registros reais persistidos no CTI.</p>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Kpi titulo="Registros" valor={loading ? "..." : String(dados?.total_registros ?? 0)} />
            <Kpi titulo="Valor total" valor={loading ? "..." : `R$ ${(dados?.valor_total ?? 0).toLocaleString("pt-BR")}`} />
            <Kpi titulo="Linhas" valor={loading ? "..." : String(dados?.linhas.length ?? 0)} />
          </div>

          {loading ? (
            <p className="text-gray-400">Carregando dados reais...</p>
          ) : !dados || dados.total_registros === 0 ? (
            <div className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6 text-gray-300">
              Nenhum registro encontrado para este equipamento na base CTI atual.
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <Ranking titulo="Linhas de produto" itens={dados.linhas} />
              <Ranking titulo="Implementadoras" itens={dados.implementadoras} />
              <Ranking titulo="Estados" itens={dados.estados} />
              <Ranking titulo="Empresas" itens={dados.empresas} />
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6">
      <p className="text-gray-400 text-sm">{titulo}</p>
      <p className="text-3xl text-cyan-400 font-bold mt-2">{valor}</p>
    </div>
  )
}

function Ranking({ titulo, itens }: { titulo: string; itens: RankingItem[] }) {
  return (
    <section className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6">
      <h2 className="text-white text-xl font-semibold">{titulo}</h2>
      <div className="mt-4 space-y-3">
        {itens.map((item) => (
          <div key={item.nome} className="flex justify-between gap-4 rounded-xl bg-[#071028] p-4 text-gray-200">
            <span>{item.nome}</span>
            <strong className="text-cyan-400">{item.quantidade_registros}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}
