"use client"

import Link from "next/link"
import { ArrowLeft, BriefcaseBusiness, ChevronRight, ClipboardCheck, FileText, MapPinned, Search, Users } from "lucide-react"
import { useOperationalI18n } from "@/core/i18n/operational"

type Locale = "pt-BR" | "en" | "es"

const textos = {
  "pt-BR": {
    eyebrow: "CTI CRM · uso em campo",
    title: "O que você quer fazer agora?",
    subtitle: "Escolha uma ação. O CTI reaproveita os dados da negociação e evita caminhos desnecessários.",
    visit: "Registrar visita",
    visitHelp: "Presencial ou remota, ligada ao cliente e à negociação quando houver.",
    contact: "Registrar contato",
    contactHelp: "Ligação, WhatsApp, e-mail, reunião ou follow-up.",
    continueDeal: "Continuar negociação",
    continueDealHelp: "Escolha o cliente e continue exatamente do ponto em que parou.",
    proposal: "Proposta",
    proposalHelp: "Escolha a negociação em andamento; o CTI leva você ao processo correto.",
    findAccount: "Encontrar cliente",
    findAccountHelp: "Consulte a carteira e parta do cliente para a próxima ação.",
    activities: "Ver meu dia",
    activitiesHelp: "Pendências, retornos e atividades que precisam de atenção.",
    hint: "Uma ação por vez. O vendedor informa o que aconteceu; o CTI mantém atividade, negociação, proposta e pedido sincronizados por trás do aplicativo.",
  },
  en: {
    eyebrow: "CTI CRM · field use",
    title: "What do you want to do now?",
    subtitle: "Choose one action. CTI reuses deal data and avoids unnecessary navigation.",
    visit: "Log a visit",
    visitHelp: "On-site or remote, linked to the account and deal when available.",
    contact: "Log a contact",
    contactHelp: "Call, WhatsApp, email, meeting or follow-up.",
    continueDeal: "Continue a deal",
    continueDealHelp: "Choose the account and continue exactly where you stopped.",
    proposal: "Proposal",
    proposalHelp: "Choose the active deal and CTI opens the right process.",
    findAccount: "Find account",
    findAccountHelp: "Open your portfolio and start the next action from the account.",
    activities: "View my day",
    activitiesHelp: "Pending items, follow-ups and activities that need attention.",
    hint: "One action at a time. The seller records what happened; CTI keeps activities, deals, proposals and orders synchronized behind the app.",
  },
  es: {
    eyebrow: "CTI CRM · uso en campo",
    title: "¿Qué quieres hacer ahora?",
    subtitle: "Elige una acción. CTI reutiliza los datos del negocio y evita recorridos innecesarios.",
    visit: "Registrar visita",
    visitHelp: "Presencial o remota, vinculada al cliente y al negocio cuando exista.",
    contact: "Registrar contacto",
    contactHelp: "Llamada, WhatsApp, correo, reunión o seguimiento.",
    continueDeal: "Continuar negocio",
    continueDealHelp: "Elige el cliente y continúa exactamente desde donde paraste.",
    proposal: "Propuesta",
    proposalHelp: "Elige el negocio activo y CTI abre el proceso correcto.",
    findAccount: "Buscar cliente",
    findAccountHelp: "Consulta tu cartera y parte del cliente hacia la próxima acción.",
    activities: "Ver mi día",
    activitiesHelp: "Pendientes, retornos y actividades que requieren atención.",
    hint: "Una acción a la vez. El vendedor registra lo ocurrido; CTI mantiene actividades, negocios, propuestas y pedidos sincronizados detrás de la aplicación.",
  },
} satisfies Record<Locale, Record<string, string>>

export default function AcaoRapidaPage() {
  const { locale } = useOperationalI18n()
  const t = textos[(locale as Locale) || "pt-BR"] || textos["pt-BR"]

  const principais = [
    { href: "/crm-app/atividades/nova?tipo=VISITA_PRESENCIAL", titulo: t.visit, descricao: t.visitHelp, icon: MapPinned },
    { href: "/crm-app/atividades/nova?tipo=FOLLOW_UP", titulo: t.contact, descricao: t.contactHelp, icon: ClipboardCheck },
    { href: "/crm-app/acao/negociacao", titulo: t.continueDeal, descricao: t.continueDealHelp, icon: BriefcaseBusiness },
    { href: "/crm-app/acao/negociacao", titulo: t.proposal, descricao: t.proposalHelp, icon: FileText },
  ]

  const apoio = [
    { href: "/crm-app/clientes", titulo: t.findAccount, descricao: t.findAccountHelp, icon: Search },
    { href: "/crm-app/agenda", titulo: t.activities, descricao: t.activitiesHelp, icon: Users },
  ]

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-6 flex items-start gap-3">
          <Link href="/crm-app" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300">
            <ArrowLeft size={21} />
          </Link>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">{t.eyebrow}</p>
            <h1 className="mt-1 text-3xl font-bold leading-tight">{t.title}</h1>
            <p className="mt-2 text-base leading-6 text-slate-300">{t.subtitle}</p>
          </div>
        </header>

        <section className="grid gap-3">
          {principais.map(({ href, titulo, descricao, icon: Icon }, indice) => (
            <Link key={`${href}-${indice}`} href={href} className="flex min-h-28 items-center gap-4 rounded-3xl border border-[#1c3f68] bg-gradient-to-br from-[#0b2342] to-[#07172c] p-5 shadow-lg active:scale-[.99]">
              <span className="grid size-14 shrink-0 place-items-center rounded-2xl bg-cyan-500 text-slate-950"><Icon size={27} /></span>
              <span className="min-w-0 flex-1">
                <span className="block text-xl font-bold">{titulo}</span>
                <span className="mt-1 block text-sm leading-5 text-slate-300">{descricao}</span>
              </span>
              <ChevronRight size={22} className="shrink-0 text-cyan-300" />
            </Link>
          ))}
        </section>

        <section className="mt-5 grid gap-3 sm:grid-cols-2">
          {apoio.map(({ href, titulo, descricao, icon: Icon }) => (
            <Link key={href} href={href} className="flex min-h-24 items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 active:scale-[.99]">
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-cyan-950/70 text-cyan-300"><Icon size={21} /></span>
              <span className="min-w-0 flex-1">
                <span className="block text-base font-semibold">{titulo}</span>
                <span className="mt-1 block text-xs leading-5 text-slate-400">{descricao}</span>
              </span>
            </Link>
          ))}
        </section>

        <div className="mt-5 rounded-2xl border border-emerald-900/70 bg-emerald-950/20 p-4 text-sm leading-6 text-emerald-100/80">
          {t.hint}
        </div>
      </div>
    </main>
  )
}
