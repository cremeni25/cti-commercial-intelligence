"use client"

import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { useI18n } from "@/core/i18n"

const textos = {
  "pt-BR": {
    eyebrow: "NÚCLEO DE INTELIGÊNCIA COMERCIAL",
    title: "Inteligência Comercial",
    intro: "Uma única entrada para entender o mercado, aprender com o histórico, acompanhar território e equipe e aprofundar decisões com a IA Comercial.",
    scope: "Visão ativa",
    team: "Toda a equipe comercial",
    personal: "Meu escopo comercial",
    principle: "Primeiro a decisão. O detalhe, a auditoria e a metodologia ficam disponíveis quando forem necessários.",
    executive: "Visão Executiva",
    executiveText: "Mercado → posição Carrier → concorrência → prioridades. A leitura principal para decisão rápida.",
    market: "Mercado",
    marketText: "ANFIR, presença Carrier, concorrência, segmentos e sinais de cobertura comercial.",
    history: "Histórico",
    historyText: "Aprendizado comercial 2023–2026: resultados, padrões, perdas, equipamentos e evidências preservadas.",
    territory: "Equipe e Território",
    territoryText: "Responsável, carteira, cobertura do mercado real e conexão entre ANFIR, Histórico/Funil e CRM.",
    open: "Abrir visualização",
    aiTitle: "Precisa aprofundar?",
    aiText: "Use a IA Comercial para investigar por quê, comparar cenários, priorizar contas ou construir uma ação específica sem sobrecarregar a leitura principal.",
    aiButton: "Abrir IA Comercial",
    trustTitle: "Contrato de leitura",
    trustText: "Nenhuma informação foi descartada nesta evolução. As fontes e cálculos existentes permanecem preservados; esta camada reorganiza o acesso para reduzir repetição e confusão.",
  },
  en: {
    eyebrow: "COMMERCIAL INTELLIGENCE HUB",
    title: "Commercial Intelligence",
    intro: "One entry point to understand the market, learn from history, follow territory and team, and deepen decisions with Commercial AI.",
    scope: "Active view",
    team: "Entire commercial team",
    personal: "My commercial scope",
    principle: "Decision first. Detail, audit and methodology remain available when needed.",
    executive: "Executive View",
    executiveText: "Market → Carrier position → competition → priorities. The primary view for fast decisions.",
    market: "Market",
    marketText: "ANFIR, Carrier presence, competition, segments and commercial coverage signals.",
    history: "History",
    historyText: "Commercial learning 2023–2026: results, patterns, losses, equipment and preserved evidence.",
    territory: "Team and Territory",
    territoryText: "Owner, portfolio, real-market coverage and the connection between ANFIR, History/Funnel and CRM.",
    open: "Open view",
    aiTitle: "Need to go deeper?",
    aiText: "Use Commercial AI to investigate why, compare scenarios, prioritize accounts or build a specific action without overloading the primary view.",
    aiButton: "Open Commercial AI",
    trustTitle: "Reading contract",
    trustText: "No information was discarded in this evolution. Existing sources and calculations remain preserved; this layer reorganizes access to reduce repetition and confusion.",
  },
  es: {
    eyebrow: "NÚCLEO DE INTELIGENCIA COMERCIAL",
    title: "Inteligencia Comercial",
    intro: "Una sola entrada para entender el mercado, aprender del histórico, acompañar territorio y equipo y profundizar decisiones con la IA Comercial.",
    scope: "Visión activa",
    team: "Todo el equipo comercial",
    personal: "Mi alcance comercial",
    principle: "Primero la decisión. El detalle, la auditoría y la metodología siguen disponibles cuando sean necesarios.",
    executive: "Visión Ejecutiva",
    executiveText: "Mercado → posición Carrier → competencia → prioridades. La lectura principal para una decisión rápida.",
    market: "Mercado",
    marketText: "ANFIR, presencia Carrier, competencia, segmentos y señales de cobertura comercial.",
    history: "Histórico",
    historyText: "Aprendizaje comercial 2023–2026: resultados, patrones, pérdidas, equipos y evidencias preservadas.",
    territory: "Equipo y Territorio",
    territoryText: "Responsable, cartera, cobertura del mercado real y conexión entre ANFIR, Histórico/Embudo y CRM.",
    open: "Abrir visualización",
    aiTitle: "¿Necesita profundizar?",
    aiText: "Use la IA Comercial para investigar por qué, comparar escenarios, priorizar cuentas o construir una acción específica sin sobrecargar la lectura principal.",
    aiButton: "Abrir IA Comercial",
    trustTitle: "Contrato de lectura",
    trustText: "Ninguna información fue descartada en esta evolución. Las fuentes y cálculos existentes permanecen preservados; esta capa reorganiza el acceso para reducir repetición y confusión.",
  },
} as const

const visualizacoes = [
  { key: "executive", textKey: "executiveText", href: "/dashboard", icon: "◎" },
  { key: "market", textKey: "marketText", href: "/inteligencia", icon: "◉" },
  { key: "history", textKey: "historyText", href: "/historico-comercial", icon: "↺" },
  { key: "territory", textKey: "territoryText", href: "/mapa-estrategico", icon: "⌖" },
] as const

export default function InteligenciaComercialPage() {
  const { usuario } = useAuth()
  const { locale } = useI18n()
  const tx = textos[locale]
  const consolidada = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER" || Boolean(usuario?.acesso_total || usuario?.permissoes?.acesso_total)

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-hidden">
        <Topbar />
        <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="rounded-3xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.10),transparent_42%),#07142b] p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">{tx.eyebrow}</p>
            <div className="mt-3 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
              <div className="max-w-4xl">
                <h1 className="text-3xl font-bold sm:text-4xl">{tx.title}</h1>
                <p className="mt-3 text-base leading-7 text-slate-300">{tx.intro}</p>
              </div>
              <div className="shrink-0 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-300">{tx.scope}</p>
                <p className="mt-1 text-sm font-semibold text-white">{consolidada ? tx.team : tx.personal}</p>
              </div>
            </div>
            <p className="mt-6 border-t border-white/10 pt-5 text-sm font-medium text-cyan-100">{tx.principle}</p>
          </header>

          <section className="grid gap-4 md:grid-cols-2">
            {visualizacoes.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                className="group flex min-h-[190px] flex-col justify-between rounded-3xl border border-[#1b2d50] bg-[#07142b] p-6 transition hover:-translate-y-0.5 hover:border-cyan-400/60 hover:bg-[#0a1933]"
              >
                <div>
                  <div className="flex items-center justify-between gap-4">
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-500/10 text-xl font-bold text-cyan-300">{item.icon}</span>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{tx.open} →</span>
                  </div>
                  <h2 className="mt-5 text-2xl font-bold text-white">{tx[item.key]}</h2>
                  <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">{tx[item.textKey]}</p>
                </div>
              </Link>
            ))}
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <div className="rounded-3xl border border-violet-500/25 bg-violet-500/5 p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">IA COMERCIAL</p>
              <h2 className="mt-2 text-2xl font-bold">{tx.aiTitle}</h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">{tx.aiText}</p>
              <Link href="/ia-comercial" className="mt-5 inline-flex rounded-xl bg-violet-400 px-5 py-3 text-sm font-bold text-[#071028] transition hover:bg-violet-300">{tx.aiButton}</Link>
            </div>
            <div className="rounded-3xl border border-emerald-500/20 bg-emerald-500/5 p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">{tx.trustTitle}</p>
              <p className="mt-3 text-sm leading-6 text-slate-300">{tx.trustText}</p>
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}
