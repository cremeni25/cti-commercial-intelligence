"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const etapas = [
  { href: "/crm-app/propostas", label: "Propostas", descricao: "documento, versão e aceite" },
  { href: "/crm-app/pedidos", label: "Pedidos", descricao: "execução e envio pós-aceite" },
  { href: "/crm-app/vendas", label: "Vendas", descricao: "negócios efetivamente concluídos" },
]

export default function JornadaDocumentalNav() {
  const pathname = usePathname()
  return <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4">
    <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Da negociação ao realizado</p>
    <p className="mt-1 text-sm text-slate-400">São etapas do mesmo negócio: proposta negocia, pedido executa e venda registra o realizado.</p>
    <div className="mt-3 grid gap-2 sm:grid-cols-3">{etapas.map((item) => {
      const ativo = pathname === item.href || pathname.startsWith(`${item.href}/`)
      return <Link key={item.href} href={item.href} className={`rounded-2xl border px-4 py-3 ${ativo ? "border-cyan-500 bg-cyan-950/40" : "border-[#24466f] bg-[#020817]"}`}>
        <strong className={ativo ? "text-cyan-300" : "text-slate-200"}>{item.label}</strong>
        <span className="mt-1 block text-xs text-slate-500">{item.descricao}</span>
      </Link>
    })}</div>
  </section>
}
