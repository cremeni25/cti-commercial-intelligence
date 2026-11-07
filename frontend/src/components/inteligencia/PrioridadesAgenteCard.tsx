"use client"

import Link from "next/link"
import { useState } from "react"
import { CheckCircle2, ChevronRight, Sparkles } from "lucide-react"
import { useOperationalI18n } from "@/core/i18n/operational"
import AcoesPrioridade from "@/components/inteligencia/AcoesPrioridade"
import { LinkSeguro, rotaDoCanal } from "@/components/inteligencia/BriefingComercialView"
import { useBriefingComercial } from "@/components/inteligencia/useBriefingComercial"

/**
 * "Comece por aqui": UMA prioridade por vez, com as ações para resolvê-la ali
 * mesmo. Ao resolver, a próxima aparece. Menos leitura, mais ação.
 * Independente do restante da tela: se a leitura falhar, o card não aparece.
 */
export default function PrioridadesAgenteCard() {
  const { formatCurrency } = useOperationalI18n()
  const { briefing, carregando, erro, atualizar } = useBriefingComercial({ limite: 10 })
  const [resolvidos, setResolvidos] = useState<Set<string>>(() => new Set())
  const [aviso, setAviso] = useState("")

  if (erro) return null

  const pendentes = (briefing?.prioridades || []).filter((item) => !resolvidos.has(`${item.entidade_tipo}:${item.entidade_id}`))
  const atual = pendentes[0]

  return (
    <section className="mt-4 rounded-3xl border border-cyan-900/70 bg-[#06182f] p-4" aria-busy={carregando} aria-label="Comece por aqui">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.2em] text-cyan-400"><Sparkles size={14}/> Comece por aqui</p>
        {pendentes.length > 1 && <Link href="/crm-app/prioridades" className="flex items-center gap-1 text-xs font-semibold text-cyan-200">Ver todas ({pendentes.length})<ChevronRight size={14}/></Link>}
      </div>

      {aviso && <p role="status" className="mt-3 rounded-xl border border-emerald-800 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-200">{aviso}</p>}

      {!briefing ? (
        <div className="mt-3 space-y-2" aria-hidden><div className="h-4 w-4/5 animate-pulse rounded bg-[#0b2342]"/><div className="h-4 w-3/5 animate-pulse rounded bg-[#0b2342]"/></div>
      ) : !atual ? (
        <p className="mt-3 flex items-center gap-2 text-sm text-slate-300"><CheckCircle2 size={18} className="text-emerald-400"/> Tudo em dia. Nenhuma pendência urgente na sua carteira.</p>
      ) : (
        <div className="mt-3">
          <LinkSeguro href={rotaDoCanal(atual, "app")} className="block">
            <p className="font-semibold leading-6 text-white">{atual.titulo}</p>
            <p className="mt-1 text-sm leading-6 text-cyan-100">{atual.acao_recomendada}</p>
            {atual.valor > 0 && <p className="mt-1 text-xs text-emerald-300">{formatCurrency(atual.valor)}</p>}
          </LinkSeguro>
          <AcoesPrioridade
            key={`${atual.entidade_tipo}:${atual.entidade_id}`}
            item={atual}
            onResolvido={(mensagem) => {
              setResolvidos((anteriores) => new Set(anteriores).add(`${atual.entidade_tipo}:${atual.entidade_id}`))
              setAviso(mensagem)
              window.setTimeout(() => setAviso(""), 4000)
              window.setTimeout(atualizar, 600)
            }}
          />
        </div>
      )}
    </section>
  )
}
