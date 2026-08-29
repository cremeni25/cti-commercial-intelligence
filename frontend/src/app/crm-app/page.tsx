"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Bot,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  ClipboardCheck,
  FileText,
  PackageCheck,
  PiggyBank,
  RefreshCw,
  Route,
  Target,
  TrendingUp,
  UserPlus,
  Users,
} from "lucide-react"
import { useAuth } from "@/core/auth"
import { useI18n } from "@/core/i18n"
import LanguageSwitcher from "@/components/i18n/LanguageSwitcher"
import { pertenceAoEscopoDoUsuario, possuiEscopoProprio } from "@/core/rbac/commercial-scope"
import { lerContextoOportunidade, textoSeguro } from "@/lib/crm-opportunity"

type Registro = Record<string, unknown>
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
  const { t } = useI18n()
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [resumo, setResumo] = useState<Resumo>({
    visitas: 0,
    pendencias: 0,
    atividades: 0,
    oportunidades: 0,
    pipeline: 0,
    clientes: 0,
    propostas: 0,
    pedidos: 0,
    vendas: 0,
    destaque: t("crm.home.noOpenOpportunity"),
  })
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
      setAviso(t("crm.home.syncFailed"))
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
    const visitas = atividades.filter((item) =>
      String(item.tipo || "").toUpperCase().includes("VISITA") &&
      String(item.data || item.data_atividade || "").slice(0, 10) === hoje
    ).length
    const pendencias = agendaItens.filter((item) => !["CONCLUIDA", "CONCLUÍDA", "CANCELADA"].includes(String(item.status || "").toUpperCase())).length
    const destaque = abertas[0]
    const contexto = destaque ? lerContextoOportunidade(destaque) : null
    const titulo = destaque ? textoSeguro(destaque.titulo) || textoSeguro(destaque.equipamento) || t("crm.opportunity.generic") : ""
    const cliente = destaque ? textoSeguro(destaque.cliente_nome) || t("crm.account.identifying") : ""

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
      destaque: destaque ? `${cliente} · ${titulo} · ${contexto?.quantidade || 1} un.` : t("crm.home.noOpenOpportunity"),
    })
    setOnline(true)
    setSincronizando(false)
  }, [t, usuario])

  useEffect(() => {
    queueMicrotask(() => void sincronizar())
    const id = window.setInterval(() => void sincronizar(), 60_000)
    return () => window.clearInterval(id)
  }, [sincronizar])

  const modulos = useMemo(() => {
    const base = [
      { href: "/crm-app/agenda", label: t("crm.module.agenda"), valor: resumo.pendencias, descricao: t("crm.module.agendaDescription"), icon: CalendarDays, financeiro: false },
      { href: "/crm-app/atividades", label: t("crm.module.activities"), valor: resumo.atividades, descricao: t("crm.module.activitiesDescription"), icon: ClipboardCheck, financeiro: false },
      { href: "/crm-app/clientes", label: t("crm.module.accounts"), valor: resumo.clientes, descricao: t("crm.module.accountsDescription"), icon: Users, financeiro: false },
      { href: "/crm-app/visitas", label: t("crm.module.visits"), valor: resumo.visitas, descricao: t("crm.module.visitsDescription"), icon: Route, financeiro: false },
      { href: "/crm-app/oportunidades", label: t("crm.module.opportunities"), valor: resumo.oportunidades, descricao: resumo.destaque, icon: BriefcaseBusiness, financeiro: false },
      { href: "/crm-app/pipeline", label: t("crm.module.pipeline"), valor: resumo.pipeline, descricao: t("crm.module.pipelineDescription"), icon: TrendingUp, financeiro: false },
      { href: "/crm-app/propostas", label: t("crm.module.proposals"), valor: resumo.propostas, descricao: t("crm.module.proposalsDescription"), icon: FileText, financeiro: false },
      { href: "/crm-app/pedidos", label: t("crm.module.orders"), valor: resumo.pedidos, descricao: t("crm.module.ordersDescription"), icon: PackageCheck, financeiro: false },
      { href: "/crm-app/vendas", label: t("crm.module.sales"), valor: resumo.vendas, descricao: t("crm.module.salesDescription"), icon: CircleDollarSign, financeiro: false },
      { href: "/ia-comercial", label: t("crm.module.salesAi"), valor: "IA", descricao: t("crm.module.salesAiDescription"), icon: Bot, financeiro: false },
    ]

    if (adminMaster) {
      base.push({
        href: "/crm-app/controle-financeiro",
        label: t("crm.module.financialControl"),
        valor: "MASTER",
        descricao: t("crm.module.financialControlDescription"),
        icon: PiggyBank,
        financeiro: true,
      })
    }

    return base
  }, [adminMaster, resumo, t])

  const atalhos = useMemo(() => [
    { href: "/crm-app/clientes/nova", titulo: t("crm.action.newAccount"), descricao: t("crm.action.newAccountDescription"), icon: UserPlus },
    { href: "/crm-app/atividades/nova", titulo: t("crm.action.logActivity"), descricao: t("crm.action.logActivityDescription"), icon: ClipboardCheck },
    { href: "/crm-app/oportunidades/nova", titulo: t("crm.action.newOpportunity"), descricao: t("crm.action.newOpportunityDescription"), icon: Target },
    { href: "/crm-app/clientes", titulo: t("crm.action.findAccount"), descricao: t("crm.action.findAccountDescription"), icon: Building2 },
  ], [t])

  const primeiroNome = usuario?.nome?.split(" ")[0] || t("crm.home.defaultUser")

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4">
        <div className="mx-auto flex w-full max-w-[94vw] items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[.28em] text-cyan-400 sm:text-xs">{t("crm.home.brand")}</p>
            <h1 className="mt-1 text-lg font-bold sm:text-2xl">{t("crm.home.title")}</h1>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher compact />
            <div className={`rounded-full border px-3 py-1 text-xs ${online ? "border-emerald-900 bg-emerald-950/30 text-emerald-300" : "border-amber-900 bg-amber-950/30 text-amber-300"}`}>
              {online ? t("common.online") : t("common.reconnecting")}
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-[94vw] px-4 py-4 sm:px-6 sm:py-6">
        {aviso && <div className="mb-4 rounded-2xl border border-amber-900/70 bg-amber-950/20 p-4 text-sm text-amber-100">{aviso}</div>}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(360px,.65fr)]">
          <div className="space-y-5">
            <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 shadow-xl sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400 sm:text-base">{t("crm.home.dailyOperation")}</p>
                  <h2 className="mt-1 text-2xl font-bold sm:text-3xl">{t("crm.home.hello", { name: primeiroNome })}</h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">{t("crm.home.truthFlow")}</p>
                </div>
                <button type="button" onClick={() => void sincronizar()} aria-label="Sincronizar CRM" className="rounded-2xl border border-cyan-800 bg-cyan-950/30 p-3 text-cyan-300">
                  <RefreshCw size={20} className={sincronizando ? "animate-spin" : ""} />
                </button>
              </div>
              <div className="mt-6 grid grid-cols-3 gap-3">
                <Indicador valor={resumo.visitas} label={t("crm.home.visitsToday")} />
                <Indicador valor={resumo.pendencias} label={t("crm.home.pending")} />
                <Indicador valor={resumo.oportunidades} label={t("crm.module.opportunities")} />
              </div>
            </section>

            <section>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold">{t("crm.home.quickActions")}</h2>
                <span className="text-sm text-slate-500">{t("crm.home.fieldUse")}</span>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {atalhos.map(({ href, titulo, descricao, icon: Icon }) => (
                  <Link key={href} href={href} className="flex min-h-24 items-center gap-4 rounded-2xl border border-[#16325c] bg-[#091a33] p-5">
                    <span className="rounded-2xl bg-cyan-950/50 p-4 text-cyan-300"><Icon size={22} /></span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-lg font-semibold">{titulo}</span>
                      <span className="mt-1 block text-sm text-slate-400">{descricao}</span>
                    </span>
                    <ChevronRight size={18} className="text-slate-600" />
                  </Link>
                ))}
              </div>
            </section>
          </div>

          <section>
            <h2 className="mb-4 text-xl font-semibold">{t("crm.home.modules")}</h2>
            <div className="grid grid-cols-2 gap-4 xl:grid-cols-3">
              {modulos.map(({ href, label, valor, descricao, icon: Icon, financeiro }) => (
                <Link href={href} key={href} className={`flex min-h-36 flex-col justify-between rounded-2xl border p-5 transition ${financeiro ? "border-emerald-800 bg-emerald-950/15 hover:border-emerald-500" : "border-[#16325c] bg-[#07162b] hover:border-cyan-700"}`}>
                  <Icon className={financeiro ? "text-emerald-300" : "text-cyan-300"} size={24} />
                  <div>
                    <strong className={`mt-3 block text-2xl ${financeiro ? "text-emerald-300" : "text-cyan-300"}`}>{valor}</strong>
                    <span className="block font-semibold">{label}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-400">{descricao}</span>
                  </div>
                </Link>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-emerald-900/70 bg-emerald-950/20 p-4">
              <p className="text-sm font-semibold text-emerald-200">Núcleo único sincronizado</p>
              <p className="mt-1 text-xs leading-5 text-emerald-100/70">Proposta negocia, pedido executa e venda registra o realizado. Nenhuma dessas telas cria um segundo negócio.</p>
            </div>
          </section>
        </div>
      </div>
    </main>
  )
}

function Indicador({ valor, label }: { valor: number; label: string }) {
  return (
    <div className="rounded-2xl border border-[#17365f] bg-[#061126]/70 px-4 py-4 text-center">
      <strong className="block text-2xl text-cyan-300">{valor}</strong>
      <span className="mt-1 block text-xs text-slate-400">{label}</span>
    </div>
  )
}
