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
    <main className="min-h-screen bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-4 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400">CTI / Viena São Paulo</p>
            <h1 className="mt-1 text-xl font-bold">CRM Comercial</h1>
          </div>
          <div className="rounded-full border border-emerald-900 bg-emerald-950/30 px-3 py-1 text-xs text-emerald-300">
            Online
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-5">
        <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 shadow-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm text-slate-400">Operação comercial diária</p>
              <h2 className="mt-1 text-2xl font-bold">Olá, {usuario?.nome?.split(" ")[0] || "usuário CTI"}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Registre visitas, oportunidades e próximas ações. Os dados serão sincronizados com o portal CTI.
              </p>
            </div>
            <button type="button" aria-label="Sincronizar" className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-3 text-cyan-300">
              <RefreshCw size={20} />
            </button>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3">
            <Indicador valor="0" label="Visitas hoje" />
            <Indicador valor="0" label="Pendências" />
            <Indicador valor="0" label="Oportunidades" />
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Ações rápidas</h2>
            <span className="text-xs text-slate-500">uso em campo</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {atalhos.map(({ href, titulo, descricao, icon: Icon }) => (
              <Link key={href} href={href} className="flex items-center gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 active:scale-[0.99]">
                <span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Icon size={22} /></span>
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold">{titulo}</span>
                  <span className="mt-1 block text-xs text-slate-400">{descricao}</span>
                </span>
                <ChevronRight size={18} className="text-slate-600" />
              </Link>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Módulos do CRM</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {modulos.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4 text-center">
                <Icon className="mx-auto text-cyan-300" size={23} />
                <span className="mt-2 block text-sm font-medium">{label}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-amber-900/70 bg-amber-950/20 p-4">
          <p className="text-sm font-semibold text-amber-200">Fundação operacional da Etapa 19</p>
          <p className="mt-1 text-xs leading-5 text-amber-100/70">
            A interface está preparada para receber os formulários reais, sincronização online e regras de território do CTI.
          </p>
        </section>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(10px,env(safe-area-inset-bottom))] pt-2 backdrop-blur">
        <div className="mx-auto grid max-w-3xl grid-cols-4 gap-1">
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
    <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-3 py-3 text-center">
      <strong className="block text-xl text-cyan-300">{valor}</strong>
      <span className="mt-1 block text-[10px] leading-4 text-slate-400">{label}</span>
    </div>
  )
}

function NavItem({ href, label, icon: Icon, destaque = false }: { href: string; label: string; icon: typeof Building2; destaque?: boolean }) {
  return (
    <Link href={href} className={`flex flex-col items-center gap-1 rounded-xl px-2 py-2 text-[10px] ${destaque ? "bg-cyan-500 text-slate-950" : "text-slate-400"}`}>
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  )
}
