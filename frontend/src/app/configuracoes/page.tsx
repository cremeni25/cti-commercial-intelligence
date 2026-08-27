"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import {
  CatalogLine,
  CatalogModel,
  ProductCatalog,
  createCatalogAlias,
  createCatalogModel,
  getProductCatalog,
  setCatalogEntityActive,
} from "@/services/product-catalog-admin"

function aliasLabel(alias: string | { alias: string }) {
  return typeof alias === "string" ? alias : alias.alias
}

function aliasId(alias: string | { id?: string }) {
  return typeof alias === "string" ? undefined : alias.id
}

export default function Page() {
  const { usuario, loading: authLoading } = useAuth()
  const [catalog, setCatalog] = useState<ProductCatalog | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [selectedLine, setSelectedLine] = useState("")
  const [selectedModel, setSelectedModel] = useState("")
  const [modelName, setModelName] = useState("")
  const [aliasName, setAliasName] = useState("")
  const [aliasTarget, setAliasTarget] = useState<"line" | "model">("model")

  const role = String(usuario?.tipo_usuario || "").toUpperCase()
  const canRead = role === "ADMIN_MASTER" || role === "DIRETOR" || role === "DIRETOR_VIENA_SP"
  const canWrite = role === "ADMIN_MASTER" || role === "DIRETOR_VIENA_SP"

  const loadCatalog = useCallback(async () => {
    if (!canRead) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError("")
    try {
      const data = await getProductCatalog()
      setCatalog(data)
      const firstLine = data.lines[0]
      if (firstLine) {
        setSelectedLine((current) => current || firstLine.id || "")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar o catálogo.")
    } finally {
      setLoading(false)
    }
  }, [canRead])

  useEffect(() => {
    if (!authLoading) {
      void loadCatalog()
    }
  }, [authLoading, loadCatalog])

  const lineOptions = catalog?.lines ?? []
  const activeLine = useMemo(
    () => lineOptions.find((line) => line.id === selectedLine) ?? null,
    [lineOptions, selectedLine],
  )
  const modelOptions = activeLine?.models ?? []

  useEffect(() => {
    if (activeLine?.models.length && !activeLine.models.some((model) => model.id === selectedModel)) {
      setSelectedModel(activeLine.models[0].id || "")
    }
  }, [activeLine, selectedModel])

  async function runMutation(action: () => Promise<unknown>, successMessage: string) {
    setSaving(true)
    setError("")
    setMessage("")
    try {
      await action()
      setMessage(successMessage)
      await loadCatalog()
    } catch (err) {
      setError(err instanceof Error ? err.message : "A operação não pôde ser concluída.")
    } finally {
      setSaving(false)
    }
  }

  async function submitModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedLine || !modelName.trim()) return
    await runMutation(
      () => createCatalogModel(selectedLine, modelName.trim()),
      "Modelo incluído e registrado na auditoria.",
    )
    setModelName("")
  }

  async function submitAlias(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!aliasName.trim()) return
    if (aliasTarget === "line" && !selectedLine) return
    if (aliasTarget === "model" && !selectedModel) return

    await runMutation(
      () => createCatalogAlias(
        aliasName.trim(),
        aliasTarget === "line" ? { lineId: selectedLine } : { modelId: selectedModel },
      ),
      "Alias incluído e registrado na auditoria.",
    )
    setAliasName("")
  }

  async function toggleEntity(
    entity: "lines" | "models" | "aliases",
    id: string | undefined,
    active: boolean,
    label: string,
  ) {
    if (!id) return
    await runMutation(
      () => setCatalogEntityActive(entity, id, !active),
      `${label} ${active ? "desativado" : "ativado"} com sucesso.`,
    )
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-6 lg:p-8">
          <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">
              Governança administrativa
            </p>
            <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="text-3xl font-bold lg:text-4xl">Linhas e modelos de produtos</h1>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                  Fonte oficial usada pela classificação, filtros, rankings e indicadores do CTI.
                  Alterações preservam o histórico e ficam registradas em auditoria.
                </p>
              </div>
              <div className="rounded-2xl border border-cyan-900/70 bg-[#061326] px-4 py-3 text-sm">
                <div className="font-semibold text-cyan-300">{role || "PERFIL NÃO IDENTIFICADO"}</div>
                <div className="mt-1 text-slate-400">
                  {canWrite ? "Leitura e administração" : canRead ? "Somente leitura" : "Sem acesso"}
                </div>
              </div>
            </div>
          </header>

          {authLoading || loading ? (
            <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-8 text-slate-300">
              Carregando catálogo e permissões...
            </div>
          ) : !canRead ? (
            <div className="rounded-3xl border border-red-900/60 bg-red-950/20 p-8">
              <h2 className="text-xl font-bold text-red-300">Acesso não autorizado</h2>
              <p className="mt-2 text-sm text-red-100/70">
                Este módulo é restrito ao ADMIN_MASTER e à Diretoria Viena autorizada.
              </p>
            </div>
          ) : (
            <>
              {error && (
                <div className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">
                  {error}
                </div>
              )}
              {message && (
                <div className="rounded-2xl border border-emerald-900/60 bg-emerald-950/30 px-5 py-4 text-sm text-emerald-200">
                  {message}
                </div>
              )}

              {catalog && (
                <div className="grid gap-4 md:grid-cols-3">
                  <Metric label="Fonte do catálogo" value={catalog.source === "supabase" ? "Supabase" : "Fallback seguro"} />
                  <Metric label="Linhas configuradas" value={String(catalog.lines.length)} />
                  <Metric
                    label="Modelos configurados"
                    value={String(catalog.lines.reduce((total, line) => total + line.models.length, 0))}
                  />
                </div>
              )}

              <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
                <div className="space-y-5">
                  {(catalog?.lines ?? []).map((line) => (
                    <LineCard
                      key={line.id || line.code}
                      line={line}
                      canWrite={canWrite}
                      saving={saving}
                      onToggleLine={() => toggleEntity("lines", line.id, line.active, `Linha ${line.code}`)}
                      onToggleModel={(model) => toggleEntity("models", model.id, model.active, `Modelo ${model.canonical_name}`)}
                      onToggleAlias={(id, active, label) => toggleEntity("aliases", id, active, `Alias ${label}`)}
                    />
                  ))}
                </div>

                <aside className="space-y-5">
                  <div className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
                    <h2 className="text-lg font-bold">Administração do catálogo</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                      ADMIN_MASTER e DIRETOR_VIENA_SP autorizado podem administrar o catálogo operacional. Ferramentas técnicas de desenvolvimento e homologação permanecem separadas.
                    </p>

                    <label className="mt-5 block text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Linha de produto
                    </label>
                    <select
                      value={selectedLine}
                      onChange={(event) => setSelectedLine(event.target.value)}
                      className="mt-2 w-full rounded-xl border border-[#203252] bg-[#030b18] px-3 py-3 text-sm"
                    >
                      {lineOptions.map((line) => (
                        <option key={line.id || line.code} value={line.id || ""}>
                          {line.code} · {line.name}
                        </option>
                      ))}
                    </select>

                    <form onSubmit={submitModel} className="mt-6 space-y-3 border-t border-[#182744] pt-5">
                      <h3 className="font-semibold">Novo modelo oficial</h3>
                      <input
                        value={modelName}
                        onChange={(event) => setModelName(event.target.value)}
                        placeholder="Ex.: VECTOR HE 19"
                        disabled={!canWrite || saving}
                        className="w-full rounded-xl border border-[#203252] bg-[#030b18] px-3 py-3 text-sm disabled:opacity-50"
                      />
                      <button
                        type="submit"
                        disabled={!canWrite || saving || !selectedLine || !modelName.trim()}
                        className="w-full rounded-xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Incluir modelo
                      </button>
                    </form>

                    <form onSubmit={submitAlias} className="mt-6 space-y-3 border-t border-[#182744] pt-5">
                      <h3 className="font-semibold">Novo alias de importação</h3>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => setAliasTarget("line")}
                          className={`rounded-xl border px-3 py-2 text-xs font-semibold ${aliasTarget === "line" ? "border-cyan-400 bg-cyan-400/10 text-cyan-300" : "border-[#203252] text-slate-400"}`}
                        >
                          Para linha
                        </button>
                        <button
                          type="button"
                          onClick={() => setAliasTarget("model")}
                          className={`rounded-xl border px-3 py-2 text-xs font-semibold ${aliasTarget === "model" ? "border-cyan-400 bg-cyan-400/10 text-cyan-300" : "border-[#203252] text-slate-400"}`}
                        >
                          Para modelo
                        </button>
                      </div>

                      {aliasTarget === "model" && (
                        <select
                          value={selectedModel}
                          onChange={(event) => setSelectedModel(event.target.value)}
                          className="w-full rounded-xl border border-[#203252] bg-[#030b18] px-3 py-3 text-sm"
                        >
                          {modelOptions.map((model) => (
                            <option key={model.id || model.canonical_name} value={model.id || ""}>
                              {model.canonical_name}
                            </option>
                          ))}
                        </select>
                      )}

                      <input
                        value={aliasName}
                        onChange={(event) => setAliasName(event.target.value)}
                        placeholder="Ex.: X4 7500"
                        disabled={!canWrite || saving}
                        className="w-full rounded-xl border border-[#203252] bg-[#030b18] px-3 py-3 text-sm disabled:opacity-50"
                      />
                      <button
                        type="submit"
                        disabled={!canWrite || saving || !aliasName.trim() || (aliasTarget === "model" && !selectedModel)}
                        className="w-full rounded-xl bg-violet-400 px-4 py-3 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Incluir alias
                      </button>
                    </form>
                  </div>
                </aside>
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#13203f] bg-[#071427] p-5">
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-2 text-xl font-bold text-cyan-300">{value}</div>
    </div>
  )
}

function LineCard({
  line,
  canWrite,
  saving,
  onToggleLine,
  onToggleModel,
  onToggleAlias,
}: {
  line: CatalogLine
  canWrite: boolean
  saving: boolean
  onToggleLine: () => void
  onToggleModel: (model: CatalogModel) => void
  onToggleAlias: (id: string | undefined, active: boolean, label: string) => void
}) {
  return (
    <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-400">{line.code}</div>
          <h2 className="mt-1 text-2xl font-bold">{line.name}</h2>
          <div className="mt-2 text-xs text-slate-500">
            {line.models.length} modelos · {line.aliases.length} aliases de linha
          </div>
        </div>
        <StatusButton
          active={line.active}
          disabled={!canWrite || saving || !line.id}
          onClick={onToggleLine}
        />
      </div>

      {line.aliases.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {line.aliases.map((alias, index) => {
            const label = aliasLabel(alias)
            const id = aliasId(alias)
            const active = typeof alias === "string" ? true : alias.active !== false
            return (
              <button
                key={id || `${label}-${index}`}
                type="button"
                disabled={!canWrite || saving || !id}
                onClick={() => onToggleAlias(id, active, label)}
                className={`rounded-full border px-3 py-1 text-xs ${active ? "border-cyan-900 bg-cyan-950/40 text-cyan-300" : "border-slate-700 text-slate-500 line-through"}`}
              >
                {label}
              </button>
            )
          })}
        </div>
      )}

      <div className="mt-6 grid gap-3 md:grid-cols-2">
        {line.models.map((model) => (
          <div key={model.id || model.canonical_name} className="rounded-2xl border border-[#182744] bg-[#040d1c] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className={`font-semibold ${model.active ? "text-white" : "text-slate-500 line-through"}`}>
                  {model.canonical_name}
                </div>
                <div className="mt-1 text-xs text-slate-500">{model.aliases.length} aliases</div>
              </div>
              <StatusButton
                active={model.active}
                disabled={!canWrite || saving || !model.id}
                compact
                onClick={() => onToggleModel(model)}
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {model.aliases.map((alias, index) => {
                const label = aliasLabel(alias)
                const id = aliasId(alias)
                const active = typeof alias === "string" ? true : alias.active !== false
                return (
                  <button
                    key={id || `${label}-${index}`}
                    type="button"
                    disabled={!canWrite || saving || !id}
                    onClick={() => onToggleAlias(id, active, label)}
                    className={`rounded-lg border px-2 py-1 text-[11px] ${active ? "border-violet-900 bg-violet-950/30 text-violet-300" : "border-slate-800 text-slate-600 line-through"}`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

function StatusButton({
  active,
  disabled,
  compact = false,
  onClick,
}: {
  active: boolean
  disabled: boolean
  compact?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`rounded-full border font-semibold disabled:cursor-not-allowed disabled:opacity-50 ${compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-xs"} ${active ? "border-emerald-800 bg-emerald-950/40 text-emerald-300" : "border-slate-700 bg-slate-900 text-slate-500"}`}
    >
      {active ? "ATIVO" : "INATIVO"}
    </button>
  )
}
