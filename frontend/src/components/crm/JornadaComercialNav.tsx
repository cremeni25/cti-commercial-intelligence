"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useI18n, type MessageKey } from "@/core/i18n"

type Etapa = { href: string; labelKey: MessageKey; descricao: { "pt-BR": string; en: string; es: string } }

const etapas: Etapa[] = [
  { href: "/oportunidades", labelKey: "nav.opportunities", descricao: { "pt-BR": "negócio e próximos passos", en: "deal and next steps", es: "negocio y próximos pasos" } },
  { href: "/pipeline", labelKey: "nav.pipeline", descricao: { "pt-BR": "posição por estágio", en: "position by stage", es: "posición por etapa" } },
  { href: "/forecast", labelKey: "nav.forecast", descricao: { "pt-BR": "projeção por competência", en: "period-based projection", es: "proyección por período" } },
  { href: "/propostas", labelKey: "nav.proposals", descricao: { "pt-BR": "documento e negociação", en: "document and negotiation", es: "documento y negociación" } },
  { href: "/pedidos", labelKey: "nav.orders", descricao: { "pt-BR": "execução pós-aceite", en: "post-acceptance execution", es: "ejecución posterior a la aceptación" } },
  { href: "/vendas", labelKey: "nav.sales", descricao: { "pt-BR": "realizado e histórico", en: "completed business and history", es: "realizado e historial" } },
]

const cabecalho = {
  "pt-BR": { titulo: "Jornada comercial única", descricao: "O mesmo negócio atravessa seis visões. Cada tela responde uma função diferente, sem criar uma segunda fonte de verdade." },
  en: { titulo: "Single commercial journey", descricao: "The same deal moves through six views. Each screen serves a different purpose without creating a second source of truth." },
  es: { titulo: "Jornada comercial única", descricao: "El mismo negocio recorre seis vistas. Cada pantalla cumple una función distinta sin crear una segunda fuente de verdad." },
}

export default function JornadaComercialNav() {
  const pathname = usePathname()
  const { locale, t } = useI18n()
  const texto = cabecalho[locale]
  return <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-4">
    <div className="mb-3"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">{texto.titulo}</p><p className="mt-1 text-sm text-slate-400">{texto.descricao}</p></div>
    <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">{etapas.map((item) => {
      const ativo = pathname === item.href || pathname.startsWith(`${item.href}/`)
      return <Link key={item.href} href={item.href} className={`rounded-xl border px-4 py-3 ${ativo ? "border-cyan-500 bg-cyan-950/40" : "border-[#24466f] bg-[#020817] hover:border-cyan-800"}`}>
        <strong className={ativo ? "text-cyan-300" : "text-slate-200"}>{t(item.labelKey)}</strong>
        <span className="mt-1 block text-xs text-slate-500">{item.descricao[locale]}</span>
      </Link>
    })}</div>
  </section>
}
