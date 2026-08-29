"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CalendarRange, ChevronRight, Loader2, Target, TrendingUp } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { useOperationalI18n } from "@/core/i18n/operational"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"

type Registro=Record<string,unknown>
type Linha={oportunidade_id:string;responsavel_id?:string|null;cliente_nome:string;titulo:string;competencia:string;etapa:string;valor:number;valor_ponderado:number;probabilidade:number;encerrada:boolean}
type Locale="pt-BR"|"en"|"es"

const textos={
 "pt-BR":{title:"Forecast comercial",subtitle:"Projeção de fechamento dos mesmos negócios do Pipeline",period:"Competência",all:"Todas",projected:"Negócios projetados",pipeline:"Pipeline",weighted:"Forecast ponderado",empty:"Nenhuma oportunidade aberta nesta competência.",load:"Não foi possível carregar o Forecast.",accountIdentifying:"Cliente em identificação",deal:"Negociação comercial",forecast:"Forecast"},
 en:{title:"Sales forecast",subtitle:"Expected close projection for the same deals shown in Pipeline",period:"Forecast period",all:"All",projected:"Projected deals",pipeline:"Pipeline",weighted:"Weighted forecast",empty:"No open opportunities in this forecast period.",load:"We couldn't load the sales forecast.",accountIdentifying:"Account being identified",deal:"Sales opportunity",forecast:"Forecast"},
 es:{title:"Forecast comercial",subtitle:"Proyección de cierre de los mismos negocios del Pipeline",period:"Período previsto",all:"Todas",projected:"Negocios proyectados",pipeline:"Pipeline",weighted:"Forecast ponderado",empty:"No hay oportunidades abiertas en este período previsto.",load:"No fue posible cargar el forecast comercial.",accountIdentifying:"Cliente en identificación",deal:"Negocio comercial",forecast:"Forecast"},
} satisfies Record<Locale,Record<string,string>>

function lista(payload:unknown):Registro[]{if(Array.isArray(payload))return payload as Registro[];if(payload&&typeof payload==="object"){const o=payload as Registro;for(const k of["dados","itens","oportunidades","resultado"])if(Array.isArray(o[k]))return o[k] as Registro[]}return[]}
function texto(v:unknown){return String(v||"").trim()}
function mesAtual(){return new Date().toISOString().slice(0,7)}
function etapaLegivel(valor:string,locale:Locale){const mapas:Record<Locale,Record<string,string>>={"pt-BR":{QUALIFICACAO:"Qualificação",PROPOSTA:"Proposta",NEGOCIACAO:"Negociação",FECHAMENTO:"Fechamento",GANHO:"Ganho",PERDIDO:"Perdido"},en:{QUALIFICACAO:"Qualification",PROPOSTA:"Proposal",NEGOCIACAO:"Negotiation",FECHAMENTO:"Closing",GANHO:"Won",PERDIDO:"Lost"},es:{QUALIFICACAO:"Calificación",PROPOSTA:"Propuesta",NEGOCIACAO:"Negociación",FECHAMENTO:"Cierre",GANHO:"Ganado",PERDIDO:"Perdido"}};return mapas[locale][valor]||valor.replaceAll("_"," ")}

export default function CrmAppForecastPage(){
 const { usuario } = useAuth()
 const { locale, formatCurrency, formatNumber } = useOperationalI18n()
 const idioma=locale as Locale
 const t=textos[idioma]||textos["pt-BR"]
 const[dados,setDados]=useState<Linha[]>([]),[competencia,setCompetencia]=useState(mesAtual()),[carregando,setCarregando]=useState(true),[erro,setErro]=useState("")
 useEffect(()=>{fetch("/api/crm-proxy/crm/nucleo-comercial",{cache:"no-store"}).then(async r=>{const p=await r.json().catch(()=>({}));if(!r.ok)throw new Error(String((p as Registro).detail||`HTTP ${r.status}`));setDados(lista(p).map(i=>({oportunidade_id:texto(i.oportunidade_id||i.id),responsavel_id:texto(i.responsavel_id)||null,cliente_nome:texto(i.cliente_nome||i.cliente)||t.accountIdentifying,titulo:texto(i.titulo||i.equipamento)||t.deal,competencia:texto(i.competencia||i.data_fechamento_prevista).slice(0,7),etapa:texto(i.etapa||i.status).toUpperCase(),valor:Number(i.valor||i.valor_estimado||0),valor_ponderado:Number(i.valor_ponderado||0),probabilidade:Number(i.probabilidade||0),encerrada:Boolean(i.encerrada)})).filter(i=>i.oportunidade_id))}).catch(e=>setErro(e instanceof Error?e.message:t.load)).finally(()=>setCarregando(false))},[t.accountIdentifying,t.deal,t.load])
 const abertas=useMemo(()=>dados.filter(i=>!i.encerrada&&pertenceAoEscopoDoUsuario(i.responsavel_id,usuario)),[dados,usuario])
 const competencias=useMemo(()=>Array.from(new Set(abertas.map(i=>i.competencia).filter(Boolean))).sort(),[abertas])
 const filtradas=useMemo(()=>abertas.filter(i=>!competencia||i.competencia===competencia),[abertas,competencia])
 const total=filtradas.reduce((s,i)=>s+i.valor,0),ponderado=filtradas.reduce((s,i)=>s+(i.valor_ponderado||i.valor*(i.probabilidade>1?i.probabilidade/100:i.probabilidade)),0)
 return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
  <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">{t.title}</h1><p className="text-sm text-slate-400">{t.subtitle}</p></div></header>
  <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-center gap-3"><CalendarRange className="text-cyan-300" size={20}/><label className="flex-1 text-sm text-slate-300">{t.period}<select value={competencia} onChange={e=>setCompetencia(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 text-white"><option value="">{t.all}</option>{competencias.map(c=><option key={c} value={c}>{c}</option>)}</select></label></div></section>
  <section className="mb-4 grid gap-3 sm:grid-cols-3"><Kpi label={t.projected} valor={formatNumber(filtradas.length)} icon={<Target size={18}/>}/><Kpi label={t.pipeline} valor={formatCurrency(total)} icon={<TrendingUp size={18}/>}/><Kpi label={t.weighted} valor={formatCurrency(ponderado)} icon={<TrendingUp size={18}/>}/></section>
  {erro&&<div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
  {carregando?<div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:filtradas.length===0?<div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">{t.empty}</div>:<div className="space-y-3">{filtradas.map(i=><Link key={i.oportunidade_id} href={`/crm-app/oportunidades/${i.oportunidade_id}/editar?origem=forecast`} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4"><div className="min-w-0 flex-1"><p className="font-semibold text-cyan-200">{i.cliente_nome}</p><p className="mt-1 font-medium">{i.titulo}</p><div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400"><span>{etapaLegivel(i.etapa,idioma)}</span><span>{formatCurrency(i.valor)}</span><span>{formatNumber(Math.round(i.probabilidade>1?i.probabilidade:i.probabilidade*100))}%</span><span className="text-emerald-300">{t.forecast} {formatCurrency(i.valor_ponderado||i.valor*(i.probabilidade>1?i.probabilidade/100:i.probabilidade))}</span></div></div><ChevronRight size={18} className="text-slate-600"/></Link>)}</div>}
 </div></main>
}
function Kpi({label,valor,icon}:{label:string;valor:string;icon:React.ReactNode}){return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="flex items-center gap-2 text-cyan-300">{icon}<p className="text-xs text-slate-400">{label}</p></div><strong className="mt-2 block text-lg text-cyan-300">{valor}</strong></div>}
