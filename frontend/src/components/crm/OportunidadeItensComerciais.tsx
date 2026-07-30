/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { useAuth } from "@/core/auth"
import { API_URL } from "@/lib/api"

type Item = {
  id: string
  linha_produto: string
  equipamento: string
  configuracao?: string
  quantidade: number
  preco_unitario: number
  desconto_percentual: number
  valor_total?: number
  condicao_pagamento?: string
  prazo_entrega?: string
  validade_condicao?: string
  frete?: string
  local_entrega?: string
  garantia?: string
  opcionais?: string[]
  observacoes_comerciais?: string
  observacoes_tecnicas?: string
  status: string
}

type Proposta = {
  id: string
  numero?: string
  versao?: number
  valor?: number
  status_documento?: string
  validade?: string
}

const produtosPorLinha: Record<string, string[]> = {
  TRAILER: ["X4-7500", "X4-7700", "Vector HE19", "Vector 8600MT"],
  "DIESEL TRUCK": ["Supra 1150", "Supra 850", "Supra 850MT", "Supra 750"],
  "DIRECT DRIVE": ["CM500", "CM400", "CM280", "Xarios 350", "Xarios 600", "D7", "D7 AE", "D6", "D6 AE"],
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export default function OportunidadeItensComerciais({ oportunidadeId }: { oportunidadeId: string }) {
  const { usuario } = useAuth()
  const [itens, setItens] = useState<Item[]>([])
  const [propostas, setPropostas] = useState<Record<string, Proposta[]>>({})
  const [linha, setLinha] = useState("TRAILER")
  const [equipamento, setEquipamento] = useState(produtosPorLinha.TRAILER[0])
  const [mensagem, setMensagem] = useState("")
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)

  const equipamentos = useMemo(() => produtosPorLinha[linha] || [], [linha])

  const carregar = useCallback(async () => {
    if (!oportunidadeId) return
    setCarregando(true)
    setErro("")
    try {
      const resposta = await fetch(`${API_URL}/crm-documentos/oportunidades/${oportunidadeId}/itens`, { cache: "no-store" })
      const dados = await resposta.json().catch(() => [])
      if (!resposta.ok) throw new Error(dados?.detail || "Não foi possível carregar os itens comerciais.")
      const lista = Array.isArray(dados) ? dados : []
      setItens(lista)
      const pares = await Promise.all(lista.map(async (item: Item) => {
        const r = await fetch(`${API_URL}/crm-documentos/itens/${item.id}/propostas`, { cache: "no-store" })
        return [item.id, r.ok ? await r.json() : []] as const
      }))
      setPropostas(Object.fromEntries(pares))
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao carregar a negociação.")
    } finally {
      setCarregando(false)
    }
  }, [oportunidadeId])

  useEffect(() => { void carregar() }, [carregar])

  async function criarItem(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true)
    setErro("")
    setMensagem("")
    const dados = new FormData(evento.currentTarget)
    const payload = {
      linha_produto: linha,
      equipamento,
      configuracao: String(dados.get("configuracao") || "") || null,
      quantidade: Number(dados.get("quantidade") || 1),
      preco_unitario: Number(dados.get("preco_unitario") || 0),
      desconto_percentual: Number(dados.get("desconto_percentual") || 0),
      condicao_pagamento: String(dados.get("condicao_pagamento") || "") || null,
      prazo_entrega: String(dados.get("prazo_entrega") || "") || null,
      validade_condicao: String(dados.get("validade_condicao") || "") || null,
      frete: String(dados.get("frete") || "") || null,
      local_entrega: String(dados.get("local_entrega") || "") || null,
      garantia: String(dados.get("garantia") || "") || null,
      opcionais: String(dados.get("opcionais") || "").split(",").map((v) => v.trim()).filter(Boolean),
      observacoes_comerciais: String(dados.get("observacoes_comerciais") || "") || null,
      observacoes_tecnicas: String(dados.get("observacoes_tecnicas") || "") || null,
      ordem: itens.length,
    }
    try {
      const resposta = await fetch(`${API_URL}/crm-documentos/oportunidades/${oportunidadeId}/itens`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      })
      const retorno = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(retorno?.detail || "Não foi possível adicionar o item.")
      evento.currentTarget.reset()
      setMensagem("Item comercial adicionado à oportunidade.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao adicionar item.")
    } finally { setSalvando(false) }
  }

  async function acao(endpoint: string, body?: object, sucesso = "Operação concluída.") {
    setErro("")
    setMensagem("")
    const resposta = await fetch(`${API_URL}${endpoint}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    const retorno = await resposta.json().catch(() => null)
    if (!resposta.ok) throw new Error(retorno?.detail || "Não foi possível concluir a operação.")
    setMensagem(sucesso)
    await carregar()
    return retorno
  }

  async function gerarProposta(item: Item) {
    try {
      await acao(`/crm-documentos/itens/${item.id}/propostas`, {
        responsavel_id: String(usuario?.id || ""),
        validade: item.validade_condicao || null,
        observacoes: item.observacoes_comerciais || null,
        condicoes_adicionais: item.condicao_pagamento || null,
      }, "Proposta criada a partir dos dados do item, sem redigitação.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao gerar proposta.") }
  }

  async function emitir(proposta: Proposta) {
    try { await acao(`/crm-documentos/propostas/${proposta.id}/emitir`, undefined, "Proposta emitida.") }
    catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao emitir proposta.") }
  }

  async function solicitarAceite(proposta: Proposta, metodo: "PRESENCIAL_TELA" | "REMOTO_LINK") {
    const nome = window.prompt("Nome completo do signatário")?.trim()
    if (!nome) return
    const email = metodo === "REMOTO_LINK" ? window.prompt("E-mail do signatário")?.trim() : undefined
    try {
      const retorno = await acao(`/crm-documentos/propostas/${proposta.id}/aceites`, {
        metodo, nome_signatario: nome, email_signatario: email || null,
      }, metodo === "PRESENCIAL_TELA" ? "Aceite presencial iniciado." : "Link de aceite remoto gerado.")
      if (retorno?.link_token) window.prompt("Copie o identificador do link de aceite", String(retorno.link_token))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao solicitar aceite.") }
  }

  async function converterPedido(proposta: Proposta) {
    try {
      await acao(`/crm-documentos/propostas/${proposta.id}/converter-pedido`, {
        responsavel_id: String(usuario?.id || ""), origem_comercial: "CRM",
      }, "Pedido gerado a partir da proposta aceita.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao gerar pedido.") }
  }

  return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
    <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
      <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Negociação estruturada</p><h2 className="mt-2 text-2xl font-bold">Itens, propostas e pedidos</h2><p className="mt-2 text-sm text-slate-400">Cada equipamento possui condições próprias e pode gerar sua própria proposta e pedido.</p></div>
      <span className="text-sm text-cyan-300">{itens.length} item(ns)</span>
    </div>

    {erro && <div className="mt-5 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
    {mensagem && <div className="mt-5 rounded-xl border border-emerald-900 bg-emerald-950/30 p-4 text-sm text-emerald-200">{mensagem}</div>}

    <form onSubmit={criarItem} className="mt-6 grid gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-5 md:grid-cols-2 xl:grid-cols-4">
      <CampoSelect label="Linha" value={linha} onChange={(v) => { setLinha(v); setEquipamento(produtosPorLinha[v]?.[0] || "") }} opcoes={Object.keys(produtosPorLinha)} />
      <CampoSelect label="Equipamento" value={equipamento} onChange={setEquipamento} opcoes={equipamentos} />
      <Campo nome="configuracao" label="Configuração" />
      <Campo nome="quantidade" label="Quantidade" type="number" padrao="1" required />
      <Campo nome="preco_unitario" label="Preço unitário" type="number" padrao="0" step="0.01" required />
      <Campo nome="desconto_percentual" label="Desconto %" type="number" padrao="0" step="0.01" />
      <Campo nome="condicao_pagamento" label="Condição de pagamento" />
      <Campo nome="prazo_entrega" label="Prazo de entrega" />
      <Campo nome="validade_condicao" label="Validade" type="date" />
      <Campo nome="frete" label="Frete" />
      <Campo nome="local_entrega" label="Local de entrega" />
      <Campo nome="garantia" label="Garantia" />
      <Campo nome="opcionais" label="Opcionais, separados por vírgula" classe="md:col-span-2" />
      <Campo nome="observacoes_comerciais" label="Observações comerciais" classe="md:col-span-2" />
      <Campo nome="observacoes_tecnicas" label="Observações técnicas" classe="md:col-span-2" />
      <button disabled={salvando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60 md:col-span-2">{salvando ? "Adicionando..." : "Adicionar item à oportunidade"}</button>
    </form>

    <div className="mt-6 space-y-4">
      {carregando ? <p className="text-slate-400">Carregando itens...</p> : itens.length === 0 ? <p className="text-slate-500">Nenhum item comercial cadastrado.</p> : itens.map((item) => {
        const lista = propostas[item.id] || []
        return <article key={item.id} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">{item.linha_produto}</p><h3 className="mt-1 text-xl font-bold">{item.equipamento}</h3><p className="mt-2 text-sm text-slate-400">{item.quantidade} unidade(s) • {moeda(item.preco_unitario)} • desconto {Number(item.desconto_percentual || 0)}%</p><p className="mt-1 font-semibold text-emerald-300">Total: {moeda(item.valor_total ?? Number(item.quantidade) * Number(item.preco_unitario))}</p></div>
            <div className="flex flex-wrap gap-2"><span className="rounded-full border border-cyan-800 px-3 py-1 text-xs text-cyan-200">{item.status}</span><button onClick={() => void gerarProposta(item)} className="rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-950">Gerar proposta</button></div>
          </div>
          <div className="mt-4 grid gap-2 text-sm text-slate-300 md:grid-cols-3"><p>Pagamento: {item.condicao_pagamento || "A definir"}</p><p>Entrega: {item.prazo_entrega || "A definir"}</p><p>Garantia: {item.garantia || "A definir"}</p></div>
          {lista.length > 0 && <div className="mt-5 space-y-2 border-t border-[#16325c] pt-4">{lista.map((proposta) => <div key={proposta.id} className="flex flex-col gap-3 rounded-xl bg-[#061326] p-4 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold text-white">{proposta.numero || "Proposta"} • versão {proposta.versao || 1}</p><p className="text-xs text-slate-400">{proposta.status_documento} • {moeda(proposta.valor)}</p></div><div className="flex flex-wrap gap-2">{["RASCUNHO","EM_REVISAO","APROVADA_INTERNA"].includes(String(proposta.status_documento)) && <button onClick={() => void emitir(proposta)} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs text-cyan-300">Emitir</button>}{["EMITIDA","ENVIADA","VISUALIZADA","EM_NEGOCIACAO"].includes(String(proposta.status_documento)) && <><button onClick={() => void solicitarAceite(proposta, "PRESENCIAL_TELA")} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs text-cyan-300">Aceite presencial</button><button onClick={() => void solicitarAceite(proposta, "REMOTO_LINK")} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs text-cyan-300">Aceite por link</button></>}{String(proposta.status_documento) === "ACEITA" && <button onClick={() => void converterPedido(proposta)} className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-slate-950">Gerar pedido</button>}</div></div>)}</div>}
        </article>
      })}
    </div>
  </section>
}

function Campo({ nome, label, type = "text", padrao, step, required = false, classe = "" }: { nome: string; label: string; type?: string; padrao?: string; step?: string; required?: boolean; classe?: string }) {
  return <label className={`text-sm text-slate-300 ${classe}`}>{label}<input name={nome} type={type} defaultValue={padrao} step={step} required={required} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white" /></label>
}
function CampoSelect({ label, value, onChange, opcoes }: { label: string; value: string; onChange: (v: string) => void; opcoes: string[] }) {
  return <label className="text-sm text-slate-300">{label}<select value={value} onChange={(e) => onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3 text-white">{opcoes.map((opcao) => <option key={opcao}>{opcao}</option>)}</select></label>
}
