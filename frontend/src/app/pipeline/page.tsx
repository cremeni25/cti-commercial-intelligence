/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import JornadaComercialNav from "@/components/crm/JornadaComercialNav"
import { API_URL } from "@/lib/api"

type LinhaNucleo = { oportunidade_id:string; titulo:string; cliente_nome:string; etapa:string; valor:number; probabilidade:number; valor_ponderado:number; data_fechamento_prevista?:string|null; encerrada:boolean }
const ETAPAS_PIPELINE=["OPORTUNIDADE","ATIVIDADE","PROPOSTA","ACEITE","PEDIDO","DOSSIÊ","CARRIER","FATURADO","ENCERRADO"]
function moeda(valor:number){return Number(valor||0).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}
function percentual(valor:number){return `${Math.round(Number(valor||0)*100)}%`}
function inicioMesAtual(){const agora=new Date();return `${agora.getFullYear()}-${String(agora.getMonth()+1).padStart(2,"0")}-01`}
function fimMesAtual(){const agora=new Date();return new Date(agora.getFullYear(),agora.getMonth()+1,0).toISOString().slice(0,10)}
function dataIsoValida(valor?:string|null){return Boolean(valor&&/^\d{4}-\d{2}-\d{2}$/.test(valor)&&!Number.isNaN(new Date(`${valor}T12:00:00`).getTime()))}
function dataPrevista(valor?:string|null){return dataIsoValida(valor)?new Date(`${valor}T12:00:00`).toLocaleDateString("pt-BR"):"Sem previsão"}

export default function PipelinePage(){
 const[dados,setDados]=useState<LinhaNucleo[]>([]),[inicio,setInicio]=useState(inicioMesAtual),[fim,setFim]=useState(fimMesAtual),[loading,setLoading]=useState(true),[erro,setErro]=useState("")
 useEffect(()=>{let ativo=true;setLoading(true);setErro("");fetch(`${API_URL}/crm/nucleo-comercial`,{cache:"no-store"}).then(async r=>{const p=await r.json().catch(()=>[]);if(!r.ok)throw new Error(p?.detail||"Falha ao carregar núcleo comercial");return Array.isArray(p)?p:[]}).then(p=>{if(ativo)setDados(p)}).catch(e=>{if(ativo)setErro(e instanceof Error?e.message:"Não foi possível carregar o pipeline.")}).finally(()=>{if(ativo)setLoading(false)});return()=>{ativo=false}},[])
 const filtrados=useMemo(()=>dados.filter(item=>{const data=dataIsoValida(item.data_fechamento_prevista)?String(item.data_fechamento_prevista):"";if(!data)return true;return data>=inicio&&data<=fim}),[dados,fim,inicio])
 const valorTotal=filtrados.reduce((t,i)=>t+Number(i.valor||0),0),valorPonderado=filtrados.reduce((t,i)=>t+Number(i.valor_ponderado||0),0)
 const grafico=useMemo(()=>ETAPAS_PIPELINE.map(etapa=>{const itens=filtrados.filter(item=>item.etapa===etapa);return{etapa:etapa.replaceAll("_"," "),valor:itens.reduce((t,i)=>t+Number(i.valor||0),0),negociacoes:itens.length}}),[filtrados])
 return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/><div className="space-y-6 p-4 sm:p-6 lg:p-8">
  <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Movimento do negócio</p><h1 className="mt-2 text-3xl font-bold sm:text-4xl">CRM • Pipeline Comercial</h1><p className="mt-2 text-gray-400">Visão por estágio do mesmo núcleo de oportunidades. Aqui o objetivo é identificar onde cada negociação está e o que precisa avançar.</p></div><Link href="/crm-app/oportunidades/nova" className="rounded-xl bg-cyan-500 px-5 py-3 text-center font-semibold text-slate-950">Nova oportunidade</Link></div>
  <JornadaComercialNav/>
  <section className="grid gap-4 rounded-2xl border border-[#13203f] bg-[#071226] p-5 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto]"><CampoData label="Início" value={inicio} onChange={setInicio}/><CampoData label="Fim" value={fim} onChange={setFim}/><button type="button" onClick={()=>{setInicio(inicioMesAtual());setFim(fimMesAtual())}} className="self-end rounded-xl border border-cyan-700 px-4 py-3 text-cyan-300">Mês atual</button></section>
  {erro&&<div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
  <section className="grid grid-cols-1 gap-4 md:grid-cols-3"><Kpi titulo="Negociações no período" valor={filtrados.length.toLocaleString("pt-BR")}/><Kpi titulo="Pipeline total" valor={moeda(valorTotal)}/><Kpi titulo="Pipeline ponderado" valor={moeda(valorPonderado)}/></section>

  {!loading&&filtrados.length>0&&<section className="rounded-3xl border border-[#13203f] bg-gradient-to-b from-[#081a33] to-[#050d1d] p-5 shadow-[0_18px_45px_rgba(0,0,0,.35)]">
    <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[.18em] text-cyan-400">Leitura visual do funil</p><h2 className="mt-1 text-xl font-bold">Valor por estágio</h2><p className="mt-1 text-sm text-slate-400">A linha evidencia concentração, avanço e retenção de valor ao longo da jornada comercial.</p></div>
    <div className="h-[300px] w-full [perspective:1000px]"><div className="h-full rounded-2xl border border-[#17365f] bg-[#04101f] p-2 shadow-[0_16px_30px_rgba(6,182,212,.08)] [transform:rotateX(1.5deg)]">
      <ResponsiveContainer width="100%" height="100%"><AreaChart data={grafico} margin={{top:18,right:20,left:8,bottom:8}}><defs><linearGradient id="pipelineArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity={.55}/><stop offset="78%" stopColor="#0891b2" stopOpacity={.12}/><stop offset="100%" stopColor="#020817" stopOpacity={0}/></linearGradient><filter id="linhaGlow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><CartesianGrid stroke="#15304f" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="etapa" stroke="#7890ab" tick={{fontSize:11}} interval={0}/><YAxis stroke="#7890ab" tick={{fontSize:11}} tickFormatter={v=>`R$ ${(Number(v)/1000).toFixed(0)}k`}/><Tooltip contentStyle={{backgroundColor:"#061126",border:"1px solid #24507a",borderRadius:"14px",color:"#fff"}} formatter={(v)=>[moeda(Number(v)),"Valor"]}/><Area type="monotone" dataKey="valor" stroke="#22d3ee" strokeWidth={4} fill="url(#pipelineArea)" filter="url(#linhaGlow)" dot={{r:4,fill:"#22d3ee",stroke:"#0e7490",strokeWidth:2}} activeDot={{r:6}}/></AreaChart></ResponsiveContainer>
    </div></div>
  </section>}

  {loading?<Aviso>Carregando pipeline...</Aviso>:filtrados.length===0?<Aviso>Nenhuma negociação encontrada no período.</Aviso>:<section className="overflow-hidden rounded-3xl border border-[#13203f] bg-[#071427]">
    <div className="border-b border-[#13203f] p-5"><h2 className="text-xl font-bold">Negociações por estágio</h2><p className="mt-1 text-sm text-slate-400">Leitura objetiva em linha, sem cartões verticais extensos. Cada negócio ocupa apenas o espaço necessário.</p></div>
    <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead><tr className="border-b border-[#16325c] text-left text-slate-400"><Th>Cliente</Th><Th>Oportunidade</Th><Th>Etapa</Th><Th>Valor</Th><Th>Chance</Th><Th>Previsão</Th><Th>Ação</Th></tr></thead><tbody>{filtrados.map(item=><tr key={item.oportunidade_id} className="border-b border-[#13203f] hover:bg-[#091a33]/60"><Td forte>{item.cliente_nome||"Cliente não identificado"}</Td><Td>{item.titulo||"Oportunidade comercial"}</Td><td className="p-4"><span className="rounded-full border border-cyan-800 bg-cyan-950/30 px-3 py-1 text-xs text-cyan-300">{item.etapa.replaceAll("_"," ")}</span></td><td className="p-4 font-semibold text-emerald-300">{moeda(item.valor)}</td><Td>{percentual(item.probabilidade)}</Td><Td>{dataPrevista(item.data_fechamento_prevista)}</Td><td className="p-4"><Link href={`/oportunidades/${item.oportunidade_id}`} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Abrir negócio</Link></td></tr>)}</tbody></table></div>
  </section>}
 </div></section></main>
}
function CampoData({label,value,onChange}:{label:string;value:string;onChange:(value:string)=>void}){return <label className="text-sm text-slate-300">{label}<input type="date" value={value} onChange={e=>onChange(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label>}
function Kpi({titulo,valor}:{titulo:string;valor:string}){return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-400">{valor}</p></div>}
function Aviso({children}:{children:React.ReactNode}){return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-10 text-gray-300">{children}</div>}
function Th({children}:{children:React.ReactNode}){return <th className="p-4 font-medium">{children}</th>}
function Td({children,forte=false}:{children:React.ReactNode;forte?:boolean}){return <td className={`p-4 ${forte?"font-semibold text-cyan-300":"text-slate-200"}`}>{children}</td>}
