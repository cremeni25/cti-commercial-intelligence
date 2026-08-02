"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CalendarDays, ChevronLeft, ChevronRight, Clock3, Loader2, MapPinned, Plus } from "lucide-react"

type Registro = Record<string, unknown>
type ItemAgenda = { id: string; titulo: string; tipo: string; status: string; data: string; hora: string; cliente: string; local: string }

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["itens", "dados", "resultado", "atividades"]) if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
  }
  return []
}
function texto(valor: unknown) { return String(valor || "").trim() }
function chaveMes(data: Date) { return `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}` }

export default function AgendaCrmAppPage() {
  const [mes, setMes] = useState(() => new Date())
  const [itens, setItens] = useState<ItemAgenda[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    setCarregando(true); setErro("")
    fetch("/api/crm-proxy/crm/agenda", { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => ({}))
        if (!resposta.ok) throw new Error(String((payload as Registro).detail || `Falha ${resposta.status}`))
        setItens(lista(payload).map((item) => ({
          id: texto(item.id || item.atividade_id),
          titulo: texto(item.titulo || item.assunto || item.descricao) || "Atividade comercial",
          tipo: texto(item.tipo || item.tipo_atividade).toUpperCase() || "ATIVIDADE",
          status: texto(item.status).toUpperCase() || "PENDENTE",
          data: texto(item.data || item.data_atividade || item.inicio || item.created_at).slice(0, 10),
          hora: texto(item.hora || item.horario || item.inicio).slice(11, 16),
          cliente: texto(item.cliente_nome || item.cliente),
          local: texto(item.local || item.endereco),
        })).filter((item) => item.data))
      })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar a agenda."))
      .finally(() => setCarregando(false))
  }, [])

  const doMes = useMemo(() => itens.filter((item) => item.data.startsWith(chaveMes(mes))).sort((a, b) => `${a.data}${a.hora}`.localeCompare(`${b.data}${b.hora}`)), [itens, mes])
  const tituloMes = mes.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })
  function mover(delta: number) { setMes((atual) => new Date(atual.getFullYear(), atual.getMonth() + delta, 1)) }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-4xl">
      <header className="mb-5 flex items-center justify-between gap-3"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Agenda comercial</h1></div></div><Link href="/crm-app/atividades/nova" className="grid size-11 place-items-center rounded-2xl bg-cyan-500 text-slate-950"><Plus size={20}/></Link></header>

      <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-center justify-between"><button onClick={() => mover(-1)} className="rounded-xl border border-[#24466f] p-2 text-cyan-300"><ChevronLeft/></button><div className="text-center"><CalendarDays className="mx-auto text-cyan-300"/><h2 className="mt-1 font-bold capitalize">{tituloMes}</h2><p className="text-xs text-slate-400">{doMes.length} compromisso(s)</p></div><button onClick={() => mover(1)} className="rounded-xl border border-[#24466f] p-2 text-cyan-300"><ChevronRight/></button></div></section>

      {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : doMes.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum compromisso registrado neste mês.</div> : <div className="space-y-3">{doMes.map((item) => <article key={`${item.id}-${item.data}-${item.hora}`} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-xs text-cyan-300">{new Date(`${item.data}T12:00:00`).toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" })}</p><h3 className="mt-1 font-bold">{item.titulo}</h3><p className="mt-1 text-sm text-slate-400">{item.cliente || item.tipo}</p></div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{item.status}</span></div><div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">{item.hora && <span className="inline-flex items-center gap-1"><Clock3 size={14}/>{item.hora}</span>}{item.local && <span className="inline-flex items-center gap-1"><MapPinned size={14}/>{item.local}</span>}</div></article>)}</div>}
    </div>
  </main>
}
