"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { Activity, Building2, CalendarDays, ChevronRight, CircleDollarSign, ClipboardCheck, MapPinned, Plus, RefreshCw, Target, TrendingUp } from "lucide-react"
import { useAuth } from "@/core/auth"
import { lerContextoOportunidade, textoSeguro } from "@/lib/crm-opportunity"

const atalhos = [
  { href: "/crm-app/visitas/nova", titulo: "Nova visita", descricao: "Registrar atendimento em campo", icon: MapPinned },
  { href: "/crm-app/oportunidades/nova", titulo: "Nova oportunidade", descricao: "Abrir negociação comercial", icon: Target },
  { href: "/crm-app/atividades/nova", titulo: "Nova atividade", descricao: "Criar tarefa e próxima ação", icon: ClipboardCheck },
  { href: "/crm-app/clientes", titulo: "Consultar cliente", descricao: "Carteira, histórico e contatos", icon: Building2 },
]

type Resumo = { visitas: number; pendencias: number; oportunidades: number; pipeline: number; clientes: number; atividades: number; destaque: string }

export default function CrmAppPage() {
  const { usuario } = useAuth()
  const [resumo, setResumo] = useState<Resumo>({ visitas: 0, pendencias: 0, oportunidades: 0, pipeline: 0, clientes: 0, atividades: 0, destaque: "Nenhuma oportunidade aberta" })
  const [sincronizando, setSincronizando] = useState(false)
  const [online, setOnline] = useState(true)

  const sincronizar = useCallback(async () => {
    setSincronizando(true)
    try {
      const [agendaResposta, oportunidadesResposta, atividadesResposta, clientesResposta] = await Promise.all([
        fetch("/api/crm-proxy/crm/agenda", { cache: "no-store" }),
        fetch("/api/crm-proxy/crm/oportunidades", { cache: "no-store" }),
        fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }),
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }),
      ])
      if (!agendaResposta.ok || !oportunidadesResposta.ok || !atividadesResposta.ok) throw new Error()
      const agenda = await agendaResposta.json() as { resumo?: { hoje?: number; atrasadas?: number } }
      const oportunidades = await oportunidadesResposta.json() as Record<string, unknown>[]
      const atividades = await atividadesResposta.json() as Record<string, unknown>[]
      const clientes = clientesResposta.ok ? await clientesResposta.json() as Record<string, unknown>[] : []
      const oportunidadesApp = oportunidades.filter((item) => String(item.origem || "").toUpperCase() === "CRM_APP")
      const hoje = new Date().toISOString().slice(0, 10)
      const visitasHoje = atividades.filter((item) => String(item.tipo || "").toUpperCase().includes("VISITA") && String(item.data || "").slice(0, 10) === hoje).length
      const abertasLista = oportunidadesApp.filter((item) => !["GANHO", "PERDIDO", "CANCELADO"].includes(String(item.status || "").toUpperCase()))
      const ultima = abertasLista[0]
      const contexto = ultima ? lerContextoOportunidade(ultima) : null
      const destaque = ultima ? `${textoSeguro(ultima.titulo) || "Oportunidade"} · ${contexto?.quantidade || 1} un. · ${contexto?.equipamentos.join(", ") || "produto a definir"}` : "Nenhuma oportunidade aberta"
      setResumo({ visitas: visitasHoje, pendencias: Number(agenda.resumo?.atrasadas || 0) + Number(agenda.resumo?.hoje || 0), oportunidades: abertasLista.length, pipeline: oportunidadesApp.length, clientes: Array.isArray(clientes) ? clientes.length : 0, atividades: atividades.length, destaque })
      setOnline(true)
    } catch { setOnline(false) } finally { setSincronizando(false) }
  }, [])

  useEffect(() => { void sincronizar() }, [sincronizar])

  const analises = [
    { href: "/crm-app/agenda", label: "Agenda", valor: resumo.pendencias, descricao: "ações pendentes", icon: CalendarDays },
    { href: "/crm-app/clientes", label: "Carteira", valor: resumo.clientes, descricao: "clientes disponíveis", icon: Building2 },
    { href: "/crm-app/visitas", label: "Visitas", valor: resumo.visitas, descricao: "realizadas hoje", icon: MapPinned },
    { href: "/crm-app/oportunidades", label: "Oportunidades", valor: resumo.oportunidades, descricao: resumo.destaque, icon: CircleDollarSign },
    { href: "/crm-app/pipeline", label: "Pipeline", valor: resumo.pipeline, descricao: "detalhamento das negociações", icon: TrendingUp },
    { href: "/crm-app/atividades", label: "Atividades", valor: resumo.atividades, descricao: "interações registradas", icon: Activity },
  ]

  return <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
    <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4"><div className="mx-auto flex w-full max-w-[94vw] items-center justify-between gap-4"><div><p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400 sm:text-xs">CTI / Viena São Paulo</p><h1 className="mt-1 text-lg font-bold sm:text-2xl">CRM Comercial</h1></div><div className={`rounded-full border px-3 py-1 text-xs ${online ? "border-emerald-900 bg-emerald-950/30 text-emerald-300" : "border-amber-900 bg-amber-950/30 text-amber-300"}`}>{online ? "Online" : "Reconectando"}</div></div></header>
    <div className="mx-auto w-full max-w-[94vw] px-4 py-4 sm:px-6 sm:py-6"><div className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]"><div className="space-y-5">
      <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 shadow-xl sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-sm text-slate-400 sm:text-base">Operação comercial diária</p><h2 className="mt-1 text-2xl font-bold sm:text-3xl">Olá, {usuario?.nome?.split(" ")[0] || "usuário CTI"}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">Registre as interações comerciais. As análises são atualizadas exclusivamente com os dados gravados no CTI.</p></div><button type="button" onClick={() => void sincronizar()} className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-3 text-cyan-300"><RefreshCw size={20} className={sincronizando ? "animate-spin" : ""} /></button></div><div className="mt-6 grid grid-cols-3 gap-3"><Indicador valor={resumo.visitas} label="Visitas hoje" /><Indicador valor={resumo.pendencias} label="Pendências" /><Indicador valor={resumo.oportunidades} label="Oportunidades" /></div></section>
      <section><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">Interações rápidas</h2><span className="text-sm text-slate-500">uso em campo</span></div><div className="grid gap-4 sm:grid-cols-2">{atalhos.map(({ href, titulo, descricao, icon: Icon }) => <Link key={href} href={href} className="flex min-h-24 items-center gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-5"><span className="rounded-2xl bg-cyan-950/50 p-4 text-cyan-300"><Icon size={22} /></span><span className="min-w-0 flex-1"><span className="block text-lg font-semibold">{titulo}</span><span className="mt-1 block text-sm text-slate-400">{descricao}</span></span><ChevronRight size={18} className="text-slate-600" /></Link>)}</div></section>
    </div><section><h2 className="mb-4 text-xl font-semibold">Análises do CRM</h2><div className="grid grid-cols-2 gap-4 xl:grid-cols-3">{analises.map(({ href, label, valor, descricao, icon: Icon }) => <Link href={href} key={label} className="flex min-h-36 flex-col justify-between rounded-2xl border border-[#16325c] bg-[#07162b] p-5 transition hover:border-cyan-700"><Icon className="text-cyan-300" size={24} /><div><strong className="mt-3 block text-2xl text-cyan-300">{valor}</strong><span className="block font-semibold">{label}</span><span className="mt-1 block text-xs leading-5 text-slate-400">{descricao}</span></div></Link>)}</div></section></div></div>
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 backdrop-blur"><div className="mx-auto grid max-w-4xl grid-cols-4 gap-2"><NavItem href="/crm-app" label="Início" icon={Building2} /><NavItem href="/crm-app/agenda" label="Agenda" icon={CalendarDays} /><NavItem href="/crm-app/oportunidades" label="Negócios" icon={Target} /><NavItem href="/crm-app/atividades/nova" label="Nova interação" icon={Plus} destaque /></div></nav>
  </main>
}

function Indicador({ valor, label }: { valor: number; label: string }) { return <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-4 py-4 text-center"><strong className="block text-2xl text-cyan-300">{valor}</strong><span className="mt-1 block text-xs text-slate-400">{label}</span></div> }
function NavItem({ href, label, icon: Icon, destaque = false }: { href: string; label: string; icon: typeof Building2; destaque?: boolean }) { return <Link href={href} className={`flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-xs ${destaque ? "bg-cyan-500 font-semibold text-slate-950" : "text-slate-400"}`}><Icon size={20} /><span>{label}</span></Link> }
