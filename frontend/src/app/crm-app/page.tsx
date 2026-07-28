"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import {
  Activity,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  ClipboardCheck,
  MapPinned,
  Plus,
  RefreshCw,
  Route,
  Target,
  Users,
} from "lucide-react"
import { useAuth } from "@/core/auth"
import { API_URL } from "@/lib/api"

const atalhos = [
  { href: "/crm-app/visitas/nova", titulo: "Nova visita", descricao: "Registrar atendimento em campo", icon: MapPinned },
  { href: "/crm-app/oportunidades/nova", titulo: "Nova oportunidade", descricao: "Abrir negociação comercial", icon: Target },
  { href: "/crm-app/atividades/nova", titulo: "Nova atividade", descricao: "Criar tarefa e próxima ação", icon: ClipboardCheck },
  { href: "/crm-app/clientes", titulo: "Consultar cliente", descricao: "Carteira, histórico e contatos", icon: Building2 },
]

const modulos = [
  { href: "/crm-app/agenda", label: "Agenda", icon: CalendarDays },
  { href: "/crm-app/clientes", label: "Clientes", icon: Users },
  { href: "/crm-app/visitas", label: "Visitas", icon: Route },
  { href: "/crm-app/oportunidades", label: "Oportunidades", icon: BriefcaseBusiness },
  { href: "/crm-app/pipeline", label: "Pipeline", icon: CircleDollarSign },
  { href: "/crm-app/atividades", label: "Atividades", icon: Activity },
]

type Resumo = { visitas: number; pendencias: number; oportunidades: number }

export default function CrmAppPage() {
  const { usuario } = useAuth()
  const [resumo, setResumo] = useState<Resumo>({ visitas: 0, pendencias: 0, oportunidades: 0 })
  const [sincronizando, setSincronizando] = useState(false)
  const [online, setOnline] = useState(true)

  const sincronizar = useCallback(async () => {
    setSincronizando(true)
    try {
      const [agendaResposta, oportunidadesResposta, atividadesResposta] = await Promise.all([
        fetch(`${API_URL}/crm/agenda`, { cache: "no-store" }),
        fetch(`${API_URL}/crm/oportunidades`, { cache: "no-store" }),
        fetch(`${API_URL}/crm/atividades`, { cache: "no-store" }),
      ])
      if (!agendaResposta.ok || !oportunidadesResposta.ok || !atividadesResposta.ok) throw new Error()
      const agenda = await agendaResposta.json() as { resumo?: { hoje?: number; atrasadas?: number } }
      const oportunidades = await oportunidadesResposta.json() as Record<string, unknown>[]
      const atividades = await atividadesResposta.json() as Record<string, unknown>[]
      const hoje = new Date().toISOString().slice(0, 10)
      const visitasHoje = atividades.filter((item) => String(item.tipo || "").toUpperCase().includes("VISITA") && String(item.data || "").slice(0, 10) === hoje).length
      const abertas = oportunidades.filter((item) => !["GANHO", "PERDIDO", "CANCELADO"].includes(String(item.status || "").toUpperCase())).length
      setResumo({ visitas: visitasHoje, pendencias: Number(agenda.resumo?.atrasadas || 0) + Number(agenda.resumo?.hoje || 0), oportunidades: abertas })
      setOnline(true)
    } catch {
      setOnline(false)
    } finally {
      setSincronizando(false)
    }
  }, [])

  useEffect(() => { void sincronizar() }, [sincronizar])

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4 lg:px-8">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400 sm:text-xs">CTI / Viena São Paulo</p>
            <h1 className="mt-1 text-lg font-bold sm:text-2xl">CRM Comercial</h1>
          </div>
          <div className={`rounded-full border px-3 py-1 text-xs sm:px-4 sm:py-1.5 ${online ? "border-emerald-900 bg-emerald-950/30 text-emerald-300" : "border-amber-900 bg-amber-950/30 text-amber-300"}`}>
            {online ? "Online" : "Reconectando"}
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-7xl px-4 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)] lg:gap-7">
          <div className="space-y-5">
            <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-4 shadow-xl sm:p-6 lg:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400 sm:text-base">Operação comercial diária</p>
                  <h2 className="mt-1 text-2xl font-bold sm:text-3xl">Olá, {usuario?.nome?.split(" ")[0] || "usuário CTI"}</h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base sm:leading-7">Registre visitas, oportunidades e próximas ações. Os dados são sincronizados com o portal CTI.</p>
                </div>
                <button type="button" onClick={() => void sincronizar()} aria-label="Sincronizar" className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-3 text-cyan-300 sm:p-4">
                  <RefreshCw size={20} className={sincronizando ? "animate-spin" : ""} />
                </button>
              </div>
              <div className="mt-5 grid grid-cols-3 gap-2 sm:mt-6 sm:gap-4">
                <Indicador valor={String(resumo.visitas)} label="Visitas hoje" />
                <Indicador valor={String(resumo.pendencias)} label="Pendências" />
                <Indicador valor={String(resumo.oportunidades)} label="Oportunidades" />
              </div>
            </section>

            <section>
              <div className="mb-3 flex items-center justify-between sm:mb-4"><h2 className="text-lg font-semibold sm:text-xl">Ações rápidas</h2><span className="text-xs text-slate-500 sm:text-sm">uso em campo</span></div>
              <div className="grid gap-3 sm:grid-cols-2 sm:gap-4">
                {atalhos.map(({ href, titulo, descricao, icon: Icon }) => (
                  <Link key={href} href={href} className="flex min-h-24 items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 transition active:scale-[0.99] sm:gap-4 sm:p-5">
                    <span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300 sm:p-4"><Icon size={22} /></span>
                    <span className="min-w-0 flex-1"><span className="block font-semibold sm:text-lg">{titulo}</span><span className="mt-1 block text-xs leading-5 text-slate-400 sm:text-sm">{descricao}</span></span>
                    <ChevronRight size={18} className="text-slate-600" />
                  </Link>
                ))}
              </div>
            </section>
          </div>

          <section>
            <h2 className="mb-3 text-lg font-semibold sm:mb-4 sm:text-xl">Módulos do CRM</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-2 lg:gap-4 xl:grid-cols-3">
              {modulos.map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} className="flex min-h-24 flex-col items-center justify-center rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-center transition active:scale-[0.98] sm:min-h-28 sm:p-5">
                  <Icon className="mx-auto text-cyan-300" size={24} /><span className="mt-2 block text-sm font-medium sm:text-base">{label}</span>
                </Link>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-emerald-900/70 bg-emerald-950/20 p-4 sm:p-5">
              <p className="text-sm font-semibold text-emerald-200 sm:text-base">Operação conectada</p>
              <p className="mt-1 text-xs leading-5 text-emerald-100/70 sm:text-sm sm:leading-6">Agenda, clientes, visitas, oportunidades, pipeline e atividades utilizam os dados reais do CTI.</p>
            </div>
          </section>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 backdrop-blur sm:px-6">
        <div className="mx-auto grid max-w-3xl grid-cols-4 gap-2">
          <NavItem href="/crm-app" label="Início" icon={Building2} />
          <NavItem href="/crm-app/agenda" label="Agenda" icon={CalendarDays} />
          <NavItem href="/crm-app/oportunidades" label="Negócios" icon={Target} />
          <NavItem href="/crm-app/visitas/nova" label="Registrar" icon={Plus} destaque />
        </div>
      </nav>
    </main>
  )
}

function Indicador({ valor, label }: { valor: string; label: string }) {
  return <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-2 py-3 text-center sm:px-4 sm:py-4"><strong className="block text-xl text-cyan-300 sm:text-2xl">{valor}</strong><span className="mt-1 block text-[10px] leading-4 text-slate-400 sm:text-xs">{label}</span></div>
}

function NavItem({ href, label, icon: Icon, destaque = false }: { href: string; label: string; icon: typeof Building2; destaque?: boolean }) {
  return <Link href={href} className={`flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-[10px] sm:min-h-16 sm:text-xs ${destaque ? "bg-cyan-500 font-semibold text-slate-950" : "text-slate-400"}`}><Icon size={20} /><span>{label}</span></Link>
}
