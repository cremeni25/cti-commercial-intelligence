"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { CheckCircle2, ExternalLink, FilePlus2, Loader2, Paperclip, RefreshCw } from "lucide-react"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Documento = {
  id: string
  categoria: string
  nome_arquivo: string
  created_at?: string
  observacao?: string | null
  vinculado_proposta?: boolean
}
type Cadastro = {
  status?: string
  status_calculado?: string
  validado_carrier_em?: string | null
  valido_ate?: string | null
  dias_para_vencer?: number | null
  observacao?: string | null
}
type Dossie = { cadastro: Cadastro | null; documentos: Documento[] }

const categorias = [
  ["CONTRATO_SOCIAL", "Contrato Social"],
  ["ULTIMA_ALTERACAO", "Última alteração contratual"],
  ["FATURAMENTO_12_MESES", "Faturamento dos últimos 12 meses"],
  ["DRE_ASSINADA", "DRE assinada pelo contador"],
  ["BALANCO_ASSINADO", "Balanço assinado pelo contador"],
  ["OUTRO", "Outro documento"],
] as const

const statusLabel: Record<string, string> = {
  EM_PREPARACAO: "Em preparação",
  EM_ANALISE: "Em análise pela Carrier",
  VALIDADO_CARRIER: "Validado pela Carrier",
  PROXIMO_VENCIMENTO: "Próximo do vencimento",
  VENCIDO: "Vencido — renovação necessária",
  RENOVACAO_EM_ANALISE: "Renovação em análise",
}

function dataBr(valor?: string | null) {
  if (!valor) return "—"
  const d = new Date(`${valor.slice(0, 10)}T12:00:00`)
  return Number.isNaN(d.getTime()) ? valor : new Intl.DateTimeFormat("pt-BR").format(d)
}

export default function DossieFinanceiroCarrier({ propostaId, compacto = false }: { propostaId: string; compacto?: boolean }) {
  const [dossie, setDossie] = useState<Dossie | null>(null)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [categoria, setCategoria] = useState("CONTRATO_SOCIAL")
  const [observacao, setObservacao] = useState("")
  const [validadoEm, setValidadoEm] = useState("")
  const [status, setStatus] = useState("EM_PREPARACAO")
  const fileRef = useRef<HTMLInputElement>(null)

  const statusAtual = String(dossie?.cadastro?.status_calculado || dossie?.cadastro?.status || "EM_PREPARACAO")
  const vinculados = useMemo(() => dossie?.documentos.filter((d) => d.vinculado_proposta).length || 0, [dossie])

  async function carregar() {
    setCarregando(true)
    setErro("")
    try {
      const r = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro`, { cache: "no-store" })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String(p.detail || "Não foi possível carregar o dossiê financeiro."))
      setDossie(p)
      setStatus(String(p.cadastro?.status || "EM_PREPARACAO"))
      setValidadoEm(String(p.cadastro?.validado_carrier_em || ""))
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível carregar o dossiê financeiro.")
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => { if (propostaId) void carregar() }, [propostaId])

  async function anexar() {
    const arquivo = fileRef.current?.files?.[0]
    if (!arquivo) { setErro("Selecione um arquivo."); return }
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const form = new FormData()
      form.append("categoria", categoria)
      if (observacao.trim()) form.append("observacao", observacao.trim())
      form.append("arquivo", arquivo)
      const r = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro/documentos`, { method: "POST", body: form })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String(p.detail || "Não foi possível anexar o documento."))
      setMensagem("Documento anexado ao cliente e vinculado a esta proposta.")
      setObservacao("")
      if (fileRef.current) fileRef.current.value = ""
      await carregar()
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível anexar o documento.") }
    finally { setProcessando(false) }
  }

  async function alternarVinculo(doc: Documento) {
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const path = doc.vinculado_proposta
        ? `crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro/documentos/${encodeURIComponent(doc.id)}/vinculo`
        : `crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro/vincular`
      const r = await fetchCrmSeguroProxy(path, doc.vinculado_proposta
        ? { method: "DELETE" }
        : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ documento_id: doc.id }) })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String(p.detail || "Não foi possível atualizar o vínculo."))
      setMensagem(doc.vinculado_proposta ? "Documento desvinculado desta proposta; permanece no cliente." : "Documento do cliente vinculado a esta proposta.")
      await carregar()
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível atualizar o vínculo.") }
    finally { setProcessando(false) }
  }

  async function abrir(doc: Documento) {
    setErro("")
    const r = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro/documentos/${encodeURIComponent(doc.id)}/url`, { cache: "no-store" })
    const p = await r.json().catch(() => ({}))
    if (!r.ok || !p.url) { setErro(String(p.detail || "Não foi possível abrir o documento.")); return }
    window.open(String(p.url), "_blank", "noopener,noreferrer")
  }

  async function salvarCadastro() {
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const r = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(propostaId)}/dossie-financeiro/cadastro`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, validado_carrier_em: status === "VALIDADO_CARRIER" ? validadoEm || null : null, observacao: dossie?.cadastro?.observacao || null }),
      })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String(p.detail || "Não foi possível atualizar o cadastro financeiro."))
      setMensagem(status === "VALIDADO_CARRIER" ? "Validação Carrier registrada. Validade calculada por 12 meses." : "Situação financeira atualizada.")
      await carregar()
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível atualizar o cadastro financeiro.") }
    finally { setProcessando(false) }
  }

  return <section className={`rounded-3xl border border-[#16325c] bg-[#07162b] ${compacto ? "p-5" : "p-6"}`}>
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Crédito Carrier</p><h3 className={compacto ? "mt-1 font-bold" : "mt-1 text-xl font-bold"}>Dossiê financeiro do cliente</h3><p className="mt-1 text-sm text-slate-400">Documentos pertencem ao cliente; o vínculo registra quais foram usados nesta proposta.</p></div>
      <button type="button" onClick={() => void carregar()} disabled={carregando || processando} className="w-fit rounded-xl border border-[#24466f] px-3 py-2 text-sm text-cyan-200 disabled:opacity-40"><RefreshCw className="mr-2 inline" size={15}/>Atualizar</button>
    </div>
    {erro && <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
    {mensagem && <div className="mt-4 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{mensagem}</div>}
    {carregando ? <div className="grid min-h-24 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">Cadastro financeiro</p><strong className="mt-1 block text-cyan-200">{statusLabel[statusAtual] || statusAtual}</strong></div>
        <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">Validade Carrier</p><strong className="mt-1 block">{dataBr(dossie?.cadastro?.valido_ate)}</strong></div>
        <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">Nesta proposta</p><strong className="mt-1 block">{vinculados} documento(s)</strong></div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
        <label className="block"><span className="mb-2 block text-xs text-slate-400">Situação</span><select value={status} onChange={(e)=>setStatus(e.target.value)} className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-sm"><option value="EM_PREPARACAO">Em preparação</option><option value="EM_ANALISE">Em análise pela Carrier</option><option value="VALIDADO_CARRIER">Validado pela Carrier</option><option value="RENOVACAO_EM_ANALISE">Renovação em análise</option></select></label>
        <label className="block"><span className="mb-2 block text-xs text-slate-400">Data de validação Carrier</span><input type="date" value={validadoEm} onChange={(e)=>setValidadoEm(e.target.value)} disabled={status!=="VALIDADO_CARRIER"} className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-sm disabled:opacity-40"/></label>
        <button type="button" onClick={()=>void salvarCadastro()} disabled={processando || (status==="VALIDADO_CARRIER"&&!validadoEm)} className="self-end rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200 disabled:opacity-40"><CheckCircle2 className="mr-2 inline" size={16}/>Salvar</button>
      </div>
      {dossie?.cadastro?.validado_carrier_em && <p className="mt-2 text-xs text-slate-400">Validado em {dataBr(dossie.cadastro.validado_carrier_em)}. A renovação ocorre 12 meses após a validação.</p>}

      <div className="mt-6 rounded-2xl border border-[#16325c] p-4"><h4 className="font-semibold">Adicionar documento</h4><div className="mt-3 grid gap-3 sm:grid-cols-2"><select value={categoria} onChange={(e)=>setCategoria(e.target.value)} className="rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-sm">{categorias.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select><input ref={fileRef} type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" className="rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-sm"/></div><input value={observacao} onChange={(e)=>setObservacao(e.target.value)} placeholder="Observação opcional" className="mt-3 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-sm"/><button type="button" onClick={()=>void anexar()} disabled={processando} className="mt-3 rounded-xl bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950 disabled:opacity-40"><FilePlus2 className="mr-2 inline" size={16}/>Anexar ao cliente e à proposta</button></div>

      <div className="mt-6 space-y-2"><h4 className="font-semibold">Documentos do cliente</h4>{!dossie?.documentos?.length && <p className="text-sm text-slate-400">Nenhum documento financeiro cadastrado.</p>}{dossie?.documentos?.map((doc)=><div key={doc.id} className="flex flex-col gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><p className="truncate font-medium"><Paperclip className="mr-2 inline text-cyan-300" size={15}/>{doc.nome_arquivo}</p><p className="mt-1 text-xs text-slate-400">{categorias.find(([v])=>v===doc.categoria)?.[1] || doc.categoria}{doc.vinculado_proposta ? " · vinculado a esta proposta" : " · disponível no dossiê do cliente"}</p></div><div className="flex gap-2"><button type="button" onClick={()=>void abrir(doc)} className="rounded-lg border border-[#24466f] px-3 py-2 text-xs text-cyan-200"><ExternalLink className="mr-1 inline" size={14}/>Abrir</button><button type="button" disabled={processando} onClick={()=>void alternarVinculo(doc)} className="rounded-lg border border-[#24466f] px-3 py-2 text-xs disabled:opacity-40">{doc.vinculado_proposta ? "Desvincular da proposta" : "Vincular à proposta"}</button></div></div>)}</div>
    </>}
  </section>
}
