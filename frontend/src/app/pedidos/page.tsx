"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Pedido {
  id: string
  cliente: string
  pedido_numero: string
  valor: number
  status: string
  data_pedido: string
  responsavel: string
 }

export default function PedidosPage() {
  const [dados, setDados] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(true)

  async function carregarPedidos() {
    try {
      const response = await fetch(
        `${API_URL}/crm/pedidos`
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
    carregarPedidos()
  }, [])

  const valorTotal = dados.reduce(
    (acc, item) => acc + (item.valor || 0),
    0
  )

  const emProducao = dados.filter(
    (item) => item.status === "EM_PRODUCAO"
  ).length

  const faturados = dados.filter(
    (item) => item.status === "FATURADO"
  ).length

  const entregues = dados.filter(
    (item) => item.status === "ENTREGUE"
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
              CRM • Pedidos
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Total Pedidos
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
                Em Produção 
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                {emProducao}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Faturados
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {faturados}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Entregues
              </p>

              <h2 className="text-3xl text-red-400 font-bold mt-2">
                {entregues}
              </h2>
            </div>
          </div>

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">
            <div className="p-6 border-b border-[#13203f]">
              <h2 className="text-white text-xl font-semibold">
                Gestão de Pedidos
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
                      Pedido
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Valor
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Status
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Data
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
                        {item.cliente}
                      </td>

                      <td className="p-4 text-white">
                        {item.pedido_numero}
                      </td>

                      <td className="p-4 text-green-400">
                        R$ {item.valor.toLocaleString("pt-BR")}
                      </td>

                      <td className="p-4 text-cyan-400">
                        {item.status}
                      </td>

                      <td className="p-4 text-white">
                        {formatarData(item.data_pedido)}
                      </td>

                      <td className="p-4 text-gray-300">
                        {item.responsavel}
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