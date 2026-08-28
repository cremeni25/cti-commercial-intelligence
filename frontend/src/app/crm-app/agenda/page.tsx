"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, CalendarDays, CheckCircle2, ChevronLeft, ChevronRight, Clock3, Loader2, Pencil, Plus, Save, UserRound, Building2 } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Item = {
  id: string
  usuarioId: string
  titulo: string
  tipo: string
  status: string
  data: string
  hora: string
  cliente: string
  parceiroNome: string
  parceiroOrganizacao: string
  parceiroTipo: string
  oportunidade: string
  descricao: string
}

function lista(p: unknown): Registro[] {
  if (Array.isArray(p)) return p as Registro[]
  if (p && typeof p === "object") {
    const o = p as Registro
    for (const k of ["itens", "dados", "resultado", "atividades"]) if (Array.isArray(o[k])) return o[k] as Registro[]
  }
  return []
}
function texto(v: unknown) { return String(v || "").trim() }
function chaveMes(d: Date) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}` }
function contextoCompromisso(item: Item) {
  if (item.cliente) return { pessoa: item.cliente, organizacao: "Cliente cadastrado" }
  if (item.parceiroNome) return { pessoa: item.parceiroNome, organizacao: item.parceiroOrganizacao || item.parceiroTipo || "Contato externo" }
  return { pessoa: "Contato não identificado", organizacao: "Revisar cadastro do compromisso" }
}

export default function Agenda() {
  const { usuario } = useAuth()
  const [mes, setMes] = useState(() => new Date())
  const [itens, setItens] = useState<Item[]>([])
  const [selecionado, setSelecionado] = useState<Item | null>(null)
  const [dia, setDia] = useState<string>("")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  async function carregar() {
    setCarregando(true)
    setErro("")
    try {
      const r = await fetchCrmSeguroProxy("crm-seguro/agenda", { cache: "no-store" })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String((p as Registro).detail || `Falha ${r.status}`))
      setItens(lista(p).map(i => ({
        id: texto(i.id || i.atividade_id),
        usuarioId: texto(i.usuario_id || i.responsavel_id),
        titulo: texto(i.titulo || i.assunto || i.descricao) || "Atividade comercial",
        tipo: texto(i.tipo || i.tipo_atividade).toUpperCase() || "ATIVIDADE",
        status: texto(i.status).toUpperCase() || "PENDENTE",
        data: texto(i.data || i.data_atividade || i.inicio).slice(0, 10),
        hora: texto(i.hora || i.horario || i.inicio).slice(11, 16),
        cliente: texto(i.cliente_nome || i.cliente),
        parceiroNome: texto(i.parceiro_nome),
        parceiroOrganizacao: texto(i.parceiro_organizacao),
        parceiroTipo: texto(i.parceiro_tipo),
        oportunidade: texto(i.oportunidade_titulo),
        descricao: texto(i.descricao),
      })).filter(i => i.data && !["CONCLUIDA", "CONCLUÍDA", "CANCELADA"].includes(i.status)))
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível carregar a agenda.")
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => { void carregar() }, [])

  const itensEscopados = useMemo(() => itens.filter(i => pertenceAoEscopoDoUsuario(i.usuarioId, usuario)), [itens, usuario])
  const doMes = useMemo(() => itensEscopados.filter(i => i.data.startsWith(chaveMes(mes))).sort((a, b) => `${a.data}${a.hora}`.localeCompare(`${b.data}${b.hora}`)), [itensEscopados, mes])
  const titulo = mes.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })
  const primeiro = new Date(mes.getFullYear(), mes.getMonth(), 1)
  const totalDias = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate()
  const inicio = primeiro.getDay()
  const celulas = Array.from({ length: inicio + totalDias }, (_, i) => i < inicio ? null : i - inicio + 1)
  const filtradosDia = dia ? doMes.filter(i => i.data === dia) : doMes

  function mover(n: number) { setMes(a => new Date(a.getFullYear(), a.getMonth() + n, 1)); setDia(""); setSelecionado(null) }

  async function salvar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selecionado || !pertenceAoEscopoDoUsuario(selecionado.usuarioId, usuario)) return
    setSalvando(true); setErro(""); setSucesso("")
    const f = new FormData(e.currentTarget)
    const payload = { titulo: texto(f.get("titulo")), tipo: texto(f.get("tipo")), data: texto(f.get("data")), horario: texto(f.get("horario")), descricao: texto(f.get("descricao")) || null, status: texto(f.get("status")) }
    try {
      const r = await fetchCrmSeguroProxy(`crm-seguro/atividades/${encodeURIComponent(selecionado.id)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      const p = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(String(p.detail || `Falha ${r.status}`))
      setSucesso("Compromisso atualizado."); setSelecionado(null); await carregar()
    } catch (x) { setErro(x instanceof Error ? x.message : "Não foi possível atualizar o compromisso.") }
    finally { setSalvando(false) }
  }

  async function concluir(id: string) {
    const item = itensEscopados.find(i => i.id === id)
    if (!item) return
    const r = await fetchCrmSeguroProxy(`crm-seguro/atividades/${encodeURIComponent(id)}/concluir`, { method: "PUT" })
    if (!r.ok) setErro("Não foi possível concluir o compromisso.")
    else { setSucesso("Compromisso concluído e enviado ao histórico comercial."); await carregar() }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex items-center justify-between gap-3"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Agenda comercial</h1><p className="text-sm text-slate-400">Compromissos pendentes, atrasos e próximas ações</p></div></div><Link href="/crm-app/atividades/nova" className="flex items-center gap-2 rounded-2xl bg-cyan-500 px-4 py-3 font-bold text-slate-950"><Plus size={18}/>Novo compromisso</Link></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="mb-4 flex items-center justify-between"><button onClick={() => mover(-1)} className="rounded-xl border border-[#24466f] p-2 text-cyan-300"><ChevronLeft/></button><div className="text-center"><CalendarDays className="mx-auto text-cyan-300"/><h2 className="mt-1 font-bold capitalize">{titulo}</h2><p className="text-xs text-slate-400">{doMes.length} compromisso(s) pendente(s)</p></div><button onClick={() => mover(1)} className="rounded-xl border border-[#24466f] p-2 text-cyan-300"><ChevronRight/></button></div><div className="grid grid-cols-7 gap-1 text-center text-xs text-slate-400">{["D", "S", "T", "Q", "Q", "S", "S"].map((d, i) => <div key={`${d}-${i}`} className="py-2 font-semibold">{d}</div>)}{celulas.map((n, i) => n === null ? <div key={`v-${i}`}/> : <button key={n} onClick={() => setDia(`${chaveMes(mes)}-${String(n).padStart(2, "0")}`)} className={`min-h-14 rounded-xl border p-2 ${dia === `${chaveMes(mes)}-${String(n).padStart(2, "0")}` ? "border-cyan-400 bg-cyan-950/50" : "border-[#16325c] bg-[#091a33]"}`}><span className="block font-semibold text-white">{n}</span>{doMes.some(x => Number(x.data.slice(8, 10)) === n) && <span className="mx-auto mt-1 block size-2 rounded-full bg-cyan-400"/>}</button>)}</div></section>
    {carregando ? <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : filtradosDia.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">{dia ? "Nenhum compromisso pendente neste dia." : "Selecione um dia para consultar ou editar."}</div> : <div className="space-y-3">{filtradosDia.map(i => { const contexto = contextoCompromisso(i); return <article key={i.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="text-xs text-cyan-300">{new Date(`${i.data}T12:00:00`).toLocaleDateString("pt-BR")}</p><h3 className="mt-1 font-bold">{i.titulo}</h3><div className="mt-3 rounded-2xl border border-cyan-900/70 bg-cyan-950/20 p-3"><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-cyan-400">Com quem</p><p className="mt-1 flex items-center gap-2 font-semibold text-white"><UserRound size={16} className="text-cyan-300"/>{contexto.pessoa}</p><p className="mt-1 flex items-center gap-2 text-sm text-slate-400"><Building2 size={15}/>{contexto.organizacao}</p></div><p className="mt-3 text-xs text-slate-400"><span className="font-semibold text-slate-300">Tipo:</span> {i.tipo}</p>{i.oportunidade && <p className="mt-1 text-xs text-slate-400"><span className="font-semibold text-slate-300">Negociação:</span> {i.oportunidade}</p>}{i.hora && <p className="mt-2 inline-flex items-center gap-1 text-xs text-slate-400"><Clock3 size={14}/>{i.hora}</p>}</div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs">{i.status}</span></div><div className="mt-4 grid gap-2 sm:grid-cols-2"><button onClick={() => setSelecionado(i)} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-800 px-3 py-3 text-sm font-semibold text-cyan-200"><Pencil size={16}/>Editar compromisso</button><button onClick={() => void concluir(i.id)} className="flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Concluir e enviar ao histórico</button></div></article>})}</div>}
    {selecionado && <form onSubmit={salvar} className="mt-4 grid gap-4 rounded-3xl border border-cyan-800 bg-[#07162b] p-5 sm:grid-cols-2"><h2 className="text-xl font-bold sm:col-span-2">Editar compromisso</h2><div className="sm:col-span-2 rounded-2xl border border-[#24466f] bg-[#020817]/60 p-4"><p className="text-xs font-semibold uppercase tracking-[.16em] text-cyan-400">Com quem será o compromisso</p><p className="mt-2 font-semibold text-white">{contextoCompromisso(selecionado).pessoa}</p><p className="text-sm text-slate-400">{contextoCompromisso(selecionado).organizacao}</p></div><Campo name="titulo" label="Título" valor={selecionado.titulo}/><Campo name="tipo" label="Tipo" valor={selecionado.tipo}/><Campo name="data" label="Data" type="date" valor={selecionado.data}/><Campo name="horario" label="Horário" type="time" valor={selecionado.hora}/><label><span className="mb-2 block text-sm text-slate-300">Status</span><select name="status" defaultValue={selecionado.status} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option>PENDENTE</option><option>CONCLUIDA</option><option>CANCELADA</option></select></label><label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição</span><textarea name="descricao" defaultValue={selecionado.descricao} rows={4} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><div className="grid gap-2 sm:col-span-2 sm:grid-cols-2"><button type="button" onClick={() => setSelecionado(null)} className="rounded-2xl border border-[#24466f] py-3">Cancelar edição</button><button disabled={salvando} className="flex items-center justify-center gap-2 rounded-2xl bg-cyan-500 py-3 font-bold text-slate-950">{salvando ? <Loader2 className="animate-spin"/> : <Save size={18}/>}Salvar compromisso</button></div></form>}
  </div></main>
}

function Campo({ name, label, valor, type = "text" }: { name: string; label: string; valor: string; type?: string }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} defaultValue={valor} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label> }
