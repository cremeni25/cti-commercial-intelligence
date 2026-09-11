"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import { usePathname } from "next/navigation"
import { ChevronDown, ChevronRight, ShieldCheck } from "lucide-react"
import { useAuth } from "@/core/auth"

const etapas = [
  { href: "/crm-app/oportunidades", label: "Interesse", detalhe: "qualificar a negociação" },
  { href: "/crm-app/propostas", label: "Proposta", detalhe: "gerar, revisar e enviar" },
  { href: "/crm-app/pedidos", label: "Pedido", detalhe: "acompanhar o pós-aceite" },
  { href: "/crm-app/vendas", label: "Concluído", detalhe: "negócio realizado" },
  { href: "/crm-app/atividades?tipo=POS_VENDA", label: "Pós-venda", detalhe: "acompanhar o cliente" },
]

function indiceAtual(pathname: string) {
  if (pathname.startsWith("/crm-app/propostas")) return 1
  if (pathname.startsWith("/crm-app/pedidos")) return 2
  if (pathname.startsWith("/crm-app/vendas")) return 3
  if (pathname.startsWith("/crm-app/atividades")) return 4
  return 0
}

export default function JornadaDocumentalNav() {
  const pathname = usePathname() || "/crm-app/oportunidades"
  const { usuario } = useAuth()
  const [aberto, setAberto] = useState(false)
  const atual = indiceAtual(pathname)
  const adminMaster = usuario?.tipo_usuario === "ADMIN_MASTER"
  const proxima = useMemo(() => etapas[Math.min(atual + 1, etapas.length - 1)], [atual])

  return (
    <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 shadow-lg">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-semibold uppercase tracking-[.2em] text-cyan-400">Evolução da negociação</p>
          <div className="mt-2 flex items-center gap-2" aria-label={`Etapa ${atual + 1} de ${etapas.length}: ${etapas[atual].label}`}>
            {etapas.map((item, indice) => (
              <span key={item.href} className={`h-2 flex-1 rounded-full ${indice <= atual ? "bg-cyan-400" : "bg-slate-700"}`} />
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <div>
              <strong className="block text-lg text-white">{etapas[atual].label}</strong>
              <span className="text-sm text-slate-400">{etapas[atual].detalhe}</span>
            </div>
            {atual < etapas.length - 1 && (
              <Link href={proxima.href} className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950">
                Próxima etapa <ChevronRight size={17} />
              </Link>
            )}
          </div>
        </div>
      </div>

      <button type="button" onClick={() => setAberto((v) => !v)} className="mt-4 flex min-h-11 w-full items-center justify-between rounded-xl border border-[#24466f] bg-[#020817] px-4 text-sm font-semibold text-slate-300">
        <span>{aberto ? "Ocultar etapas" : "Ver todas as etapas"}</span>
        <ChevronDown size={18} className={`transition ${aberto ? "rotate-180" : ""}`} />
      </button>

      {aberto && (
        <div className="mt-3 grid gap-2 sm:grid-cols-5">
          {etapas.map((item, indice) => {
            const ativo = indice === atual
            return (
              <Link key={item.href} href={item.href} className={`rounded-2xl border px-3 py-3 ${ativo ? "border-cyan-500 bg-cyan-950/40" : "border-[#24466f] bg-[#020817]"}`}>
                <span className="text-[10px] uppercase tracking-[.14em] text-slate-600">{indice + 1}</span>
                <strong className={`mt-1 block text-sm ${ativo ? "text-cyan-300" : "text-slate-200"}`}>{item.label}</strong>
              </Link>
            )
          })}
        </div>
      )}

      {adminMaster && (
        <Link href="/crm-app/oportunidades/homologacao" className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-xl border border-amber-700/70 bg-amber-950/30 px-3 text-xs font-semibold text-amber-200">
          <ShieldCheck size={15} /> Administração
        </Link>
      )}
    </section>
  )
}
