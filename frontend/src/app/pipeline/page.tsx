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

  useEffect(() => {
    console.log("INICIANDO CARGA DE PIPELINE")
    queueMicrotask(() => void carregarPipeline())
  }, [])

      const prospeccao = dados.filter(
      (item) => item.etapa === "OPORTUNIDADE"
    ).length

    const negociacao = dados.filter(
      (item) => item.etapa === "NEGOCIACAO"
    ).length

    const ganhos = dados.filter(
      (item) => item.etapa === "GANHO"
    ).length

    const perdidos = dados.filter(
      (item) => item.etapa === "PERDIDO"
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
                Oportunidade
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

          <div className="mb-6 rounded-2xl border border-[#13203f] bg-[#071226] p-5 text-sm text-gray-300">
            <h2 className="text-white font-semibold mb-2">Contexto dos indicadores</h2>
            <p><strong>Origem dos indicadores:</strong> CRM Operacional. <strong>Período considerado:</strong> movimentações cadastradas no pipeline do CRM. <strong>Significado operacional:</strong> histórico de avanço das oportunidades por etapa. <strong>Critério de cálculo:</strong> contagem das movimentações reais por etapa. <strong>Finalidade operacional:</strong> acompanhar a evolução do fluxo Oportunidade → Atividades → Proposta → Negociação → Pedido → Conclusão → Inteligência.</p>
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
) : dados.length === 0 ? (
  <div className="p-10 text-gray-300 space-y-4">
    <p>Nenhuma movimentação de pipeline cadastrada. Cada oportunidade deve gerar a primeira movimentação automaticamente, preservando etapa anterior, nova etapa, data, hora, usuário e observações.</p>
    <div className="flex flex-wrap gap-3">
      <a href="/oportunidades?novo=1" className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950">Nova oportunidade</a>
      <a href="/atividades?novo=1" className="rounded-xl border border-cyan-500 px-4 py-2 text-sm font-semibold text-cyan-300">Nova atividade</a>
      <a href="/propostas?novo=1" className="rounded-xl border border-cyan-500 px-4 py-2 text-sm font-semibold text-cyan-300">Nova proposta</a>
    </div>
  </div>
) : (
  <div className="grid grid-cols-6 gap-4 p-6 overflow-x-auto min-h-[600px]">

    {/* OPORTUNIDADE */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-cyan-400 font-bold">
          OPORTUNIDADE
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "OPORTUNIDADE")
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

    {/* ATIVIDADES */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-blue-400 font-bold">
          ATIVIDADES
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "ATIVIDADES")
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

    {/* GANHO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-green-400 font-bold">
          GANHO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "GANHO")
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

    {/* PERDIDO */}
    <div className="bg-[#071028] rounded-xl border border-[#13203f]">
      <div className="p-4 border-b border-[#13203f]">
        <h3 className="text-red-400 font-bold">
          PERDIDO
        </h3>
      </div>

      <div className="p-3 space-y-3">
        {dados
          .filter(item => item.etapa === "PERDIDO")
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