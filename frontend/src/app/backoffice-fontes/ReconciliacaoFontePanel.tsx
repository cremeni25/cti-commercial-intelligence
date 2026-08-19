"use client"

import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, CheckCircle2, DatabaseZap, Loader2, ShieldCheck, X } from "lucide-react"

import { getSupabaseClient } from "@/core/database/supabase"

const API = "/api/crm-proxy/backoffice-fontes"

type ItemReconciliacao = {
  id: string
  indice_semantico: number
  entidade_sugerida: string
  status_item: string
  chave_canonica?: string | null
  conflitos?: unknown
  dados_normalizados?: Record<string, unknown> | null
}

type Reconciliacao = {
  id: string
  fonte_id: string
  classificacao: string
  dominio_alvo: string
  status: string
  total_itens: number
  total_validos: number
  total_conflitos: number
  promocao_operacional_automatica: boolean
}

type Props = {
  fonteId: string
  nomeArquivo: string
  onClose: () => void
  onAtualizar: () => Promise<void> | void
}

async function tokenAtual(): Promise<string> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) throw new Error("Sessão ADMIN_MASTER não encontrada.")
  return data.session.access_token
}

async function requisitar(caminho: string, init?: RequestInit) {
  const token = await tokenAtual()
  const resposta = await fetch(`${API}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}`, ...(init?.headers || {}) },
  })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = typeof payload?.detail === "string" ? payload.detail : payload?.detail?.mensagem || `Falha ${resposta.status}`
    throw new Error(detalhe)
  }
  return payload
}

function rotuloDominio(dominio?: string) {
  switch (String(dominio || "").toUpperCase()) {
    case "CTI_ANFIR": return "ANFIR · mercado realizado"
    case "CRM_COMERCIAL": return "CRM · processo comercial / origem do Funil"
    case "CTI_TERRITORIAL": return "Territorial · inteligência geográfica"
    case "CTI_FINANCEIRO": return "Financeiro · domínio ainda bloqueado"
    default: return dominio || "Domínio ainda não definido"
  }
}

function entidadeSuportada(dominio: string, entidade: string) {
  const chave = `${dominio.toUpperCase()}::${entidade.toUpperCase()}`
  return chave === "CTI_ANFIR::ANFIR" || chave === "CRM_COMERCIAL::CLIENTE"
}

export default function ReconciliacaoFontePanel({ fonteId, nomeArquivo, onClose, onAtualizar }: Props) {
  const [reconciliacao, setReconciliacao] = useState<Reconciliacao | null>(null)
  const [itens, setItens] = useState<ItemReconciliacao[]>([])
  const [carregando, setCarregando] = useState(true)
  const [executando, setExecutando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  async function carregar() {
    const resposta = await requisitar(`/${fonteId}/reconciliacao`)
    setReconciliacao(resposta.reconciliacao || null)
    setItens(Array.isArray(resposta.itens) ? resposta.itens : [])
  }

  useEffect(() => {
    let ativo = true
    carregar()
      .catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao consultar reconciliação.") })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [fonteId])

  const suportePromocao = useMemo(() => {
    if (!reconciliacao || !itens.length) return false
    return itens.every((item) => entidadeSuportada(reconciliacao.dominio_alvo, item.entidade_sugerida))
  }, [itens, reconciliacao])

  async function executar(caminho: string, textoSucesso: string) {
    setExecutando(true)
    setErro("")
    setMensagem("")
    try {
      await requisitar(`/${fonteId}${caminho}`, { method: "POST" })
      setMensagem(textoSucesso)
      await carregar()
      await onAtualizar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha na operação de reconciliação.")
    } finally {
      setExecutando(false)
    }
  }

  return (
    <section className="mt-5 rounded-2xl border border-amber-900/70 bg-amber-950/10 p-4 sm:p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-300">ADMIN_MASTER · RECONCILIAÇÃO OPERACIONAL</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-100">{nomeArquivo}</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">Staging obrigatório antes de qualquer escrita operacional. ANFIR, CRM/Funil e demais domínios permanecem semanticamente separados.</p>
        </div>
        <button onClick={onClose} className="flex items-center gap-1 self-start rounded-lg border border-slate-700 px-2.5 py-1.5 text-xs text-slate-300"><X size={14} /> Fechar</button>
      </div>

      <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-900/60 bg-emerald-950/20 px-3 py-2 text-xs text-emerald-300">
        <ShieldCheck size={15} /> Promoção automática bloqueada. Toda promoção exige reconciliação aprovada pelo ADMIN_MASTER.
      </div>

      {carregando ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-400"><Loader2 className="animate-spin" size={17} /> Consultando staging...</div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Domínio</p><p className="mt-1 text-sm font-medium text-amber-200">{rotuloDominio(reconciliacao?.dominio_alvo)}</p></div>
            <div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Status</p><p className="mt-1 text-sm font-medium">{reconciliacao?.status || "NÃO PREPARADA"}</p></div>
            <div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Itens</p><p className="mt-1 text-xl font-semibold">{reconciliacao?.total_itens || 0}</p></div>
            <div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Válidos</p><p className="mt-1 text-xl font-semibold text-emerald-300">{reconciliacao?.total_validos || 0}</p></div>
            <div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Conflitos</p><p className={`mt-1 text-xl font-semibold ${(reconciliacao?.total_conflitos || 0) > 0 ? "text-red-300" : "text-emerald-300"}`}>{reconciliacao?.total_conflitos || 0}</p></div>
          </div>

          {(reconciliacao?.total_conflitos || 0) > 0 && (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-red-900 bg-red-950/20 px-3 py-3 text-sm text-red-200"><AlertTriangle className="mt-0.5 shrink-0" size={17} /><span>Existem conflitos. A aprovação e a promoção permanecem bloqueadas até a reconciliação ficar íntegra.</span></div>
          )}

          {itens.length > 0 && (
            <div className="mt-4 max-h-72 overflow-auto rounded-xl border border-[#253453]">
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead className="bg-[#091a33] uppercase tracking-wider text-slate-500"><tr><th className="px-3 py-2">#</th><th className="px-3 py-2">Entidade</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Chave canônica</th><th className="px-3 py-2">Promoção</th></tr></thead>
                <tbody>{itens.slice(0, 100).map((item) => <tr key={item.id} className="border-t border-[#13203f]"><td className="px-3 py-2 text-slate-500">{item.indice_semantico}</td><td className="px-3 py-2 text-slate-200">{item.entidade_sugerida}</td><td className="px-3 py-2 text-slate-300">{item.status_item}</td><td className="max-w-[280px] break-all px-3 py-2 text-slate-500">{item.chave_canonica || "—"}</td><td className="px-3 py-2">{reconciliacao && entidadeSuportada(reconciliacao.dominio_alvo, item.entidade_sugerida) ? <span className="text-emerald-300">Adaptador canônico</span> : <span className="text-amber-300">Bloqueada</span>}</td></tr>)}</tbody>
              </table>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            {!reconciliacao && <button disabled={executando} onClick={() => void executar("/reconciliacao/preparar", "Reconciliação preparada em staging. Revise os itens antes de aprovar.")} className="flex items-center gap-2 rounded-xl bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">{executando ? <Loader2 className="animate-spin" size={16} /> : <DatabaseZap size={16} />} Preparar reconciliação</button>}
            {reconciliacao?.status === "PREPARADA" && reconciliacao.total_conflitos === 0 && <button disabled={executando} onClick={() => void executar("/reconciliacao/aprovar", "Reconciliação aprovada. Os registros continuam em staging e ficaram PRONTO_PROMOCAO.")} className="flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">{executando ? <Loader2 className="animate-spin" size={16} /> : <CheckCircle2 size={16} />} Aprovar reconciliação</button>}
            {reconciliacao?.status === "PRONTO_PROMOCAO" && suportePromocao && <button disabled={executando} onClick={() => void executar("/reconciliacao/promover", "Promoção controlada concluída e auditada no domínio canônico.")} className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">{executando ? <Loader2 className="animate-spin" size={16} /> : <DatabaseZap size={16} />} Promover ao domínio canônico</button>}
            {reconciliacao?.status === "PRONTO_PROMOCAO" && !suportePromocao && <span className="rounded-xl border border-amber-900 px-3 py-2 text-xs text-amber-300">Promoção bloqueada: ainda não existe adaptador canônico seguro para todos os itens deste lote.</span>}
            {reconciliacao?.status === "PROMOVIDA" && <span className="flex items-center gap-2 rounded-xl border border-emerald-900 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-300"><CheckCircle2 size={16} /> Promoção concluída e rastreada.</span>}
          </div>
        </>
      )}

      {mensagem && <p className="mt-3 rounded-xl border border-emerald-900 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-300">{mensagem}</p>}
      {erro && <p className="mt-3 rounded-xl border border-red-900 bg-red-950/30 px-3 py-2 text-sm text-red-200">{erro}</p>}
    </section>
  )
}
