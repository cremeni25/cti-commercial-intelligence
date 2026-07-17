"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Atividade {
  id: string
  titulo: string
  tipo: string
  cliente: string
  responsavel: string
  status: string
  vencimento: string
}

export default function AtividadesPage() {
console.log("PAGINA ATIVIDADES CARREGADA")

  const [dados, setDados] = useState<Atividade[]>([])
  const [loading, setLoading] = useState(true)

  async function carregarAtividades() {
    try {
      const response = await fetch(
        `${API_URL}/crm/atividades`
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
    console.log("INICIANDO CARGA DE ATIVIDADES")
    queueMicrotask(() => void carregarAtividades())
  }, [])

  const aFazer = dados.filter(
    item => item.status === "A_FAZER"
  ).length

  const emAndamento = dados.filter(
    item => item.status === "EM_ANDAMENTO"
  ).length

  const concluidas = dados.filter(
    item => item.status === "CONCLUIDA"
  ).length

  const atrasadas = dados.filter(
    item => item.status === "ATRASADA"
  ).length

  function formatarData(data?: string) {
    if (!data) return "-"

    return new Date(data).toLocaleDateString("pt-BR")
  }

    return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <Topbar />

        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white">
              CRM • Atividades
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-8">
            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Total Atividades
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {dados.length}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                A Fazer
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {aFazer}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Em Andamento
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {emAndamento}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Concluidas
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                {concluidas}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Atrasadas
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {atrasadas}
              </h2>
            </div>
          </div>

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">
            <div className="p-6 border-b border-[#13203f]">
              <h2 className="text-white text-xl font-semibold">
                Atividades Comerciais
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
                    <th className="p-4 text-gray-400">Tipo</th>
                    <th className="p-4 text-gray-400">Cliente</th>
                    <th className="p-4 text-gray-400">Responsável</th>
                    <th className="p-4 text-gray-400">Status</th>
                    <th className="p-4 text-gray-400">Vencimento</th>
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
                        {item.tipo}
                      </td>

                      <td className="p-4 text-white">
                        {item.cliente}
                      </td>

                      <td className="p-4 text-gray-300">
                        {item.responsavel}
                      </td>

                      <td className="p-4 text-cyan-400">
                        {item.status}
                      </td>

                      <td className="p-4 text-yellow-400">
                        {formatarData(item.vencimento)}
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