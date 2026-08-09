"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Ciclo = {
  pedido_id:string
  status_ciclo:string
  etapas:string[]
  carrier_confirmado_em?:string|null
  faturado_em?:string|null
  numero_nf?:string|null
  numero_serie_nf?:string|null
  entregue_em?:string|null
  instalado_em?:string|null
  numero_serie_instalado?:string|null
  encerrado_em?:string|null
  observacao_acompanhamento?:string|null
  pode_encerrar?:boolean
  serie_divergente?:boolean
}

const ETAPAS=[
  {id:"PEDIDO",rotulo:"Pedido"},
  {id:"CARRIER",rotulo:"Enviado à CARRIER"},
  {id:"FATURADO",rotulo:"Faturado"},
  {id:"ENTREGUE",rotulo:"Entregue"},
  {id:"INSTALADO",rotulo:"Instalado"},
  {id:"ENCERRADO",rotulo:"Encerrado"},
]

function dataHora(valor?:string|null){if(!valor)return"-";const d=new Date(valor);return Number.isNaN(d.getTime())?valor:d.toLocaleString("pt-BR")}

export default function CicloPedidoPage(){
 const params=useParams<{id:string}>(),id=String(params?.id||"")
 const[dados,setDados]=useState<Ciclo|null>(null),[loading,setLoading]=useState(true),[salvando,setSalvando]=useState(false),[erro,setErro]=useState(""),[mensagem,setMensagem]=useState(""),[nf,setNf]=useState(""),[serieNf,setSerieNf]=useState(""),[serieInstalada,setSerieInstalada]=useState(""),[observacao,setObservacao]=useState("")
 async function carregar(){setLoading(true);setErro("");try{const r=await fetch(`${API_URL}/carrier-operacional/pedidos/${id}/ciclo`,{cache:"no-store"});const p=await r.json().catch(()=>null);if(!r.ok)throw new Error(p?.detail||"Falha ao carregar ciclo.");setDados(p);setNf(String(p.numero_nf||""));setSerieNf(String(p.numero_serie_nf||""));setSerieInstalada(String(p.numero_serie_instalado||""));setObservacao(String(p.observacao_acompanhamento||""))}catch(e){setErro(e instanceof Error?e.message:"Falha ao carregar ciclo.")}finally{setLoading(false)}}
 useEffect(()=>{if(id)void carregar()},[id])
 const atual=dados?.status_ciclo||"PEDIDO",indiceAtual=ETAPAS.findIndex(e=>e.id===atual),proxima=ETAPAS[indiceAtual+1]
 async function avancar(etapa:string){setSalvando(true);setErro("");setMensagem("");try{const r=await fetch(`${API_URL}/carrier-operacional/pedidos/${id}/ciclo`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({etapa,numero_nf:nf||null,numero_serie_nf:serieNf||null,numero_serie_instalado:serieInstalada||null,observacao:observacao||null})});const p=await r.json().catch(()=>null);if(!r.ok)throw new Error(p?.detail||"Não foi possível atualizar o ciclo.");setMensagem(`Etapa ${etapa.replaceAll("_"," ")} confirmada.`);await carregar()}catch(e){setErro(e instanceof Error?e.message:"Falha ao atualizar ciclo.")}finally{setSalvando(false)}}
 const bloqueado=salvando||(proxima?.id==="FATURADO"&&(!nf.trim()||!serieNf.trim()))||(proxima?.id==="INSTALADO"&&!serieInstalada.trim())
 return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/><div className="space-y-6 p-4 sm:p-6 lg:p-8">
  <header className="rounded-3xl border border-[#13203f] bg-[#091a33] p-6"><Link href={`/pedidos/${id}`} className="text-sm font-semibold text-cyan-300">← Voltar ao pedido</Link><p className="mt-5 text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Ciclo operacional completo</p><h1 className="mt-2 text-3xl font-bold">Acompanhamento até instalação</h1><p className="mt-2 text-sm text-slate-400">Tela operacional do CTI Web. O CRM App apenas reflete a evolução. O ciclo só encerra após instalação confirmada.</p></header>
  {loading&&<div className="rounded-2xl border border-[#13203f] p-6 text-slate-400">Carregando...</div>}{erro&&<div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}{mensagem&&<div className="rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
  {dados&&<>
   <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">{ETAPAS.map((etapa,index)=>{const concluida=index<=indiceAtual;return <div key={etapa.id} className={`rounded-2xl border p-4 ${concluida?"border-emerald-700 bg-emerald-950/20":"border-[#24466f] bg-[#071427]"}`}><p className="text-xs text-slate-500">{index+1}</p><p className={`mt-2 font-semibold ${concluida?"text-emerald-300":"text-slate-300"}`}>{etapa.rotulo}</p></div>})}</section>
   {dados.serie_divergente&&<div className="rounded-2xl border border-amber-700 bg-amber-950/20 p-4 text-amber-200"><strong>Divergência de número de série identificada.</strong> Série da NF: {dados.numero_serie_nf||"-"} · Série instalada: {dados.numero_serie_instalado||"-"}. O registro permanece preservado para rastreio, auditoria e comprovação comercial.</div>}
   <section className="grid gap-5 lg:grid-cols-2"><article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Comprovações e rastreabilidade</h2><dl className="mt-5 space-y-3 text-sm"><Linha label="CARRIER" valor={dataHora(dados.carrier_confirmado_em)}/><Linha label="Faturamento" valor={dataHora(dados.faturado_em)}/><Linha label="NF" valor={dados.numero_nf||"-"}/><Linha label="Número de série da NF" valor={dados.numero_serie_nf||"-"}/><Linha label="Entrega" valor={dataHora(dados.entregue_em)}/><Linha label="Instalação" valor={dataHora(dados.instalado_em)}/><Linha label="Número de série instalado" valor={dados.numero_serie_instalado||"-"}/><Linha label="Encerramento" valor={dataHora(dados.encerrado_em)}/></dl></article>
   <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6"><h2 className="text-xl font-bold">Atualizar acompanhamento</h2><p className="mt-2 text-sm text-slate-400">Etapa atual: <strong className="text-cyan-300">{atual}</strong></p>{proxima?.id==="FATURADO"&&<div className="mt-5 grid gap-4 md:grid-cols-2"><label className="block text-sm text-slate-300">Número da NF<input value={nf} onChange={e=>setNf(e.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" placeholder="Obrigatório"/></label><label className="block text-sm text-slate-300">Número de série da NF<input value={serieNf} onChange={e=>setSerieNf(e.target.value.toUpperCase())} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" placeholder="Obrigatório para rastreio"/></label></div>}{proxima?.id==="INSTALADO"&&<label className="mt-5 block text-sm text-slate-300">Número de série instalado<input value={serieInstalada} onChange={e=>setSerieInstalada(e.target.value.toUpperCase())} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" placeholder="Série efetivamente instalada"/><span className="mt-2 block text-xs text-slate-500">Pode ser diferente da série faturada. A divergência será preservada e sinalizada, não sobrescrita.</span></label>}<label className="mt-5 block text-sm text-slate-300">Observação<textarea value={observacao} onChange={e=>setObservacao(e.target.value)} rows={4} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label>{proxima?<button disabled={bloqueado} onClick={()=>void avancar(proxima.id)} className="mt-5 w-full rounded-xl bg-cyan-500 px-5 py-3 font-bold text-slate-950 disabled:opacity-50">{salvando?"Salvando...":`Confirmar: ${proxima.rotulo}`}</button>:<div className="mt-5 rounded-xl border border-emerald-800 bg-emerald-950/20 p-4 text-emerald-300">Ciclo operacional encerrado após instalação confirmada.</div>}</article></section>
  </>}
 </div></section></main>
}
function Linha({label,valor}:{label:string;valor:string}){return <div className="flex justify-between gap-4 border-b border-[#13203f] pb-3"><dt className="text-slate-500">{label}</dt><dd className="text-right text-slate-200">{valor}</dd></div>}
