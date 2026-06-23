"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Proposta {
  id: string
  cliente_id: string
  titulo: string
  valor: number
  status: string
  validade?: string
  responsavel_id?: string
  created_at?: string
}

export default function PropostasPage() {
  const [dados, setDados] = useState<Proposta[]>([])
  const [loading, setLoading] = useState(true)

  async function carregarPropostas() {
    try {
      const response = await fetch(
        `${API_URL}/crm/propostas`
      )

      const json = await response.json()

      setDados(json)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    carregarPropostas()
  }, [])

  const valorTotal = dados.reduce(
    (acc, item) => acc + (item.valor || 0),
    0
  )

  const emAnalise = dados.filter(
    (item) => item.status === "EM_ANALISE"
  ).length

  const aprovadas = dados.filter(
    (item) => item.status === "APROVADA"
  ).length

  const rejeitadas = dados.filter(
    (item) => item.status === "REJEITADA"
  ).length

  function formatarData(data?: string) {
    if (!data) return "-"

    return new Date(data).toLocaleDateString(
      "pt-BR"
    )
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <Topbar />

        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white">
              CRM • Propostas
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-8">
            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Total Propostas
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {dados.length}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Valor Total
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                R$ {valorTotal.toLocaleString()}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Em Análise
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                {emAnalise}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Aprovadas
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {aprovadas}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Rejeitadas
              </p>

              <h2 className="text-3xl text-red-400 font-bold mt-2">
                {rejeitadas}
              </h2>
            </div>
          </div>

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">
            <div className="p-6 border-b border-[#13203f]">
              <h2 className="text-white text-xl font-semibold">
                Propostas Comerciais
              </h2>
            </div>

            {loading ? (
              <div className="p-10 text-gray-400">
                Carregando...
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#13203f]">
                    <th className="p-4 text-left text-gray-400">
                      Cliente
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Proposta
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Valor
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Status
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Validade
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Responsável
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {dados.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b border-[#13203f]"
                    >
                      <td className="p-4 text-white">
                        {item.cliente_id}
                      </td>

                      <td className="p-4 text-white">
                        {item.titulo}
                      </td>

                      <td className="p-4 text-green-400">
                        R$ {item.valor}
                      </td>

                      <td className="p-4 text-cyan-400">
                        {item.status}
                      </td>

                      <td className="p-4 text-white">
                        {formatarData(item.validade)}
                      </td>

                      <td className="p-4 text-gray-300">
                        {item.responsavel_id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}