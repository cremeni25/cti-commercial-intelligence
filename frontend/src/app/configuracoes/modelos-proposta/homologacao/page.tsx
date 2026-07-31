"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { ModeloHomologacao, carregarFilaHomologacao, homologarModelos } from "@/services/modelos-proposta-homologacao"

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [fila, setFila] = useState<ModeloHomologacao[]>([])
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const role = String(usuario?.tipo_usuario || "").toUpperCase()
  const canManage = role === "ADMIN_MASTER"
  const selected = useMemo(() => fila.filter((item) => checked[item.id]), [fila, checked])

  async function load() {
    if (!canManage) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError("")
    try {
      const result = await carregarFilaHomologacao()
      setFila(result.fila)
      setChecked({})
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar a fila.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!authLoading) void load()
  }, [authLoading, canManage])

  async function submit() {
    if (!selected.length || saving) return
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const result = await homologarModelos(selected)
      if (result.falhas) setError(`${result.falhas} modelo(s) não puderam ser homologados.`)
      else setMessage(`${result.homologados} modelo(s) homologados com sucesso.`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "A homologação não pôde ser concluída.")
    } finally {
      setSaving(false)
    }
  }

  const allChecked = fila.length > 0 && selected.length === fila.length

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Modelos de proposta</p>
            <h1 className="mt-3 text-3xl font-bold lg:text-4xl">Homologação visual dos documentos</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Abra cada documento e confirme páginas, textos, imagens, tabelas e formatação. O CTI gera automaticamente o acesso seguro ao arquivo privado.
            </p>
            <Link href="/configuracoes/modelos-proposta" className="mt-5 inline-block text-sm font-semibold text-cyan-300">
              Voltar para importação
            </Link>
          </header>

          {authLoading || loading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">Carregando fila de homologação...</div>
          ) : !canManage ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8 text-red-200">Somente ADMIN_MASTER pode homologar modelos.</div>
          ) : (
            <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6 lg:p-8">
              {error && <div className="mb-5 rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{error}</div>}
              {message && <div className="mb-5 rounded-2xl border border-emerald-900/60 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">{message}</div>}

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-cyan-300">Pendentes: {fila.length}</div>
                  <div className="mt-1 text-xs text-slate-500">Conferidos: {selected.length}</div>
                </div>
                {fila.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setChecked(Object.fromEntries(fila.map((item) => [item.id, !allChecked])))}
                    className="rounded-xl border border-cyan-800 px-4 py-2 text-xs font-semibold text-cyan-300"
                  >
                    {allChecked ? "Desmarcar todos" : "Marcar todos conferidos"}
                  </button>
                )}
              </div>

              <div className="mt-6 space-y-3">
                {fila.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-[#182744] bg-[#040d1c] p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <div className="text-xs font-bold uppercase tracking-wider text-cyan-400">{item.linha_produto}</div>
                        <h2 className="mt-1 text-lg font-bold">{item.equipamento}</h2>
                        <p className="mt-1 text-xs text-slate-500">{item.arquivo_template_nome_original}</p>
                      </div>
                      <div className="flex flex-wrap items-center gap-3">
                        <a href={item.url_temporaria} target="_blank" rel="noreferrer" className="rounded-xl bg-violet-400 px-4 py-3 text-sm font-bold text-slate-950">
                          Abrir documento
                        </a>
                        <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-emerald-900/60 bg-emerald-950/20 px-4 py-3 text-sm text-emerald-200">
                          <input type="checkbox" checked={Boolean(checked[item.id])} onChange={(event) => setChecked((current) => ({ ...current, [item.id]: event.target.checked }))} className="h-4 w-4" />
                          Conferência integral concluída
                        </label>
                      </div>
                    </div>
                  </article>
                ))}
                {fila.length === 0 && <div className="rounded-2xl border border-emerald-900/60 bg-emerald-950/20 p-8 text-center text-emerald-200">Nenhum modelo pendente de homologação.</div>}
              </div>

              {fila.length > 0 && (
                <button type="button" onClick={submit} disabled={!selected.length || saving} className="mt-6 w-full rounded-2xl bg-cyan-400 px-5 py-4 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40">
                  {saving ? "Homologando..." : `Homologar ${selected.length} modelo(s) conferido(s)`}
                </button>
              )}
            </section>
          )}
        </div>
      </section>
    </main>
  )
}
