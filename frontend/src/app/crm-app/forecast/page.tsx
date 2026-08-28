"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CalendarRange, ChevronRight, Loader2, Target, TrendingUp } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"

type Registro=Record<string,unknown>
type Linha={oportunidade_id:string;responsavel_id?:string|null;cliente_nome:string;titulo:string;competencia:string;etapa:string;valor:number;valor_ponderado:number;probabilidade:number;encerrada:boolean}
function lista(payload:unknown):Registro[]{if(Array.isArray(payload))return payload as Registro[];if(payload&&typeof payload==="object"){const o=payload as Registro;for(const k of["dados","itens","oportunidades","resultado"])if(Array.isArray(o[k]))return o[k] as Registro[]}return[]}
function texto(v:unknown){return String(v||"").trim()}
function moeda(v:number){return Number(v||0).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}
function mesAtual(){return new Date().toISOString().slice(0,7)}

export default function CrmAppForecastPage(){
 const { usuario } = useAuth()
 const[dados,setDados]=useState<Linha[]>([]),[competencia,setCompetencia]=useState(mesAtual()),[carregando,setCarregando]=useState(true),[erro,setErro]=useState("")
 useEffect(()=>{fetch("/api/crm-proxy/crm/nucleo-comercial",{cache:"no-store"}).then(async r=>{const p=await r.json().catch(()=>({}));if(!r.ok)throw new Error(String((p as Registro).detail||`Falha ${r.status}`));setDados(lista(p).map(i=>({oportunidade_id:texto(i.oportunidade_id||i.id),responsavel_id:texto(i.responsavel_id)||null,cliente_nome:texto(i.cliente_nome||i.cliente)||"Cliente em identificação",titulo:texto(i.titulo||i.equipamento)||"Negociação comercial",competencia:texto(i.competencia||i.data_fechamento_prevista).slice(0,7),etapa:texto(i.etapa||i.status).toUpperCase(),valor:Number(i.valor||i.valor_estimado||0),valor_ponderado:Number(i.valor_ponderado||0),probabilidade:Number(i.probabilidade||0),encerrada:Boolean(i.encerrada)})).filter(i=>i.oportunidade_id))}).catch(e=>setErro(e instanceof Error?e.message:"Não foi possível carregar o Forecast.")).finally(()=>setCarregando(false))},[])
 const abertas=useMemo(()=>dados.filter(i=>!i.encerrada&&pertenceAoEscopoDoUsuario(i.responsavel_id,usuario)),[dados,usuario])
 const competencias=useMemo(()=>Array.from(new Set(abertas.map(i=>i.competencia).filter(Boolean))).sort(),[abertas])
 const filtradas=useMemo(()=>abertas.filter(i=>!competencia||i.competencia===competencia),[abertas,competencia])
 const total=filtradas.reduce((s,i)=>s+i.valor,0),ponderado=filtradas.reduce((s,i)=>s+(i.valor_ponderado||i.valor*(i.probabilidade>1?i.probabilidade/100:i.probabilidade)),0)
 return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
  <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Forecast comercial</h1><p className="text-sm text-slate-400">Projeção de fechamento dos mesmos negócios do Pipeline</p></div></header>
  <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-center gap-3"><CalendarRange className="text-cyan-300" size={20}/><label className="flex-1 text-sm text-slate-300">Competência<select value={competencia} onChange={e=>setCompetencia(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-white"><option value="">Todas</option>{competencias.map(c=><option key={c} value={c}>{c}</option>)}</select></label></div></section>
  <section className="mb-4 grid gap-3 sm:grid-cols-3"><Kpi label="Negócios projetados" valor={String(filtradas.length)} icon={<Target size={18}/>}/><Kpi label="Pipeline" valor={moeda(total)} icon={<TrendingUp size={18}/>}/><Kpi label="Forecast ponderado" valor={moeda(ponderado)} icon={<TrendingUp size={18}/>}/></section>
  {erro&&<div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
  {carregando?<div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:filtradas.length===0?<div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhuma oportunidade aberta nesta competência.</div>:<div className="space-y-3">{filtradas.map(i=><Link key={i.oportunidade_id} href={`/crm-app/oportunidades/${i.oportunidade_id}/editar?origem=forecast`} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="min-w-0 flex-1"><p className="font-semibold text-cyan-200">{i.cliente_nome}</p><p className="mt-1 font-medium">{i.titulo}</p><div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400"><span>{i.etapa}</span><span>{moeda(i.valor)}</span><span>{Math.round((i.probabilidade>1?i.probabilidade:i.probabilidade*100))}%</span><span className="text-emerald-300">Forecast {moeda(i.valor_ponderado||i.valor*(i.probabilidade>1?i.probabilidade/100:i.probabilidade))}</span></div></div><ChevronRight size={18} className="text-slate-600"/></Link>)}</div>}
 </div></main>
}
function Kpi({label,valor,icon}:{label:string;valor:string;icon:React.ReactNode}){return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="flex items-center gap-2 text-cyan-300">{icon}<p className="text-xs text-slate-400">{label}</p></div><strong className="mt-2 block text-lg text-cyan-300">{valor}</strong></div>}
