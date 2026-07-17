"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Oportunidade {
  id: string
  titulo: string
  origem: string
  status: string
  valor_estimado: number
  probabilidade: number
  data_abertura?: string
  created_at: string
}

export default function OportunidadesPage() {
console.log("PAGINA OPORTUNIDADES CARREGADA")

  const [dados, setDados] = useState<Oportunidade[]>([])
  const [loading, setLoading] = useState(true)

  async function carregarOportunidades() {
    try {
      const response = await fetch(
        `${API_URL}/crm/oportunidades`
      )

      const json = await response.json()
      console.log("JSON RECEBIDO:", json)

      setDados(json)
      console.log("SET DADOS EXECUTADO")
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    console.log("INICIANDO CARGA DE OPORTUNIDADES")
    queueMicrotask(() => void carregarOportunidades())
  }, [])

  const valorPipeline = dados.reduce(
   (acc: number, item: Oportunidade) =>
    acc + (item.valor_estimado || 0),
  0
)
  const pipelinePonderado = dados.reduce(
    (acc: number, item: Oportunidade) =>
    acc +
    ((item.valor_estimado || 0) *
      ((item.probabilidade || 0) / 100)),
  0
)

  function formatarData(data?: string) {
    if (!data) return "-"

    return new Date(data).toLocaleDateString("pt-BR")
  }

  function calcularAging(data?: string) {
    if (!data) return "-"

    const abertura = new Date(data)
    const hoje = new Date()

    const diffMs =
      hoje.getTime() - abertura.getTime()

    const dias = Math.max(
      0,
      Math.floor(diffMs / (1000 * 60 * 60 * 24))
    )

    return dias
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <Topbar />

        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white">
              CRM • Oportunidades
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-8">
            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Oportunidades
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {dados.length}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Pipeline Total
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                R$ {valorPipeline.toLocaleString()}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Pipeline Ponderado
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                R$ {pipelinePonderado.toLocaleString()}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Probabilidade Média
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                {dados.length
                  ? Math.round(
                      dados.reduce(
                        (acc, item) =>
                          acc + item.probabilidade,
                        0
                      ) / dados.length
                    )
                  : 0}
                %
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
                Oportunidades Comerciais
              </h2>
            </div>

            {loading ? (
              <div className="p-10 text-gray-400">
                Carregando...
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-[#13203f]">
                    <th className="p-4 text-gray-400">Título</th>
                    <th className="p-4 text-gray-400">Origem</th>
                    <th className="p-4 text-gray-400">Status</th>
                    <th className="p-4 text-gray-400">Valor</th>
                    <th className="p-4 text-gray-400">Probabilidade</th>
                    <th className="p-4 text-gray-400">Abertura</th>
                    <th className="p-4 text-gray-400">Aging</th>
                  </tr>
                </thead>

                <tbody>
                  {dados.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b border-[#13203f]"
                    >
                      <td className="p-4 text-white">
                        {item.titulo}
                      </td>

                      <td className="p-4 text-gray-300">
                        {item.origem}
                      </td>

                      <td className="p-4 text-cyan-400">
                        {item.status}
                      </td>

                      <td className="p-4 text-green-400">
                        R$ {item.valor_estimado}
                      </td>

                      <td className="p-4 text-yellow-400">
                        {item.probabilidade}%
                      </td>

                      <td className="p-4 text-white">
                        {formatarData(item.data_abertura)}
                      </td>

                      <td className="p-4 text-orange-400">
                        {calcularAging(item.data_abertura)} dias
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