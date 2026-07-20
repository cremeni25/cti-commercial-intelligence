"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Proposta { id: string; numero?: string; cliente_id: string; oportunidade_id?: string; valor: number; status: string; validade?: string; responsavel_id?: string }

export default function PropostasPage() {
  const [dados, setDados] = useState<Proposta[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [erro, setErro] = useState("")

  async function carregarPropostas() {
    try { const response = await fetch(`${API_URL}/crm/propostas`); const json = await response.json(); setDados(Array.isArray(json) ? json : []) }
    catch (error) { console.error(error); setErro("Não foi possível carregar as propostas operacionais.") }
    finally { setLoading(false) }
  }

  async function criarProposta(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setErro("")
    const form = new FormData(event.currentTarget)
    const payload = { numero: String(form.get("numero") || ""), cliente_id: String(form.get("cliente_id") || ""), oportunidade_id: String(form.get("oportunidade_id") || ""), responsavel_id: String(form.get("responsavel_id") || "") || undefined, valor: Number(form.get("valor") || 0), status: String(form.get("status") || "ELABORACAO"), validade: String(form.get("validade") || "") || undefined, produtos: String(form.get("produtos") || "") || undefined, equipamentos: String(form.get("equipamentos") || "") || undefined, condicoes: String(form.get("condicoes") || "") || undefined, observacoes: String(form.get("observacoes") || "") || undefined }
    try { const response = await fetch(`${API_URL}/crm/propostas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); if (!response.ok) throw new Error("Falha ao criar proposta"); setMostrarFormulario(false); await carregarPropostas() }
    catch (error) { console.error(error); setErro("Não foi possível criar a proposta. Toda proposta precisa de uma oportunidade existente vinculada.") }
  }

  useEffect(() => { queueMicrotask(() => { if (new URLSearchParams(window.location.search).get("novo") === "1") setMostrarFormulario(true); void carregarPropostas() }) }, [])

  const valorTotal = dados.reduce((acc, item) => acc + (item.valor || 0), 0)
  const emAnalise = dados.filter((item) => item.status === "EM_ANALISE").length
  const aprovadas = dados.filter((item) => item.status === "APROVADA").length

  return <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="flex-1"><Topbar /><div className="p-8 space-y-6">
    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between"><div><h1 className="text-4xl font-bold text-white">CRM • Propostas</h1><p className="text-gray-400 mt-2">Propostas criadas exclusivamente a partir de oportunidades existentes.</p></div><button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova proposta</button></div>
    {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
    {mostrarFormulario && <form onSubmit={criarProposta} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200"><h2 className="text-xl font-bold text-white">Cadastro de nova proposta</h2><p className="mt-2 text-sm text-gray-400">Informe obrigatoriamente a oportunidade existente. O backend bloqueia proposta isolada.</p><div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3"><Campo nome="numero" label="Número" obrigatorio /><Campo nome="cliente_id" label="Cliente" obrigatorio /><Campo nome="oportunidade_id" label="Oportunidade" obrigatorio /><Campo nome="responsavel_id" label="Responsável" /><Campo nome="valor" label="Valor" tipo="number" obrigatorio /><Campo nome="validade" label="Validade" tipo="date" /><Campo nome="status" label="Status" padrao="ELABORACAO" /><Campo nome="produtos" label="Produtos" /><Campo nome="equipamentos" label="Equipamentos" /><Campo nome="condicoes" label="Condições" /><Campo nome="observacoes" label="Observações" /></div><div className="mt-5 flex gap-3"><button className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Salvar proposta</button><button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button></div></form>}
    <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Total Propostas" valor={dados.length} /><Kpi titulo="Valor Total" valor={`R$ ${valorTotal.toLocaleString("pt-BR")}`} /><Kpi titulo="Em Análise" valor={emAnalise} /><Kpi titulo="Aprovadas" valor={aprovadas} /></section>
    <Contexto />
    <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden"><div className="p-6 border-b border-[#13203f]"><h2 className="text-white text-xl font-semibold">Propostas Comerciais</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : dados.length === 0 ? <EstadoVazio onNova={() => setMostrarFormulario(true)} /> : <table className="w-full"><thead><tr className="border-b border-[#13203f]"><th className="p-4 text-left text-gray-400">Cliente</th><th className="p-4 text-left text-gray-400">Proposta</th><th className="p-4 text-left text-gray-400">Oportunidade</th><th className="p-4 text-left text-gray-400">Valor</th><th className="p-4 text-left text-gray-400">Status</th><th className="p-4 text-left text-gray-400">Validade</th></tr></thead><tbody>{dados.map((item) => <tr key={item.id} className="border-b border-[#13203f]"><td className="p-4 text-white">{item.cliente_id}</td><td className="p-4 text-white">{item.numero || item.id}</td><td className="p-4 text-gray-300">{item.oportunidade_id}</td><td className="p-4 text-green-400">R$ {(item.valor || 0).toLocaleString("pt-BR")}</td><td className="p-4 text-cyan-400">{item.status}</td><td className="p-4 text-white">{item.validade || "-"}</td></tr>)}</tbody></table>}</div>
  </div></section></main>
}

function Campo({ nome, label, tipo = "text", obrigatorio = false, padrao = "" }: { nome: string; label: string; tipo?: string; obrigatorio?: boolean; padrao?: string }) { return <label className="text-sm text-gray-300">{label}<input name={nome} type={tipo} required={obrigatorio} defaultValue={padrao} className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /></label> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]"><p className="text-gray-400 text-sm">{titulo}</p><h2 className="text-3xl text-cyan-400 font-bold mt-2">{valor}</h2></div> }
function Contexto() { return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-5 text-sm text-gray-300"><h2 className="text-white font-semibold mb-2">Contexto dos indicadores</h2><p><strong>Origem dos indicadores:</strong> CRM Operacional.</p><p><strong>Período considerado:</strong> propostas cadastradas e atualizadas no CRM.</p><p><strong>Significado operacional:</strong> proposta comercial vinculada obrigatoriamente a uma oportunidade existente.</p><p><strong>Critério de cálculo:</strong> soma dos valores de propostas e contagem por status.</p><p><strong>Finalidade operacional:</strong> conduzir a negociação até aprovação, rejeição, expiração ou cancelamento.</p></div> }
function EstadoVazio({ onNova }: { onNova: () => void }) { return <div className="p-10 text-gray-300 space-y-4"><p><strong>Por que não existem registros:</strong> nenhuma proposta foi cadastrada a partir de uma oportunidade.</p><p><strong>O que esta tela representa:</strong> propostas comerciais em elaboração, análise e negociação.</p><p><strong>Próximo passo esperado:</strong> iniciar uma proposta vinculada a uma oportunidade existente.</p><button type="button" onClick={onNova} className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950">Nova proposta</button></div> }
