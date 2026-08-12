"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, Check, ClipboardCheck, Loader2, MapPinned, Search } from "lucide-react"
import { useAuth } from "@/core/auth"

type Cliente = { id: string; nome: string; cidade?: string; estado?: string }
type Negociacao = { oportunidade_id: string; cliente_id: string; cliente_nome?: string; titulo: string; etapa: string; proposta_id?: string | null; proposta_numero?: string | null; pedido_id?: string | null; pedido_numero?: string | null; encerrada?: boolean }
type Registro = Record<string, unknown>

const tipos = [["VISITA_PRESENCIAL","Visita presencial"],["VISITA_REMOTA","Visita remota"],["LIGACAO","Ligação"],["WHATSAPP","WhatsApp"],["EMAIL","E-mail"],["FOLLOW_UP","Follow-up"],["REUNIAO","Reunião"],["APRESENTACAO","Apresentação"],["PROSPECCAO","Prospecção"],["POS_VENDA","Pós-venda"],["OUTRO","Outro"]] as const
function texto(valor: unknown): string { return String(valor ?? "").trim() }
function chave(valor: unknown): string { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }

export default function NovaAtividadePage() {
  const { usuario } = useAuth()
  const search = useSearchParams()
  const clienteContexto = texto(search.get("cliente"))
  const oportunidadeContexto = texto(search.get("oportunidade"))
  const [clientes,setClientes]=useState<Cliente[]>([]), [negociacoes,setNegociacoes]=useState<Negociacao[]>([])
  const [clienteBusca,setClienteBusca]=useState(""), [cliente,setCliente]=useState<Cliente|null>(null), [oportunidadeId,setOportunidadeId]=useState(""), [tipo,setTipo]=useState("FOLLOW_UP")
  const [carregando,setCarregando]=useState(true), [salvando,setSalvando]=useState(false), [erro,setErro]=useState(""), [sucesso,setSucesso]=useState("")

  useEffect(()=>{let ativo=true; void (async()=>{setCarregando(true);setErro("");try{
    const [clientesResposta,nucleoResposta]=await Promise.all([fetch("/api/crm-proxy/crm-app/clientes",{cache:"no-store"}),fetch("/api/crm-proxy/crm/nucleo-comercial",{cache:"no-store"})])
    const clientesDados=await clientesResposta.json().catch(()=>[]), nucleoDados=await nucleoResposta.json().catch(()=>[])
    if(!clientesResposta.ok) throw new Error(String((clientesDados as Registro).detail||`Clientes: HTTP ${clientesResposta.status}`))
    if(!nucleoResposta.ok) throw new Error(String((nucleoDados as Registro).detail||`Núcleo: HTTP ${nucleoResposta.status}`))
    if(!ativo)return
    const listaClientes=(Array.isArray(clientesDados)?clientesDados:[]).map((item:Registro)=>({id:texto(item.id),nome:texto(item.nome||item.razao_social||item.nome_fantasia),cidade:texto(item.cidade||item.municipio),estado:texto(item.estado||item.uf)})).filter((item)=>item.id&&item.nome).sort((a,b)=>a.nome.localeCompare(b.nome,"pt-BR"))
    const listaNegociacoes=(Array.isArray(nucleoDados)?nucleoDados:[]).map((item:Registro)=>({oportunidade_id:texto(item.oportunidade_id),cliente_id:texto(item.cliente_id),cliente_nome:texto(item.cliente_nome),titulo:texto(item.titulo)||"Oportunidade comercial",etapa:texto(item.etapa)||"OPORTUNIDADE",proposta_id:texto(item.proposta_id)||null,proposta_numero:texto(item.proposta_numero)||null,pedido_id:texto(item.pedido_id)||null,pedido_numero:texto(item.pedido_numero)||null,encerrada:Boolean(item.encerrada)})).filter((item)=>item.oportunidade_id)
    setClientes(listaClientes)
    setNegociacoes(listaNegociacoes)

    const negociacaoInicial=oportunidadeContexto?listaNegociacoes.find((item)=>item.oportunidade_id===oportunidadeContexto):undefined
    const idClienteInicial=clienteContexto||negociacaoInicial?.cliente_id||""
    const nomeClienteInicial=negociacaoInicial?.cliente_nome||""
    const clienteInicial=listaClientes.find((item)=>item.id===idClienteInicial)||listaClientes.find((item)=>nomeClienteInicial&&chave(item.nome)===chave(nomeClienteInicial))
    if(clienteInicial){setCliente(clienteInicial);setClienteBusca(clienteInicial.nome)}
    if(negociacaoInicial)setOportunidadeId(negociacaoInicial.oportunidade_id)
  }catch(falha){if(ativo)setErro(falha instanceof Error?falha.message:"Não foi possível carregar clientes e negociações.")}finally{if(ativo)setCarregando(false)}})();return()=>{ativo=false}},[clienteContexto,oportunidadeContexto])

  const sugestoes=useMemo(()=>{const termo=clienteBusca.trim().toLocaleLowerCase("pt-BR");if(termo.length<2||cliente)return[];return clientes.filter((item)=>`${item.nome} ${item.cidade||""} ${item.estado||""}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0,12)},[clienteBusca,cliente,clientes])
  const negociacoesDoCliente=useMemo(()=>negociacoes.filter((item)=>!item.encerrada&&(item.cliente_id===cliente?.id||item.cliente_nome?.toLocaleLowerCase("pt-BR")===cliente?.nome.toLocaleLowerCase("pt-BR"))),[cliente,negociacoes])
  const negociacaoSelecionada=useMemo(()=>negociacoes.find((item)=>item.oportunidade_id===oportunidadeId)||null,[negociacoes,oportunidadeId])
  const visita=tipo.startsWith("VISITA")

  async function salvar(evento:FormEvent<HTMLFormElement>){evento.preventDefault();setErro("");setSucesso("");if(!cliente)return setErro("Selecione um cliente da lista sugerida.");if(!usuario?.id)return setErro("Não foi possível confirmar o usuário autenticado.");const dados=new FormData(evento.currentTarget);setSalvando(true);try{
    const resposta=await fetch("/api/crm-proxy/crm/atividades",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({cliente_id:cliente.id,oportunidade_id:negociacaoSelecionada?.oportunidade_id||null,proposta_id:negociacaoSelecionada?.proposta_id||null,pedido_id:negociacaoSelecionada?.pedido_id||null,usuario_id:usuario.id,tipo,titulo:texto(dados.get("titulo")),descricao:texto(dados.get("descricao"))||null,data:texto(dados.get("data"))||null,horario:texto(dados.get("horario"))||null,status:"PENDENTE"})})
    const detalhe=await resposta.json().catch(()=>({}));if(!resposta.ok)throw new Error(texto(detalhe.detail)||`Falha ${resposta.status}`);evento.currentTarget.reset();setCliente(null);setClienteBusca("");setOportunidadeId("");setTipo("FOLLOW_UP");setSucesso("Atividade registrada com sucesso.")
  }catch(falha){setErro(falha instanceof Error?falha.message:"Não foi possível salvar a atividade.")}finally{setSalvando(false)}}

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Nova atividade</h1></div></header>
    <section className="mb-4 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><div className="flex items-center gap-3"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">{visita?<MapPinned/>:<ClipboardCheck/>}</span><div><strong className="block text-lg">Uma única criação para todas as interações</strong><span className="text-sm text-slate-400">O contexto do cliente e da negociação é preservado ao navegar pelo CRM.</span></div></div></section>
    {erro&&<div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}{sucesso&&<div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">{sucesso}</div>}
    {carregando?<div className="grid min-h-72 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:<form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
      <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Cliente</span><div className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={clienteBusca} onChange={(e)=>{setClienteBusca(e.target.value);setCliente(null);setOportunidadeId("")}} placeholder="Digite pelo menos 2 letras do nome" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-11 pr-4"/></div>{sugestoes.length>0&&<div className="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((item)=><button type="button" key={item.id} onClick={()=>{setCliente(item);setClienteBusca(item.nome);setOportunidadeId("")}} className="flex w-full items-center justify-between border-b border-[#16325c] px-4 py-3 text-left last:border-0"><span><strong className="block">{item.nome}</strong><small className="text-slate-400">{[item.cidade,item.estado].filter(Boolean).join("/")||"Cliente cadastrado"}</small></span><Check size={16} className="text-cyan-300"/></button>)}</div>}</label>
      {cliente&&<div className="sm:col-span-2 rounded-xl border border-emerald-900 bg-emerald-950/20 p-3 text-sm text-emerald-200">Cliente selecionado: <strong>{cliente.nome}</strong>{oportunidadeId?" · negociação preservada":""}</div>}
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Negociação relacionada</span><select value={oportunidadeId} onChange={(e)=>setOportunidadeId(e.target.value)} disabled={!cliente} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 disabled:opacity-60"><option value="">Interação geral com o cliente</option>{negociacoesDoCliente.map((item)=><option key={item.oportunidade_id} value={item.oportunidade_id}>{item.titulo} — {item.etapa}</option>)}</select></label>
      <label><span className="mb-2 block text-sm text-slate-300">Tipo de atividade</span><select value={tipo} onChange={(e)=>setTipo(e.target.value)} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4">{tipos.map(([valor,rotulo])=><option key={valor} value={valor}>{rotulo}</option>)}</select></label><Campo name="titulo" label={visita?"Objetivo da visita":"Título"} required/><Campo name="data" label="Data" type="date" required/><Campo name="horario" label="Horário" type="time"/><label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição</span><textarea name="descricao" rows={5} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4"/></label><button disabled={salvando||!cliente} className="sm:col-span-2 h-12 rounded-2xl bg-cyan-500 font-semibold text-slate-950 disabled:opacity-60">{salvando?"Salvando...":"Salvar atividade"}</button>
    </form>}
  </div></main>
}
function Campo({name,label,type="text",required=false}:{name:string;label:string;type?:string;required?:boolean}){return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label>}