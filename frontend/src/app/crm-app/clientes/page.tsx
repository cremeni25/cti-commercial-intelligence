"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ArrowLeft, Building2, ChevronRight, Loader2, Plus, Search } from "lucide-react"

type Registro = Record<string, unknown>
type Cliente = { id: string; chave: string; nome: string; cidade: string; estado: string; negocios: number }
function texto(valor: unknown) { return String(valor ?? "").trim() }
function chaveNome(valor: unknown) { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }

export default function ClientesCrmAppPage() {
  const [clientes,setClientes]=useState<Cliente[]>([]),[busca,setBusca]=useState(""),[carregando,setCarregando]=useState(true),[erro,setErro]=useState("")
  useEffect(()=>{let ativo=true;void(async()=>{setCarregando(true);setErro("");try{
    const [cadastro,nucleo]=await Promise.all([fetch("/api/crm-proxy/crm-app/clientes",{cache:"no-store"}),fetch("/api/crm-proxy/crm/nucleo-comercial",{cache:"no-store"})])
    const cadastroDados=await cadastro.json().catch(()=>[]), nucleoDados=await nucleo.json().catch(()=>[])
    if(!cadastro.ok)throw new Error(String((cadastroDados as Registro).detail||`Clientes: HTTP ${cadastro.status}`));if(!nucleo.ok)throw new Error(String((nucleoDados as Registro).detail||`Núcleo: HTTP ${nucleo.status}`));if(!ativo)return
    const mapa=new Map<string,Cliente>()
    for(const item of Array.isArray(cadastroDados)?cadastroDados:[]){const nome=texto(item.nome||item.razao_social||item.nome_fantasia);if(!nome)continue;const chave=chaveNome(nome);mapa.set(chave,{id:texto(item.id)||nome,chave,nome,cidade:texto(item.cidade||item.municipio),estado:texto(item.estado||item.uf).toUpperCase(),negocios:0})}
    for(const item of Array.isArray(nucleoDados)?nucleoDados:[]){const nome=texto(item.cliente_nome);if(!nome)continue;const chave=chaveNome(nome), existente=mapa.get(chave);mapa.set(chave,{id:texto(item.cliente_id)||existente?.id||nome,chave,nome:existente?.nome||nome,cidade:existente?.cidade||texto(item.cliente_cidade||item.municipio),estado:existente?.estado||texto(item.cliente_estado||item.uf).toUpperCase(),negocios:(existente?.negocios||0)+1})}
    setClientes([...mapa.values()].sort((a,b)=>a.nome.localeCompare(b.nome,"pt-BR")))
  }catch(falha){if(ativo)setErro(falha instanceof Error?falha.message:"Não foi possível carregar a carteira de clientes.")}finally{if(ativo)setCarregando(false)}})();return()=>{ativo=false}},[])
  const filtrados=useMemo(()=>{const termo=busca.trim().toLocaleLowerCase("pt-BR");return termo?clientes.filter((item)=>`${item.nome} ${item.cidade} ${item.estado}`.toLocaleLowerCase("pt-BR").includes(termo)):clientes},[busca,clientes])
  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Carteira de clientes</h1>{!carregando&&!erro&&<p className="mt-1 text-sm text-slate-400">{clientes.length} clientes cadastrados</p>}</div></div><Link href="/crm-app/clientes/nova" className="flex h-11 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 font-bold text-slate-950"><Plus size={18}/>Novo cliente</Link></header>
    <label className="relative mb-4 block"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e)=>setBusca(e.target.value)} placeholder="Buscar cliente ou cidade" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label>
    {erro&&<div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {carregando?<div className="grid min-h-64 place-items-center gap-3 text-slate-400"><Loader2 className="animate-spin text-cyan-300"/><span>Carregando carteira comercial...</span></div>:erro?null:filtrados.length===0?<div className="grid min-h-64 place-items-center rounded-3xl border border-dashed border-[#24466f] p-8 text-center"><div><AlertCircle className="mx-auto mb-3 text-cyan-300"/><p className="font-semibold">Nenhum cliente encontrado</p><Link href="/crm-app/clientes/nova" className="mt-3 inline-flex text-sm font-semibold text-cyan-300">Cadastrar novo cliente</Link></div></div>:<div className="grid gap-4 md:grid-cols-2">{filtrados.map((cliente)=><Link key={cliente.chave} href={`/crm-app/clientes/${encodeURIComponent(cliente.id)}?nome=${encodeURIComponent(cliente.nome)}`} className="group rounded-3xl border border-[#16325c] bg-[#07162b] p-5 transition hover:border-cyan-700"><div className="flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div className="min-w-0 flex-1"><h2 className="truncate font-bold">{cliente.nome}</h2><p className="text-xs text-slate-400">{cliente.cidade?`${cliente.cidade}${cliente.estado?`/${cliente.estado}`:""}`:"Cadastro comercial"}</p><p className="mt-2 text-xs font-semibold text-cyan-300">{cliente.negocios} {cliente.negocios===1?"negociação":"negociações"} · abrir dossiê</p></div><ChevronRight size={20} className="text-cyan-300"/></div></Link>)}</div>}
  </div></main>
}
