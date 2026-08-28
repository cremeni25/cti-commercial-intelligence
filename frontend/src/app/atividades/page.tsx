"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"
import { useAuth } from "@/core/auth"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type SituacaoCalendario = "ATRASADA" | "HOJE" | "FUTURA" | "SEM_DATA"

type Atividade = {
  id: string
  titulo?: string
  descricao?: string
  tipo: string
  cliente_id?: string
  cliente_nome?: string
  parceiro_nome?: string
  parceiro_tipo?: string
  parceiro_organizacao?: string
  oportunidade_id?: string
  oportunidade_titulo?: string
  responsavel_id?: string
  responsavel_nome?: string
  usuario_id?: string
  status: string
  situacao: "ATRASADA" | "HOJE" | "FUTURA" | "SEM_DATA" | "CONCLUIDA" | "CANCELADA"
  situacao_calendario?: SituacaoCalendario
  data?: string
  horario?: string
}

type AgendaResponse = {
  itens: Atividade[]
  resumo: { total: number; atrasadas: number; hoje: number; futuras: number; sem_data: number; concluidas: number }
}

type ClienteMestre = { id?: string; nome: string }
type Oportunidade = { id: string; titulo: string; cliente_id?: string; responsavel_id?: string }
type Registro = Record<string, unknown>

const tipos = ["FOLLOW_UP", "LIGACAO", "VISITA_COMERCIAL", "VISITA_TECNICA", "REUNIAO", "EMAIL", "WHATSAPP", "TAREFA", "LEMBRETE"]
const filtrosAgenda = ["ABERTAS", "ATRASADA", "HOJE", "FUTURA", "SEM_DATA", "CONCLUIDA", "TODAS"]

function estaConcluida(item: Atividade) {
  const status = String(item.status || "").toUpperCase()
  return status === "CONCLUIDA" || status === "CONCLUÍDA" || item.situacao === "CONCLUIDA"
}

function situacaoCalendario(item: Atividade): SituacaoCalendario {
  if (item.situacao_calendario) return item.situacao_calendario
  if (!item.data) return "SEM_DATA"
  const [ano, mes, dia] = item.data.slice(0, 10).split("-").map(Number)
  if (!ano || !mes || !dia) return "SEM_DATA"
  const hoje = new Date()
  const referencia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate()).getTime()
  const atividade = new Date(ano, mes - 1, dia).getTime()
  if (atividade < referencia) return "ATRASADA"
  if (atividade === referencia) return "HOJE"
  return "FUTURA"
}

function resumir(itens: Atividade[]): AgendaResponse["resumo"] {
  return {
    total: itens.length,
    atrasadas: itens.filter((i) => situacaoCalendario(i) === "ATRASADA").length,
    hoje: itens.filter((i) => situacaoCalendario(i) === "HOJE").length,
    futuras: itens.filter((i) => situacaoCalendario(i) === "FUTURA").length,
    sem_data: itens.filter((i) => situacaoCalendario(i) === "SEM_DATA").length,
    concluidas: itens.filter(estaConcluida).length,
  }
}

export default function AtividadesPage() {
  const { usuario } = useAuth()
  const [agenda, setAgenda] = useState<AgendaResponse>({ itens: [], resumo: { total: 0, atrasadas: 0, hoje: 0, futuras: 0, sem_data: 0, concluidas: 0 } })
  const [clientes, setClientes] = useState<ClienteMestre[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState("ABERTAS")
  const [detalhe, setDetalhe] = useState<Atividade | null>(null)
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false)

  async function carregar() {
    setLoading(true)
    try {
      const [agendaResponse, clientesResponse, nucleoResponse] = await Promise.all([
        fetchCrmSeguroProxy("crm-seguro/agenda", { cache: "no-store" }),
        fetch(`${API_URL}/modulos/clientes?contexto=brasil&periodo=TODO_HISTORICO`),
        fetchCrmSeguroProxy("crm-seguro/nucleo-comercial", { cache: "no-store" }),
      ])
      if (!agendaResponse.ok || !clientesResponse.ok || !nucleoResponse.ok) throw new Error("Falha de carregamento")
      const [agendaJson, clientesJson, nucleoJson] = await Promise.all([agendaResponse.json(), clientesResponse.json(), nucleoResponse.json()])
      setAgenda(agendaJson)
      setClientes(Array.isArray(clientesJson) ? clientesJson : [])
      const nucleo = Array.isArray(nucleoJson) ? nucleoJson as Registro[] : []
      const mapa = new Map<string, Oportunidade>()
      nucleo.forEach((item) => {
        const id = String(item.oportunidade_id || item.id || "").trim()
        if (!id || mapa.has(id)) return
        mapa.set(id, {
          id,
          titulo: String(item.titulo || "Oportunidade comercial"),
          cliente_id: item.cliente_id ? String(item.cliente_id) : undefined,
          responsavel_id: item.responsavel_id ? String(item.responsavel_id) : undefined,
        })
      })
      setOportunidades([...mapa.values()])
    } catch {
      setErro("Não foi possível carregar a agenda comercial e seus vínculos.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      if (new URLSearchParams(window.location.search).get("novo") === "1") setMostrarFormulario(true)
      void carregar()
    })
  }, [])

  const agendaEscopada = useMemo<AgendaResponse>(() => {
    const itens = agenda.itens.filter((item) => pertenceAoEscopoDoUsuario(item.usuario_id || item.responsavel_id, usuario))
    return { itens, resumo: resumir(itens) }
  }, [agenda.itens, usuario])

  const oportunidadesEscopadas = useMemo(
    () => oportunidades.filter((item) => pertenceAoEscopoDoUsuario(item.responsavel_id, usuario)),
    [oportunidades, usuario],
  )

  async function criarAtividade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")
    const form = new FormData(event.currentTarget)
    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      oportunidade_id: String(form.get("oportunidade_id") || "") || undefined,
      usuario_id: String(usuario?.id || form.get("usuario_id") || ""),
      tipo: String(form.get("tipo") || "FOLLOW_UP"),
      titulo: String(form.get("titulo") || "") || undefined,
      descricao: String(form.get("descricao") || "") || undefined,
      data: String(form.get("data") || "") || undefined,
      horario: String(form.get("horario") || "") || undefined,
      status: "PENDENTE",
    }
    try {
      const response = await fetchCrmSeguroProxy("crm-seguro/atividades", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      if (!response.ok) throw new Error("Falha ao criar atividade")
      setMostrarFormulario(false)
      await carregar()
    } catch {
      setErro("Não foi possível criar a atividade. Informe cliente, tipo e data do próximo contato.")
    }
  }

  async function concluir(id: string) {
    try {
      const response = await fetchCrmSeguroProxy(`crm-seguro/atividades/${id}/concluir`, { method: "PUT" })
      if (!response.ok) throw new Error("Falha ao concluir")
      await carregar()
    } catch {
      setErro("Não foi possível concluir a atividade.")
    }
  }

  async function abrirDetalhe(item: Atividade) {
    setDetalhe(item)
    setCarregandoDetalhe(true)
    try {
      const response = await fetchCrmSeguroProxy(`crm-seguro/atividades/${item.id}`, { cache: "no-store" })
      if (!response.ok) throw new Error("Falha ao carregar detalhe")
      const registro = await response.json() as Atividade
      setDetalhe({ ...item, ...registro })
    } catch {
      setErro("Não foi possível atualizar os detalhes desta atividade. Os dados já carregados continuam disponíveis.")
    } finally {
      setCarregandoDetalhe(false)
    }
  }

  function clienteLegivel(item: Atividade) {
    if (item.cliente_nome) return item.cliente_nome
    const encontrado = clientes.find((cliente) => cliente.id && cliente.id === item.cliente_id)
    return encontrado?.nome || (item.cliente_id ? "Cliente vinculado" : "")
  }

  function comQuem(item: Atividade) {
    const cliente = clienteLegivel(item)
    if (cliente) return { nome: cliente, organizacao: "Cliente cadastrado" }
    if (item.parceiro_nome) return { nome: item.parceiro_nome, organizacao: item.parceiro_organizacao || item.parceiro_tipo || "Contato externo" }
    return { nome: "Não identificado", organizacao: "Revisar cadastro da atividade" }
  }

  function responsavelLegivel(item: Atividade) {
    if (item.responsavel_nome) return item.responsavel_nome
    const idRegistro = item.usuario_id || item.responsavel_id || ""
    if (idRegistro && usuario?.id && idRegistro === usuario.id) return usuario.nome || usuario.email || "Usuário do login"
    return idRegistro ? "Usuário CTI vinculado" : "-"
  }

  const itensFiltrados = agendaEscopada.itens.filter((item) => {
    if (filtro === "TODAS") return true
    if (filtro === "ABERTAS") return !estaConcluida(item) && item.situacao !== "CANCELADA"
    if (filtro === "CONCLUIDA") return estaConcluida(item)
    if (["ATRASADA", "HOJE", "FUTURA", "SEM_DATA"].includes(filtro)) return situacaoCalendario(item) === filtro
    return false
  })

  function abrirComposicao(novoFiltro: string) {
    setFiltro(novoFiltro)
    window.setTimeout(() => document.getElementById("composicao-agenda")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0)
  }

  const contextoDetalhe = detalhe ? comQuem(detalhe) : null

  return (
    <main className="flex min-h-screen bg-[#020817]"><Sidebar /><section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between"><div><h1 className="text-4xl font-bold text-white">CRM • Agenda e Follow-up</h1><p className="mt-2 text-gray-400">Próximos contatos, visitas, reuniões e tarefas com identificação clara de cliente, contato ou parceiro envolvido.</p></div><button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova atividade</button></div>
      {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

      {mostrarFormulario && <form onSubmit={criarAtividade} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200"><h2 className="text-xl font-bold text-white">Agendar atividade comercial</h2><p className="mt-2 text-sm text-gray-400">A atividade é registrada para o usuário autenticado e passa a integrar seu histórico comercial.</p><div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
        <label className="text-sm text-gray-300">Cliente da base<input name="cliente_id" list="clientes-agenda" required className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /><datalist id="clientes-agenda">{clientes.map((cliente) => <option key={cliente.nome} value={cliente.nome} />)}</datalist></label>
        <label className="text-sm text-gray-300">Oportunidade<select name="oportunidade_id" className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white"><option value="">Sem vínculo específico</option>{oportunidadesEscopadas.map((item) => <option key={item.id} value={item.id}>{item.titulo} • {item.cliente_id || "Cliente"}</option>)}</select></label>
        <div className="rounded-lg border border-[#13203f] bg-[#020817] p-3 text-sm text-gray-300"><span className="block text-xs text-gray-500">Responsável comercial</span><strong className="mt-1 block text-cyan-200">{usuario?.nome || "Usuário autenticado"}</strong></div>
        <label className="text-sm text-gray-300">Tipo<select name="tipo" className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white">{tipos.map((tipo) => <option key={tipo}>{tipo}</option>)}</select></label>
        <Campo nome="titulo" label="Assunto" obrigatorio /><Campo nome="data" label="Data" tipo="date" obrigatorio /><Campo nome="horario" label="Horário" tipo="time" /><Campo nome="descricao" label="Orientação / observação" />
      </div><div className="mt-5 flex gap-3"><button className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Salvar atividade</button><button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button></div></form>}

      <section className="grid grid-cols-2 gap-4 md:grid-cols-6"><Kpi titulo="Total" valor={agendaEscopada.resumo.total} onOpen={() => abrirComposicao("TODAS")} /><Kpi titulo="Atrasadas" valor={agendaEscopada.resumo.atrasadas} destaque="text-red-400" onOpen={() => abrirComposicao("ATRASADA")} /><Kpi titulo="Hoje" valor={agendaEscopada.resumo.hoje} destaque="text-yellow-400" onOpen={() => abrirComposicao("HOJE")} /><Kpi titulo="Futuras" valor={agendaEscopada.resumo.futuras} onOpen={() => abrirComposicao("FUTURA")} /><Kpi titulo="Sem data" valor={agendaEscopada.resumo.sem_data} onOpen={() => abrirComposicao("SEM_DATA")} /><Kpi titulo="Concluídas" valor={agendaEscopada.resumo.concluidas} destaque="text-green-400" onOpen={() => abrirComposicao("CONCLUIDA")} /></section>

      <div className="flex flex-wrap gap-2">{filtrosAgenda.map((item) => <button key={item} type="button" onClick={() => setFiltro(item)} className={`rounded-lg px-4 py-2 text-sm font-semibold ${filtro === item ? "bg-cyan-500 text-slate-950" : "border border-[#20345e] text-gray-300"}`}>{item}</button>)}</div>

      <div id="composicao-agenda" className="scroll-mt-24 overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">{loading ? <div className="p-10 text-gray-400">Carregando agenda...</div> : itensFiltrados.length === 0 ? <div className="p-10 text-gray-300">Nenhuma atividade encontrada neste filtro.</div> : <><div className="border-b border-[#13203f] px-5 py-3 text-xs text-cyan-300">Composição exata: {itensFiltrados.length.toLocaleString("pt-BR")} atividade(s) no filtro {filtro}. Clique em qualquer linha para abrir o histórico da atividade.</div><table className="w-full text-left"><thead><tr className="border-b border-[#13203f] text-gray-400"><th className="p-4">Situação</th><th className="p-4">Data/Hora</th><th className="p-4">Atividade</th><th className="p-4">Com quem</th><th className="p-4">Negociação</th><th className="p-4">Responsável CTI</th><th className="p-4">Ação</th></tr></thead><tbody>{itensFiltrados.map((item) => { const contexto = comQuem(item); return <tr key={item.id} role="button" tabIndex={0} onClick={() => void abrirDetalhe(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") void abrirDetalhe(item) }} className="cursor-pointer border-b border-[#13203f] text-gray-200 transition hover:bg-[#0d2342]"><td className="p-4"><Situacao valor={item.situacao} /></td><td className="p-4 text-yellow-300">{formatarData(item.data)} {item.horario || ""}</td><td className="p-4"><div className="font-semibold text-white">{item.titulo || item.tipo}</div><div className="text-xs text-gray-400">{item.tipo}</div></td><td className="p-4"><div className="font-semibold text-cyan-200">{contexto.nome}</div><div className="mt-1 text-xs text-gray-400">{contexto.organizacao}</div></td><td className="p-4">{item.oportunidade_titulo || "Sem negociação vinculada"}</td><td className="p-4">{responsavelLegivel(item)}</td><td className="p-4"><div className="flex flex-wrap gap-2"><button type="button" onClick={(event) => { event.stopPropagation(); void abrirDetalhe(item) }} className="rounded-lg border border-cyan-500 px-3 py-2 text-xs font-semibold text-cyan-300">Detalhes</button>{!estaConcluida(item) && item.situacao !== "CANCELADA" && <button type="button" onClick={(event) => { event.stopPropagation(); void concluir(item.id) }} className="rounded-lg border border-green-500 px-3 py-2 text-xs font-semibold text-green-300">Concluir</button>}</div></td></tr> })}</tbody></table></>}</div>
    </div></section>

    {detalhe && contextoDetalhe && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setDetalhe(null)}><section role="dialog" aria-modal="true" aria-label="Detalhes da atividade comercial" onClick={(event) => event.stopPropagation()} className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Histórico da atividade</p><h2 className="mt-2 text-2xl font-bold text-white">{detalhe.titulo || detalhe.tipo}</h2><p className="mt-1 text-sm text-gray-400">Registro comercial completo da atividade selecionada.</p></div><button type="button" onClick={() => setDetalhe(null)} className="rounded-lg border border-[#20345e] px-3 py-2 text-sm text-gray-300">Fechar</button></div>
      {carregandoDetalhe && <div className="mt-4 text-sm text-cyan-300">Atualizando dados da atividade...</div>}
      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"><DetalheCampo label="Status" valor={detalhe.situacao} /><DetalheCampo label="Calendário" valor={situacaoCalendario(detalhe)} /><DetalheCampo label="Data / hora" valor={`${formatarData(detalhe.data)} ${detalhe.horario || ""}`.trim()} /><DetalheCampo label="Tipo" valor={detalhe.tipo} /><DetalheCampo label="Com quem" valor={contextoDetalhe.nome} complemento={contextoDetalhe.organizacao} /><DetalheCampo label="Responsável CTI" valor={responsavelLegivel(detalhe)} /><DetalheCampo label="Negociação relacionada" valor={detalhe.oportunidade_titulo || "Sem negociação vinculada"} /></div>
      <div className="mt-6 rounded-xl border border-[#20345e] bg-[#020817] p-5"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-400">Observações / histórico da conversa</p><div className="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-200">{detalhe.descricao?.trim() || "Nenhuma observação foi registrada nesta atividade."}</div></div>
    </section></div>}
    </main>
  )
}

function formatarData(valor?: string) { if (!valor) return "-"; const [ano, mes, dia] = valor.slice(0, 10).split("-"); return `${dia}/${mes}/${ano}` }
function Campo({ nome, label, tipo = "text", obrigatorio = false }: { nome: string; label: string; tipo?: string; obrigatorio?: boolean }) { return <label className="text-sm text-gray-300">{label}<input name={nome} type={tipo} required={obrigatorio} className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /></label> }
function Kpi({ titulo, valor, destaque = "text-cyan-400", onOpen }: { titulo: string; valor: number; destaque?: string; onOpen?: () => void }) { const body = <><p className="text-sm text-gray-400">{titulo}</p><p className={`mt-2 text-3xl font-bold ${destaque}`}>{valor}</p>{onOpen && <p className="mt-2 text-[11px] text-cyan-400">Clique para detalhar</p>}</>; return onOpen ? <button type="button" onClick={onOpen} className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5 text-left transition hover:border-cyan-500/70 hover:bg-[#0b1d38]">{body}</button> : <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5">{body}</div> }
function Situacao({ valor }: { valor: Atividade["situacao"] }) { const classe = valor === "ATRASADA" ? "border-red-500 text-red-300" : valor === "HOJE" ? "border-yellow-500 text-yellow-300" : valor === "CONCLUIDA" ? "border-green-500 text-green-300" : "border-cyan-700 text-cyan-300"; return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${classe}`}>{valor}</span> }
function DetalheCampo({ label, valor, complemento }: { label: string; valor: string; complemento?: string }) { return <div className="rounded-xl border border-[#20345e] bg-[#091a33] p-4"><p className="text-xs uppercase tracking-wide text-gray-500">{label}</p><p className="mt-2 font-semibold text-white">{valor || "-"}</p>{complemento && <p className="mt-1 text-xs text-gray-400">{complemento}</p>}</div> }
