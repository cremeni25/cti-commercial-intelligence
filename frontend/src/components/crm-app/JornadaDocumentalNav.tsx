"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const etapas = [
  { href: "/crm-app/oportunidades", label: "Oportunidades", descricao: "qualificar e conduzir a negociação" },
  { href: "/crm-app/propostas", label: "Propostas", descricao: "documento, versão e aceite" },
  { href: "/crm-app/pedidos", label: "Pedidos", descricao: "execução e envio pós-aceite" },
  { href: "/crm-app/vendas", label: "Vendas", descricao: "negócios efetivamente concluídos" },
  { href: "/crm-app/atividades?tipo=POS_VENDA", label: "Pós-venda", descricao: "acompanhar cliente depois da venda" },
]

export default function JornadaDocumentalNav() {
  const pathname = usePathname()
  return <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4">
    <p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Jornada comercial completa</p>
    <p className="mt-1 text-sm text-slate-400">O mesmo negócio evolui sem criar uma segunda fonte de verdade: oportunidade → proposta → pedido → venda → pós-venda.</p>
    <div className="mt-3 grid gap-2 sm:grid-cols-5">{etapas.map((item, indice) => {
      const ativo = pathname === item.href.split("?")[0] || pathname.startsWith(`${item.href.split("?")[0]}/`)
      return <div key={item.href} className="relative">
        <Link href={item.href} className={`block h-full rounded-2xl border px-4 py-3 ${ativo ? "border-cyan-500 bg-cyan-950/40" : "border-[#24466f] bg-[#020817]"}`}>
          <span className="text-[10px] uppercase tracking-[.16em] text-slate-600">Etapa {indice + 1}</span>
          <strong className={`mt-1 block ${ativo ? "text-cyan-300" : "text-slate-200"}`}>{item.label}</strong>
          <span className="mt-1 block text-xs text-slate-500">{item.descricao}</span>
        </Link>
      </div>
    })}</div>
  </section>
}
