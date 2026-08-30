"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, Search } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { possuiVisaoConsolidada } from "@/core/rbac/commercial-scope"
import { definirResponsavelClienteSeguro, getClientesCanonicosSeguros, getResponsaveisComerciaisSeguros, type ClienteCanonicoSeguro, type ResponsavelComercialSeguro } from "@/services/modulos-api"

function norm(v?:string){return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase()}

export default function CarteirasComerciaisPage(){
 const{usuario}=useAuth(),master=possuiVisaoConsolidada(usuario)
 const[responsaveis,setResponsaveis]=useState<ResponsavelComercialSeguro[]>([]),[filtroResponsavel,setFiltroResponsavel]=useState("")
 const[clientes,setClientes]=useState<ClienteCanonicoSeguro[]>([]),[busca,setBusca]=useState(""),[loading,setLoading]=useState(true),[erro,setErro]=useState("")
 const[destino,setDestino]=useState<Record<string,string>>({}),[salvando,setSalvando]=useState("")

 async function carregar(responsavelId=filtroResponsavel){setLoading(true);setErro("");try{const lista=await getClientesCanonicosSeguros(responsavelId||undefined);setClientes(lista)}catch(e){setErro(e instanceof Error?e.message:"Não foi possível carregar a carteira.")}finally{setLoading(false)}}
 useEffect(()=>{if(!master)return;let ativo=true;queueMicrotask(async()=>{if(!ativo)return;try{const[r,c]=await Promise.all([getResponsaveisComerciaisSeguros(),getClientesCanonicosSeguros()]);if(ativo){setResponsaveis(r);setClientes(c)}}catch(e){if(ativo)setErro(e instanceof Error?e.message:"Não foi possível carregar a carteira.")}finally{if(ativo)setLoading(false)}});return()=>{ativo=false}},[master])
 async function trocarFiltro(id:string){setFiltroResponsavel(id);await carregar(id)}
 async function atribuir(cliente:ClienteCanonicoSeguro,restaurar=false){const responsavelId=destino[cliente.id]||usuario?.id||"";setSalvando(cliente.id);setErro("");try{await definirResponsavelClienteSeguro(cliente.id,restaurar?{restaurar_territorio:true,motivo:"Restaurado ao responsável territorial pelo Master."}:{responsavel_id:responsavelId,conta_direta_master:responsavelId===usuario?.id||responsaveis.some(r=>r.id===responsavelId&&["ADMIN_MASTER","DIRETOR_VIENA_SP"].includes(String(r.tipo_usuario||""))),motivo:"Atribuição comercial definida pelo Master."});await carregar()}catch(e){setErro(e instanceof Error?e.message:"Não foi possível alterar a responsabilidade.")}finally{setSalvando("")}}
 const lista=useMemo(()=>{const q=norm(busca);return clientes.filter(c=>!q||norm(`${c.nome} ${c.cnpj||""} ${c.cidade||""}`).includes(q))},[clientes,busca])
 const nomeFiltro=responsaveis.find(r=>r.id===filtroResponsavel)?.nome||"Toda a equipe comercial"

 if(!master)return <main className="min-h-screen bg-[#020817] text-white"><Sidebar/><section className="flex-1"><Topbar/><div className="p-8"><p className="rounded-2xl border border-amber-700 bg-amber-950/20 p-5 text-amber-200">Gestão de carteiras disponível somente para usuários Master.</p></div></section></main>
 return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/><div className="space-y-5 p-4 sm:p-6 lg:p-8">
  <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"><div><Link href="/dashboard" className="mb-3 inline-flex items-center gap-2 text-sm text-cyan-300"><ArrowLeft size={16}/>Dashboard Executivo</Link><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Governança comercial</p><h1 className="mt-2 text-3xl font-bold">Carteiras por responsável</h1><p className="mt-2 text-sm text-slate-400">O território define a origem geográfica. O responsável comercial define quem efetivamente atende o cliente.</p></div><div className="min-w-[280px]"><label className="text-xs font-semibold text-slate-400">Visualizar carteira</label><select value={filtroResponsavel} onChange={e=>void trocarFiltro(e.target.value)} className="mt-1 w-full rounded-xl border border-cyan-700 bg-[#071427] px-3 py-3"><option value="">Toda a equipe comercial</option>{responsaveis.map(r=><option key={r.id} value={r.id}>{r.nome}</option>)}</select></div></header>
  <section className="rounded-2xl border border-[#17304d] bg-[#071427] p-4"><div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><p className="text-sm text-slate-400">Carteira selecionada</p><p className="font-bold text-cyan-300">{nomeFiltro} · {clientes.length} clientes</p></div><label className="relative min-w-[280px]"><Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"/><input value={busca} onChange={e=>setBusca(e.target.value)} placeholder="Buscar cliente, CNPJ ou cidade" className="w-full rounded-xl border border-[#24466f] bg-[#020817] py-3 pl-10 pr-3"/></label></div></section>
  {erro&&<p className="rounded-xl border border-red-800 bg-red-950/20 p-4 text-red-200">{erro}</p>}
  {loading?<p className="p-6 text-slate-400">Carregando carteira...</p>:<div className="grid gap-3">{lista.map(c=><article key={c.id} className="rounded-2xl border border-[#17304d] bg-[#071427] p-4"><div className="grid gap-4 xl:grid-cols-[1fr_220px_180px_160px]"><div><h2 className="font-bold">{c.nome}</h2><p className="mt-1 text-xs text-slate-400">{c.cnpj?`CNPJ/CPF ${c.cnpj} · `:""}{c.cidade||""}{c.estado?` / ${c.estado}`:""}</p><p className="mt-2 text-xs text-cyan-300">Território interno: {c.sub_regiao||"pendente"} · Responsável atual: {c.responsavel_comercial_nome||"não atribuído"}</p>{c.responsabilidade_tipo==="CONTA_DIRETA_MASTER"&&<span className="mt-2 inline-flex rounded-full border border-amber-600/50 bg-amber-500/10 px-2 py-1 text-[11px] font-bold text-amber-200">Conta direta Master</span>}</div><select value={destino[c.id]||c.responsavel_comercial_id||usuario?.id||""} onChange={e=>setDestino(v=>({...v,[c.id]:e.target.value}))} className="rounded-xl border border-[#24466f] bg-[#020817] px-3 py-2 text-sm">{responsaveis.map(r=><option key={r.id} value={r.id}>{r.nome}</option>)}</select><button disabled={salvando===c.id} onClick={()=>void atribuir(c,false)} className="rounded-xl bg-cyan-500 px-3 py-2 text-sm font-bold text-slate-950 disabled:opacity-50">{salvando===c.id?"Salvando...":"Definir responsável"}</button><button disabled={salvando===c.id} onClick={()=>void atribuir(c,true)} className="rounded-xl border border-slate-600 px-3 py-2 text-sm font-semibold text-slate-200 disabled:opacity-50">Restaurar território</button></div></article>)}</div>}
 </div></section></main>
}
