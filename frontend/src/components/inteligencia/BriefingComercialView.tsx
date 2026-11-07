"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Flame, Gauge, ListChecks, ShieldCheck, Sparkles } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { useOperationalI18n } from "@/core/i18n/operational"
import { rotaAutorizadaCTI } from "@/core/rbac/route-access"
import AcoesPrioridade from "@/components/inteligencia/AcoesPrioridade"
import type { BriefingComercial, CategoriaSinal, IndicadorBriefing, PrioridadeComercial } from "@/services/inteligencia-comercial"

export type CanalBriefing = "web" | "app"

const ROTULO_CATEGORIA: Record<CategoriaSinal, string> = {
  acao: "Fazer agora",
  risco: "Risco",
  oportunidade: "Oportunidade",
  qualidade: "Dados",
}

const ESTILO_CATEGORIA: Record<CategoriaSinal, string> = {
  acao: "border-cyan-700/70 bg-cyan-950/40 text-cyan-200",
  risco: "border-amber-700/70 bg-amber-950/40 text-amber-200",
  oportunidade: "border-emerald-700/70 bg-emerald-950/40 text-emerald-200",
  qualidade: "border-slate-600 bg-slate-900 text-slate-300",
}

const ESTILO_TOM: Record<IndicadorBriefing["tom"], string> = {
  neutro: "text-cyan-300",
  atencao: "text-amber-300",
  positivo: "text-emerald-300",
}

type Filtro = "todas" | CategoriaSinal

/** Data civil (AAAA-MM-DD) exibida sem conversão de fuso: evita mostrar o dia anterior no Brasil. */
function dataCivil(valor: string) {
  const [ano, mes, dia] = String(valor || "").slice(0, 10).split("-")
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : valor
}

export function rotaDoCanal(item: { rota: string; rota_app: string }, canal: CanalBriefing) {
  return (canal === "app" ? item.rota_app || item.rota : item.rota || item.rota_app) || ""
}

/** Link que só é renderizado quando o perfil pode abrir o destino; senão vira texto. */
export function LinkSeguro({ href, className, children, ...resto }: Omit<React.ComponentProps<typeof Link>, "href"> & { href: string }) {
  const { usuario } = useAuth()
  if (!href || !usuario || !rotaAutorizadaCTI(href.split("?")[0], usuario)) return <div className={className}>{children}</div>
  return <Link href={href} className={className} {...resto}>{children}</Link>
}

export default function BriefingComercialView({ briefing, canal, onAtualizar }: { briefing: BriefingComercial; canal: CanalBriefing; onAtualizar?: () => void }) {
  const { formatCurrency, formatNumber } = useOperationalI18n()
  const [filtro, setFiltro] = useState<Filtro>("todas")
  // Itens resolvidos somem na hora; a leitura completa é refeita em seguida.
  const [resolvidos, setResolvidos] = useState<Set<string>>(() => new Set())
  const [aviso, setAviso] = useState("")
  const chaveItem = (item: PrioridadeComercial) => `${item.entidade_tipo}:${item.entidade_id}`
  const ativos = useMemo(() => briefing.prioridades.filter((item) => !resolvidos.has(chaveItem(item))), [briefing.prioridades, resolvidos])
  useEffect(() => {
    if (!aviso) return
    const temporizador = window.setTimeout(() => setAviso(""), 5000)
    return () => window.clearTimeout(temporizador)
  }, [aviso])
  function resolver(item: PrioridadeComercial, mensagem: string) {
    setResolvidos((atual) => new Set(atual).add(chaveItem(item)))
    setAviso(mensagem)
    if (onAtualizar) window.setTimeout(onAtualizar, 600)
  }

  const contagem = useMemo(() => {
    const base: Record<Filtro, number> = { todas: ativos.length, acao: 0, risco: 0, oportunidade: 0, qualidade: 0 }
    ativos.forEach((item) => { base[item.categoria] += 1 })
    return base
  }, [ativos])

  const prioridades = filtro === "todas" ? ativos : ativos.filter((item) => item.categoria === filtro)
  const formatar = (indicador: IndicadorBriefing) => indicador.formato === "moeda" ? (canal === "app" ? formatCurrency(indicador.valor, { currency: "BRL", notation: "compact", maximumFractionDigits: 2 }) : formatCurrency(indicador.valor)) : indicador.formato === "percentual" ? `${formatNumber(indicador.valor)}%` : formatNumber(indicador.valor)
  const maiorEtapa = Math.max(1, ...briefing.pipeline.etapas.map((etapa) => etapa.valor))
  const compacto = canal === "app"

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-[#163356] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5 sm:p-6">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.22em] text-cyan-400"><Sparkles size={14}/> Leitura do agente · {dataCivil(briefing.data_referencia)}</p>
        <h2 className="mt-3 text-xl font-bold leading-snug text-white sm:text-2xl">{briefing.manchete}</h2>
        <p className="mt-2 text-sm text-slate-400">{briefing.escopo.tipo === "consolidado" ? "Visão consolidada da equipe" : "Sua carteira comercial"} · {briefing.total_sinais} sinais analisados</p>
      </section>

      <section className={`grid gap-3 ${compacto ? "grid-cols-2" : "grid-cols-2 lg:grid-cols-5"}`} aria-label="Indicadores principais">
        {briefing.indicadores.map((indicador) => (
          <LinkSeguro key={indicador.codigo} href={rotaDoCanal(indicador, canal)} className="rounded-2xl border border-[#163356] bg-[#081a32] p-4 transition hover:border-cyan-700">
            <span className="block text-xs uppercase tracking-wider text-slate-400">{indicador.rotulo}</span>
            <strong className={`mt-2 block font-bold [overflow-wrap:anywhere] ${canal === "app" ? "text-xl" : "text-2xl"} ${ESTILO_TOM[indicador.tom]}`}>{formatar(indicador)}</strong>
            <span className="mt-1 block text-xs leading-5 text-slate-500">{indicador.detalhe}</span>
          </LinkSeguro>
        ))}
      </section>

      <div className={`grid gap-5 ${compacto ? "" : "xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]"}`}>
        <section className="rounded-3xl border border-[#163356] bg-[#061126] p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-white"><ListChecks size={20} className="text-cyan-400"/> Prioridades agora</h3>
            <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filtrar prioridades">
              {(["todas", "acao", "risco", "oportunidade"] as Filtro[]).map((chave) => (
                <button key={chave} type="button" role="tab" aria-selected={filtro === chave} onClick={() => setFiltro(chave)} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${filtro === chave ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`}>
                  {chave === "todas" ? "Todas" : ROTULO_CATEGORIA[chave]} · {contagem[chave]}
                </button>
              ))}
            </div>
          </div>
          {aviso && <p role="status" className="mt-3 rounded-xl border border-emerald-800 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-200">{aviso}</p>}
          {prioridades.length === 0 ? (
            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-dashed border-[#24466f] p-6 text-sm text-slate-400"><CheckCircle2 className="text-emerald-400"/> Nada pendente nesta categoria.</div>
          ) : (
            <ol className="mt-4 space-y-3" aria-label="Lista de prioridades">
              {prioridades.map((item, indice) => <CartaoPrioridade key={`${item.entidade_tipo}-${item.entidade_id}-${item.codigo}`} item={item} posicao={indice + 1} canal={canal} formatCurrency={formatCurrency} onResolvido={(mensagem) => resolver(item, mensagem)}/>)}
            </ol>
          )}
        </section>

        <aside className="space-y-5">
          <section className="rounded-3xl border border-[#163356] bg-[#061126] p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white"><AlertTriangle size={18} className="text-amber-300"/> Onde está o risco</h3>
            {briefing.riscos.length === 0 ? <p className="mt-3 text-sm text-slate-400">Nenhum risco identificado na carteira.</p> : (
              <ul className="mt-3 space-y-2">
                {briefing.riscos.map((risco) => (
                  <li key={risco.codigo} className="flex items-center justify-between gap-3 rounded-xl bg-[#0b1d38] px-3 py-2 text-sm">
                    <span className="text-slate-200">{risco.rotulo}</span>
                    <span className="shrink-0 text-right"><strong className="text-amber-200">{risco.quantidade}</strong>{risco.valor > 0 && <span className="block text-xs text-slate-500">{formatCurrency(risco.valor)}</span>}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-3xl border border-[#163356] bg-[#061126] p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white"><Gauge size={18} className="text-cyan-400"/> Funil aberto</h3>
            <p className="mt-1 text-xs text-slate-500">{briefing.pipeline.quantidade_aberta} negócios · {formatCurrency(briefing.pipeline.valor_aberto)} · ponderado {formatCurrency(briefing.pipeline.valor_ponderado)}</p>
            <ul className="mt-4 space-y-3">
              {briefing.pipeline.etapas.map((etapa) => (
                <li key={etapa.etapa}>
                  <div className="flex justify-between text-xs text-slate-300"><span>{etapa.rotulo} · {etapa.quantidade}</span><span>{formatCurrency(etapa.valor)}</span></div>
                  <div className="mt-1 h-2 rounded-full bg-[#0b1d38]"><div className="h-2 rounded-full bg-cyan-500" style={{ width: `${Math.max(3, Math.round((etapa.valor / maiorEtapa) * 100))}%` }}/></div>
                </li>
              ))}
              {briefing.pipeline.etapas.length === 0 && <li className="text-sm text-slate-400">Sem negócios abertos.</li>}
            </ul>
          </section>

          <section className="rounded-3xl border border-[#163356] bg-[#061126] p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white"><ShieldCheck size={18} className="text-emerald-300"/> Confiabilidade dos dados</h3>
            <div className="mt-3 flex items-end gap-2"><strong className={`text-3xl ${briefing.qualidade.indice >= 85 ? "text-emerald-300" : briefing.qualidade.indice >= 60 ? "text-amber-300" : "text-red-300"}`}>{briefing.qualidade.indice}</strong><span className="pb-1 text-xs text-slate-500">de 100 · {briefing.qualidade.negocios_avaliados} negócios avaliados</span></div>
            {briefing.qualidade.problemas.length > 0 && (
              <ul className="mt-3 space-y-3 text-sm">
                {briefing.qualidade.problemas.map((problema) => (
                  <li key={problema.codigo} className="rounded-xl bg-[#0b1d38] p-3">
                    <p className="flex justify-between gap-2 text-slate-200"><span>{problema.rotulo}</span><strong>{problema.quantidade}</strong></p>
                    <p className="mt-1 text-xs text-slate-500">{problema.impacto}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">{problema.exemplos.map((exemplo) => <LinkSeguro key={exemplo.oportunidade_id} href={rotaDoCanal(exemplo, canal)} className="rounded-md border border-[#24466f] px-2 py-0.5 text-[11px] text-cyan-200">{exemplo.cliente_nome}</LinkSeguro>)}</div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>

      <details className="rounded-2xl border border-[#13203f] bg-[#050f22] p-4 text-xs text-slate-400">
        <summary className="cursor-pointer font-semibold text-slate-300">Como o agente chegou a esta leitura</summary>
        <p className="mt-2">Fontes: {briefing.fontes.join(" · ")}. As prioridades combinam gravidade, valor em jogo e tempo parado; cada negócio aparece uma única vez, com seus demais sinais agrupados. O agente apenas lê — nenhum registro é alterado.</p>
        {briefing.limitacoes.length > 0 && <ul className="mt-2 list-disc pl-5 text-amber-200/80">{briefing.limitacoes.map((limitacao) => <li key={limitacao}>{limitacao}</li>)}</ul>}
        <p className="mt-2 text-slate-600">Gerado em {new Date(briefing.gerado_em).toLocaleString("pt-BR")} · versão {briefing.versao}</p>
      </details>
    </div>
  )
}

function CartaoPrioridade({ item, posicao, canal, formatCurrency, onResolvido }: { item: PrioridadeComercial; posicao: number; canal: CanalBriefing; formatCurrency: (valor: number) => string; onResolvido: (mensagem: string) => void }) {
  const Icone = item.categoria === "oportunidade" ? Flame : item.categoria === "risco" ? AlertTriangle : Clock3
  return (
    <li className="rounded-2xl border border-[#163356] bg-[#081a32] p-4">
      <div className="flex items-start gap-3">
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-[#0b2342] text-sm font-bold text-cyan-200">{posicao}</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${ESTILO_CATEGORIA[item.categoria]}`}><Icone size={12}/>{ROTULO_CATEGORIA[item.categoria]}</span>
            {item.severidade === "alta" || item.severidade === "critica" ? <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">Alta prioridade</span> : null}
            {item.valor > 0 && <span className="text-xs text-emerald-300">{formatCurrency(item.valor)}</span>}
          </div>
          <p className="mt-2 font-semibold leading-6 text-white">{item.titulo}</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">{item.explicacao}</p>
          <p className="mt-2 rounded-xl bg-[#0b1d38] px-3 py-2 text-sm leading-6 text-cyan-100"><strong className="text-cyan-300">Próximo passo:</strong> {item.acao_recomendada}</p>
          {item.sinais_relacionados.length > 0 && <p className="mt-2 text-xs text-slate-500">+{item.sinais_relacionados.length} outro{item.sinais_relacionados.length > 1 ? "s" : ""} sinal{item.sinais_relacionados.length > 1 ? "is" : ""} neste negócio</p>}
          <AcoesPrioridade item={item} onResolvido={onResolvido}/>
        </div>
        <LinkSeguro href={rotaDoCanal(item, canal)} aria-label={`Abrir ${item.cliente_nome || item.titulo}`} className="grid size-10 shrink-0 place-items-center rounded-xl border border-cyan-800 text-cyan-300 hover:bg-cyan-950/40"><ArrowRight size={18}/></LinkSeguro>
      </div>
    </li>
  )
}
