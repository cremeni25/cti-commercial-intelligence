"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CalendarClock, CheckCircle2, CircleAlert, ClipboardCheck, Filter, Loader2, Plus, RefreshCw } from "lucide-react"

type Registro = Record<string, unknown>
type Atividade = {
  id: string
  titulo: string
  tipo: string
  status: string
  data: string
  horario: string
  clienteId: string
  cliente: string
  oportunidadeId: string
  descricao: string
}

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["atividades", "itens", "dados", "resultado"]) {
      if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
    }
  }
  return []
}
function normalizarStatus(valor: unknown): string {
  return texto(valor).toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") || "PENDENTE"
}
function concluida(status: string): boolean { return ["CONCLUIDA", "CONCLUIDO", "REALIZADA", "FINALIZADA"].includes(status) }
function cancelada(status: string): boolean { return ["CANCELADA", "CANCELADO"].includes(status) }
function hojeIso(): string { return new Date().toISOString().slice(0, 10) }

export default function AtividadesPage() {
  const [atividades, setAtividades] = useState<Atividade[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [statusFiltro, setStatusFiltro] = useState("TODAS")
  const [tipoFiltro, setTipoFiltro] = useState("TODOS")
  const [busca, setBusca] = useState("")

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" })
      const payload = await resposta.json().catch(() => ([]))
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      const dados = lista(payload).map((item): Atividade => ({
        id: texto(item.id || item.atividade_id),
        titulo: texto(item.titulo || item.assunto || item.descricao) || "Atividade comercial",
        tipo: texto(item.tipo || item.tipo_atividade).toUpperCase() || "ATIVIDADE",
        status: normalizarStatus(item.status),
        data: texto(item.data || item.data_atividade || item.inicio).slice(0, 10),
        horario: texto(item.horario || item.hora || item.inicio).slice(11, 16),
        clienteId: texto(item.cliente_id),
        cliente: texto(item.cliente_nome || item.cliente),
        oportunidadeId: texto(item.oportunidade_id),
        descricao: texto(item.descricao),
      })).filter((item) => item.id)
      setAtividades(dados.sort((a, b) => `${b.data}${b.horario}`.localeCompare(`${a.data}${a.horario}`)))
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as atividades.")
    } finally { setCarregando(false) }
  }

  useEffect(() => { void carregar() }, [])

  const resumo = useMemo(() => {
    const hoje = hojeIso()
    return {
      pendentes: atividades.filter((a) => !concluida(a.status) && !cancelada(a.status)).length,
      concluidas: atividades.filter((a) => concluida(a.status)).length,
      atrasadas: atividades.filter((a) => !concluida(a.status) && !cancelada(a.status) && a.data && a.data < hoje).length,
    }
  }, [atividades])

  const tipos = useMemo(() => [...new Set(atividades.map((a) => a.tipo).filter(Boolean))].sort(), [atividades])
  const filtradas = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    const hoje = hojeIso()
    return atividades.filter((a) => {
      if (statusFiltro === "PENDENTES" && (concluida(a.status) || cancelada(a.status))) return false
      if (statusFiltro === "CONCLUIDAS" && !concluida(a.status)) return false
      if (statusFiltro === "ATRASADAS" && (concluida(a.status) || cancelada(a.status) || !a.data || a.data >= hoje)) return false
      if (tipoFiltro !== "TODOS" && a.tipo !== tipoFiltro) return false
      if (termo && !`${a.titulo} ${a.cliente} ${a.tipo} ${a.descricao}`.toLocaleLowerCase("pt-BR").includes(termo)) return false
      return true
    })
  }, [atividades, busca, statusFiltro, tipoFiltro])

  async function concluirAtividade(id: string) {
    setErro(""); setSucesso("")
    const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(id)}/concluir`, { method: "PUT" })
    if (!resposta.ok) return setErro("Não foi possível concluir a atividade.")
    setSucesso("Atividade concluída e preservada no histórico comercial.")
    await carregar()
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6">
    <div className="mx-auto max-w-5xl">
      <header className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Central de Atividades</h1><p className="text-sm text-slate-400">Histórico, pendências e interações comerciais</p></div></div>
        <div className="flex gap-2"><button onClick={() => void carregar()} className="grid size-12 place-items-center rounded-2xl border border-[#24466f] text-cyan-300" aria-label="Atualizar"><RefreshCw size={18}/></button><Link href="/crm-app/atividades/nova" className="flex items-center gap-2 rounded-2xl bg-cyan-500 px-4 py-3 font-bold text-slate-950"><Plus size={18}/>Nova atividade</Link></div>
      </header>

      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}

      <section className="mb-5 grid grid-cols-3 gap-3">
        <Indicador icone={<ClipboardCheck size={18}/>} valor={resumo.pendentes} rotulo="Pendentes"/>
        <Indicador icone={<CheckCircle2 size={18}/>} valor={resumo.concluidas} rotulo="Concluídas"/>
        <Indicador icone={<CircleAlert size={18}/>} valor={resumo.atrasadas} rotulo="Atrasadas"/>
      </section>

      <section className="mb-5 grid gap-3 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:grid-cols-[1fr_auto_auto]">
        <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar por cliente, título, tipo ou descrição" className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"/>
        <label className="relative"><Filter className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16}/><select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] pl-9 pr-8"><option value="TODAS">Todos os status</option><option value="PENDENTES">Pendentes</option><option value="CONCLUIDAS">Concluídas</option><option value="ATRASADAS">Atrasadas</option></select></label>
        <select value={tipoFiltro} onChange={(e) => setTipoFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option value="TODOS">Todos os tipos</option>{tipos.map((tipo) => <option key={tipo} value={tipo}>{tipo.replaceAll("_", " ")}</option>)}</select>
      </section>

      {carregando ? <div className="grid min-h-52 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : filtradas.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-10 text-center text-slate-400">Nenhuma atividade encontrada para os filtros selecionados.</div> : <div className="space-y-3">{filtradas.map((atividade) => {
        const aberta = !concluida(atividade.status) && !cancelada(atividade.status)
        const atrasada = aberta && Boolean(atividade.data) && atividade.data < hojeIso()
        return <article key={atividade.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <div className="flex items-start justify-between gap-4"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-[#24466f] px-3 py-1 text-[11px] text-cyan-200">{atividade.tipo.replaceAll("_", " ")}</span>{atrasada && <span className="rounded-full border border-amber-700 bg-amber-950/30 px-3 py-1 text-[11px] text-amber-200">ATRASADA</span>}</div><h2 className="mt-3 text-lg font-bold">{atividade.titulo}</h2><p className="mt-1 text-sm text-slate-400">{atividade.cliente || "Cliente não informado"}</p>{atividade.descricao && <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-300">{atividade.descricao}</p>}</div><span className={`shrink-0 rounded-full px-3 py-1 text-xs ${concluida(atividade.status) ? "bg-emerald-950/50 text-emerald-300" : cancelada(atividade.status) ? "bg-slate-800 text-slate-400" : "bg-cyan-950/50 text-cyan-300"}`}>{atividade.status}</span></div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-400">{atividade.data && <span className="inline-flex items-center gap-1"><CalendarClock size={14}/>{new Date(`${atividade.data}T12:00:00`).toLocaleDateString("pt-BR")}{atividade.horario ? ` · ${atividade.horario}` : ""}</span>}{atividade.oportunidadeId && <Link href={`/crm-app/oportunidades/${encodeURIComponent(atividade.oportunidadeId)}`} className="rounded-lg border border-[#24466f] px-2 py-1 text-cyan-300">Abrir negociação</Link>}{atividade.clienteId && <Link href={`/crm-app/clientes/${encodeURIComponent(atividade.clienteId)}`} className="rounded-lg border border-[#24466f] px-2 py-1 text-cyan-300">Abrir cliente</Link>}</div>
          {aberta && <button onClick={() => void concluirAtividade(atividade.id)} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Concluir atividade</button>}
        </article>
      })}</div>}
    </div>
  </main>
}

function Indicador({icone, valor, rotulo}:{icone:React.ReactNode;valor:number;rotulo:string}) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><div className="text-cyan-300">{icone}</div><strong className="mt-2 block text-2xl text-white">{valor}</strong><span className="text-xs text-slate-400">{rotulo}</span></div>
}
