"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Bot,
  BriefcaseBusiness,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  ClipboardCheck,
  FileText,
  MapPinned,
  PackageCheck,
  PiggyBank,
  Plus,
  RefreshCw,
  Search,
  Target,
  TrendingUp,
  Users,
} from "lucide-react"
import { useAuth } from "@/core/auth"
import { useOperationalI18n } from "@/core/i18n/operational"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"
import { pertenceAoEscopoDoUsuario, possuiEscopoProprio } from "@/core/rbac/commercial-scope"
import { lerContextoOportunidade, textoSeguro } from "@/lib/crm-opportunity"

type Registro = Record<string, unknown>
type Locale = "pt-BR" | "en" | "es"
type Resumo = {
  visitas: number
  pendencias: number
  atividades: number
  oportunidades: number
  pipeline: number
  clientes: number
  propostas: number
  pedidos: number
  vendas: number
  destaque: string
}

const FINAIS = new Set(["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO"])

const textos = {
  "pt-BR": {
    brand: "CTI CRM · campo",
    hello: "Olá, {name}",
    subtitle: "Seu dia comercial em uma tela. Escolha a próxima ação e deixe o CTI cuidar do restante.",
    today: "Meu dia",
    visits: "Visitas hoje",
    pending: "Pendências",
    openDeals: "Negócios abertos",
    mainAction: "Nova ação",
    mainActionHelp: "Visita, contato, proposta ou continuidade da negociação.",
    next: "Continuar negociação",
    nextHelp: "Abra sua carteira e avance exatamente de onde parou.",
    agenda: "Ver pendências",
    agendaHelp: "Retornos, compromissos e atividades que precisam de atenção.",
    clients: "Buscar cliente",
    clientsHelp: "Encontre o cliente e parta dele para a próxima ação.",
    current: "Negociação em destaque",
    noCurrent: "Nenhuma negociação aberta no momento.",
    details: "Abrir negócios",
    more: "Mais recursos",
    moreHelp: "Recursos completos continuam disponíveis quando você precisar.",
    syncError: "Não foi possível sincronizar o CRM agora.",
    online: "Online",
    reconnecting: "Reconectando",
    activities: "Atividades",
    pipeline: "Pipeline",
    proposals: "Propostas",
    orders: "Pedidos",
    sales: "Vendas",
    ai: "IA Comercial",
    financial: "Controle financeiro",
  },
  en: {
    brand: "CTI CRM · field",
    hello: "Hello, {name}",
    subtitle: "Your sales day on one screen. Choose the next action and let CTI handle the rest.",
    today: "My day",
    visits: "Visits today",
    pending: "Pending",
    openDeals: "Open deals",
    mainAction: "New action",
    mainActionHelp: "Visit, contact, proposal or continue a deal.",
    next: "Continue deal",
    nextHelp: "Open your portfolio and continue exactly where you left off.",
    agenda: "View pending",
    agendaHelp: "Follow-ups, appointments and activities requiring attention.",
    clients: "Find account",
    clientsHelp: "Find the account and start the next action from there.",
    current: "Highlighted deal",
    noCurrent: "No open deal right now.",
    details: "Open deals",
    more: "More resources",
    moreHelp: "Full CRM resources remain available whenever needed.",
    syncError: "CRM could not synchronize right now.",
    online: "Online",
    reconnecting: "Reconnecting",
    activities: "Activities",
    pipeline: "Pipeline",
    proposals: "Proposals",
    orders: "Orders",
    sales: "Sales",
    ai: "Sales AI",
    financial: "Financial control",
  },
  es: {
    brand: "CTI CRM · campo",
    hello: "Hola, {name}",
    subtitle: "Tu día comercial en una sola pantalla. Elige la próxima acción y deja que CTI gestione el resto.",
    today: "Mi día",
    visits: "Visitas hoy",
    pending: "Pendientes",
    openDeals: "Negocios abiertos",
    mainAction: "Nueva acción",
    mainActionHelp: "Visita, contacto, propuesta o continuidad del negocio.",
    next: "Continuar negocio",
    nextHelp: "Abre tu cartera y continúa exactamente donde la dejaste.",
    agenda: "Ver pendientes",
    agendaHelp: "Retornos, compromisos y actividades que requieren atención.",
    clients: "Buscar cliente",
    clientsHelp: "Encuentra al cliente y parte desde él hacia la próxima acción.",
    current: "Negocio destacado",
    noCurrent: "No hay negocios abiertos en este momento.",
    details: "Abrir negocios",
    more: "Más recursos",
    moreHelp: "Los recursos completos siguen disponibles cuando los necesites.",
    syncError: "No fue posible sincronizar el CRM ahora.",
    online: "Online",
    reconnecting: "Reconectando",
    activities: "Actividades",
    pipeline: "Pipeline",
    proposals: "Propuestas",
    orders: "Pedidos",
    sales: "Ventas",
    ai: "IA Comercial",
    financial: "Control financiero",
  },
} satisfies Record<Locale, Record<string, string>>

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const item = payload as Registro
    for (const chave of ["dados", "itens", "oportunidades", "resultado", "atividades"]) {
      if (Array.isArray(item[chave])) return item[chave] as Registro[]
    }
  }
  return []
}

async function json(resposta: Response) {
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`)
  return resposta.json()
}

function etapa(item: Registro) {
  return String(item.etapa || item.status || item.status_oportunidade || "").trim().toUpperCase()
}

export default function CrmAppPage() {
  const { usuario } = useAuth()
  const { locale } = useOperationalI18n()
  const idioma = (locale as Locale) || "pt-BR"
  const t = textos[idioma] || textos["pt-BR"]
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [resumo, setResumo] = useState<Resumo>({ visitas: 0, pendencias: 0, atividades: 0, oportunidades: 0, pipeline: 0, clientes: 0, propostas: 0, pedidos: 0, vendas: 0, destaque: t.noCurrent })
  const [sincronizando, setSincronizando] = useState(false)
  const [online, setOnline] = useState(true)
  const [aviso, setAviso] = useState("")

  const sincronizar = useCallback(async () => {
    setSincronizando(true)
    setAviso("")
    const resultados = await Promise.allSettled([
      fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/crm/agenda", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/crm-documentos/propostas", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/crm-documentos/pedidos", { cache: "no-store" }).then(json),
      fetch("/api/crm-proxy/vendas", { cache: "no-store" }).then(json),
    ])
    const [nucleoR, agendaR, atividadesR, clientesR, propostasR, pedidosR, vendasR] = resultados
    if (nucleoR.status === "rejected") {
      setOnline(false)
      setAviso(t.syncError)
      setSincronizando(false)
      return
    }

    const oportunidadesTodas = lista(nucleoR.value)
    const oportunidades = oportunidadesTodas.filter((item) => pertenceAoEscopoDoUsuario(String(item.responsavel_id || ""), usuario))
    const abertas = oportunidades.filter((item) => !FINAIS.has(etapa(item)))
    const idsPermitidos = new Set(oportunidades.map((item) => String(item.oportunidade_id || item.id || "")).filter(Boolean))
    const escopoProprio = possuiEscopoProprio(usuario)
    const agendaItens = agendaR.status === "fulfilled" ? lista(agendaR.value).filter((item) => pertenceAoEscopoDoUsuario(String(item.usuario_id || item.responsavel_id || ""), usuario)) : []
    const atividades = atividadesR.status === "fulfilled" ? lista(atividadesR.value).filter((item) => pertenceAoEscopoDoUsuario(String(item.usuario_id || item.responsavel_id || ""), usuario)) : []
    const clientes = clientesR.status === "fulfilled" ? lista(clientesR.value) : []
    const propostasTodas = propostasR.status === "fulfilled" ? lista(propostasR.value) : []
    const pedidosTodos = pedidosR.status === "fulfilled" ? lista(pedidosR.value) : []
    const vendasTodas = vendasR.status === "fulfilled" ? lista(vendasR.value) : []
    const propostas = escopoProprio ? propostasTodas.filter((item) => idsPermitidos.has(String(item.oportunidade_id || ""))) : propostasTodas
    const pedidos = escopoProprio ? pedidosTodos.filter((item) => idsPermitidos.has(String(item.oportunidade_id || ""))) : pedidosTodos
    const vendas = escopoProprio ? vendasTodas.filter((item) => pertenceAoEscopoDoUsuario(String(item.responsavel_id || ""), usuario) || idsPermitidos.has(String(item.oportunidade_id || ""))) : vendasTodas
    const hoje = new Date().toISOString().slice(0, 10)
    const visitas = atividades.filter((item) => String(item.tipo || "").toUpperCase().includes("VISITA") && String(item.data || item.data_atividade || "").slice(0, 10) === hoje).length
    const pendencias = agendaItens.filter((item) => !["CONCLUIDA", "CONCLUÍDA", "CANCELADA"].includes(String(item.status || "").toUpperCase())).length
    const destaque = abertas[0]
    const contexto = destaque ? lerContextoOportunidade(destaque) : null
    const titulo = destaque ? textoSeguro(destaque.titulo) || textoSeguro(destaque.equipamento) || "Negociação" : ""
    const cliente = destaque ? textoSeguro(destaque.cliente_nome) || "Cliente" : ""

    setResumo({
      visitas,
      pendencias,
      atividades: atividades.length,
      oportunidades: abertas.length,
      pipeline: oportunidades.length,
      clientes: clientes.length,
      propostas: propostas.length,
      pedidos: pedidos.length,
      vendas: vendas.length,
      destaque: destaque ? `${cliente} · ${titulo} · ${contexto?.quantidade || 1} un.` : t.noCurrent,
    })
    setOnline(true)
    setSincronizando(false)
  }, [t.noCurrent, t.syncError, usuario])

  useEffect(() => {
    queueMicrotask(() => void sincronizar())
    const id = window.setInterval(() => void sincronizar(), 60_000)
    return () => window.clearInterval(id)
  }, [sincronizar])

  const recursos = useMemo(() => {
    const base = [
      { href: "/crm-app/atividades", label: t.activities, valor: resumo.atividades, icon: ClipboardCheck },
      { href: "/crm-app/pipeline", label: t.pipeline, valor: resumo.pipeline, icon: TrendingUp },
      { href: "/crm-app/propostas", label: t.proposals, valor: resumo.propostas, icon: FileText },
      { href: "/crm-app/pedidos", label: t.orders, valor: resumo.pedidos, icon: PackageCheck },
      { href: "/crm-app/vendas", label: t.sales, valor: resumo.vendas, icon: CircleDollarSign },
      { href: "/ia-comercial", label: t.ai, valor: "IA", icon: Bot },
    ]
    if (adminMaster) base.push({ href: "/crm-app/controle-financeiro", label: t.financial, valor: "MASTER", icon: PiggyBank })
    return base
  }, [adminMaster, resumo, t])

  const primeiroNome = usuario?.nome?.split(" ")[0] || ""
  const hello = t.hello.replace("{name}", primeiroNome)

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-28 text-white">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[.28em] text-cyan-400">{t.brand}</p>
            <h1 className="mt-1 text-lg font-bold">{t.today}</h1>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher compact />
            <span className={`rounded-full border px-3 py-1 text-xs ${online ? "border-emerald-900 bg-emerald-950/30 text-emerald-300" : "border-amber-900 bg-amber-950/30 text-amber-300"}`}>{online ? t.online : t.reconnecting}</span>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-4 py-5 sm:px-6">
        {aviso && <div className="mb-4 rounded-2xl border border-amber-900/70 bg-amber-950/20 p-4 text-sm text-amber-100">{aviso}</div>}

        <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 shadow-xl">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-3xl font-bold">{hello}</h2>
              <p className="mt-2 text-base leading-6 text-slate-300">{t.subtitle}</p>
            </div>
            <button type="button" onClick={() => void sincronizar()} aria-label="Sincronizar CRM" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-cyan-800 bg-cyan-950/30 text-cyan-300">
              <RefreshCw size={20} className={sincronizando ? "animate-spin" : ""} />
            </button>
          </div>
          <div className="mt-5 grid grid-cols-3 gap-2">
            <Indicador valor={resumo.visitas} label={t.visits} />
            <Indicador valor={resumo.pendencias} label={t.pending} />
            <Indicador valor={resumo.oportunidades} label={t.openDeals} />
          </div>
        </section>

        <section className="mt-5 grid gap-3">
          <Link href="/crm-app/acao" className="flex min-h-28 items-center gap-4 rounded-3xl bg-cyan-500 p-5 text-slate-950 shadow-xl active:scale-[.99]">
            <span className="grid size-14 shrink-0 place-items-center rounded-2xl bg-slate-950/10"><Plus size={30} /></span>
            <span className="min-w-0 flex-1"><span className="block text-2xl font-black">{t.mainAction}</span><span className="mt-1 block text-sm font-medium text-slate-900/75">{t.mainActionHelp}</span></span>
            <ChevronRight size={25} />
          </Link>

          <div className="grid gap-3 sm:grid-cols-3">
            <Acao href="/crm-app/oportunidades" titulo={t.next} descricao={t.nextHelp} icon={Target} />
            <Acao href="/crm-app/agenda" titulo={t.agenda} descricao={t.agendaHelp} icon={CalendarDays} />
            <Acao href="/crm-app/clientes" titulo={t.clients} descricao={t.clientsHelp} icon={Search} />
          </div>
        </section>

        <section className="mt-5 rounded-3xl border border-[#16325c] bg-[#081a32] p-5">
          <div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-cyan-950/60 text-cyan-300"><BriefcaseBusiness size={22} /></span><div><p className="text-xs uppercase tracking-[.18em] text-slate-500">{t.current}</p><p className="mt-1 font-semibold leading-6">{resumo.destaque}</p></div></div>
          <Link href="/crm-app/oportunidades" className="mt-4 flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#24466f] bg-[#0b2342] font-semibold text-cyan-200">{t.details}<ChevronRight size={18}/></Link>
        </section>

        <details className="mt-5 rounded-3xl border border-[#16325c] bg-[#061126] p-4">
          <summary className="cursor-pointer list-none rounded-2xl px-1 py-2"><span className="block text-lg font-semibold">{t.more}</span><span className="mt-1 block text-sm text-slate-400">{t.moreHelp}</span></summary>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {recursos.map(({ href, label, valor, icon: Icon }) => (
              <Link key={href} href={href} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4">
                <div className="flex items-center justify-between gap-2"><Icon size={20} className="text-cyan-300"/><strong className="text-sm text-cyan-200">{valor}</strong></div>
                <span className="mt-3 block text-sm font-semibold">{label}</span>
              </Link>
            ))}
          </div>
        </details>
      </div>
    </main>
  )
}

function Indicador({ valor, label }: { valor: number; label: string }) {
  return <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-2 py-4 text-center"><strong className="block text-2xl text-cyan-300">{valor}</strong><span className="mt-1 block text-[11px] leading-4 text-slate-400">{label}</span></div>
}

function Acao({ href, titulo, descricao, icon: Icon }: { href: string; titulo: string; descricao: string; icon: React.ComponentType<{ size?: number; className?: string }> }) {
  return <Link href={href} className="flex min-h-28 items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4 active:scale-[.99] sm:block"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-cyan-950/70 text-cyan-300"><Icon size={21}/></span><span className="min-w-0 flex-1 sm:mt-3 sm:block"><span className="block text-base font-semibold">{titulo}</span><span className="mt-1 block text-xs leading-5 text-slate-400">{descricao}</span></span><ChevronRight size={18} className="shrink-0 text-slate-600 sm:hidden"/></Link>
}
