"use client"

import Link from "next/link"
import { useState } from "react"
import { useAuth } from "@/core/auth/AuthContext"
import { getSupabaseClient } from "@/core/database/supabase"

const STATUS_ENCERRADOS = new Set(["GANHO","PERDIDO","CANCELADO","CANCELADA","ENCERRADO","ENCERRADA"])

const MOTIVOS = [
  ["VENDA_CONCLUIDA","Venda concluída"],
  ["PERDA_CONCORRENCIA","Perda para concorrência"],
  ["COMPRA_INDIRETA","Compra indireta"],
  ["DESISTENCIA_CLIENTE","Desistência do cliente"],
  ["SEM_CONTINUIDADE","Sem continuidade"],
  ["SOLUCAO_GARANTIA_FABRICANTE","Solução por garantia/troca do fabricante"],
  ["PROJETO_ADIADO","Projeto adiado"],
  ["PRECO_CONDICAO_COMERCIAL","Preço/condição comercial"],
  ["PRODUTO_INADEQUADO_INDISPONIVEL","Produto inadequado/indisponível"],
  ["OUTRO","Outro"],
] as const

type Props = {
  oportunidadeId: string
  status?: string
  motivoAtual?: string
  historicoHref: string
  onEncerrada?: (registro: Record<string, unknown>) => void
}

export default function EncerramentoNegociacao({ oportunidadeId, status, motivoAtual, historicoHref, onEncerrada }: Props) {
  const { usuario } = useAuth()
  const [aberto,setAberto]=useState(false)
  const [motivo,setMotivo]=useState("")
  const [observacao,setObservacao]=useState("")
  const [salvando,setSalvando]=useState(false)
  const [erro,setErro]=useState("")
  const [sucesso,setSucesso]=useState("")
  const encerrada=STATUS_ENCERRADOS.has(String(status||"").toUpperCase()) && Boolean(motivoAtual)

  async function encerrar(){
    if(!usuario?.id){setErro("Sessão do usuário não identificada.");return}
    if(!motivo){setErro("Selecione o motivo do encerramento.");return}
    if(observacao.trim().length<5){setErro("Descreva o motivo do encerramento com pelo menos 5 caracteres.");return}
    setSalvando(true);setErro("");setSucesso("")
    try{
      const supabase=getSupabaseClient()
      const {data,error}=await supabase.rpc("cti_encerrar_negociacao",{
        p_oportunidade_id:oportunidadeId,
        p_usuario_id:String(usuario.id),
        p_motivo:motivo,
        p_observacao:observacao.trim(),
      })
      if(error)throw error
      setSucesso("Negociação encerrada. O histórico foi preservado e retirado da carteira aberta.")
      setAberto(false)
      onEncerrada?.((data||{}) as Record<string,unknown>)
    }catch(e){setErro(e instanceof Error?e.message:"Não foi possível encerrar a negociação.")}
    finally{setSalvando(false)}
  }

  if(encerrada||sucesso){
    return <section className="rounded-3xl border border-emerald-800 bg-emerald-950/20 p-5">
      <p className="text-xs font-bold uppercase tracking-[.18em] text-emerald-300">Ciclo comercial encerrado</p>
      <p className="mt-2 text-sm leading-6 text-slate-300">{sucesso||"Esta negociação está encerrada e permanece disponível para análise histórica."}</p>
      <Link href={historicoHref} className="mt-4 inline-flex rounded-xl border border-emerald-700 px-4 py-3 text-sm font-semibold text-emerald-200">Ver histórico de encerrados</Link>
    </section>
  }

  return <section className="rounded-3xl border border-[#24466f] bg-[#07162b] p-5">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">Encerramento comercial</p><h2 className="mt-1 text-lg font-bold">O negócio não terá continuidade?</h2><p className="mt-1 text-sm text-slate-400">Encerre sem apagar propostas, atividades, documentos ou linha do tempo.</p></div>
      <button type="button" onClick={()=>setAberto(v=>!v)} className="rounded-xl border border-amber-700 px-4 py-3 text-sm font-semibold text-amber-200">Encerrar negociação</button>
    </div>
    {aberto&&<div className="mt-5 space-y-4 border-t border-[#16325c] pt-5">
      <label className="block"><span className="mb-2 block text-sm font-medium">Motivo *</span><select value={motivo} onChange={e=>setMotivo(e.target.value)} className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3"><option value="">Selecione</option>{MOTIVOS.map(([valor,label])=><option key={valor} value={valor}>{label}</option>)}</select></label>
      <label className="block"><span className="mb-2 block text-sm font-medium">Observação obrigatória *</span><textarea value={observacao} onChange={e=>setObservacao(e.target.value)} rows={4} placeholder="Registre objetivamente o que encerrou esta negociação." className="w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label>
      {erro&&<div className="rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
      <div className="grid gap-2 sm:grid-cols-2"><button type="button" onClick={()=>setAberto(false)} disabled={salvando} className="rounded-xl border border-[#24466f] px-4 py-3">Cancelar</button><button type="button" onClick={()=>void encerrar()} disabled={salvando} className="rounded-xl bg-amber-400 px-4 py-3 font-bold text-slate-950 disabled:opacity-50">{salvando?"Encerrando...":"Confirmar encerramento"}</button></div>
    </div>}
  </section>
}
