/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { useEffect, useState } from "react"

type Campos = {
  voltagem: string | null
  tipo_equipamento: string | null
  impostos: string | null
  acessorios: string | null
  condicao_pagamento: string | null
  possui_entrada: boolean | null
  valor_entrada: number | null
  local_entrega: string | null
  autorizada_nome_endereco: string | null
  frete: string | null
  prazo_entrega: string | null
  validade: string | null
  lynx_meses: number | null
}

type Resposta = {
  proposta_id: string
  item_id: string
  equipamento: string
  editavel: boolean
  campos: Campos
  valores_negociados?: {
    quantidade?: number
    preco_unitario?: number | string
    desconto_percentual?: number | string
    valor_proposta?: number | string
  }
}

const camposVazios: Campos = {
  voltagem: null,
  tipo_equipamento: null,
  impostos: "04% ICMS/PIS/COFINS",
  acessorios: null,
  condicao_pagamento: null,
  possui_entrada: null,
  valor_entrada: null,
  local_entrega: null,
  autorizada_nome_endereco: null,
  frete: null,
  prazo_entrega: null,
  validade: null,
  lynx_meses: null,
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export default function PrimeiraPaginaProposta({ propostaId, compacto = false }: { propostaId: string; compacto?: boolean }) {
  const [dados, setDados] = useState<Resposta | null>(null)
  const [campos, setCampos] = useState<Campos>(camposVazios)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [salvando, setSalvando] = useState(false)

  async function carregar() {
    setErro("")
    const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(propostaId)}/primeira-pagina`, { cache: "no-store" })
    const payload = await resposta.json().catch(() => ({}))
    if (!resposta.ok) throw new Error(String(payload.detail || "Não foi possível carregar os dados finais do documento."))
    setDados(payload)
    setCampos({ ...camposVazios, ...(payload.campos || {}) })
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
      if (!resposta.ok) throw new Error(String(payload.detail || "Não foi possível salvar os dados finais."))
      setMensagem("Dados finais salvos. A proposta e o pedido usarão este mesmo conteúdo.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao salvar os campos.") }
    finally { setSalvando(false) }
  }

  if (!dados && !erro) return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-sm text-slate-400">Carregando dados finais do documento...</div>

  return <section className={`rounded-3xl border border-[#16325c] bg-[#07162b] ${compacto ? "p-4" : "p-6"}`}>
    <div><p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Documento oficial Carrier</p><h2 className="mt-1 text-lg font-bold">Dados finais da proposta / pedido</h2>{dados && <p className="mt-1 text-sm text-slate-400">{dados.equipamento} • mesmo conteúdo documental para proposta e pedido</p>}</div>
    {erro && <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
    {mensagem && <div className="mt-4 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{mensagem}</div>}
    {dados?.valores_negociados && <div className="mt-4 grid gap-2 rounded-2xl border border-[#16325c] bg-[#020817] p-4 text-sm sm:grid-cols-4"><Resumo label="Quantidade" valor={String(dados.valores_negociados.quantidade ?? 1)}/><Resumo label="Valor unitário" valor={moeda(dados.valores_negociados.preco_unitario)}/><Resumo label="Desconto" valor={`${Number(dados.valores_negociados.desconto_percentual || 0).toLocaleString("pt-BR")}%`}/><Resumo label="Valor proposta" valor={moeda(dados.valores_negociados.valor_proposta)}/></div>}
    {dados && <div className="mt-5 space-y-6">
      <div><h3 className="mb-3 font-semibold text-cyan-200">Tabela técnica e complementos</h3><div className="grid gap-4 sm:grid-cols-2">
        <Campo label="Voltagem"><input disabled={!dados.editavel} value={campos.voltagem ?? ""} onChange={(e) => setCampos({ ...campos, voltagem: e.target.value || null })} className="entrada" placeholder="Ex.: 12V / 24V" /></Campo>
        <Campo label="Tipo de equipamento / configuração"><input disabled={!dados.editavel} value={campos.tipo_equipamento ?? ""} onChange={(e) => setCampos({ ...campos, tipo_equipamento: e.target.value || null })} className="entrada" placeholder="Ex.: Acoplado e elétrico" /></Campo>
        <Campo label="Impostos inclusos"><input disabled={!dados.editavel} value={campos.impostos ?? ""} onChange={(e) => setCampos({ ...campos, impostos: e.target.value || null })} className="entrada" /></Campo>
        <Campo label="Acessórios / Itens Complementares"><textarea disabled={!dados.editavel} rows={3} value={campos.acessorios ?? ""} onChange={(e) => setCampos({ ...campos, acessorios: e.target.value || null })} className="entrada" /></Campo>
      </div></div>
      <div><h3 className="mb-3 font-semibold text-cyan-200">Condições de pagamento, entrega e validade</h3><div className="grid gap-4 sm:grid-cols-2">
        <Campo label="Condições de pagamentos"><textarea disabled={!dados.editavel} rows={2} value={campos.condicao_pagamento ?? ""} onChange={(e) => setCampos({ ...campos, condicao_pagamento: e.target.value || null })} className="entrada" placeholder="Ex.: 30/60/90 dias" /></Campo>
        <Campo label="Possui entrada?"><select disabled={!dados.editavel} value={campos.possui_entrada === null ? "" : campos.possui_entrada ? "SIM" : "NAO"} onChange={(e) => setCampos({ ...campos, possui_entrada: e.target.value === "" ? null : e.target.value === "SIM", valor_entrada: e.target.value === "NAO" ? null : campos.valor_entrada })} className="entrada"><option value="">Selecione</option><option value="SIM">Sim</option><option value="NAO">Não</option></select></Campo>
        <Campo label="Valor da entrada"><input disabled={!dados.editavel || campos.possui_entrada === false} type="number" min="0" step="0.01" value={campos.valor_entrada ?? ""} onChange={(e) => setCampos({ ...campos, valor_entrada: e.target.value === "" ? null : Number(e.target.value) })} className="entrada" placeholder="0,00" /></Campo>
        <Campo label="Entrega"><select disabled={!dados.editavel} value={campos.local_entrega ?? ""} onChange={(e) => setCampos({ ...campos, local_entrega: e.target.value || null })} className="entrada"><option value="">Selecione</option><option value="AUTORIZADA CARRIER">Autorizada Carrier</option><option value="ENDEREÇO CLIENTE">Endereço do cliente</option></select></Campo>
        <Campo label="Nome e endereço da Autorizada"><textarea disabled={!dados.editavel} rows={3} value={campos.autorizada_nome_endereco ?? ""} onChange={(e) => setCampos({ ...campos, autorizada_nome_endereco: e.target.value || null })} className="entrada" /></Campo>
        <Campo label="Frete"><select disabled={!dados.editavel} value={campos.frete ?? ""} onChange={(e) => setCampos({ ...campos, frete: e.target.value || null })} className="entrada"><option value="">Selecione</option><option value="CIF">CIF</option><option value="FOB">FOB</option></select></Campo>
        <Campo label="Prazo de entrega"><input disabled={!dados.editavel} value={campos.prazo_entrega ?? ""} onChange={(e) => setCampos({ ...campos, prazo_entrega: e.target.value || null })} className="entrada" placeholder="Ex.: 30 dias" /></Campo>
        <Campo label="Validade da proposta"><input disabled={!dados.editavel} type="date" value={(campos.validade ?? "").slice(0, 10)} onChange={(e) => setCampos({ ...campos, validade: e.target.value || null })} className="entrada" /></Campo>
        <Campo label="Período Lynx Fleet (meses)"><input disabled={!dados.editavel} type="number" min="0" step="1" value={campos.lynx_meses ?? ""} onChange={(e) => setCampos({ ...campos, lynx_meses: e.target.value === "" ? null : Number(e.target.value) })} className="entrada" /></Campo>
      </div></div>
    </div>}
    {dados?.editavel ? <button disabled={salvando} onClick={() => void salvar()} className="mt-5 w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">{salvando ? "Salvando..." : "Salvar dados finais do documento"}</button> : <p className="mt-5 text-sm text-amber-300">Documento final já gerado: dados bloqueados para preservar sua imutabilidade.</p>}
    <style jsx>{`.entrada{width:100%;border:1px solid #24466f;border-radius:12px;background:#020817;padding:12px;color:white}.entrada:disabled{opacity:.6}`}</style>
  </section>
}

function Campo({ label, children }: { label: string; children: React.ReactNode }) { return <label className="block"><span className="mb-2 block text-sm text-slate-300">{label}</span>{children}</label> }
function Resumo({ label, valor }: { label: string; valor: string }) { return <div><span className="block text-xs text-slate-500">{label}</span><strong className="text-slate-200">{valor}</strong></div> }
