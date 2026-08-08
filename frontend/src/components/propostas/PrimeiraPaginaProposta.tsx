/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useState } from "react"

type Campos = {
  voltagem: string | null
  valor_entrada: number | null
  autorizada_nome_endereco: string | null
  lynx_meses: number | null
}

type Resposta = {
  documento: string
  equipamento: string
  editavel: boolean
  campos: Campos
  aplicabilidade: Record<keyof Campos, boolean>
}

export default function PrimeiraPaginaProposta({ propostaId, compacto = false }: { propostaId: string; compacto?: boolean }) {
  const [dados, setDados] = useState<Resposta | null>(null)
  const [campos, setCampos] = useState<Campos>({ voltagem: null, valor_entrada: null, autorizada_nome_endereco: null, lynx_meses: null })
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [salvando, setSalvando] = useState(false)

  async function carregar() {
    setErro("")
    const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(propostaId)}/primeira-pagina`, { cache: "no-store" })
    const payload = await resposta.json().catch(() => ({}))
    if (!resposta.ok) throw new Error(String(payload.detail || "Não foi possível carregar os campos da primeira página."))
    setDados(payload)
    setCampos(payload.campos)
  }

  useEffect(() => { void carregar().catch((falha) => setErro(falha instanceof Error ? falha.message : "Falha ao carregar os campos.")) }, [propostaId])

  async function salvar() {
    setSalvando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(propostaId)}/primeira-pagina`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(campos),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || "Não foi possível salvar os campos."))
      setMensagem("Campos da primeira página salvos.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao salvar os campos.") }
    finally { setSalvando(false) }
  }

  if (!dados && !erro) return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-sm text-slate-400">Carregando campos da primeira página...</div>

  return <section className={`rounded-3xl border border-[#16325c] bg-[#07162b] ${compacto ? "p-4" : "p-6"}`}>
    <div><p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Documento oficial</p><h2 className="mt-1 text-lg font-bold">Campos variáveis da primeira página</h2>{dados && <p className="mt-1 text-sm text-slate-400">{dados.equipamento} • {dados.documento}</p>}</div>
    {erro && <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
    {mensagem && <div className="mt-4 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{mensagem}</div>}
    {dados && <div className="mt-5 grid gap-4 sm:grid-cols-2">
      {dados.aplicabilidade.voltagem && <Campo label="Voltagem"><input disabled={!dados.editavel} value={campos.voltagem ?? ""} onChange={(e) => setCampos({ ...campos, voltagem: e.target.value || null })} className="entrada" placeholder="Ex.: 220V / 380V" /></Campo>}
      {dados.aplicabilidade.valor_entrada && <Campo label="Valor da entrada"><input disabled={!dados.editavel} type="number" min="0" step="0.01" value={campos.valor_entrada ?? ""} onChange={(e) => setCampos({ ...campos, valor_entrada: e.target.value === "" ? null : Number(e.target.value) })} className="entrada" placeholder="0,00" /></Campo>}
      {dados.aplicabilidade.autorizada_nome_endereco && <Campo label="Nome e endereço da Autorizada"><textarea disabled={!dados.editavel} rows={3} value={campos.autorizada_nome_endereco ?? ""} onChange={(e) => setCampos({ ...campos, autorizada_nome_endereco: e.target.value || null })} className="entrada" /></Campo>}
      {dados.aplicabilidade.lynx_meses && <Campo label="Período Lynx Fleet (meses)"><input disabled={!dados.editavel} type="number" min="0" step="1" value={campos.lynx_meses ?? ""} onChange={(e) => setCampos({ ...campos, lynx_meses: e.target.value === "" ? null : Number(e.target.value) })} className="entrada" /></Campo>}
    </div>}
    {dados?.editavel ? <button disabled={salvando} onClick={() => void salvar()} className="mt-5 w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">{salvando ? "Salvando..." : "Salvar campos da primeira página"}</button> : <p className="mt-5 text-sm text-amber-300">Proposta já emitida: campos bloqueados para preservar o documento.</p>}
    <style jsx>{`.entrada{width:100%;border:1px solid #24466f;border-radius:12px;background:#020817;padding:12px;color:white}.entrada:disabled{opacity:.6}`}</style>
  </section>
}

function Campo({ label, children }: { label: string; children: React.ReactNode }) { return <label className="block"><span className="mb-2 block text-sm text-slate-300">{label}</span>{children}</label> }
