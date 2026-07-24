"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Atividade = {
  id: string
  titulo?: string
  descricao?: string
  tipo: string
  cliente_id?: string
  oportunidade_id?: string
  oportunidade_titulo?: string
  responsavel_id?: string
  usuario_id?: string
  status: string
  situacao: "ATRASADA" | "HOJE" | "FUTURA" | "SEM_DATA" | "CONCLUIDA" | "CANCELADA"
  data?: string
  horario?: string
}

type AgendaResponse = {
  itens: Atividade[]
  resumo: { total: number; atrasadas: number; hoje: number; futuras: number; sem_data: number; concluidas: number }
}

type ClienteMestre = { nome: string }
type Oportunidade = { id: string; titulo: string; cliente_id?: string }

const tipos = ["FOLLOW_UP", "LIGACAO", "VISITA_COMERCIAL", "VISITA_TECNICA", "REUNIAO", "EMAIL", "WHATSAPP", "TAREFA", "LEMBRETE"]

export default function AtividadesPage() {
  const [agenda, setAgenda] = useState<AgendaResponse>({ itens: [], resumo: { total: 0, atrasadas: 0, hoje: 0, futuras: 0, sem_data: 0, concluidas: 0 } })
  const [clientes, setClientes] = useState<ClienteMestre[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState("ABERTAS")

  async function carregar() {
    setLoading(true)
    try {
      const [agendaResponse, clientesResponse, oportunidadesResponse] = await Promise.all([
        fetch(`${API_URL}/crm/agenda`),
        fetch(`${API_URL}/modulos/clientes?contexto=brasil&periodo=TODO_HISTORICO`),
        fetch(`${API_URL}/crm/oportunidades`),
      ])
      if (!agendaResponse.ok || !clientesResponse.ok || !oportunidadesResponse.ok) throw new Error("Falha de carregamento")
      const [agendaJson, clientesJson, oportunidadesJson] = await Promise.all([agendaResponse.json(), clientesResponse.json(), oportunidadesResponse.json()])
      setAgenda(agendaJson)
      setClientes(Array.isArray(clientesJson) ? clientesJson : [])
      setOportunidades(Array.isArray(oportunidadesJson) ? oportunidadesJson : [])
    } catch {
      setErro("Não foi possível carregar a agenda comercial e seus vínculos.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("novo") === "1") setMostrarFormulario(true)
    void carregar()
  }, [])

  async function criarAtividade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    const form = new FormData(event.currentTarget)
    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      oportunidade_id: String(form.get("oportunidade_id") || "") || undefined,
      usuario_id: String(form.get("usuario_id") || ""),
      tipo: String(form.get("tipo") || "FOLLOW_UP"),
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
      await carregar()
    } catch {
      setErro("Não foi possível criar a atividade. Informe cliente, responsável, tipo e data do próximo contato.")
    }
  }

  async function concluir(id: string) {
    try {
      const response = await fetch(`${API_URL}/crm/atividades/${id}/concluir`, { method: "PUT" })
      if (!response.ok) throw new Error("Falha ao concluir")
      await carregar()
    } catch {
      setErro("Não foi possível concluir a atividade.")
    }
  }

  const itensFiltrados = agenda.itens.filter((item) => {
    if (filtro === "TODAS") return true
    if (filtro === "ABERTAS") return !["CONCLUIDA", "CANCELADA"].includes(item.situacao)
    return item.situacao === filtro
  })

  return (
    <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between"><div><h1 className="text-4xl font-bold text-white">CRM • Agenda e Follow-up</h1><p className="mt-2 text-gray-400">Próximos contatos, visitas, reuniões e tarefas vinculados aos clientes e oportunidades existentes.</p></div><button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova atividade</button></div>
      {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

      {mostrarFormulario && <form onSubmit={criarAtividade} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200"><h2 className="text-xl font-bold text-white">Agendar atividade comercial</h2><p className="mt-2 text-sm text-gray-400">O registro utiliza os clientes e oportunidades já existentes e passa a integrar o histórico comercial.</p><div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
        <label className="text-sm text-gray-300">Cliente da base<input name="cliente_id" list="clientes-agenda" required className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /><datalist id="clientes-agenda">{clientes.map((cliente) => <option key={cliente.nome} value={cliente.nome} />)}</datalist></label>
        <label className="text-sm text-gray-300">Oportunidade<select name="oportunidade_id" className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white"><option value="">Sem vínculo específico</option>{oportunidades.map((item) => <option key={item.id} value={item.id}>{item.titulo} • {item.cliente_id || "Cliente"}</option>)}</select></label>
        <Campo nome="usuario_id" label="Responsável comercial" obrigatorio />
        <label className="text-sm text-gray-300">Tipo<select name="tipo" className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white">{tipos.map((tipo) => <option key={tipo}>{tipo}</option>)}</select></label>
        <Campo nome="titulo" label="Assunto" obrigatorio /><Campo nome="data" label="Data" tipo="date" obrigatorio /><Campo nome="horario" label="Horário" tipo="time" /><Campo nome="descricao" label="Orientação / observação" />
      </div><div className="mt-5 flex gap-3"><button className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Salvar atividade</button><button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button></div></form>}

      <section className="grid grid-cols-2 gap-4 md:grid-cols-6"><Kpi titulo="Total" valor={agenda.resumo.total} /><Kpi titulo="Atrasadas" valor={agenda.resumo.atrasadas} destaque="text-red-400" /><Kpi titulo="Hoje" valor={agenda.resumo.hoje} destaque="text-yellow-400" /><Kpi titulo="Futuras" valor={agenda.resumo.futuras} /><Kpi titulo="Sem data" valor={agenda.resumo.sem_data} /><Kpi titulo="Concluídas" valor={agenda.resumo.concluidas} destaque="text-green-400" /></section>

      <div className="flex flex-wrap gap-2">{["ABERTAS", "ATRASADA", "HOJE", "FUTURA", "CONCLUIDA", "TODAS"].map((item) => <button key={item} type="button" onClick={() => setFiltro(item)} className={`rounded-lg px-4 py-2 text-sm font-semibold ${filtro === item ? "bg-cyan-500 text-slate-950" : "border border-[#20345e] text-gray-300"}`}>{item}</button>)}</div>

      <div className="overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">{loading ? <div className="p-10 text-gray-400">Carregando agenda...</div> : itensFiltrados.length === 0 ? <div className="p-10 text-gray-300">Nenhuma atividade encontrada neste filtro.</div> : <table className="w-full text-left"><thead><tr className="border-b border-[#13203f] text-gray-400"><th className="p-4">Situação</th><th className="p-4">Data/Hora</th><th className="p-4">Atividade</th><th className="p-4">Cliente</th><th className="p-4">Oportunidade</th><th className="p-4">Responsável</th><th className="p-4">Ação</th></tr></thead><tbody>{itensFiltrados.map((item) => <tr key={item.id} className="border-b border-[#13203f] text-gray-200"><td className="p-4"><Situacao valor={item.situacao} /></td><td className="p-4 text-yellow-300">{formatarData(item.data)} {item.horario || ""}</td><td className="p-4"><div className="font-semibold text-white">{item.titulo || item.tipo}</div><div className="text-xs text-gray-400">{item.tipo}</div></td><td className="p-4 text-cyan-300">{item.cliente_id || "-"}</td><td className="p-4">{item.oportunidade_titulo || "-"}</td><td className="p-4">{item.responsavel_id || item.usuario_id || "-"}</td><td className="p-4">{!["CONCLUIDA", "CANCELADA"].includes(item.situacao) && <button type="button" onClick={() => void concluir(item.id)} className="rounded-lg border border-green-500 px-3 py-2 text-xs font-semibold text-green-300">Concluir</button>}</td></tr>)}</tbody></table>}</div>
    </div></section></main>
  )
}

function formatarData(valor?: string) { if (!valor) return "-"; const [ano, mes, dia] = valor.slice(0, 10).split("-"); return `${dia}/${mes}/${ano}` }
function Campo({ nome, label, tipo = "text", obrigatorio = false }: { nome: string; label: string; tipo?: string; obrigatorio?: boolean }) { return <label className="text-sm text-gray-300">{label}<input name={nome} type={tipo} required={obrigatorio} className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /></label> }
function Kpi({ titulo, valor, destaque = "text-cyan-400" }: { titulo: string; valor: number; destaque?: string }) { return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5"><p className="text-sm text-gray-400">{titulo}</p><p className={`mt-2 text-3xl font-bold ${destaque}`}>{valor}</p></div> }
function Situacao({ valor }: { valor: Atividade["situacao"] }) { const classe = valor === "ATRASADA" ? "border-red-500 text-red-300" : valor === "HOJE" ? "border-yellow-500 text-yellow-300" : valor === "CONCLUIDA" ? "border-green-500 text-green-300" : "border-cyan-700 text-cyan-300"; return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${classe}`}>{valor}</span> }
