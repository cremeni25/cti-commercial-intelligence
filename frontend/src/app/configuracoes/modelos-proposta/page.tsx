"use client"

import { ChangeEvent, useMemo, useState } from "react"
import Link from "next/link"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import {
  ImportacaoPacoteResultado,
  importarPacoteModelos,
} from "@/services/modelos-proposta-importacao"

const MAX_ZIP_BYTES = 25 * 1024 * 1024

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<ImportacaoPacoteResultado | null>(null)

  const role = String(usuario?.tipo_usuario || "").toUpperCase()
  const canImport = role === "ADMIN_MASTER"
  const fileLabel = useMemo(() => {
    if (!file) return "Nenhum pacote selecionado"
    return `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`
  }, [file])

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] || null
    setError("")
    setResult(null)

    if (!selected) {
      setFile(null)
      return
    }
    if (!selected.name.toLowerCase().endsWith(".zip")) {
      setFile(null)
      setError("Selecione exclusivamente o pacote ZIP oficial.")
      return
    }
    if (selected.size > MAX_ZIP_BYTES) {
      setFile(null)
      setError("O pacote excede o limite de 25 MB.")
      return
    }
    setFile(selected)
  }

  async function submit() {
    if (!file || !canImport || sending) return
    setSending(true)
    setError("")
    setResult(null)
    try {
      setResult(await importarPacoteModelos(file))
    } catch (err) {
      setError(err instanceof Error ? err.message : "A importação não pôde ser concluída.")
    } finally {
      setSending(false)
    }
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Modelos de proposta</p>
            <div className="mt-3 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="text-3xl font-bold lg:text-4xl">Importação única dos documentos originais</h1>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                  Selecione somente o pacote ZIP oficial. O CTI extrai, confere os 11 documentos,
                  valida nome, tamanho e SHA-256, grava no Storage privado e registra a auditoria.
                </p>
              </div>
              <Link href="/configuracoes/modelos-proposta/homologacao" className="rounded-2xl border border-violet-700 bg-violet-500/10 px-5 py-3 text-center text-sm font-bold text-violet-200">
                Abrir homologação visual
              </Link>
            </div>
          </header>

          {authLoading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">Validando sessão administrativa...</div>
          ) : !canImport ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8">
              <h2 className="text-xl font-bold text-red-300">Acesso restrito</h2>
              <p className="mt-2 text-sm text-red-100/70">Somente o perfil ADMIN_MASTER pode executar esta importação.</p>
            </div>
          ) : (
            <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 lg:p-8">
              <div className="rounded-2xl border border-dashed border-cyan-800 bg-[#040d1c] p-6">
                <label className="block text-sm font-semibold text-cyan-300" htmlFor="pacote-modelos">Pacote ZIP oficial</label>
                <input id="pacote-modelos" type="file" accept=".zip,application/zip" onChange={selectFile} disabled={sending} className="mt-4 block w-full text-sm text-slate-300 file:mr-4 file:rounded-xl file:border-0 file:bg-cyan-400 file:px-4 file:py-3 file:font-bold file:text-slate-950" />
                <p className="mt-3 text-xs text-slate-500">{fileLabel}</p>
              </div>

              {error && <div className="mt-5 rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{error}</div>}

              <button type="button" onClick={submit} disabled={!file || sending} className="mt-6 w-full rounded-2xl bg-cyan-400 px-5 py-4 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40">
                {sending ? "Validando e importando..." : "Importar pacote e preparar homologação"}
              </button>

              {result && (
                <div className="mt-6 rounded-3xl border border-emerald-900/60 bg-emerald-950/20 p-6">
                  <h2 className="text-xl font-bold text-emerald-300">Importação concluída</h2>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <Metric label="Esperados" value={String(result.total_esperado)} />
                    <Metric label="Importados" value={String(result.importados)} />
                    <Metric label="Já armazenados" value={String(result.ignorados_ja_armazenados)} />
                  </div>
                  <div className="mt-5 space-y-2">
                    {result.resultados.map((item) => (
                      <div key={`${item.modelo_id}-${item.arquivo}`} className="rounded-xl border border-emerald-900/40 bg-black/10 px-4 py-3 text-sm">
                        <span className="font-semibold text-emerald-200">{item.equipamento}</span>
                        <span className="mx-2 text-slate-600">·</span>
                        <span className="text-slate-300">{item.arquivo}</span>
                        <span className="float-right text-xs uppercase tracking-wider text-emerald-400">{item.status}</span>
                      </div>
                    ))}
                  </div>
                  <Link href="/configuracoes/modelos-proposta/homologacao" className="mt-6 block w-full rounded-2xl bg-violet-400 px-5 py-4 text-center text-sm font-bold text-slate-950">
                    Seguir para homologação visual
                  </Link>
                </div>
              )}
            </section>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-emerald-900/50 bg-black/10 p-4">
      <div className="text-xs uppercase tracking-wider text-emerald-300/60">{label}</div>
      <div className="mt-1 text-2xl font-bold text-emerald-200">{value}</div>
    </div>
  )
}
