"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowLeft, Printer } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

type Competidor={fabricante:string;registros:number;percentual_mercado:number}
type Segmento={codigo:string;segmento:string;mercado:number;carrier:number;carrier_percentual:number;concorrencia:number;concorrencia_percentual:number;reaproveitamento_documentacao:number;a_identificar:number;fabricantes_concorrentes:Competidor[];mensal:Array<{mes:string;carrier:number;concorrencia:number;reaproveitamento:number;a_identificar:number;mercado:number}>}
type Payload={metadata:{competencia:string;fonte_taxonomia:string;fabricantes_ativos:string[];regra_documentacao:string};resumo:{mercado:number;carrier:number;carrier_percentual:number;concorrencia_identificada:number;concorrencia_percentual:number;reaproveitamento_documentacao:number;a_identificar:number};ranking_concorrentes:Competidor[];segmentos:Segmento[];leituras_estrategicas:string[]}

export default function RelatorioCompetitividade(){
 const[data,setData]=useState<Payload|null>(null),[erro,setErro]=useState(false)
 useEffect(()=>{let active=true;fetch("/api/cti/analytics/anfir-competitividade-2026",{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()).then(p=>{if(active)setData(p)}).catch(()=>{if(active)setErro(true)});return()=>{active=false}},[])
 if(erro)return <div className="min-h-screen bg-[#020817] p-8 text-amber-200">Não foi possível carregar a inteligência competitiva ANFIR.</div>
 if(!data)return <div className="min-h-screen bg-[#020817] p-8 text-slate-300">Carregando inteligência competitiva ANFIR...</div>
 const r=data.resumo
 return <main className="flex min-h-screen bg-[#020817] text-white print:block print:bg-white print:text-black">
  <div className="print:hidden"><Sidebar/></div>
  <section className="min-w-0 flex-1"><div className="print:hidden"><Topbar/></div><div className="space-y-5 p-4 sm:p-6 lg:p-8 print:p-0">
   <header className="rounded-3xl border border-[#17304d] bg-[#071226] p-6 print:rounded-none print:border-0 print:bg-white print:p-0">
    <Link href="/dashboard" className="mb-4 inline-flex items-center gap-2 rounded-xl border border-[#17304d] px-4 py-2 text-sm text-cyan-200 print:hidden"><ArrowLeft size={16}/>Voltar ao Dashboard</Link>
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-amber-300 print:text-black">ANFIR 2026 · Viena SP</p><h1 className="mt-2 text-3xl font-bold">Relatório de Inteligência Competitiva</h1><p className="mt-2 max-w-4xl text-sm text-slate-400 print:text-gray-700">Carrier comparada aos fabricantes concorrentes identificados pela taxonomia oficial do CTI. Documento apto para impressão e exportação em PDF.</p></div><button onClick={()=>window.print()} className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 print:hidden"><Printer size={17}/>Imprimir / Salvar PDF</button></div>
   </header>
   <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6 print:grid-cols-3"><Metric label="Mercado" value={r.mercado}/><Metric label="Carrier" value={`${r.carrier} · ${r.carrier_percentual.toFixed(1)}%`}/><Metric label="Concorrência identificada" value={`${r.concorrencia_identificada} · ${r.concorrencia_percentual.toFixed(1)}%`}/><Metric label="Reaproveitamento / documentação" value={r.reaproveitamento_documentacao}/><Metric label="Fabricante a identificar" value={r.a_identificar}/><Metric label="Fabricantes ativos na taxonomia" value={data.metadata.fabricantes_ativos.length}/></section>
   <Section title="Carrier × concorrência por segmento"><Table headers={["Segmento","Mercado","Carrier","Carrier %","Concorrência","Concorrência %","Reaproveitamento","A identificar"]} rows={data.segmentos.map(s=>[s.segmento,s.mercado,s.carrier,`${s.carrier_percentual.toFixed(1)}%`,s.concorrencia,`${s.concorrencia_percentual.toFixed(1)}%`,s.reaproveitamento_documentacao,s.a_identificar])}/></Section>
   <Section title="Ranking de fabricantes concorrentes"><Table headers={["Fabricante","Registros","% do mercado total"]} rows={data.ranking_concorrentes.map(x=>[x.fabricante,x.registros,`${x.percentual_mercado.toFixed(1)}%`])}/></Section>
   {data.segmentos.map(s=><Section key={s.codigo} title={`${s.segmento} · evolução mensal Carrier × concorrência`}><Table headers={["Mês","Carrier","Concorrência","Reaproveitamento","A identificar","Mercado"]} rows={s.mensal.map(m=>[m.mes,m.carrier,m.concorrencia,m.reaproveitamento,m.a_identificar,m.mercado])}/><h3 className="mt-5 mb-2 font-semibold">Fabricantes concorrentes identificados</h3><Table headers={["Fabricante","Registros","% do mercado do segmento"]} rows={s.fabricantes_concorrentes.map(x=>[x.fabricante,x.registros,`${x.percentual_mercado.toFixed(1)}%`])}/></Section>)}
   <Section title="Leituras estratégicas"><ol className="list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-300 print:text-black">{data.leituras_estrategicas.map(x=><li key={x}>{x}</li>)}</ol><div className="mt-4 rounded-xl border border-violet-500/30 bg-violet-500/10 p-4 text-sm leading-6 print:border-gray-300 print:bg-white"><strong>Regra DOCUMENTAÇÃO:</strong> {data.metadata.regra_documentacao}</div></Section>
   <footer className="hidden border-t border-gray-300 pt-3 text-xs text-gray-600 print:block">CTI · ANFIR 2026 · Inteligência Competitiva · Taxonomia {data.metadata.fonte_taxonomia}</footer>
  </div></section>
 </main>
}
function Metric({label,value}:{label:string;value:string|number}){return <div className="rounded-xl border border-[#193354] bg-[#08162d] p-4 print:border-gray-300 print:bg-white"><p className="text-[10px] uppercase text-slate-500 print:text-gray-600">{label}</p><p className="mt-1 text-lg font-bold text-cyan-300 print:text-black">{value}</p></div>}
function Section({title,children}:{title:string;children:React.ReactNode}){return <section className="space-y-4 rounded-2xl border border-[#17304d] bg-[#071226] p-5 print:break-inside-auto print:rounded-none print:border-0 print:bg-white print:p-0 print:pb-6"><h2 className="text-xl font-bold text-cyan-300 print:text-black">{title}</h2>{children}</section>}
function Table({headers,rows}:{headers:string[];rows:Array<Array<React.ReactNode>>}){return <div className="overflow-x-auto"><table className="min-w-full border-separate border-spacing-0 text-sm print:text-xs"><thead><tr>{headers.map(h=><th key={h} className="border-b border-[#1d3655] bg-[#0b1b34] px-3 py-2 text-left text-xs uppercase text-slate-400 print:border-gray-300 print:bg-white print:text-black">{h}</th>)}</tr></thead><tbody>{rows.length?rows.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j} className="border-b border-[#132842] px-3 py-2 align-top print:border-gray-200">{cell}</td>)}</tr>):<tr><td colSpan={headers.length} className="px-3 py-4 text-slate-500">Sem registros no escopo atual.</td></tr>}</tbody></table></div>}
