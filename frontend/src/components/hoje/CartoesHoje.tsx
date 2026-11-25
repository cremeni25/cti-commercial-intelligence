"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { AlertTriangle, BadgeDollarSign, CalendarClock, CheckCircle2, ChevronRight, Compass, Loader2, Target } from "lucide-react"
import { useAuth } from "@/core/auth"
import { rotaAutorizadaCTI } from "@/core/rbac/route-access"
import { buscarHoje, type CartaoHoje, type Hoje } from "@/services/tela-hoje"

const ICONE = { negocio: Target, agenda: CalendarClock, carteira: Compass, comissao: BadgeDollarSign }
const COR = { risco: "border-amber-800/80", oportunidade: "border-emerald-800/80", acao: "border-cyan-800/80" }

/**
 * Os cartões do dia. `canal="app"` usa as rotas do aplicativo e mostra só o que o
 * app ainda não tem ("Comece por aqui" já cobre os negócios).
 */
export default function CartoesHoje({ canal = "web" }: { canal?: "web" | "app" }) {
  const { usuario } = useAuth()
  const [dados, setDados] = useState<Hoje | null>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    buscarHoje().then((d) => { if (ativo) setDados(d) }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Indisponível.") })
    return () => { ativo = false }
  }, [])

  const destino = (c: CartaoHoje) => (canal === "app" ? c.href_app : c.href)
  const cartoes = (dados?.cartoes || [])
    .filter((c) => canal === "web" || c.tipo === "carteira" || c.tipo === "comissao")
    .filter((c) => usuario && rotaAutorizadaCTI(destino(c).split("?")[0], usuario))

  if (canal === "app" && (erro || !dados || cartoes.length === 0)) return null

  return (
    <section aria-label="O que fazer hoje" className={canal === "app" ? "mt-4 space-y-2" : "space-y-4"}>
      {canal === "web" && (
        <>
          {dados?.manchete && <p className="max-w-3xl text-lg text-slate-200">{dados.manchete}</p>}
          {erro && <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>}
          {!dados && !erro && <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
          {dados && cartoes.length === 0 && <p className="flex items-center gap-2 text-slate-300"><CheckCircle2 className="text-emerald-400"/> Tudo em dia. Nenhuma ação urgente agora.</p>}
        </>
      )}
      <ol className={canal === "app" ? "space-y-2" : "grid gap-3 lg:grid-cols-2"}>
        {cartoes.map((c, i) => {
          const Icone = ICONE[c.tipo] || AlertTriangle
          return (
            <li key={`${c.tipo}-${i}`}>
              <Link href={destino(c)} className={`flex h-full items-start gap-3 rounded-3xl border bg-[#06182f] p-4 transition hover:bg-[#0a2242] ${COR[c.tom] || COR.acao}`}>
                <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-[#0b2342] text-cyan-300"><Icone size={20}/></span>
                <span className="min-w-0 flex-1">
                  {canal === "web" && <span className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">{i + 1}º</span>}
                  <strong className="block leading-6 text-white">{c.titulo}</strong>
                  {c.detalhe && <span className="mt-1 block text-sm text-slate-300">{c.detalhe}</span>}
                  <span className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-cyan-300">{c.acao}<ChevronRight size={16}/></span>
                </span>
              </Link>
            </li>
          )
        })}
      </ol>
      {canal === "web" && dados && dados.limitacoes.length > 0 && <p className="text-xs text-slate-500">{dados.limitacoes.join(" ")}</p>}
    </section>
  )
}
