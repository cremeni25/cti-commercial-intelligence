"use client"

import { useEffect, useMemo, useState } from "react"

type DashboardBrasil = { total_registros?: number; total_clientes?: number; total_estados?: number; total_implementadoras?: number }
type ImplementadoraResumo = { nome: string; aliases?: string[]; quantidade_registros?: number; valor_total?: number }
import Link from "next/link"
import { getBrasilDashboard, getBrasilImplementadoras } from "@/services/cti-api"

function normalizarBusca(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}


export default function BrasilPage() {
  const [dashboard, setDashboard] = useState<DashboardBrasil | null>(null)
  const [implementadoras, setImplementadoras] = useState<ImplementadoraResumo[]>([])
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")

  useEffect(() => {
    Promise.all([
      getBrasilDashboard(),
      getBrasilImplementadoras(),
    ])
      .then(([dash, imps]) => {
        setDashboard(dash)
        setImplementadoras(imps)
      })
      .catch(() => setErro("Erro ao carregar dados reais da visão Brasil."))
  }, [])

  const lista = useMemo(() => {
    return implementadoras.filter((item) =>
      normalizarBusca([item.nome, ...(item.aliases ?? [])].join(" ")).includes(normalizarBusca(busca))
    )
  }, [implementadoras, busca])

  return (
    <main className="min-h-screen bg-[#020817] p-8 text-white">
      <Link href="/dashboard" className="text-cyan-400">← Hub CTI</Link>
      <h1 className="text-3xl font-bold mt-6">Brasil</h1>
      <p className="text-gray-400">Visão nacional — origem_base BRASIL.</p>
      {erro && <div className="mt-4 rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
        <Kpi titulo="Registros" valor={dashboard?.total_registros ?? 0} />
        <Kpi titulo="Clientes" valor={dashboard?.total_clientes ?? 0} />
        <Kpi titulo="Estados" valor={dashboard?.total_estados ?? 0} />
        <Kpi titulo="Implementadoras" valor={dashboard?.total_implementadoras ?? 0} />
      </section>
      <section className="mt-8 rounded-2xl bg-[#071226] border border-[#13203f] p-6">
        <h2 className="text-2xl font-bold">Implementadoras Brasil</h2>
        <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar implementadora" className="mt-4 w-full rounded-xl bg-[#0b1730] border border-[#13203f] px-4 py-3" />
        {lista.length === 0 ? <p className="text-gray-400 mt-6">Nenhuma implementadora encontrada na base CTI.</p> : (
          <div className="mt-6 space-y-3">
            {lista.map((item) => <Card key={item.nome} item={item} />)}
          </div>
        )}
      </section>
    </main>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: number }) {
  return <div className="rounded-2xl bg-[#071226] border border-[#13203f] p-5"><p className="text-gray-400">{titulo}</p><p className="text-3xl font-bold text-cyan-400">{valor}</p></div>
}

function Card({ item }: { item: ImplementadoraResumo }) {
  return <div className="rounded-xl border border-[#13203f] p-4"><p className="font-bold">{item.nome}</p><p className="text-gray-400">{item.quantidade_registros} registros • R$ {Number(item.valor_total).toLocaleString("pt-BR")}</p></div>
}
