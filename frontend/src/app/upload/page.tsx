"use client"

import { useEffect, useRef, useState } from "react"
import { useOperationalContext } from "@/context/OperationalContext"
import { getDebugAmostra, getPipelineStatus, importarDados } from "@/services/cti-api"

type BaseProcessada = {
  abas?: string[]
  linhas_lidas?: number
  registros_validos?: number
  inseridos?: number
  atualizados?: number
  duplicados_ignorados?: number
  erros?: number
  erros_por_tipo?: Record<string, number>
  amostra_erros?: Array<{ linha?: number; etapa?: string; tipo?: string; mensagem?: string }>
}

type ResultadoAnfir = {
  arquivo?: string
  status?: string
  contexto_operacional?: string
  bases_processadas?: Record<string, BaseProcessada>
  persistencia?: { inseridos?: number; atualizados?: number }
}

type ResultadoGovernanca = {
  duplicado?: boolean
  fonte?: {
    id?: string
    nome_arquivo?: string
    status_governanca?: string
    tipo_detectado?: string
  }
  mensagem?: string
}

export default function UploadPage() {
  const { contexto, contextoAtual } = useOperationalContext()
  const [file, setFile] = useState<File | null>(null)
  const [, setStatus] = useState<Record<string, unknown> | null>(null)
  const [, setAuditoria] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(false)
  const [statusUpload, setStatusUpload] = useState("Selecione um arquivo para importar.")
  const [resultadoAnfir, setResultadoAnfir] = useState<ResultadoAnfir | null>(null)
  const [resultadoGovernanca, setResultadoGovernanca] = useState<ResultadoGovernanca | null>(null)
  const [nomeArquivo, setNomeArquivo] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function carregarDados() {
    try {
      setStatus(await getPipelineStatus())
      setAuditoria(await getDebugAmostra())
    } catch (error) {
      console.error(error)
    }
  }

  async function enviarArquivo(arquivoSelecionado?: File) {
    const arquivoAtual = arquivoSelecionado ?? file
    if (!arquivoAtual) {
      setStatusUpload("Selecione um arquivo para iniciar a importação.")
      return
    }

    try {
      setLoading(true)
      setResultadoAnfir(null)
      setResultadoGovernanca(null)
      setStatusUpload("Identificando a natureza do arquivo e o destino correto...")

      const resposta = await importarDados(arquivoAtual, contexto)

      if (resposta.destino === "ANFIR") {
        const resultado = resposta.resultado as ResultadoAnfir
        setResultadoAnfir(resultado)
        if (resultado.status === "ERRO_PERSISTENCIA") {
          setStatusUpload("ANFIR reconhecida, mas os registros não puderam ser persistidos.")
        } else if (resultado.status === "SUCESSO_PARCIAL") {
          setStatusUpload("ANFIR reconhecida e importada parcialmente. Consulte os erros abaixo.")
        } else if (resultado.status === "SUCESSO") {
          setStatusUpload("ANFIR reconhecida e importada com sucesso.")
        } else {
          setStatusUpload(String(resultado.status || "ANFIR processada"))
        }
        await carregarDados()
        window.dispatchEvent(new Event("cti-upload-finalizado"))
      } else {
        const resultado = resposta.resultado as ResultadoGovernanca
        setResultadoGovernanca(resultado)
        setStatusUpload(
          resultado.duplicado
            ? "Fonte já registrada. Nenhuma duplicação foi criada."
            : "Fonte recebida e preservada. Ela seguirá pela governança e reconciliação adequadas ao seu conteúdo."
        )
      }
    } catch (error) {
      console.error(error)
      setStatusUpload(error instanceof Error ? error.message : "Falha durante a importação.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    queueMicrotask(() => void carregarDados())
  }, [])

  return (
    <main className="min-h-screen bg-[#020817] p-4 sm:p-8 text-white">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold">Importar Dados</h1>
          <p className="mt-2 max-w-3xl text-gray-400">
            Um único ponto de entrada para ANFIR, Funil de Vendas, CRM, histórico comercial e demais fontes do CTI.
          </p>
          <p className="mt-2 text-sm text-cyan-300">
            Contexto ativo: {contextoAtual.label}. O CTI identifica o tratamento correto sem misturar as fontes.
          </p>
          <button onClick={() => { window.location.href = "/dashboard" }} className="mt-4 rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-black hover:bg-cyan-400">← Voltar ao Dashboard</button>
        </div>

        <section className="rounded-2xl border border-[#17345e] bg-[#071427] p-5">
          <h2 className="text-xl font-bold">Arquivo</h2>
          <p className="mt-1 text-sm text-slate-400">
            Planilhas ANFIR reconhecidas seguem para o domínio realizado. Outras fontes seguem automaticamente para classificação, governança e reconciliação.
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv,.ods,.pdf,.doc,.docx,.ppt,.pptx,.txt,.md,.json,.xml,.png,.jpg,.jpeg,.webp,.tif,.tiff"
            onChange={(e) => {
              const arquivo = e.target.files?.[0] ?? null
              setFile(arquivo)
              setNomeArquivo(arquivo?.name ?? "")
              setResultadoAnfir(null)
              setResultadoGovernanca(null)
              if (arquivo) {
                setStatusUpload("Arquivo selecionado. Iniciando importação...")
                void enviarArquivo(arquivo)
              } else {
                setStatusUpload("Selecione um arquivo para importar.")
              }
            }}
            className="hidden"
          />

          <button
            onClick={() => {
              if (!file) {
                fileInputRef.current?.click()
                return
              }
              void enviarArquivo()
            }}
            disabled={loading}
            className="mt-5 w-full rounded-xl bg-cyan-500 py-3 font-bold text-black disabled:opacity-50"
          >
            {!file ? "Selecionar arquivo" : loading ? "Importando..." : "Importar novamente"}
          </button>

          {nomeArquivo && (
            <div className="mt-4 rounded-xl border border-emerald-500/60 bg-emerald-500/10 p-4">
              <p className="text-sm font-semibold text-emerald-300">Arquivo selecionado</p>
              <p className="mt-1 break-all">{nomeArquivo}</p>
            </div>
          )}
        </section>

        <section className="mt-6 rounded-2xl border border-[#13203f] bg-[#071226] p-6">
          <h2 className="text-xl font-bold">Status da importação</h2>
          <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-[#13203f]">
            <div className="h-full bg-cyan-400 transition-all duration-700" style={{ width: loading ? "70%" : (resultadoAnfir || resultadoGovernanca) ? "100%" : nomeArquivo ? "20%" : "0%" }} />
          </div>
          <p className="mt-4 text-slate-200">{statusUpload}</p>
        </section>

        {resultadoGovernanca && (
          <section className="mt-6 rounded-2xl border border-violet-700/50 bg-violet-950/20 p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-300">Destino definido pelo CTI</p>
            <h2 className="mt-2 text-xl font-bold">Governança de fontes</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Info label="Arquivo" value={resultadoGovernanca.fonte?.nome_arquivo || nomeArquivo || "-"} />
              <Info label="Tipo" value={resultadoGovernanca.fonte?.tipo_detectado || "A identificar"} />
              <Info label="Status" value={resultadoGovernanca.fonte?.status_governanca || "RECEBIDO"} />
              <Info label="Duplicado" value={resultadoGovernanca.duplicado ? "Sim" : "Não"} />
            </div>
            <p className="mt-4 text-sm text-slate-300">
              O arquivo original foi preservado e não alterou automaticamente CRM, ANFIR, Pipeline ou Vendas.
            </p>
            <button onClick={() => { window.location.href = "/backoffice-fontes" }} className="mt-4 rounded-xl border border-violet-500 px-4 py-2 font-semibold text-violet-100 hover:bg-violet-500/10">Abrir governança</button>
          </section>
        )}

        {resultadoAnfir && (
          <section className="mt-6 rounded-2xl border border-[#13203f] bg-[#071226] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-cyan-300">Destino definido pelo CTI</p>
            <h2 className="mt-2 text-2xl font-bold">ANFIR · realizado de mercado</h2>
            <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-2">
              {Object.entries(resultadoAnfir.bases_processadas ?? {}).map(([base, dados]) => (
                <div key={base} className="rounded-xl border border-[#13203f] bg-[#091a33] p-4">
                  <h3 className="font-bold text-cyan-400">{base}</h3>
                  <p className="mt-2 text-gray-400">Abas: {dados.abas?.join(", ") || "-"}</p>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <Info label="Linhas lidas" value={dados.linhas_lidas} />
                    <Info label="Registros válidos" value={dados.registros_validos} />
                    <Info label="Inseridos" value={dados.inseridos} />
                    <Info label="Atualizados" value={dados.atualizados} />
                    <Info label="Duplicados ignorados" value={dados.duplicados_ignorados} />
                    <Info label="Erros" value={dados.erros} />
                  </div>
                  {(dados.erros ?? 0) > 0 && (
                    <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-200">
                      <p className="font-semibold">Erros por tipo</p>
                      {Object.entries(dados.erros_por_tipo ?? {}).map(([tipo, total]) => total ? <p key={tipo}>{tipo}: {total}</p> : null)}
                      <div className="mt-3 space-y-2">
                        {(dados.amostra_erros ?? []).slice(0, 5).map((erro, index) => <p key={index}>Linha {erro.linha ?? "-"} • {erro.etapa} • {erro.tipo}: {erro.mensagem}</p>)}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-6 grid grid-cols-2 gap-6 xl:grid-cols-4">
              <Info label="Arquivo" value={resultadoAnfir.arquivo || nomeArquivo || "-"} />
              <Info label="Status" value={resultadoAnfir.status || statusUpload} />
              <Info label="Contexto" value={resultadoAnfir.contexto_operacional || contextoAtual.label} />
              <Info label="Inseridos totais" value={resultadoAnfir.persistencia?.inseridos ?? 0} />
              <Info label="Atualizados totais" value={resultadoAnfir.persistencia?.atualizados ?? 0} />
            </div>
          </section>
        )}
      </div>
    </main>
  )
}

function Info({ label, value }: { label: string; value: React.ReactNode }) {
  return <div><p className="text-gray-400">{label}</p><p className="text-lg text-white">{value ?? "-"}</p></div>
}
