"use client"

import { useEffect, useRef, useState } from "react"
import { getMapaAlvoInteligencia, type MapaAlvoInteligencia } from "@/services/mapa-equipe-api"

type FontesDirecionamento = {
  anfir?: { ocorrencias?: number; unidades?: number }
  historico?: { registros?: number; unidades?: number }
  crm?: { registros?: number; ativos?: number; pipeline?: number }
}

type CicloComercial = {
  estado?: "NOVO_SINAL" | "ESTAGNADO" | "ACAO_NECESSARIA" | "EM_ACOMPANHAMENTO" | "CONVERTIDO" | string
  rotulo?: string
  oportunidades?: number
  oportunidades_ativas?: number
  ganhos?: number
  atividades?: number
  atividades_pendentes?: number
  ultima_movimentacao?: string | null
  proxima_atividade?: string | null
  dias_sem_movimento?: number | null
  leitura?: string
  acao?: string
}

type AlvoDirecionamento = {
  responsavel: string
  cliente: string
  unidades: number
  ocorrencias: number
  linha_principal: string
  fontes?: FontesDirecionamento
  cobertura?: "CRM_ATIVO" | "CRM_SEM_ATIVO" | "SEM_CRM" | string
  concorrencia?: string | null
  leitura_decisao?: string
  acao_decisao?: string
  leitura_ciclo?: string
  acao_ciclo?: string
  ciclo_comercial?: CicloComercial
  temporalidade?: {
    ultimo_anfir?: string | null
    ultimo_historico?: string | null
    ultimo_crm?: string | null
  }
}

type Direcionamento = {
  alvos: AlvoDirecionamento[]
  texto: string
  regra_evidencia?: string
  regra_ranking?: string
}

function limparAcao(acao: string, direcionamento?: Direcionamento) {
  const textoDirecionamento = direcionamento?.texto?.trim()
  if (!textoDirecionamento) return acao.trim()
  return acao.replace(textoDirecionamento, "").replace(/\s+/g, " ").trim()
}

function rotuloPrioridade(direcionamento?: Direcionamento) {
  const texto = direcionamento?.texto || ""
  const prefixo = texto.split(":")[0]?.trim()
  if (prefixo === "Prioridade sem CRM ativo") return "Sem CRM ativo"
  if (prefixo === "Prioridade comercial fora da captura Carrier") return "Fora da captura Carrier"
  if (prefixo === "Prioridade de proteção Carrier") return "Proteção Carrier"
  if (prefixo === "Prioridade de acompanhamento") return "Acompanhamento"
  if (prefixo === "Quem deve agir / para quem") return "Recuperação prioritária"
  return prefixo || "Prioridade comercial"
}

function rotuloCobertura(alvo?: AlvoDirecionamento) {
  if (alvo?.cobertura === "CRM_ATIVO") return "CRM ativo"
  if (alvo?.cobertura === "CRM_SEM_ATIVO") return "CRM sem ativo"
  if (alvo?.cobertura === "SEM_CRM") return "Sem CRM"
  return null
}

function classeCiclo(estado?: string) {
  if (estado === "CONVERTIDO") return "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
  if (estado === "EM_ACOMPANHAMENTO") return "border-cyan-400/30 bg-cyan-400/10 text-cyan-200"
  if (estado === "ESTAGNADO") return "border-rose-400/30 bg-rose-400/10 text-rose-200"
  if (estado === "ACAO_NECESSARIA") return "border-orange-400/30 bg-orange-400/10 text-orange-200"
  return "border-amber-400/30 bg-amber-400/10 text-amber-200"
}

export default function SinalDecisaoInterativo({
  leitura,
  acao,
  direcionamento,
  origem = "auto",
  responsavelId,
  destaque = "cyan",
}: {
  leitura: string
  acao: string
  direcionamento?: Direcionamento
  origem?: string
  responsavelId?: string | null
  destaque?: "cyan" | "amber"
}) {
  const alvos = direcionamento?.alvos || []
  const [indiceSelecionado, setIndiceSelecionado] = useState(0)
  const [aberto, setAberto] = useState(false)
  const [leiturasIA, setLeiturasIA] = useState<Record<string, MapaAlvoInteligencia>>({})
  const [erroChave, setErroChave] = useState<string | null>(null)
  const requisicoesEmCurso = useRef<Set<string>>(new Set())
  const indiceSeguro = Math.min(indiceSelecionado, Math.max(0, alvos.length - 1))
  const alvo = alvos[indiceSeguro]
  const chaveAlvo = alvo ? `${origem}::${alvo.responsavel}::${alvo.cliente}` : ""

  useEffect(() => {
    if (!aberto || !alvo || !chaveAlvo || leiturasIA[chaveAlvo] || erroChave === chaveAlvo || requisicoesEmCurso.current.has(chaveAlvo)) return
    let ativo = true
    requisicoesEmCurso.current.add(chaveAlvo)
    void getMapaAlvoInteligencia(origem, alvo.cliente, alvo.responsavel, responsavelId)
      .then((resultado) => {
        if (!ativo) return
        setLeiturasIA((atual) => ({ ...atual, [chaveAlvo]: resultado }))
      })
      .catch(() => {
        if (ativo) setErroChave(chaveAlvo)
      })
      .finally(() => {
        requisicoesEmCurso.current.delete(chaveAlvo)
      })
    return () => { ativo = false }
  }, [aberto, alvo, chaveAlvo, leiturasIA, erroChave, origem, responsavelId])

  if (!alvo) return null

  const ciclo = alvo.ciclo_comercial
  const inteligencia = leiturasIA[chaveAlvo]
  const leituraFactual = alvo.leitura_decisao || (indiceSeguro === 0 ? leitura : "Sem interpretação factual específica disponível para este alvo.")
  const acaoFactual = alvo.acao_decisao || (indiceSeguro === 0 ? limparAcao(acao, direcionamento) || acao : "Sem ação factual específica disponível para este alvo.")
  const leituraSelecionada = inteligencia?.interpretacao || leituraFactual
  const acaoSelecionada = inteligencia?.acao || acaoFactual
  const cobertura = rotuloCobertura(alvo)
  const historico = Number(alvo.fontes?.historico?.registros || 0)
  const crmAtivos = Number(alvo.fontes?.crm?.ativos || 0)
  const ultimoAnfir = alvo.temporalidade?.ultimo_anfir
  const borda = destaque === "amber" ? "border-amber-500/30 bg-amber-500/[.04]" : "border-cyan-500/20 bg-cyan-500/[.04]"

  return (
    <div className="mt-5 border-t border-slate-700/50 pt-4">
      <div className={`flex flex-col gap-3 rounded-2xl border p-3 sm:flex-row sm:items-center sm:justify-between ${borda}`}>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[.12em] text-amber-200">{rotuloPrioridade(direcionamento)}</span>
            {ciclo?.rotulo && <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[.12em] ${classeCiclo(ciclo.estado)}`}>{ciclo.rotulo}</span>}
            {cobertura && <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[.1em] ${crmAtivos > 0 ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200" : "border-rose-400/30 bg-rose-400/10 text-rose-200"}`}>{cobertura}</span>}
            {historico > 0 && <span className="rounded-full border border-violet-400/30 bg-violet-400/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[.1em] text-violet-200">Histórico {historico}</span>}
            {alvo.concorrencia && <span className="rounded-full border border-slate-500/40 bg-slate-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[.1em] text-slate-300">{alvo.concorrencia}</span>}
          </div>
          <p className="mt-2 break-words text-base font-semibold text-white">{alvo.cliente}</p>
          <p className="mt-1 text-xs text-slate-400">{alvo.responsavel} · {alvo.linha_principal}{ultimoAnfir ? ` · ANFIR ${ultimoAnfir}` : ""}</p>
          {ciclo && <p className="mt-1 text-[10px] text-slate-500">{ciclo.proxima_atividade ? `Próxima ação ${ciclo.proxima_atividade}` : ciclo.ultima_movimentacao ? `Última movimentação ${ciclo.ultima_movimentacao}` : "Sem movimentação CRM registrada"}</p>}
        </div>
        <div className="grid grid-cols-2 gap-2 text-center sm:flex sm:shrink-0">
          <div className="min-w-[68px] rounded-xl border border-[#17304d] bg-[#08152a] px-3 py-2"><strong className={destaque === "amber" ? "block text-base text-amber-300" : "block text-base text-cyan-300"}>{alvo.unidades}</strong><span className="text-[9px] uppercase tracking-[.1em] text-slate-500">unidades</span></div>
          <div className="min-w-[68px] rounded-xl border border-[#17304d] bg-[#08152a] px-3 py-2"><strong className="block text-base text-white">{alvo.ocorrencias}</strong><span className="text-[9px] uppercase tracking-[.1em] text-slate-500">ocorrências</span></div>
        </div>
      </div>

      <details className="group mt-2" onToggle={(evento) => setAberto(evento.currentTarget.open)}>
        <summary className={`cursor-pointer list-none py-2 text-xs font-semibold ${destaque === "amber" ? "text-amber-300" : "text-cyan-300"}`}><span className="group-open:hidden">Ver decisão e evidências ↓</span><span className="hidden group-open:inline">Recolher decisão ↑</span></summary>
        <div className="space-y-4 rounded-2xl border border-[#17304d] bg-[#071226] p-3 sm:p-4">
          {inteligencia && <div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-2 py-1 text-[9px] font-semibold uppercase tracking-[.12em] text-cyan-200">IA Comercial CTI · leitura contextual</span></div>}
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="min-w-0"><p className={`text-[10px] font-semibold uppercase tracking-[.14em] ${destaque === "amber" ? "text-amber-300" : "text-cyan-300"}`}>Interpretação</p><p className="mt-2 break-words text-sm leading-6 text-slate-300">{leituraSelecionada}</p></div>
            <div className="min-w-0"><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-emerald-300">Ação</p><p className="mt-2 break-words text-sm leading-6 text-slate-300">{acaoSelecionada}</p></div>
          </div>
          <div className="border-t border-slate-700/50 pt-4">
            <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-violet-300">Evidência cruzada</p>
            <div className="mt-2 grid grid-cols-3 gap-2 text-center">
              <div className="min-w-0 rounded-xl border border-cyan-500/20 px-2 py-2"><strong className="block text-sm text-cyan-200">{alvo.fontes?.anfir?.unidades ?? alvo.unidades}</strong><span className="block truncate text-[8px] uppercase text-slate-500 sm:text-[9px]">ANFIR</span></div>
              <div className="min-w-0 rounded-xl border border-violet-500/20 px-2 py-2"><strong className="block text-sm text-violet-200">{alvo.fontes?.historico?.registros ?? 0}</strong><span className="block truncate text-[8px] uppercase text-slate-500 sm:text-[9px]">HIST/FUNIL</span></div>
              <div className="min-w-0 rounded-xl border border-emerald-500/20 px-2 py-2"><strong className="block text-sm text-emerald-200">{alvo.fontes?.crm?.ativos ?? ciclo?.oportunidades_ativas ?? 0}</strong><span className="block truncate text-[8px] uppercase text-slate-500 sm:text-[9px]">CRM ativo</span></div>
            </div>
          </div>
          {alvos.length > 1 && <div className="border-t border-slate-700/50 pt-4">
            <div className="mb-2 flex items-center justify-between gap-3"><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-slate-400">Outros alvos priorizados</p><span className="text-[10px] text-slate-600">toque para analisar</span></div>
            <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
              {alvos.map((item, index) => {
                const selecionado = index === indiceSeguro
                return <button key={`${item.responsavel}-${item.cliente}-${index}`} type="button" onClick={() => setIndiceSelecionado(index)} aria-pressed={selecionado} className={`min-w-0 rounded-xl border px-3 py-3 text-left transition ${selecionado ? "border-cyan-400/60 bg-cyan-500/10" : "border-slate-700/50 bg-[#08152a] hover:border-cyan-500/30"}`}>
                  <div className="flex flex-wrap items-center gap-2"><p className={`break-words text-xs font-semibold ${selecionado ? "text-cyan-200" : "text-slate-200"}`}>{item.cliente}</p>{item.ciclo_comercial?.rotulo && <span className={`rounded-full border px-1.5 py-0.5 text-[8px] font-semibold uppercase ${classeCiclo(item.ciclo_comercial.estado)}`}>{item.ciclo_comercial.rotulo}</span>}</div>
                  <p className="mt-1 break-words text-[10px] leading-4 text-slate-500">{item.responsavel} · {item.unidades} un. · {item.ocorrencias} ocorr. · {item.linha_principal}{item.fontes?.crm?.ativos ? ` · CRM ${item.fontes.crm.ativos}` : " · sem CRM ativo"}</p>
                </button>
              })}
            </div>
          </div>}
        </div>
      </details>
    </div>
  )
}
