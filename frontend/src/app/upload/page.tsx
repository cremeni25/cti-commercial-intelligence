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

        setStatusUpload(
            "Selecione um arquivo para iniciar o upload."
        )

        return

    }

    try {
      setLoading(true)
      setResultadoUpload(null)
      setStatusUpload("Selecionando arquivo...")

      const resultado = await uploadArquivo(file)
      console.log(
          "RETORNO UPLOAD:",
          resultado
      )
      setStatusUpload("Validando registros...")

      setResultadoUpload(resultado)
      console.table(resultado)
      setStatusUpload(resultado.status ?? "Upload processado")

      await carregarDados()
      window.dispatchEvent(
        new Event("cti-upload-finalizado")
      )
    } catch (error) {
      console.error(error)
      setStatusUpload(
          "Falha durante o upload."
      )
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

        <div className="mt-4">
            <button
              onClick={() => window.location.href = "/dashboard"}
              className="px-4 py-2 rounded-lg bg-cyan-500 text-black font-semibold hover:bg-cyan-400 transition-colors"
            >
              ← Voltar ao Dashboard
            </button>
        </div>

          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

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

                  <div className="mt-3">

                      <div className="h-2 rounded-full bg-[#13203f]">

                          <div
                              className="h-2 rounded-full bg-cyan-400 transition-all duration-700"
                              style={{
                                  width:
                                      resultadoUpload
                                          ? "100%"
                                          : loading
                                          ? "65%"
                                          : nomeArquivo
                                          ? "20%"
                                          : "0%"
                                }}
                            />

                      </div>

                  </div>

              </div>
              </div>

            </div>

<div className="mt-8 bg-[#071226] border border-[#13203f] rounded-2xl p-6">

    <h2 className="text-white text-2xl font-bold mb-6">
        Painel Oficial do Upload
    </h2>

    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {Object.entries(resultadoUpload?.bases_processadas ?? {}).map(([base, dados]: any) => (
            <div key={base} className="rounded-xl border border-[#13203f] bg-[#091a33] p-4">
                <h3 className="text-cyan-400 font-bold">{base}</h3>
                <p className="text-gray-400 mt-2">Abas: {dados.abas?.join(", ") || "-"}</p>
                <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                    <Info label="Linhas lidas" value={dados.linhas_lidas} />
                    <Info label="Inseridos" value={dados.inseridos} />
                    <Info label="Atualizados" value={dados.atualizados} />
                    <Info label="Duplicados ignorados" value={dados.duplicados_ignorados} />
                    <Info label="Erros" value={dados.erros} />
                </div>
            </div>
        ))}
    </div>

    <div className="mt-6 grid grid-cols-2 xl:grid-cols-4 gap-6">
        <Info label="Arquivo" value={resultadoUpload?.arquivo ?? nomeArquivo ?? "-"} />
        <Info label="Status" value={resultadoUpload?.status ?? statusUpload} />
        <Info label="Inseridos totais" value={resultadoUpload?.persistencia?.inseridos ?? 0} />
        <Info label="Atualizados totais" value={resultadoUpload?.persistencia?.atualizados ?? 0} />
    </div>

</div>
      </div>
    </main>
  )
}

function Info({ label, value }: { label: string; value: any }) {
  return (
    <div>
      <p className="text-gray-400">{label}</p>
      <p className="text-white text-xl">{value ?? "-"}</p>
    </div>
  )
}
