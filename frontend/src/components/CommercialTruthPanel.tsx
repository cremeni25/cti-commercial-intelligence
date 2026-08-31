"use client"

import { useEffect, useState } from "react"
import { getSupabaseClient } from "@/core/database/supabase"

type Resumo={evidencias:number;clientes_reconciliados:number;evidencias_sem_cliente_reconciliado:number;por_fonte:Record<string,number>;por_desfecho:Record<string,number>;cadeias_crm_funil_realizado:number;cadeias_temporais_confirmadas:number;cadeias_confirmadas?:number}
type Jornada={cliente_id:string;cliente_nome:string;cidade?:string|null;ddd?:string|null;origens:string[];quantidade_evidencias:number;primeiro_evento?:string|null;ultimo_evento?:string|null;desfecho:string;cadeia_crm_funil_realizado:boolean;ordem_temporal_confirmada:boolean;cadeia_confirmada?:boolean;confianca_cadeia?:number}
type Payload={contrato:{principio:string;anfir:string;funil:string;crm:string};resumo:Resumo;jornadas:Jornada[]}

async function buscarSeguro(url:string):Promise<Payload>{
 const supabase=getSupabaseClient();const {data,error}=await supabase.auth.getSession();const token=data.session?.access_token
 if(error||!token)throw new Error("Sessão CTI não autenticada.")
 const resposta=await fetch(url,{cache:"no-store",headers:{Authorization:`Bearer ${token}`,Accept:"application/json"}})
 if(!resposta.ok){const payload=await resposta.json().catch(()=>null);throw new Error(payload?.detail||`Falha ${resposta.status}`)}
 return resposta.json()
}
function rotuloDesfecho(valor:string){return ({SUCESSO_COMERCIAL_CONFIRMADO:"Sucesso confirmado",RESULTADO_CONCORRENTE_CONFIRMADO:"Resultado concorrente",EM_CURSO_BACKLOG:"Em curso / backlog",PROSPECCAO_OU_ACAO_ATIVA:"Prospecção / ação ativa",SEM_DESFECHO_COMERCIAL:"Sem desfecho"} as Record<string,string>)[valor]||valor.replaceAll("_"," ")}

export default function CommercialTruthPanel({responsavelId}:{responsavelId?:string}){
 const[data,setData]=useState<Payload|null>(null),[erro,setErro]=useState(""),[loading,setLoading]=useState(true)
 useEffect(()=>{let ativo=true;const q=new URLSearchParams({limite_clientes:"20"});if(responsavelId)q.set("responsavel_id",responsavelId);void buscarSeguro(`/api/cti/analytics/verdade-comercial?${q.toString()}`).then(p=>{if(ativo){setData(p);setErro("")}}).catch(e=>{if(ativo)setErro(e instanceof Error?e.message:"Falha ao carregar reconciliação comercial.")}).finally(()=>{if(ativo)setLoading(false)});return()=>{ativo=false}},[responsavelId])
 if(loading)return <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-5 text-sm text-slate-400">Conferindo consistência transversal ANFIR × Funil × CRM...</section>
 if(!data)return <section className="rounded-2xl border border-amber-700/50 bg-amber-950/10 p-5 text-sm text-amber-200"><strong>Reconciliação transversal indisponível.</strong><span className="ml-2">{erro}</span></section>
 const r=data.resumo,top=data.jornadas.filter(j=>j.cadeia_crm_funil_realizado||j.desfecho!=="SEM_DESFECHO_COMERCIAL").slice(0,10)
 return <section className="rounded-3xl border border-emerald-500/25 bg-[#071427] p-5 sm:p-6">
  <div><p className="text-xs font-semibold uppercase tracking-[.18em] text-emerald-300">Consistência transversal</p><h2 className="mt-2 text-2xl font-bold">Jornada comercial reconciliada</h2><p className="mt-2 max-w-5xl text-sm leading-6 text-slate-400">ANFIR = realizado. CRM = operação comercial. Funil = ciclo das oportunidades. Entre eles existe correlação analítica, nunca fusão de registros.</p></div>
  <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-6"><Kpi label="Clientes reconciliados" value={r.clientes_reconciliados}/><Kpi label="CRM → Funil → realizado" value={r.cadeias_crm_funil_realizado}/><Kpi label="Ordem temporal confirmada" value={r.cadeias_temporais_confirmadas}/><Kpi label="Cadeias confirmadas" value={r.cadeias_confirmadas||0}/><Kpi label="Sucessos confirmados" value={r.por_desfecho.SUCESSO_COMERCIAL_CONFIRMADO||0}/><Kpi label="Em curso / backlog" value={r.por_desfecho.EM_CURSO_BACKLOG||0}/></div>
  <div className="mt-5 rounded-2xl border border-[#17304d] bg-[#061126] p-4"><p className="text-sm font-semibold">Regra oficial de leitura</p><p className="mt-3 text-xs leading-6 text-slate-300">ANFIR = realizado. CRM = operação comercial. Funil = ciclo das oportunidades. Entre eles existe correlação analítica, nunca fusão de registros.</p></div>
  {top.length>0&&<div className="mt-5 overflow-x-auto rounded-2xl border border-[#17304d]"><table className="min-w-full text-sm"><thead className="bg-[#0b1b34] text-left text-xs uppercase text-slate-400"><tr><th className="p-3">Cliente</th><th className="p-3">Fontes encontradas</th><th className="p-3">Desfecho</th><th className="p-3">Evidências</th><th className="p-3">Cadeia temporal</th><th className="p-3">Confirmação</th></tr></thead><tbody>{top.map(j=><tr key={j.cliente_id} className="border-t border-[#17304d]"><td className="p-3"><p className="font-semibold text-cyan-200">{j.cliente_nome}</p><p className="text-xs text-slate-500">{[j.cidade,j.ddd].filter(Boolean).join(" · ")}</p></td><td className="p-3">{j.origens.join(" → ")}</td><td className="p-3 font-semibold">{rotuloDesfecho(j.desfecho)}</td><td className="p-3">{j.quantidade_evidencias}</td><td className="p-3">{j.ordem_temporal_confirmada?"Confirmada":"Ainda não confirmada"}</td><td className="p-3">{j.cadeia_confirmada?`Confirmada · ${Math.round((j.confianca_cadeia||0)*100)}%`:"Não confirmada"}</td></tr>)}</tbody></table></div>}
  {r.evidencias_sem_cliente_reconciliado>0&&<p className="mt-4 text-xs text-slate-500">Existem {r.evidencias_sem_cliente_reconciliado} evidências ainda sem vínculo seguro a um cliente. Elas permanecem fora das cadeias comerciais até reconciliação confiável; não são fundidas por aproximação.</p>}
 </section>
}
function Kpi({label,value}:{label:string;value:number}){return <div className="rounded-2xl border border-[#17304d] bg-[#061126] p-4"><p className="text-[10px] uppercase tracking-[.12em] text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-emerald-300">{value}</p></div>}
