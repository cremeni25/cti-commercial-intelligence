"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ArrowLeft, Archive, Loader2, RotateCcw, ShieldCheck } from "lucide-react"
import { useAuth } from "@/core/auth"
import { getSupabaseClient } from "@/core/database/supabase"

type Registro = Record<string, unknown>
type Previa = {
  oportunidade_ids: string[]
  resumo: Record<string, number>
  oportunidades: Registro[]
  aviso_clientes: string
  confirmacao_exigida: string
}
type Lote = Registro & { lote_id?: string; resumo?: Record<string, number>; revertido_em?: string | null }

async function lerJson(resposta: Response) {
  const payload = await resposta.json().catch(() => ({})) as Registro
  if (!resposta.ok) throw new Error(String(payload.detail || `Erro HTTP ${resposta.status}`))
  return payload
}

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

function normalizarConfirmacao(valor: string) {
  return valor
    .replaceAll("\u00a0", " ")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .replace(/\s+/g, " ")
    .toUpperCase()
}

export default function HomologacaoPage() {
  const { usuario } = useAuth()
  const [universo, setUniverso] = useState<Previa | null>(null)
  const [previa, setPrevia] = useState<Previa | null>(null)
  const [selecionados, setSelecionados] = useState<string[]>([])
  const [lotes, setLotes] = useState<Lote[]>([])
  const [confirmacao, setConfirmacao] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [recalculando, setRecalculando] = useState(false)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  const adminMaster = usuario?.tipo_usuario === "ADMIN_MASTER"

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const [previaResposta, lotesResposta] = await Promise.all([
        fetchProtegido("/api/crm-proxy/crm-app/oportunidades/homologacao/previa", { cache: "no-store" }),
        fetchProtegido("/api/crm-proxy/crm-app/oportunidades/homologacao/lotes", { cache: "no-store" }),
      ])
      const p = await lerJson(previaResposta) as unknown as Previa
      const l = await lerJson(lotesResposta)
      setUniverso(p)
      setPrevia(p)
      setSelecionados(p.oportunidade_ids)
      setLotes(Array.isArray(l) ? l as unknown as Lote[] : [])
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar a administração de homologação.")
    } finally { setCarregando(false) }
  }

  useEffect(() => { if (adminMaster) void carregar(); else if (usuario) setCarregando(false) }, [adminMaster, usuario])

  const totalAfetado = useMemo(() => previa ? Object.entries(previa.resumo)
    .filter(([chave]) => chave !== "clientes_mestre_preservados")
    .reduce((soma, [, valor]) => soma + Number(valor || 0), 0) : 0, [previa])

  const confirmacaoValida = Boolean(previa && normalizarConfirmacao(confirmacao) === normalizarConfirmacao(previa.confirmacao_exigida))
  const todosSelecionados = Boolean(universo && selecionados.length === universo.oportunidade_ids.length && universo.oportunidade_ids.length > 0)

  async function atualizarSelecao(ids: string[]) {
    const unicos = Array.from(new Set(ids))
    setSelecionados(unicos)
    setConfirmacao("")
    setRecalculando(true)
    setErro("")
    try {
      const resposta = await fetchProtegido("/api/crm-proxy/crm-app/oportunidades/homologacao/previa-selecao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ oportunidade_ids: unicos }),
      })
      setPrevia(await lerJson(resposta) as unknown as Previa)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível recalcular a prévia.")
    } finally { setRecalculando(false) }
  }

  async function arquivar() {
    if (!previa || !confirmacaoValida || selecionados.length === 0) return
    setProcessando(true); setErro(""); setSucesso("")
    try {
      const resposta = await fetchProtegido("/api/crm-proxy/crm-app/oportunidades/homologacao/arquivar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          oportunidade_ids: selecionados,
          confirmacao,
          motivo: "Limpeza do histórico criado para teste/homologação do CRM App",
        }),
      })
      const retorno = await lerJson(resposta)
      setConfirmacao("")
      setSucesso(`Histórico de homologação arquivado com sucesso. Lote ${String(retorno.lote_id || "registrado")}.`)
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao arquivar histórico.")
    } finally { setProcessando(false) }
  }

  async function restaurar(loteId: string) {
    if (!window.confirm("Restaurar integralmente este lote de homologação?")) return
    const digitado = window.prompt("Para confirmar, digite: RESTAURAR LOTE") || ""
    if (normalizarConfirmacao(digitado) !== "RESTAURAR LOTE") return
    setProcessando(true); setErro(""); setSucesso("")
    try {
      const resposta = await fetchProtegido(`/api/crm-proxy/crm-app/oportunidades/homologacao/lotes/${encodeURIComponent(loteId)}/restaurar`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmacao: digitado }),
      })
      await lerJson(resposta)
      setSucesso("Lote restaurado integralmente.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao restaurar lote.")
    } finally { setProcessando(false) }
  }

  if (carregando) return <main className="grid min-h-[100dvh] place-items-center bg-[#020817] text-cyan-300"><Loader2 className="animate-spin"/></main>
  if (!adminMaster) return <main className="min-h-[100dvh] bg-[#020817] p-6 text-white"><div className="mx-auto max-w-3xl rounded-3xl border border-red-900 bg-red-950/20 p-6"><h1 className="text-xl font-bold text-red-200">Acesso restrito</h1><p className="mt-2 text-sm text-red-100/80">Somente ADMIN_MASTER pode administrar registros de homologação.</p></div></main>

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/oportunidades" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.22em] text-amber-400">ADMIN_MASTER</p><h1 className="text-2xl font-bold">Administração de homologação</h1><p className="text-sm text-slate-400">Arquivamento coordenado, seletivo e reversível do histórico de teste do CRM App.</p></div></header>

    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{sucesso}</div>}

    <section className="rounded-3xl border border-amber-800/60 bg-amber-950/15 p-5 sm:p-6">
      <div className="flex items-start gap-3"><AlertTriangle className="mt-1 text-amber-300"/><div><h2 className="text-lg font-bold text-amber-100">Prévia do lote selecionado</h2><p className="mt-1 text-sm leading-6 text-amber-100/70">Escolha quais oportunidades serão arquivadas. Nada é apagado e os cadastros mestres de clientes são preservados.</p></div></div>

      {universo && <div className="mt-5 rounded-2xl border border-[#24466f] bg-[#061126] p-4">
        <div className="mb-3 flex items-center justify-between gap-3"><div><strong className="text-sm text-cyan-100">Selecionar oportunidades</strong><p className="text-xs text-slate-400">{selecionados.length} de {universo.oportunidade_ids.length} selecionadas</p></div><button type="button" disabled={recalculando || processando} onClick={() => void atualizarSelecao(todosSelecionados ? [] : universo.oportunidade_ids)} className="rounded-xl border border-cyan-800 px-3 py-2 text-xs font-semibold text-cyan-300 disabled:opacity-40">{todosSelecionados ? "Limpar" : "Selecionar todas"}</button></div>
        <div className="space-y-2">{universo.oportunidades.map(item => { const id = String(item.id); const marcado = selecionados.includes(id); return <label key={id} className="flex cursor-pointer items-start gap-3 rounded-xl border border-[#16325c] bg-[#020817] px-4 py-3 text-sm"><input type="checkbox" checked={marcado} disabled={recalculando || processando} onChange={() => void atualizarSelecao(marcado ? selecionados.filter(valor => valor !== id) : [...selecionados, id])} className="mt-1 size-4 accent-cyan-400"/><span><strong>{String(item.cliente_nome || "Cliente")}</strong><span className="text-slate-400"> · {String(item.titulo || "Oportunidade")} · {String(item.status || "")}</span></span></label> })}</div>
      </div>}

      {previa && <>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-5">{Object.entries(previa.resumo).map(([chave, valor]) => <div key={chave} className="rounded-2xl border border-[#24466f] bg-[#07162b] p-3"><strong className="block text-xl text-cyan-300">{valor}</strong><span className="text-xs text-slate-400">{chave.replaceAll("_", " ")}</span></div>)}</div>
        <p className="mt-4 rounded-xl border border-cyan-900 bg-cyan-950/20 p-3 text-xs leading-5 text-cyan-100">{recalculando ? "Recalculando impacto da seleção..." : previa.aviso_clientes}</p>
        <div className="mt-5 rounded-2xl border border-red-900/70 bg-red-950/20 p-4"><p className="text-sm font-semibold text-red-200">Confirmação obrigatória</p><p className="mt-1 text-xs text-red-100/70">Esta ação arquivará {totalAfetado} registros transacionais ligados às {selecionados.length} oportunidades selecionadas.</p><input value={confirmacao} onChange={e => setConfirmacao(e.target.value)} placeholder={previa.confirmacao_exigida} className="mt-3 h-12 w-full rounded-xl border border-red-800 bg-[#020817] px-4 text-sm"/><p className="mt-2 text-[11px] text-red-100/60">A confirmação aceita diferenças de acentuação e espaços, mas a frase precisa ser a mesma.</p><button type="button" onClick={() => void arquivar()} disabled={processando || recalculando || selecionados.length === 0 || !confirmacaoValida} className="mt-3 flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-red-500 font-bold text-white disabled:opacity-40">{processando || recalculando ? <Loader2 className="animate-spin" size={18}/> : <Archive size={18}/>}Arquivar histórico selecionado</button></div>
      </>}
    </section>

    <section className="mt-6 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6"><div className="flex items-center gap-3"><ShieldCheck className="text-cyan-300"/><div><h2 className="font-bold">Lotes arquivados</h2><p className="text-sm text-slate-400">Restauração é integral por lote.</p></div></div><div className="mt-4 space-y-3">{lotes.length === 0 ? <p className="text-sm text-slate-500">Nenhum lote arquivado ainda.</p> : lotes.map(lote => <div key={String(lote.id)} className="flex flex-col gap-3 rounded-2xl border border-[#24466f] bg-[#020817] p-4 sm:flex-row sm:items-center sm:justify-between"><div><strong className="text-sm">{String(lote.lote_id || "Lote")}</strong><p className="mt-1 text-xs text-slate-500">{String(lote.created_at || "")} {lote.revertido_em ? "· restaurado" : "· arquivado"}</p></div>{!lote.revertido_em && lote.lote_id && <button type="button" disabled={processando} onClick={() => void restaurar(String(lote.lote_id))} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-cyan-800 px-3 text-xs font-semibold text-cyan-300"><RotateCcw size={15}/>Restaurar lote</button>}</div>)}</div></section>
  </div></main>
}
