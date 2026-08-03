"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, CalendarDays, CheckCircle2, Clock3, Loader2, Pencil, Plus, Search } from "lucide-react"

type Registro = Record<string, unknown>
type Atividade = {
  id: string
  titulo: string
  tipo: string
  status: string
  data: string
  horario: string
  cliente: string
  oportunidadeId: string
}

function texto(valor: unknown) { return String(valor || "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const obj = payload as Registro
    for (const chave of ["itens", "dados", "atividades", "resultado"]) if (Array.isArray(obj[chave])) return obj[chave] as Registro[]
  }
  return []
}

export default function AtividadesComerciaisPage() {
  const router = useRouter()
  const [itens, setItens] = useState<Atividade[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetch("/api/crm-proxy/crm/agenda", { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${resposta.status}`)
      setItens(lista(payload).map((item) => ({
        id: texto(item.id || item.atividade_id),
        titulo: texto(item.titulo || item.assunto || item.descricao) || "Atividade comercial",
        tipo: texto(item.tipo || item.tipo_atividade).toUpperCase() || "ATIVIDADE",
        status: texto(item.status || item.situacao).toUpperCase() || "PENDENTE",
        data: texto(item.data || item.data_atividade || item.inicio).slice(0, 10),
        horario: texto(item.horario || item.hora || item.inicio).slice(11, 16),
        cliente: texto(item.cliente_nome || item.cliente || item.oportunidade_titulo),
        oportunidadeId: texto(item.oportunidade_id),
      })).filter((item) => item.id))
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as atividades comerciais.")
    } finally { setCarregando(false) }
  }

  useEffect(() => { void carregar() }, [])

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return termo ? itens.filter((item) => `${item.titulo} ${item.tipo} ${item.cliente} ${item.status}`.toLocaleLowerCase("pt-BR").includes(termo)) : itens
  }, [busca, itens])

  async function concluir(id: string) {
    const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(id)}/concluir`, { method: "PUT" })
    const payload = await resposta.json().catch(() => ({}))
    if (!resposta.ok) return setErro(texto((payload as Registro).detail) || "Não foi possível concluir a atividade.")
    await carregar()
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-5xl">
      <header className="mb-5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3"><button onClick={() => router.push("/crm-app")} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></button><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Atividades comerciais</h1><p className="text-sm text-slate-400">Visitas, ligações, reuniões, retornos e próximas ações</p></div></div>
        <button onClick={() => router.push("/crm-app/atividades/nova")} className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-500 px-4 font-bold text-slate-950"><Plus size={18}/>Nova atividade</button>
      </header>

      <div className="relative mb-4"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, atividade, tipo ou status" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></div>
      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400"><p>Nenhuma atividade comercial registrada.</p><button onClick={() => router.push("/crm-app/atividades/nova")} className="mt-4 rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950">Registrar primeira atividade</button></div> : <div className="space-y-3">{visiveis.map((item) => <article key={item.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold text-cyan-300">{item.tipo}</p><h2 className="mt-1 text-lg font-bold">{item.titulo}</h2><p className="mt-1 text-sm text-slate-400">{item.cliente || "Cliente não informado"}</p></div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs">{item.status}</span></div><div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">{item.data && <span className="inline-flex items-center gap-1"><CalendarDays size={14}/>{new Date(`${item.data}T12:00:00`).toLocaleDateString("pt-BR")}</span>}{item.horario && <span className="inline-flex items-center gap-1"><Clock3 size={14}/>{item.horario}</span>}</div><div className="mt-4 grid gap-2 sm:grid-cols-3">{item.oportunidadeId && <button onClick={() => router.push(`/crm-app/historico/${item.oportunidadeId}?origem=atividades`)} className="rounded-xl border border-cyan-800 px-3 py-3 text-sm font-semibold text-cyan-200">Abrir histórico</button>}<button onClick={() => router.push(`/crm-app/atividades/nova?atividade=${encodeURIComponent(item.id)}`)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#24466f] px-3 py-3 text-sm"><Pencil size={15}/>Editar</button>{!item.status.includes("CONCLU") && <button onClick={() => concluir(item.id)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Concluir</button>}</div></article>)}</div>}
    </div>
  </main>
}
