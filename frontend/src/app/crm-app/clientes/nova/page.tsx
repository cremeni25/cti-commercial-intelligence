"use client"

import Link from "next/link"
import { FormEvent, useRef, useState } from "react"
import { ArrowLeft, Building2, Loader2, Save, Search } from "lucide-react"

const categorias = [
  ["TRANSPORTADORA", "Transportadora"], ["PRODUTOR", "Produtor"], ["EMBARCADOR", "Embarcador"],
  ["LOCADORA", "Locadora"], ["IMPLEMENTADORA", "Implementadora"], ["DISTRIBUIDORA", "Distribuidora"],
] as const

type Registro = Record<string, unknown>
function valor(dados: FormData, campo: string) { return String(dados.get(campo) || "").trim() }
function texto(v: unknown) { return String(v ?? "").trim() }

export default function NovoClientePage() {
  const formRef = useRef<HTMLFormElement>(null)
  const [salvando,setSalvando]=useState(false),[consultando,setConsultando]=useState(false),[erro,setErro]=useState(""),[sucesso,setSucesso]=useState(""),[aviso,setAviso]=useState("")

  function preencher(dados: Registro) {
    const form = formRef.current; if (!form) return
    const mapa: Record<string, unknown> = {
      nome:dados.nome, cnpj:dados.cnpj, inscricao_estadual:dados.inscricao_estadual, endereco:dados.endereco,
      numero:dados.numero, complemento:dados.complemento, bairro:dados.bairro, cidade:dados.cidade,
      estado:dados.estado, cep:dados.cep, fone:dados.fone, email:dados.email, ddd:dados.ddd,
    }
    for (const [campo,v] of Object.entries(mapa)) {
      const input=form.elements.namedItem(campo) as HTMLInputElement|null
      if(input && texto(v)) input.value=texto(v)
    }
  }

  async function consultarCnpj() {
    const form=formRef.current; if(!form)return
    const cnpj=texto((form.elements.namedItem("cnpj") as HTMLInputElement|null)?.value)
    setConsultando(true);setErro("");setSucesso("");setAviso("")
    try{
      const resposta=await fetch(`/api/crm-proxy/crm-app/clientes/cnpj/${encodeURIComponent(cnpj)}`,{cache:"no-store"})
      const retorno=await resposta.json().catch(()=>({})) as Registro
      if(!resposta.ok)throw new Error(texto(retorno.detail)||`Não foi possível consultar o CNPJ (${resposta.status}).`)
      if(retorno.status==="CLIENTE_EXISTENTE"){
        const cliente=(retorno.cliente||{}) as Registro
        setAviso(`Cliente já cadastrado no CTI: ${texto(cliente.nome)||"cadastro existente"}. Abra a ficha existente em vez de criar duplicidade.`)
        return
      }
      const dados=(retorno.dados||{}) as Registro
      preencher(dados)
      setSucesso(`Dados cadastrais encontrados em ${texto(retorno.fonte)||"fonte externa"}. Revise e complete os dados comerciais antes de salvar.`)
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao consultar CNPJ.")}finally{setConsultando(false)}
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();const formulario=evento.currentTarget
    setSalvando(true);setErro("");setSucesso("")
    const dados=new FormData(formulario)
    const payload={
      nome:valor(dados,"nome"),cnpj:valor(dados,"cnpj")||null,inscricao_estadual:valor(dados,"inscricao_estadual")||null,
      endereco:valor(dados,"endereco")||null,numero:valor(dados,"numero")||null,complemento:valor(dados,"complemento")||null,
      bairro:valor(dados,"bairro")||null,cidade:valor(dados,"cidade")||null,estado:valor(dados,"estado").toUpperCase()||null,
      cep:valor(dados,"cep")||null,contato:valor(dados,"contato")||null,fone:valor(dados,"fone")||null,
      email:valor(dados,"email")||null,email_xml:valor(dados,"email_xml")||null,categoria:valor(dados,"categoria")||"TRANSPORTADORA",
      ddd:valor(dados,"ddd")||null,sub_regiao:valor(dados,"sub_regiao")||null,
    }
    if(!payload.nome||!payload.cnpj||!payload.cidade||!payload.estado||!payload.categoria){setErro("Preencha razão social, CNPJ, cidade, UF e categoria.");setSalvando(false);return}
    try{
      const checagem=await fetch(`/api/crm-proxy/crm-app/clientes/cnpj/${encodeURIComponent(payload.cnpj)}`,{cache:"no-store"})
      const existente=await checagem.json().catch(()=>({})) as Registro
      if(checagem.ok&&existente.status==="CLIENTE_EXISTENTE")throw new Error(`Este CNPJ já pertence a ${texto((existente.cliente as Registro)?.nome)||"um cliente cadastrado"}. Cadastro duplicado não foi criado.`)
      const resposta=await fetch("/api/crm-proxy/crm-app/clientes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
      const retorno=await resposta.json().catch(()=>({})) as Registro
      if(!resposta.ok)throw new Error(texto(retorno.detail)||`Não foi possível cadastrar o cliente (${resposta.status}).`)
      formulario.reset();setAviso("");setSucesso("Cliente cadastrado com sucesso e disponível em toda a jornada comercial.")
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao cadastrar cliente.")}finally{setSalvando(false)}
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Novo cliente</h1><p className="text-sm text-slate-400">Informe o CNPJ para buscar e preencher os dados cadastrais.</p></div></header>
    {erro&&<div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}{aviso&&<div className="mb-4 rounded-2xl border border-amber-800 bg-amber-950/30 p-4 text-amber-200">{aviso}</div>}{sucesso&&<div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{sucesso}</div>}
    <form ref={formRef} onSubmit={salvar} className="space-y-5 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6">
      <div className="flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div><h2 className="font-bold">Dados cadastrais</h2><p className="text-sm text-slate-400">A busca por CNPJ não substitui sua revisão antes de salvar.</p></div></div>
      <section className="grid gap-4 sm:grid-cols-2"><Campo label="Nome / razão social" name="nome" required/><div><Campo label="CNPJ" name="cnpj" inputMode="numeric" required/><button type="button" onClick={consultarCnpj} disabled={consultando} className="mt-2 flex h-10 w-full items-center justify-center gap-2 rounded-xl border border-cyan-700 bg-cyan-950/30 text-sm font-semibold text-cyan-200 disabled:opacity-50">{consultando?<Loader2 size={16} className="animate-spin"/>:<Search size={16}/>}Buscar dados pelo CNPJ</button></div><Campo label="Inscrição estadual" name="inscricao_estadual"/><label className="text-sm text-slate-300">Categoria<select name="categoria" defaultValue="TRANSPORTADORA" required className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4">{categorias.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label></section>
      <section><h3 className="mb-3 font-semibold text-slate-200">Endereço</h3><div className="grid gap-4 sm:grid-cols-2"><Campo label="Endereço" name="endereco"/><Campo label="Número" name="numero"/><Campo label="Complemento" name="complemento"/><Campo label="Bairro" name="bairro"/><Campo label="Cidade" name="cidade" required/><Campo label="UF" name="estado" maxLength={2} required/><Campo label="CEP" name="cep" inputMode="numeric"/><Campo label="DDD" name="ddd" inputMode="numeric"/><Campo label="Sub-região" name="sub_regiao"/></div></section>
      <section><h3 className="mb-3 font-semibold text-slate-200">Contato comercial e fiscal</h3><div className="grid gap-4 sm:grid-cols-2"><Campo label="Contato" name="contato"/><Campo label="Fone" name="fone" inputMode="tel"/><Campo label="E-mail" name="email" type="email"/><Campo label="E-mail para envio de XML" name="email_xml" type="email"/></div></section>
      <button disabled={salvando} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-50">{salvando?<Loader2 className="animate-spin" size={18}/>:<Save size={18}/>}Salvar cliente</button>
    </form>
  </div></main>
}
function Campo({label,name,required=false,maxLength,type="text",inputMode}:{label:string;name:string;required?:boolean;maxLength?:number;type?:string;inputMode?:"numeric"|"tel"}){return <label className="text-sm text-slate-300">{label}<input name={name} type={type} required={required} maxLength={maxLength} inputMode={inputMode} className="mt-2 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4"/></label>}
