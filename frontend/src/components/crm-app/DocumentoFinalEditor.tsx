"use client"

import { useEffect, useState } from "react"
import { FilePenLine, Loader2, Save, X } from "lucide-react"
import { useParams } from "next/navigation"

type Registro = Record<string, unknown>
type Contexto = "proposta" | "pedido"

type Campos = {
  voltagem: string
  tipo_equipamento: string
  impostos: string
  acessorios: string
  condicao_pagamento: string
  possui_entrada: "" | "SIM" | "NAO"
  valor_entrada: string
  local_entrega: string
  autorizada_nome_endereco: string
  frete: string
  prazo_entrega: string
  validade: string
  lynx_meses: string
}

const vazio: Campos = {
  voltagem: "",
  tipo_equipamento: "",
  impostos: "04% ICMS/PIS/COFINS",
  acessorios: "",
  condicao_pagamento: "",
  possui_entrada: "",
  valor_entrada: "",
  local_entrega: "",
  autorizada_nome_endereco: "",
  frete: "",
  prazo_entrega: "",
  validade: "",
  lynx_meses: "",
}

function texto(valor: unknown) { return String(valor ?? "").trim() }

function normalizarCampos(raw: Registro | null | undefined): Campos {
  const possui = raw?.possui_entrada
  return {
    voltagem: texto(raw?.voltagem),
    tipo_equipamento: texto(raw?.tipo_equipamento),
    impostos: texto(raw?.impostos) || "04% ICMS/PIS/COFINS",
    acessorios: Array.isArray(raw?.acessorios) ? raw.acessorios.map(texto).filter(Boolean).join(", ") : texto(raw?.acessorios),
    condicao_pagamento: texto(raw?.condicao_pagamento),
    possui_entrada: possui === true || String(possui).toUpperCase() === "SIM" ? "SIM" : possui === false || ["NAO", "NÃO"].includes(String(possui).toUpperCase()) ? "NAO" : "",
    valor_entrada: texto(raw?.valor_entrada),
    local_entrega: texto(raw?.local_entrega),
    autorizada_nome_endereco: texto(raw?.autorizada_nome_endereco),
    frete: texto(raw?.frete),
    prazo_entrega: texto(raw?.prazo_entrega),
    validade: texto(raw?.validade).slice(0, 10),
    lynx_meses: texto(raw?.lynx_meses),
  }
}

export function DocumentoFinalEditor({ contexto }: { contexto: Contexto }) {
  const params = useParams<{ id: string }>()
  const registroId = String(params.id || "")
  const [aberto, setAberto] = useState(false)
  const [propostaId, setPropostaId] = useState("")
  const [campos, setCampos] = useState<Campos>(vazio)
  const [editavel, setEditavel] = useState(true)
  const [equipamento, setEquipamento] = useState("")
  const [carregando, setCarregando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")

  useEffect(() => {
    let ativo = true
    async function resolver() {
      if (!registroId) return
      try {
        let id = registroId
        if (contexto === "pedido") {
          const resposta = await fetch(`/api/crm-proxy/crm-documentos/pedidos/${encodeURIComponent(registroId)}`, { cache: "no-store" })
          const payload = await resposta.json().catch(() => ({}))
          if (!resposta.ok) return
          id = texto(payload?.proposta?.id)
        }
        if (ativo && id) setPropostaId(id)
      } catch { /* editor auxiliar não interfere no carregamento da página principal */ }
    }
    void resolver()
    return () => { ativo = false }
  }, [contexto, registroId])

  useEffect(() => {
    if (!aberto || !propostaId) return
    void carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberto, propostaId])

  async function carregar() {
    setCarregando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(propostaId)}/primeira-pagina`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível carregar os dados finais (${resposta.status}).`))
      setCampos(normalizarCampos(payload.campos as Registro))
      setEditavel(Boolean(payload.editavel))
      setEquipamento(texto(payload.equipamento))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar os dados finais.") }
    finally { setCarregando(false) }
  }

  function alterar<K extends keyof Campos>(chave: K, valor: Campos[K]) {
    setCampos((atual) => ({ ...atual, [chave]: valor }))
  }

  async function salvar() {
    if (!propostaId || !editavel) return
    setSalvando(true); setErro(""); setMensagem("")
    try {
      const payload: Registro = {
        ...campos,
        possui_entrada: campos.possui_entrada === "" ? null : campos.possui_entrada === "SIM",
        valor_entrada: campos.valor_entrada === "" ? null : Number(campos.valor_entrada.replace(",", ".")),
        lynx_meses: campos.lynx_meses === "" ? null : Number(campos.lynx_meses),
      }
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/propostas/${encodeURIComponent(propostaId)}/primeira-pagina`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const retorno = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(retorno.detail || `Não foi possível salvar os dados finais (${resposta.status}).`))
      setMensagem("Dados finais salvos. Proposta e pedido usarão este mesmo conteúdo.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao salvar os dados finais.") }
    finally { setSalvando(false) }
  }

  return <>
    <button type="button" onClick={() => setAberto(true)} className="fixed bottom-24 right-4 z-[70] flex items-center gap-2 rounded-full border border-cyan-700 bg-[#07162b] px-4 py-3 text-sm font-semibold text-cyan-200 shadow-2xl shadow-black/40">
      <FilePenLine size={18}/>Dados finais do documento
    </button>
    {aberto && <div className="fixed inset-0 z-[100] overflow-y-auto bg-black/70 p-3 backdrop-blur-sm sm:p-6">
      <div className="mx-auto max-w-3xl rounded-3xl border border-[#24466f] bg-[#07162b] p-5 text-white shadow-2xl">
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.22em] text-cyan-400">Documento oficial Carrier</p><h2 className="mt-1 text-xl font-bold">Dados finais da proposta / pedido</h2><p className="mt-1 text-sm text-slate-400">{equipamento || "Equipamento"} · o mesmo conteúdo será usado na proposta e no pedido.</p></div><button type="button" onClick={() => setAberto(false)} className="rounded-xl border border-[#24466f] p-2 text-slate-300"><X size={20}/></button></div>
        {!editavel && <div className="mt-4 rounded-2xl border border-amber-800 bg-amber-950/30 p-4 text-sm text-amber-200">O documento oficial já foi finalizado e está imutável. Estes campos ficam disponíveis apenas para consulta.</div>}
        {erro && <div className="mt-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
        {mensagem && <div className="mt-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-sm text-emerald-200">{mensagem}</div>}
        {carregando ? <div className="grid min-h-48 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <div className="mt-5 space-y-5">
          <section><h3 className="font-semibold text-cyan-200">Tabela técnica e valores complementares</h3><div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Campo label="Voltagem" value={campos.voltagem} disabled={!editavel} onChange={(v) => alterar("voltagem", v)} placeholder="Ex.: 12V / 24V"/>
            <Campo label="Tipo de equipamento / configuração" value={campos.tipo_equipamento} disabled={!editavel} onChange={(v) => alterar("tipo_equipamento", v)} placeholder="Ex.: Acoplado e elétrico"/>
            <Campo label="Impostos inclusos" value={campos.impostos} disabled={!editavel} onChange={(v) => alterar("impostos", v)}/>
            <Campo label="Acessórios / itens complementares" value={campos.acessorios} disabled={!editavel} onChange={(v) => alterar("acessorios", v)} placeholder="Descreva os acessórios incluídos"/>
          </div></section>
          <section><h3 className="font-semibold text-cyan-200">Condições de pagamento, entrega e validade</h3><div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Campo label="Condições de pagamento" value={campos.condicao_pagamento} disabled={!editavel} onChange={(v) => alterar("condicao_pagamento", v)} placeholder="Ex.: 30/60/90 dias"/>
            <Select label="Possui entrada?" value={campos.possui_entrada} disabled={!editavel} onChange={(v) => alterar("possui_entrada", v as Campos["possui_entrada"])} options={[['','Selecione'],['SIM','Sim'],['NAO','Não']]}/>
            <Campo label="Valor da entrada" value={campos.valor_entrada} disabled={!editavel || campos.possui_entrada === "NAO"} onChange={(v) => alterar("valor_entrada", v)} inputMode="decimal" placeholder="0,00"/>
            <Select label="Entrega" value={campos.local_entrega} disabled={!editavel} onChange={(v) => alterar("local_entrega", v)} options={[['','Selecione'],['AUTORIZADA CARRIER','Autorizada Carrier'],['ENDEREÇO CLIENTE','Endereço do cliente']]}/>
            <Campo label="Nome e endereço da autorizada" value={campos.autorizada_nome_endereco} disabled={!editavel} onChange={(v) => alterar("autorizada_nome_endereco", v)} placeholder="Preencher quando aplicável"/>
            <Select label="Frete" value={campos.frete} disabled={!editavel} onChange={(v) => alterar("frete", v)} options={[['','Selecione'],['CIF','CIF'],['FOB','FOB']]}/>
            <Campo label="Prazo de entrega" value={campos.prazo_entrega} disabled={!editavel} onChange={(v) => alterar("prazo_entrega", v)} placeholder="Ex.: 30 dias"/>
            <label className="text-sm text-slate-300">Validade da proposta<input type="date" value={campos.validade} disabled={!editavel} onChange={(e) => alterar("validade", e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-white disabled:opacity-60"/></label>
            <Campo label="Período Lynx Fleet (meses)" value={campos.lynx_meses} disabled={!editavel} onChange={(v) => alterar("lynx_meses", v)} inputMode="numeric" placeholder="Quando aplicável"/>
          </div></section>
          {editavel && <button type="button" disabled={salvando} onClick={() => void salvar()} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-50"><Save className="mr-2 inline" size={18}/>{salvando ? "Salvando..." : "Salvar dados finais do documento"}</button>}
        </div>}
      </div>
    </div>}
  </>
}

function Campo({ label, value, onChange, disabled, placeholder, inputMode }: { label: string; value: string; onChange: (value: string) => void; disabled: boolean; placeholder?: string; inputMode?: "decimal" | "numeric" }) {
  return <label className="text-sm text-slate-300">{label}<input value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} inputMode={inputMode} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-white disabled:opacity-60"/></label>
}

function Select({ label, value, onChange, disabled, options }: { label: string; value: string; onChange: (value: string) => void; disabled: boolean; options: [string, string][] }) {
  return <label className="text-sm text-slate-300">{label}<select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-white disabled:opacity-60">{options.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label>
}
