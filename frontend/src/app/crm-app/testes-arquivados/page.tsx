"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { ArchiveRestore, ArrowLeft, Loader2 } from "lucide-react"
import { useAuth } from "@/core/auth"
import { getSupabaseClient } from "@/core/database/supabase"

type Registro = Record<string, unknown>

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function moeda(valor: unknown): string { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function data(valor: unknown): string { const d = new Date(texto(valor)); return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("pt-BR") }

async function authHeaders(extra?: HeadersInit) {
  const headers = new Headers(extra)
  const supabase = getSupabaseClient()
  const { data } = await supabase.auth.getSession()
  if (!data.session?.access_token) throw new Error("Sessão expirada. Entre novamente no CRM App.")
  headers.set("Authorization", `Bearer ${data.session.access_token}`)
  if (!headers.has("Accept")) headers.set("Accept", "application/json")
  return headers
}

async function fetchProtegido(input: RequestInfo | URL, init: RequestInit = {}) {
  return fetch(input, { ...init, headers: await authHeaders(init.headers) })
}

export default function TestesArquivadosPage() {
  const { usuario } = useAuth()
  const [registros, setRegistros] = useState<Registro[]>([])
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState("")
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const admin = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  const carregar = useCallback(async () => {
    if (!admin) { setCarregando(false); return }
    setCarregando(true); setErro("")
    try {
      const resposta = await fetchProtegido("/api/crm-proxy/crm-app/oportunidades/testes-arquivados", { cache: "no-store" })
      const payload = await resposta.json().catch(() => [])
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      setRegistros(Array.isArray(payload) ? payload : [])
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível carregar os registros arquivados.") }
    finally { setCarregando(false) }
  }, [admin])

  useEffect(() => { queueMicrotask(() => void carregar()) }, [carregar])

  async function restaurar(id: string) {
    if (!window.confirm("Restaurar esta oportunidade para a operação normal?")) return
    setProcessando(id); setErro(""); setMensagem("")
    try {
      const resposta = await fetchProtegido(`/api/crm-proxy/crm-app/oportunidades/${encodeURIComponent(id)}/restaurar-teste`, { method: "POST" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      setMensagem("Registro restaurado e devolvido às leituras operacionais.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível restaurar o registro.") }
    finally { setProcessando("") }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Testes arquivados</h1><p className="text-sm text-slate-400">Registros preservados fora de Pipeline, Forecast, Relatórios e IA</p></div></header>
    {!admin && <div className="rounded-3xl border border-amber-800 bg-amber-950/30 p-5 text-amber-200">Área restrita ao ADMIN_MASTER.</div>}
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {mensagem && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
    {admin && (carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : registros.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum registro de teste arquivado.</div> : <div className="space-y-3">{registros.map((registro) => { const id = texto(registro.id); return <article key={id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-xs uppercase tracking-[.16em] text-amber-300">Teste arquivado</p><h2 className="mt-1 text-lg font-bold">{texto(registro.titulo) || "Oportunidade sem título"}</h2><p className="mt-2 text-sm text-slate-400">Valor: {moeda(registro.valor_estimado)} · Status anterior: {texto(registro.status_antes_arquivamento) || "Não informado"}</p><p className="mt-1 text-xs text-slate-500">Arquivado em {data(registro.arquivado_em)} · {texto(registro.motivo_arquivamento)}</p></div><button disabled={processando===id} onClick={() => void restaurar(id)} className="flex min-h-11 items-center justify-center gap-2 rounded-xl border border-emerald-700 px-4 text-sm font-semibold text-emerald-300 disabled:opacity-50">{processando===id ? <Loader2 size={16} className="animate-spin"/> : <ArchiveRestore size={16}/>}Restaurar</button></div></article> })}</div>)}
  </div></main>
}
