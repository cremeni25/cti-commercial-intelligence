"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Forecast {
  id: string
  vendedor: string
  carteira: string
  pipeline_total: number
  pipeline_ponderado: number
  meta: number
}

export default function ForecastPage() {
  const [dados, setDados] = useState<Forecast[]>([])
  const [loading, setLoading] = useState(true)

  async function carregarForecast() {
    try {
      const response = await fetch(
        `${API_URL}/crm/forecast`
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
    carregarForecast()
  }, [])

  const pipelineTotal = dados.reduce(
    (acc, item) => acc + item.pipeline_total,
    0
  )

  const pipelinePonderado = dados.reduce(
    (acc, item) => acc + item.pipeline_ponderado,
    0
  )

  const metaTotal = dados.reduce(
    (acc, item) => acc + item.meta,
    0
  )

  const atingimento =
    metaTotal > 0
      ? Math.round(
          (pipelinePonderado / metaTotal) * 100
        )
      : 0

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <Topbar />

        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white">
              CRM • Forecast Comercial
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-8">

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Pipeline Total
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                R$ {pipelineTotal.toLocaleString("pt-BR")}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Pipeline Ponderado
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                R$ {pipelinePonderado.toLocaleString("pt-BR")}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Meta Comercial
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                R$ {metaTotal.toLocaleString("pt-BR")}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Atingimento
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {atingimento}%
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Backend CRM
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                ONLINE
              </h2>
            </div>

          </div>

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">

            <div className="p-6 border-b border-[#13203f]">
              <h2 className="text-white text-xl font-semibold">
                Forecast Comercial
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
                      Vendedor
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Carteira
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Pipeline
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Ponderado
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Meta
                    </th>

                    <th className="p-4 text-left text-gray-400">
                      Atingimento
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {dados.map((item) => {

                    const atingimentoLinha =
                      item.meta > 0
                        ? Math.round(
                            (item.pipeline_ponderado /
                              item.meta) *
                              100
                          )
                        : 0

                    return (
                      <tr
                        key={item.id}
                        className="border-b border-[#13203f]"
                      >
                        <td className="p-4 text-white">
                          {item.vendedor}
                        </td>

                        <td className="p-4 text-white">
                          {item.carteira}
                        </td>

                        <td className="p-4 text-cyan-400">
                          R$ {item.pipeline_total.toLocaleString("pt-BR")}
                        </td>

                        <td className="p-4 text-green-400">
                          R$ {item.pipeline_ponderado.toLocaleString("pt-BR")}
                        </td>

                        <td className="p-4 text-yellow-400">
                          R$ {item.meta.toLocaleString("pt-BR")}
                        </td>

                        <td className="p-4 text-white">
                          {atingimentoLinha}%
                        </td>
                      </tr>
                    )
                  })}
                </tbody>

              </table>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}