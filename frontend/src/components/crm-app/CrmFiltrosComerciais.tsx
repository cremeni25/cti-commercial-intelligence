"use client"

import { CalendarRange, FileDown, FilterX, UserRound, Wrench } from "lucide-react"
import type { CrmFiltrosComerciais } from "@/lib/crm-analise-comercial"

type ResponsavelOpcao = { id: string; nome: string }

type Props = {
  filtros: CrmFiltrosComerciais
  onChange: (filtros: CrmFiltrosComerciais) => void
  master: boolean
  responsaveis: ResponsavelOpcao[]
  linhas: string[]
  totalFiltrado: number
  onPdf?: () => void
}

export default function CrmFiltrosComerciais({
  filtros,
  onChange,
  master,
  responsaveis,
  linhas,
  totalFiltrado,
  onPdf,
}: Props) {
  function atualizar<K extends keyof CrmFiltrosComerciais>(campo: K, valor: CrmFiltrosComerciais[K]) {
    onChange({ ...filtros, [campo]: valor })
  }

  function limpar() {
    onChange({ responsavelId: "TODOS", linha: "TODAS", campoData: "INCLUSAO", inicio: "", fim: "" })
  }

  return (
    <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 shadow-[0_18px_55px_rgba(0,0,0,.18)] sm:p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[.2em] text-cyan-400">Análise comercial</p>
          <h2 className="mt-1 text-base font-semibold text-white">Seleção temporal e de carteira</h2>
          <p className="mt-1 text-xs text-slate-400">{totalFiltrado} registro(s) na seleção atual</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={limpar} className="inline-flex items-center gap-2 rounded-xl border border-[#24466f] px-3 py-2 text-xs font-semibold text-slate-300">
            <FilterX size={15}/> Limpar filtros
          </button>
          {onPdf && <button type="button" onClick={onPdf} className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950">
            <FileDown size={15}/> Relatório / PDF
          </button>}
        </div>
      </div>

      <div className={`grid gap-3 ${master ? "md:grid-cols-2 xl:grid-cols-5" : "md:grid-cols-2 xl:grid-cols-4"}`}>
        {master && <label className="space-y-1.5 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5"><UserRound size={14}/> Responsável</span>
          <select value={filtros.responsavelId} onChange={(e)=>atualizar("responsavelId",e.target.value)} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white">
            <option value="TODOS">Todos os responsáveis</option>
            {responsaveis.map((item)=><option key={item.id} value={item.id}>{item.nome}</option>)}
          </select>
        </label>}

        <label className="space-y-1.5 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5"><Wrench size={14}/> Linha de equipamento</span>
          <select value={filtros.linha} onChange={(e)=>atualizar("linha",e.target.value)} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white">
            <option value="TODAS">Todas as linhas</option>
            {linhas.map((linha)=><option key={linha} value={linha}>{linha}</option>)}
          </select>
        </label>

        <label className="space-y-1.5 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5"><CalendarRange size={14}/> Data considerada</span>
          <select value={filtros.campoData} onChange={(e)=>atualizar("campoData",e.target.value as CrmFiltrosComerciais["campoData"])} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white">
            <option value="INCLUSAO">Data de inclusão</option>
            <option value="PREVISAO">Data prevista de conclusão</option>
          </select>
        </label>

        <label className="space-y-1.5 text-xs text-slate-400">
          <span>De</span>
          <input type="date" value={filtros.inicio} onChange={(e)=>atualizar("inicio",e.target.value)} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white"/>
        </label>

        <label className="space-y-1.5 text-xs text-slate-400">
          <span>Até</span>
          <input type="date" value={filtros.fim} onChange={(e)=>atualizar("fim",e.target.value)} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white"/>
        </label>
      </div>
    </section>
  )
}
