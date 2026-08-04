"use client"

import Link from "next/link"
import { ChangeEvent, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

type ResultadoImportacao = {
  ok?: boolean
  arquivos_unicos_recebidos?: number
  modelos_esperados?: number
  modelos_atualizados?: number
  falhas?: Array<{ equipamento?: string; arquivo?: string; erro?: string }>
}

export default function ModelosOficiaisPage() {
  const { usuario, loading } = useAuth()
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null)

  const role = String(usuario?.tipo_usuario || "").toUpperCase()
  const autorizado = role === "ADMIN_MASTER"

  function selecionar(event: ChangeEvent<HTMLInputElement>) {
    setErro("")
    setResultado(null)
    const escolhido = event.target.files?.[0] || null
    if (escolhido && !escolhido.name.toLowerCase().endsWith(".zip")) {
      setArquivo(null)
      setErro("Selecione o pacote ZIP oficial dos 16 documentos Carrier.")
      return
    }
    setArquivo(escolhido)
  }

  async function importar() {
    if (!arquivo || !autorizado) return
    setEnviando(true)
    setErro("")
    setResultado(null)

    try {
      const supabase = getSupabaseClient()
      const { data } = await supabase.auth.getSession()
      const token = data.session?.access_token
      if (!token) throw new Error("Sessão administrativa não encontrada. Entre novamente no CTI.")

      const form = new FormData()
      form.append("pacote", arquivo, arquivo.name)

      const resposta = await fetch(`${API_URL}/modelos-proposta-importacao/pacote`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) {
        const detalhe = payload?.detail
        if (typeof detalhe === "string") throw new Error(detalhe)
        throw new Error(detalhe?.mensagem || "O pacote não pôde ser importado.")
      }
      setResultado(payload)
      if (!payload?.ok) setErro("A importação terminou com bloqueios. Consulte os itens apresentados abaixo.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao importar os documentos oficiais.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="mx-auto max-w-5xl space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Documentos comerciais</p>
            <h1 className="mt-3 text-3xl font-bold">Modelos oficiais Carrier</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Substituição controlada dos 16 documentos mestres. Os arquivos são preservados integralmente e registrados por tamanho e SHA-256.
            </p>
          </header>

          {loading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">Validando perfil administrativo...</div>
          ) : !autorizado ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8 text-red-200">Acesso restrito ao ADMIN_MASTER.</div>
          ) : (
            <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 lg:p-8">
              <div className="rounded-2xl border border-amber-800/60 bg-amber-950/20 p-4 text-sm leading-6 text-amber-100">
                O pacote deve conter exatamente os 16 arquivos oficiais. A importação substitui os vínculos anteriores e recalcula os hashes sem alterar o conteúdo dos documentos.
              </div>

              <label className="mt-6 block text-sm font-semibold text-slate-200">Pacote oficial ZIP</label>
              <input
                type="file"
                accept=".zip,application/zip"
                onChange={selecionar}
                disabled={enviando}
                className="mt-3 block w-full rounded-2xl border border-[#203252] bg-[#030b18] p-4 text-sm file:mr-4 file:rounded-xl file:border-0 file:bg-cyan-400 file:px-4 file:py-2 file:font-bold file:text-slate-950"
              />

              {arquivo && <p className="mt-3 text-sm text-cyan-300">Selecionado: {arquivo.name}</p>}
              {erro && <div className="mt-5 rounded-2xl border border-red-900/60 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}

              <button
                type="button"
                onClick={() => void importar()}
                disabled={!arquivo || enviando}
                className="mt-6 w-full rounded-2xl bg-cyan-400 px-5 py-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {enviando ? "Importando e validando os 16 documentos..." : "Importar pacote oficial Carrier"}
              </button>

              {resultado && (
                <div className={`mt-6 rounded-2xl border p-5 ${resultado.ok ? "border-emerald-800 bg-emerald-950/30" : "border-amber-800 bg-amber-950/20"}`}>
                  <h2 className="text-lg font-bold">{resultado.ok ? "Importação concluída" : "Importação com bloqueios"}</h2>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <Metric label="Arquivos recebidos" value={resultado.arquivos_unicos_recebidos} />
                    <Metric label="Modelos esperados" value={resultado.modelos_esperados} />
                    <Metric label="Modelos atualizados" value={resultado.modelos_atualizados} />
                  </div>
                  {!!resultado.falhas?.length && (
                    <div className="mt-5 space-y-2">
                      {resultado.falhas.map((falha, indice) => (
                        <div key={`${falha.equipamento}-${indice}`} className="rounded-xl border border-red-900/50 bg-red-950/30 p-3 text-sm text-red-200">
                          <strong>{falha.equipamento || falha.arquivo || "Documento"}:</strong> {falha.erro || "Falha não identificada"}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="mt-6">
                <Link href="/configuracoes" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">← Voltar às configurações</Link>
              </div>
            </section>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: number | undefined }) {
  return <div className="rounded-xl border border-white/10 bg-black/10 p-4"><div className="text-xs uppercase tracking-wider text-slate-400">{label}</div><div className="mt-2 text-2xl font-bold">{value ?? 0}</div></div>
}
