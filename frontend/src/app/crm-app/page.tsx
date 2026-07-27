"use client"

import Link from "next/link"
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

export default function CrmAppPage() {
  const { usuario } = useAuth()

  return (
    <main className="min-h-screen bg-[#020817] pb-24 text-white lg:pb-28">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-4 backdrop-blur sm:px-6 lg:px-8">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400 sm:text-xs">CTI / Viena São Paulo</p>
            <h1 className="mt-1 text-xl font-bold sm:text-2xl">CRM Comercial</h1>
          </div>
          <div className="rounded-full border border-emerald-900 bg-emerald-950/30 px-3 py-1 text-xs text-emerald-300 sm:px-4 sm:py-1.5">
            Online
          </div>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-5 sm:px-6 sm:py-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)] lg:px-8 lg:py-8">
        <div className="space-y-6">
          <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 shadow-xl sm:p-6 lg:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-slate-400 sm:text-base">Operação comercial diária</p>
                <h2 className="mt-1 text-2xl font-bold sm:text-3xl">Olá, {usuario?.nome?.split(" ")[0] || "usuário CTI"}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base sm:leading-7">
                  Registre visitas, oportunidades e próximas ações. Os dados serão sincronizados com o portal CTI.
                </p>
              </div>
              <button type="button" aria-label="Sincronizar" className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-3 text-cyan-300 sm:p-4">
                <RefreshCw size={20} />
              </button>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-3 sm:mt-6 sm:gap-4">
              <Indicador valor="0" label="Visitas hoje" />
              <Indicador valor="0" label="Pendências" />
              <Indicador valor="0" label="Oportunidades" />
            </div>
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between sm:mb-4">
              <h2 className="text-lg font-semibold sm:text-xl">Ações rápidas</h2>
              <span className="text-xs text-slate-500 sm:text-sm">uso em campo</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 sm:gap-4">
              {atalhos.map(({ href, titulo, descricao, icon: Icon }) => (
                <Link key={href} href={href} className="flex min-h-24 items-center gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 transition hover:border-cyan-800 hover:bg-[#0b2140] active:scale-[0.99] sm:p-5">
                  <span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300 sm:p-4"><Icon size={22} /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold sm:text-lg">{titulo}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-400 sm:text-sm">{descricao}</span>
                  </span>
                  <ChevronRight size={18} className="text-slate-600" />
                </Link>
              ))}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section>
            <h2 className="mb-3 text-lg font-semibold sm:mb-4 sm:text-xl">Módulos do CRM</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-2 lg:gap-4 xl:grid-cols-3">
              {modulos.map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} className="flex min-h-24 flex-col items-center justify-center rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-center transition hover:border-cyan-800 hover:bg-[#0a1d37] sm:min-h-28 sm:p-5">
                  <Icon className="mx-auto text-cyan-300" size={24} />
                  <span className="mt-2 block text-sm font-medium sm:text-base">{label}</span>
                </Link>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-amber-900/70 bg-amber-950/20 p-4 sm:p-5">
            <p className="text-sm font-semibold text-amber-200 sm:text-base">Fundação operacional da Etapa 19</p>
            <p className="mt-1 text-xs leading-5 text-amber-100/70 sm:text-sm sm:leading-6">
              A interface está preparada para receber os formulários reais, sincronização online e regras de território do CTI.
            </p>
          </section>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(10px,env(safe-area-inset-bottom))] pt-2 backdrop-blur sm:px-6 sm:pt-3">
        <div className="mx-auto grid max-w-6xl grid-cols-4 gap-1 sm:gap-3">
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
  return (
    <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-3 py-3 text-center sm:px-4 sm:py-4">
      <strong className="block text-xl text-cyan-300 sm:text-2xl">{valor}</strong>
      <span className="mt-1 block text-[10px] leading-4 text-slate-400 sm:text-xs">{label}</span>
    </div>
  )
}

function NavItem({ href, label, icon: Icon, destaque = false }: { href: string; label: string; icon: typeof Building2; destaque?: boolean }) {
  return (
    <Link href={href} className={`flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-[10px] sm:min-h-16 sm:text-xs ${destaque ? "bg-cyan-500 text-slate-950" : "text-slate-400"}`}>
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  )
}
