"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const etapas = [
  { href: "/oportunidades", label: "Oportunidades", descricao: "negócio e próximos passos" },
  { href: "/pipeline", label: "Pipeline", descricao: "posição por estágio" },
  { href: "/forecast", label: "Forecast", descricao: "projeção por competência" },
  { href: "/propostas", label: "Propostas", descricao: "documento e negociação" },
  { href: "/pedidos", label: "Pedidos", descricao: "execução pós-aceite" },
  { href: "/vendas", label: "Vendas", descricao: "realizado e histórico" },
]

export default function JornadaComercialNav() {
  const pathname = usePathname()
  return <section className="rounded-2xl border border-[#13203f] bg-[#071226] p-4">
    <div className="mb-3"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">Jornada comercial única</p><p className="mt-1 text-sm text-slate-400">O mesmo negócio atravessa seis visões. Cada tela responde uma função diferente, sem criar uma segunda fonte de verdade.</p></div>
    <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">{etapas.map((item) => {
      const ativo = pathname === item.href || pathname.startsWith(`${item.href}/`)
      return <Link key={item.href} href={item.href} className={`rounded-xl border px-4 py-3 ${ativo ? "border-cyan-500 bg-cyan-950/40" : "border-[#24466f] bg-[#020817] hover:border-cyan-800"}`}>
        <strong className={ativo ? "text-cyan-300" : "text-slate-200"}>{item.label}</strong>
        <span className="mt-1 block text-xs text-slate-500">{item.descricao}</span>
      </Link>
    })}</div>
  </section>
}
