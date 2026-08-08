"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth"

type Campanha = { campanha: string; ativos: number; encerrados: number; created_at?: string }
type Previa = {
  campanha: string
  contagens: Record<string, number>
  ids: { oportunidades: string[]; propostas: string[]; pedidos: string[] }
  confirmacao_exigida: string
}

function papelDoUsuario(usuario: unknown): string {
  const item = (usuario || {}) as Record<string, unknown>
  return String(item.tipo_usuario || item.role || item.papel || item.perfil || "").trim().toUpperCase()
}

export default function TestesCampoMasterPage() {
  const { usuario } = useAuth()
  const [campanhas, setCampanhas] = useState<Campanha[]>([])
  const [previa, setPrevia] = useState<Previa | null>(null)
  const [confirmacao, setConfirmacao] = useState("")
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [carregando, setCarregando] = useState(false)
  const [processando, setProcessando] = useState(false)

  const papel = papelDoUsuario(usuario)
  const master = papel === "ADMIN_MASTER"
  const base = "/api/crm-proxy/master/testes-campo"

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const response = await fetch(base, { cache: "no-store" })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível carregar as campanhas de teste.")
      setCampanhas(Array.isArray(payload) ? payload : [])
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao carregar campanhas.")
    } finally { setCarregando(false) }
  }

  useEffect(() => { if (master) void carregar() }, [master])

  async function abrirPrevia(campanha: string) {
    setErro(""); setMensagem(""); setConfirmacao("")
    try {
      const response = await fetch(`${base}/${encodeURIComponent(campanha)}/previsualizar`, { cache: "no-store" })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "Não foi possível preparar a conferência.")
      setPrevia(payload)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao preparar conferência.") }
  }

  async function limpar() {
    if (!previa) return
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const response = await fetch(`${base}/${encodeURIComponent(previa.campanha)}/limpar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmacao }),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) throw new Error(payload?.detail || "A limpeza não foi concluída.")
      setMensagem(`Campanha ${previa.campanha} limpa. Auditoria: ${String(payload.hash_relatorio || "").slice(0, 16)}.`)
      setPrevia(null); setConfirmacao(""); await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha na limpeza.") }
    finally { setProcessando(false) }
  }

  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
    <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6"><Link href="/configuracoes" className="text-sm font-semibold text-cyan-300">← Voltar para configurações</Link><p className="mt-5 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-400">Administração MASTER</p><h1 className="mt-2 text-3xl font-bold">Testes de campo</h1><p className="mt-2 text-sm text-slate-400">Conferência e limpeza controlada de oportunidades, propostas, aceites, pedidos e vínculos criados exclusivamente em simulações.</p></header>
    {!master && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-5 text-red-200">Acesso exclusivo do ADMIN_MASTER.</div>}
    {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-5 text-red-200">{erro}</div>}
    {mensagem && <div className="rounded-2xl border border-emerald-900 bg-emerald-950/30 p-5 text-emerald-200">{mensagem}</div>}
    {master && <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Campanhas registradas</h2>{carregando ? <p className="mt-5 text-slate-400">Carregando...</p> : campanhas.length === 0 ? <p className="mt-5 text-slate-500">Nenhum teste de campo registrado.</p> : <div className="mt-5 space-y-3">{campanhas.map((item) => <article key={item.campanha} className="flex flex-col gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 md:flex-row md:items-center md:justify-between"><div><p className="font-semibold text-white">{item.campanha}</p><p className="mt-1 text-sm text-slate-400">{item.ativos} oportunidade(s) ativa(s) • {item.encerrados} encerrada(s)</p></div><button disabled={!item.ativos} onClick={() => void abrirPrevia(item.campanha)} className="rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-300 disabled:opacity-40">Conferir limpeza</button></article>)}</div>}</section>}
    {master && previa && <section className="rounded-3xl border border-amber-800 bg-amber-950/15 p-6"><h2 className="text-xl font-bold text-amber-200">Conferência obrigatória: {previa.campanha}</h2><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{Object.entries(previa.contagens).map(([chave, valor]) => <div key={chave} className="rounded-xl border border-amber-900/60 bg-[#071427] p-4"><p className="text-xs uppercase text-slate-500">{chave.replaceAll("_", " ")}</p><p className="mt-2 text-2xl font-bold text-amber-200">{valor}</p></div>)}</div><p className="mt-5 text-sm text-slate-300">A operação preserva o relatório permanente de auditoria, mas remove os registros comerciais da campanha.</p><label className="mt-5 block text-sm text-slate-300">Digite <strong>{previa.confirmacao_exigida}</strong><input value={confirmacao} onChange={(event) => setConfirmacao(event.target.value)} className="mt-2 w-full rounded-xl border border-amber-700 bg-[#020817] px-4 py-3 text-white" /></label><button disabled={processando || confirmacao.trim().toUpperCase() !== previa.confirmacao_exigida} onClick={() => void limpar()} className="mt-5 rounded-xl bg-red-600 px-5 py-3 font-semibold text-white disabled:opacity-40">{processando ? "Executando limpeza..." : "Excluir campanha de teste"}</button></section>}
  </div></section></main>
}
