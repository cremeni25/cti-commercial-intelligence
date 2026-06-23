"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Pipeline {
  id: string
  oportunidade_id: string
  etapa: string
  usuario_id: string
  observacao?: string
  created_at?: string
}

export default function PipelinePage() {
console.log("PAGINA PIPELINE CARREGADA")

  const [dados, setDados] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(true)
  const [modalAberto, setModalAberto] = useState(false)

  async function carregarPipeline() {
    try {
      const response = await fetch(
        `${API_URL}/crm/pipeline`
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

  async function salvarPipeline() {
    
  }

  useEffect(() => {
    console.log("INICIANDO CARGA DE PIPELINE")
    carregarPipeline()
  }, [])

      const prospeccao = dados.filter(
      (item) => item.etapa === "PROSPECCAO"
    ).length

    const negociacao = dados.filter(
      (item) => item.etapa === "NEGOCIACAO"
    ).length

    const ganhos = dados.filter(
      (item) => item.etapa === "FECHADO_GANHO"
    ).length

    const perdidos = dados.filter(
      (item) => item.etapa === "FECHADO_PERDIDO"
    ).length
  
  function formatarData(data?: string) {
    if (!data) return "-"

    return new Date(data).toLocaleDateString("pt-BR")
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <div className="relative">
          <Topbar />

          <button
            onClick={() => setModalAberto(true)}
            className="absolute right-56 top-5 bg-cyan-500 hover:bg-cyan-400 transition-all px-6 py-3 rounded-xl font-semibold text-black"
          >
            Novo Registro Pipeline
          </button>
        </div>

        {modalAberto && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-[#091a33] border border-[#13203f] rounded-2xl p-8 w-[600px]">
              <h2 className="text-2xl font-bold text-white mb-6">
                Novo Item do Pipeline
              </h2>

              <div className="space-y-4">
                <input
                  id="oportunidade_id"
                  placeholder="Oportunidade ID"
                  className="w-full p-3 rounded-xl bg-[#071028] border border-[#13203f] text-white"
                />

                <input
                  id="etapa"
                  placeholder="Etapa"
                  className="w-full p-3 rounded-xl bg-[#071028] border border-[#13203f] text-white"
                />

                <textarea
                  id="observacao"
                  placeholder="Observação"
                  className="w-full p-3 rounded-xl bg-[#071028] border border-[#13203f] text-white"
                />
              </div>

              <div className="flex justify-end gap-3 mt-8">
                <button
                  onClick={() => setModalAberto(false)}
                  className="px-5 py-3 rounded-xl bg-gray-600 text-white"
                >
                  Cancelar
                </button>

                <button
                  onClick={salvarPipeline}
                  className="px-5 py-3 rounded-xl bg-cyan-500 text-black font-semibold"
                >
                  Salvar
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white">
              CRM • Pipeline
            </h1>

            <p className="text-gray-400 mt-2">
              VIENA SP + CARRIER
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-8">
            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Total Pipeline
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {dados.length}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Prospecção
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {prospeccao.toLocaleString()}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Negociação
              </p>

              <h2 className="text-3xl text-cyan-400 font-bold mt-2">
                {negociacao.toLocaleString()}
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Ganhos
              </p>

              <h2 className="text-3xl text-yellow-400 font-bold mt-2">
                {ganhos}
                        
              </h2>
            </div>

            <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]">
              <p className="text-gray-400 text-sm">
                Perdidos
              </p>

              <h2 className="text-3xl text-green-400 font-bold mt-2">
                {perdidos}
              </h2>
            </div>
          </div>

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">
            <div className="p-6 border-b border-[#13203f]">
              <h2 className="text-white text-xl font-semibold">
                Pipeline Comercial
              </h2>
            </div>

            {loading ? (
  <div className="p-10 text-gray-400">
    Carregando...
  </div>
) : (
  <div className="grid grid-cols-6 gap-4 p-6 overflow-x-auto min-h-[600px]">

    {/* PROSPECÇÃO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-cyan-400 font-bold">
          PROSPECÇÃO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "PROSPECCAO")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-cyan-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

    {/* QUALIFICAÇÃO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-blue-400 font-bold">
          QUALIFICAÇÃO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "QUALIFICACAO")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-blue-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

    {/* PROPOSTA */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-yellow-400 font-bold">
          PROPOSTA
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "PROPOSTA")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-yellow-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

    {/* NEGOCIAÇÃO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-orange-400 font-bold">
          NEGOCIAÇÃO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "NEGOCIACAO")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-orange-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

    {/* FECHADO GANHO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-green-400 font-bold">
          FECHADO GANHO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "FECHADO_GANHO")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-green-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

    {/* FECHADO PERDIDO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-red-400 font-bold">
          FECHADO PERDIDO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "FECHADO_PERDIDO")
          .map(item => (
            <div
              key={item.id}
              className="bg-[#091a33] border border-[#13203f] rounded-xl p-3"
            >
              <div className="text-white text-sm font-semibold">
                {item.oportunidade_id}
              </div>

              <div className="text-xs text-gray-400 mt-2">
                {item.usuario_id}
              </div>

              <div className="text-xs text-red-400 mt-2">
                {formatarData(item.created_at)}
              </div>
            </div>
          ))}
      </div>
    </div>

  </div>
)}

          </div>
        </div>
      </section>
    </main>
  )
}