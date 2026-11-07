"use client"

import Link from "next/link"
import { ChevronRight, Sparkles } from "lucide-react"
import { useOperationalI18n } from "@/core/i18n/operational"
import { LinkSeguro, rotaDoCanal } from "@/components/inteligencia/BriefingComercialView"
import { useBriefingComercial } from "@/components/inteligencia/useBriefingComercial"

/**
 * Resumo do agente na tela inicial do app. É independente do restante da tela:
 * se a leitura falhar ou demorar, o fluxo comercial continua intacto.
 */
export default function PrioridadesAgenteCard() {
  const { formatCurrency } = useOperationalI18n()
  const { briefing, carregando, erro } = useBriefingComercial({ limite: 3 })

  if (erro) return null

  return (
    <section className="mt-5 rounded-3xl border border-cyan-900/70 bg-[#06182f] p-5" aria-busy={carregando}>
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.2em] text-cyan-400"><Sparkles size={14}/> Prioridades do agente</p>
      {!briefing ? (
        <div className="mt-3 space-y-2" aria-hidden><div className="h-4 w-4/5 animate-pulse rounded bg-[#0b2342]"/><div className="h-4 w-3/5 animate-pulse rounded bg-[#0b2342]"/></div>
      ) : (
        <>
          <p className="mt-2 font-semibold leading-6 text-white">{briefing.manchete}</p>
          {briefing.prioridades.length > 0 && (
            <ol className="mt-3 space-y-2">
              {briefing.prioridades.slice(0, 3).map((item, indice) => (
                <li key={`${item.entidade_tipo}-${item.entidade_id}`}>
                  <LinkSeguro href={rotaDoCanal(item, "app")} className="flex items-start gap-3 rounded-2xl border border-[#163356] bg-[#0b1d38] p-3 active:scale-[.99]">
                    <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[#0b2342] text-xs font-bold text-cyan-200">{indice + 1}</span>
                    <span className="min-w-0 flex-1"><span className="line-clamp-2 block text-sm font-semibold leading-5">{item.titulo}</span><span className="mt-1 line-clamp-2 block text-xs leading-5 text-slate-400">{item.acao_recomendada}</span>{item.valor > 0 && <span className="mt-1 block text-xs text-emerald-300">{formatCurrency(item.valor)}</span>}</span>
                  </LinkSeguro>
                </li>
              ))}
            </ol>
          )}
          <Link href="/crm-app/prioridades" className="mt-4 flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#22466d] bg-[#0b2342] font-semibold text-cyan-200">Ver leitura completa<ChevronRight size={18}/></Link>
        </>
      )}
    </section>
  )
}
