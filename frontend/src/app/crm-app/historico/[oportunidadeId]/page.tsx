"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import { ArrowLeft, Clock3, FileText, Loader2 } from "lucide-react"

type Registro = Record<string, unknown>
type Evento = { tipo: string; data_hora: string; titulo: string; status: string; responsavel_id: string }

function texto(valor: unknown) { return String(valor || "").trim() }
function formatarData(valor: string) {
  if (!valor) return "Data não informada"
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleString("pt-BR")
}

export default function HistoricoOportunidadePage() {
  const params = useParams<{ oportunidadeId: string }>()
  const oportunidadeId = String(params.oportunidadeId || "")
  const [oportunidade, setOportunidade] = useState<Registro>({})
  const [eventos, setEventos] = useState<Evento[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!oportunidadeId) return
    fetch(`/api/crm-proxy/crm/timeline/${encodeURIComponent(oportunidadeId)}`, { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => ({}))
        if (!resposta.ok) throw new Error(String(payload.detail || `Falha ${resposta.status}`))
        setOportunidade(payload.oportunidade || {})
        setEventos((Array.isArray(payload.eventos) ? payload.eventos : []).map((item: Registro) => ({
          tipo: texto(item.tipo || "EVENTO"),
          data_hora: texto(item.data_hora),
          titulo: texto(item.titulo || "Registro comercial"),
          status: texto(item.status),
          responsavel_id: texto(item.responsavel_id),
        })))
      })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o histórico."))
      .finally(() => setCarregando(false))
  }, [oportunidadeId])

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6">
    <div className="mx-auto max-w-4xl">
      <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Histórico da negociação</h1></div></header>
      <section className="mb-5 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><p className="text-sm text-slate-400">Oportunidade</p><h2 className="mt-1 text-xl font-bold">{texto(oportunidade.titulo) || "Negociação comercial"}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full border border-cyan-900 bg-cyan-950/40 px-3 py-1 text-cyan-200">{texto(oportunidade.status) || "OPORTUNIDADE"}</span>{oportunidade.data_fechamento_prevista && <span className="rounded-full border border-[#24466f] px-3 py-1 text-slate-300">Fechamento: {texto(oportunidade.data_fechamento_prevista)}</span>}</div></section>
      {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : eventos.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum evento registrado nesta negociação.</div> : <div className="relative space-y-4 before:absolute before:bottom-4 before:left-[19px] before:top-4 before:w-px before:bg-[#24466f]">{eventos.map((evento, indice) => <article key={`${evento.tipo}-${evento.data_hora}-${indice}`} className="relative pl-12"><span className="absolute left-0 top-1 grid size-10 place-items-center rounded-2xl border border-[#24466f] bg-[#07162b] text-cyan-300">{evento.tipo === "ATIVIDADE" ? <Clock3 size={18}/> : <FileText size={18}/>}</span><div className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{evento.titulo}</strong><span className="text-xs text-slate-500">{formatarData(evento.data_hora)}</span></div><div className="mt-2 flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-cyan-950/50 px-2 py-1 text-cyan-200">{evento.tipo}</span>{evento.status && <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-300">{evento.status}</span>}{evento.responsavel_id && <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-400">Responsável registrado</span>}</div></div></article>)}</div>}
    </div>
  </main>
}
