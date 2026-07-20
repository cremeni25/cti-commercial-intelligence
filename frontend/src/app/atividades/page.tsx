"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Atividade {
  id: string
  titulo?: string
  tipo: string
  cliente_id?: string
  oportunidade_id?: string
  usuario_id?: string
  status: string
  data?: string
}

export default function AtividadesPage() {
  const [dados, setDados] = useState<Atividade[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [erro, setErro] = useState("")

  async function carregarAtividades() {
    try {
      const response = await fetch(`${API_URL}/crm/atividades`)
      const json = await response.json()
      setDados(Array.isArray(json) ? json : [])
    } catch (error) {
      console.error(error)
      setErro("Não foi possível carregar as atividades operacionais.")
    } finally {
      setLoading(false)
    }
  }

  async function criarAtividade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    const form = new FormData(event.currentTarget)
    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      oportunidade_id: String(form.get("oportunidade_id") || "") || undefined,
      usuario_id: String(form.get("usuario_id") || ""),
      tipo: String(form.get("tipo") || "follow-up"),
      titulo: String(form.get("titulo") || "") || undefined,
      descricao: String(form.get("descricao") || "") || undefined,
      data: String(form.get("data") || "") || undefined,
      horario: String(form.get("horario") || "") || undefined,
      status: "PENDENTE",
    }
    try {
      const response = await fetch(`${API_URL}/crm/atividades`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      if (!response.ok) throw new Error("Falha ao criar atividade")
      setMostrarFormulario(false)
      await carregarAtividades()
    } catch (error) {
      console.error(error)
      setErro("Não foi possível criar a atividade. Informe cliente, responsável e tipo.")
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      if (new URLSearchParams(window.location.search).get("novo") === "1") setMostrarFormulario(true)
      void carregarAtividades()
    })
  }, [])

  const pendentes = dados.filter((item) => item.status === "PENDENTE").length
  const concluidas = dados.filter((item) => item.status === "CONCLUIDA").length

  return (
    <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="flex-1"><Topbar /><div className="p-8 space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between"><div><h1 className="text-4xl font-bold text-white">CRM • Atividades</h1><p className="text-gray-400 mt-2">Ligações, visitas, reuniões, follow-up, tarefas, lembretes e observações vinculadas ao CRM.</p></div><button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova atividade</button></div>
      {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
      {mostrarFormulario && <form onSubmit={criarAtividade} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200"><h2 className="text-xl font-bold text-white">Cadastro de nova atividade</h2><p className="mt-2 text-sm text-gray-400">Ao salvar, a atividade atualiza automaticamente o histórico da oportunidade quando houver vínculo informado.</p><div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3"><Campo nome="cliente_id" label="Cliente" obrigatorio /><Campo nome="oportunidade_id" label="Oportunidade" /><Campo nome="usuario_id" label="Responsável" obrigatorio /><Campo nome="tipo" label="Tipo" padrao="follow-up" obrigatorio /><Campo nome="titulo" label="Título" /><Campo nome="data" label="Data" tipo="date" /><Campo nome="horario" label="Horário" tipo="time" /><Campo nome="descricao" label="Descrição" /></div><div className="mt-5 flex gap-3"><button className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Salvar atividade</button><button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button></div></form>}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Total Atividades" valor={dados.length} /><Kpi titulo="Pendentes" valor={pendentes} /><Kpi titulo="Concluídas" valor={concluidas} /></section>
      <Contexto />
      <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden"><div className="p-6 border-b border-[#13203f]"><h2 className="text-white text-xl font-semibold">Atividades Comerciais</h2></div>{loading ? <div className="p-10 text-gray-400">Carregando...</div> : dados.length === 0 ? <EstadoVazio onNova={() => setMostrarFormulario(true)} /> : <table className="w-full"><thead><tr className="text-left border-b border-[#13203f]"><th className="p-4 text-gray-400">Título</th><th className="p-4 text-gray-400">Tipo</th><th className="p-4 text-gray-400">Cliente</th><th className="p-4 text-gray-400">Responsável</th><th className="p-4 text-gray-400">Status</th><th className="p-4 text-gray-400">Data</th></tr></thead><tbody>{dados.map((item) => <tr key={item.id} className="border-b border-[#13203f]"><td className="p-4 text-white">{item.titulo || "Atividade"}</td><td className="p-4 text-gray-300">{item.tipo}</td><td className="p-4 text-white">{item.cliente_id}</td><td className="p-4 text-gray-300">{item.usuario_id}</td><td className="p-4 text-cyan-400">{item.status}</td><td className="p-4 text-yellow-400">{item.data || "-"}</td></tr>)}</tbody></table>}</div>
    </div></section></main>
  )
}

function Campo({ nome, label, tipo = "text", obrigatorio = false, padrao = "" }: { nome: string; label: string; tipo?: string; obrigatorio?: boolean; padrao?: string }) { return <label className="text-sm text-gray-300">{label}<input name={nome} type={tipo} required={obrigatorio} defaultValue={padrao} className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /></label> }
function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) { return <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]"><p className="text-gray-400 text-sm">{titulo}</p><h2 className="text-3xl text-cyan-400 font-bold mt-2">{valor}</h2></div> }
function Contexto() { return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-5 text-sm text-gray-300"><h2 className="text-white font-semibold mb-2">Contexto dos indicadores</h2><p><strong>Origem dos indicadores:</strong> CRM Operacional.</p><p><strong>Período considerado:</strong> atividades cadastradas e atualizadas no CRM.</p><p><strong>Significado operacional:</strong> ações de relacionamento e execução associadas a oportunidades, propostas ou pedidos.</p><p><strong>Critério de cálculo:</strong> contagem dos registros de atividades por status.</p><p><strong>Finalidade operacional:</strong> orientar o próximo contato e manter o histórico da oportunidade atualizado.</p></div> }
function EstadoVazio({ onNova }: { onNova: () => void }) { return <div className="p-10 text-gray-300 space-y-4"><p><strong>Por que não existem registros:</strong> nenhuma atividade foi cadastrada no CRM.</p><p><strong>O que esta tela representa:</strong> o plano de ações comerciais vinculado às oportunidades.</p><p><strong>Próximo passo esperado:</strong> cadastrar a primeira atividade.</p><button type="button" onClick={onNova} className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950">Nova atividade</button></div> }
