"use client"

import { useEffect, useState } from "react"

import {
  uploadArquivo,
  processarPipeline,
  getDebugAmostra,
  getPipelineStatus,
} from "@/services/cti-api"

export default function UploadPage() {
  const [file, setFile] =
    useState<File | null>(null)

  const [status, setStatus] =
    useState<any>(null)

  const [auditoria, setAuditoria] =
    useState<any[]>([])

  const [loading, setLoading] =
    useState(false)

  async function carregarDados() {
    try {
      const pipeline =
        await getPipelineStatus()

      setStatus(pipeline)

      const amostra =
        await getDebugAmostra()

      setAuditoria(amostra)
    } catch (error) {
      console.error(error)
    }
  }

  async function enviarArquivo() {
    if (!file) {
      alert("Selecione um arquivo")
      return
    }

    try {
      setLoading(true)

      const resultado =
        await uploadArquivo(file)

      alert(
        `Upload concluído. ${resultado.linhas_extraidas} linhas encontradas.`
      )

      await carregarDados()
    } catch (error) {
      console.error(error)
      alert("Erro no upload")
    } finally {
      setLoading(false)
    }
  }

  async function executarPipeline() {
    try {
      setLoading(true)

      const resultado =
        await processarPipeline()

      console.log(resultado)

      alert("Pipeline executado")

      await carregarDados()
    } catch (error) {
      console.error(error)
      alert("Erro ao processar")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    carregarDados()
  }, [])

  return (
    <main className="min-h-screen bg-[#020817] p-8">
      <div className="max-w-7xl mx-auto">

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white">
            Upload Operacional CTI
          </h1>

          <p className="text-gray-400 mt-2">
            Ingestão, processamento e auditoria operacional
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* PIPELINE */}

          <div className="bg-[#071226] border border-[#13203f] rounded-2xl p-6">
            <h2 className="text-white text-xl font-bold mb-4">
              Pipeline
            </h2>

            <div className="space-y-3">
              <p className="text-gray-300">
                Linhas Brutas:
                {" "}
                <span className="text-cyan-400">
                  {status?.linhas_brutas ?? 0}
                </span>
              </p>

              <p className="text-gray-300">
                Processadas:
                {" "}
                <span className="text-cyan-400">
                  {status?.linhas_processadas ?? 0}
                </span>
              </p>

              <p className="text-gray-300">
                Status:
                {" "}
                <span className="text-emerald-400">
                  {status?.pipeline ?? "-"}
                </span>
              </p>
            </div>
          </div>

          {/* UPLOAD */}

          <div className="bg-[#071226] border border-[#13203f] rounded-2xl p-6">
            <h2 className="text-white text-xl font-bold mb-4">
              Upload
            </h2>

            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) =>
                setFile(
                  e.target.files?.[0] ?? null
                )
              }
              className="w-full text-white"
            />

            <button
              onClick={enviarArquivo}
              disabled={loading}
              className="mt-4 w-full bg-cyan-500 text-black font-bold py-3 rounded-xl"
            >
              Enviar Arquivo
            </button>
          </div>

          {/* PROCESSAMENTO */}

          <div className="bg-[#071226] border border-[#13203f] rounded-2xl p-6">
            <h2 className="text-white text-xl font-bold mb-4">
              Processamento
            </h2>

            <button
              onClick={executarPipeline}
              disabled={loading}
              className="w-full bg-emerald-500 text-black font-bold py-3 rounded-xl"
            >
              Executar Pipeline
            </button>
          </div>

        </div>

        {/* AUDITORIA */}

        <div className="mt-8 bg-[#071226] border border-[#13203f] rounded-2xl p-6">
          <h2 className="text-white text-2xl font-bold mb-6">
            Auditoria Operacional
          </h2>

          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#13203f]">
                  <th className="text-left p-3 text-cyan-400">
                    Produto
                  </th>

                  <th className="text-left p-3 text-cyan-400">
                    Fabricante
                  </th>

                  <th className="text-left p-3 text-cyan-400">
                    Status
                  </th>

                  <th className="text-left p-3 text-cyan-400">
                    Score
                  </th>
                </tr>
              </thead>

              <tbody>
                {auditoria.map(
                  (item, index) => (
                    <tr
                      key={index}
                      className="border-b border-[#13203f]"
                    >
                      <td className="p-3 text-white">
                        {item.produto}
                      </td>

                      <td className="p-3 text-white">
                        {
                          item.fabricante_equipamento
                        }
                      </td>

                      <td className="p-3 text-white">
                        {item.status}
                      </td>

                      <td className="p-3 text-cyan-400 font-bold">
                        {item.score_geral}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  )
}