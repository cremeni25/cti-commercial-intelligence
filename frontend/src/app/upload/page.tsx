"use client"

import { useEffect, useState, useRef } from "react"

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

  const [statusUpload, setStatusUpload] =
    useState("Aguardando arquivo")

  const [resultadoUpload, setResultadoUpload] =
    useState<any>(null)

  const [nomeArquivo, setNomeArquivo] =
    useState("")

  const fileInputRef =
    useRef<HTMLInputElement>(null)

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
      setStatusUpload("Selecionando arquivo...")

      const resultado = await uploadArquivo(file)
      setStatusUpload("Validando registros...")

      setResultadoUpload(resultado)
      setStatusUpload("Upload concluído com sucesso")

      await carregarDados()
      window.dispatchEvent(
        new Event("cti-upload-finalizado")
      )
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
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => {

                  const arquivo =
                      e.target.files?.[0] ?? null

                  setFile(arquivo)

                  setNomeArquivo(
                      arquivo
                          ? arquivo.name
                          : ""
                  )

              }}
              className="hidden"
            />

            <button
                onClick={() => {

                    if (!file) {
                        fileInputRef.current?.click()
                        return
                    }

                    enviarArquivo()

                }}
                disabled={loading}
                className="mt-4 w-full bg-cyan-500 text-black font-bold py-3 rounded-xl"
            >
                {file
                    ? "Iniciar Upload"
                    : "Selecionar Arquivo"}
            </button>

                {nomeArquivo && (

                <div className="mt-4 rounded-xl border border-emerald-500 bg-emerald-500/10 p-4">

                    <p className="text-sm text-emerald-400 font-semibold">
                        Arquivo selecionado
                    </p>

                    <p className="text-white mt-1">
                        {nomeArquivo}
                    </p>

                </div>

                )}

          </div>

          {/* PROCESSAMENTO */}

          <div className="bg-[#071226] border border-[#13203f] rounded-2xl p-6">

              <h2 className="text-white text-xl font-bold mb-4">
                  Status Operacional
              </h2>

              <div className="space-y-4">

                  <div className="w-full h-3 rounded-full bg-[#13203f] overflow-hidden">

                      <div
                          className="h-full bg-emerald-400 transition-all duration-700"
                          style={{
                              width:
                                  loading
                                      ? "70%"
                                      : resultadoUpload
                                      ? "100%"
                                      : "0%"
                            }}
                        />

                  </div>

                  <p className="text-white">
                      {statusUpload}
                  </p>

              </div>
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
                  Cliente
                </th>

                <th className="text-left p-3 text-cyan-400">
                  Implementadora
                </th>

                <th className="text-left p-3 text-cyan-400">
                  Linha
                </th>

                <th className="text-left p-3 text-cyan-400">
                  Modelo
                </th>

                <th className="text-left p-3 text-cyan-400">
                  UF
                </th>

                <th className="text-left p-3 text-cyan-400">
                  Valor
                </th>

                <th className="text-left p-3 text-cyan-400">
                  Score
                </th>

                </tr>
              </thead>

              <tbody>
                {auditoria.map((item, index) => (
                    <tr
                      key={index}
                      className="border-b border-[#13203f]"
                    >
                      <td className="p-3 text-white">
                          {item.cliente ?? "-"}
                      </td>

                      <td className="p-3 text-white">
                          {item.implementador ?? "-"}
                      </td>

                      <td className="p-3 text-white">
                          {item.linha ?? "-"}
                      </td>

                      <td className="p-3 text-white">
                          {item.modelo ?? "-"}
                      </td>

                      <td className="p-3 text-white">
                          {item.estado ?? "-"}
                      </td>

                      <td className="p-3 text-cyan-400">
                          {item.valor
                            ? Number(item.valor).toLocaleString(
                                "pt-BR",
                                {
                                  style: "currency",
                                  currency: "BRL",
                                }
                              )
                            : "-"}
                        </td>

                        <td className="p-3 text-emerald-400 font-bold">
                          {item.score_operacional ?? "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
            </table>
          </div>
        </div>

{
  resultadoUpload && (

    <div className="mt-8 bg-[#071226] border border-[#13203f] rounded-2xl p-6">

      <h2 className="text-2xl font-bold text-white mb-6">
        Resultado do Upload
      </h2>

      <div className="grid grid-cols-2 gap-4">

        <div>
          <p className="text-gray-400">Recebidos</p>
          <p className="text-cyan-400 text-xl">
            {resultadoUpload.recebidos ?? "-"}
          </p>
        </div>

        <div>
          <p className="text-gray-400">Válidos</p>
          <p className="text-cyan-400 text-xl">
            {resultadoUpload.validos ?? "-"}
          </p>
        </div>

        <div>
          <p className="text-gray-400">Inseridos</p>
          <p className="text-emerald-400 text-xl">
            {resultadoUpload.inseridos ?? "-"}
          </p>
        </div>

        <div>
          <p className="text-gray-400">Duplicados</p>
          <p className="text-yellow-400 text-xl">
            {resultadoUpload.duplicados_lote ?? "-"}
          </p>
        </div>

        <div>
          <p className="text-gray-400">Tempo</p>
          <p className="text-white text-xl">
            {resultadoUpload.tempo_execucao ?? "-"} s
          </p>
        </div>

        <div>
          <p className="text-gray-400">Status</p>
          <p className="text-emerald-400 text-xl">
            {resultadoUpload.status}
          </p>
        </div>

      </div>

    </div>

  )
}

      </div>
    </main>
  )
}