"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { CheckCircle2, FilePlus2, FileText, Loader2, Plus, Send } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type PrecoVigente = { tabela_codigo?: string; preco_cheio?: number; vigencia_inicio?: string }
type EquipamentoCatalogo = { codigo:string; linha_produto:string; nome_comercial:string; configuracao?:string; compressor?:string; preco_vigente?:PrecoVigente|null }
type Item = { id:string; equipamento:string; quantidade:number; preco_tabela:number; preco_unitario:number; desconto_percentual:number; status:string }
type Proposta = { id:string; numero:string; valor:number; status_documento:string; versao:number }

const STATUS_INATIVOS = new Set(["CANCELADA","SUBSTITUIDA","OBSOLETA","REJEITADA","EXPIRADA"])

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function moeda(valor: unknown): string { return Number(valor || 0).toLocaleString("pt-BR", { style:"currency", currency:"BRL" }) }
function propostaAtual(lista: Proposta[]): Proposta | null {
  return [...lista].sort((a,b)=>Number(b.versao||0)-Number(a.versao||0)).find((item)=>!STATUS_INATIVOS.has(texto(item.status_documento).toUpperCase())) || null
}

export default function OportunidadePropostasApp({ oportunidadeId }: { oportunidadeId:string }) {
  const { usuario } = useAuth()
  const [catalogo,setCatalogo] = useState<EquipamentoCatalogo[]>([])
  const [itens,setItens] = useState<Item[]>([])
  const [propostas,setPropostas] = useState<Record<string,Proposta[]>>({})
  const [carregando,setCarregando] = useState(true)
  const [processando,setProcessando] = useState("")
  const [erro,setErro] = useState("")
  const [mensagem,setMensagem] = useState("")
  const [formularioAberto,setFormularioAberto] = useState(false)
  const [decisaoAberta,setDecisaoAberta] = useState(false)
  const [finalizacaoAberta,setFinalizacaoAberta] = useState(false)
  const [linha,setLinha] = useState("")
  const [equipamentoCodigo,setEquipamentoCodigo] = useState("")
  const [propostasParaEnvio,setPropostasParaEnvio] = useState<string[]>([])
  const [destinatarios,setDestinatarios] = useState("")
  const [mensagemEmail,setMensagemEmail] = useState("")

  const linhas = useMemo(()=>[...new Set(catalogo.map((item)=>item.linha_produto).filter(Boolean))].sort(),[catalogo])
  const equipamentos = useMemo(()=>catalogo.filter((item)=>item.linha_produto===linha),[catalogo,linha])
  const equipamentoSelecionado = useMemo(()=>catalogo.find((item)=>item.codigo===equipamentoCodigo),[catalogo,equipamentoCodigo])
  const totalNegociado = useMemo(()=>itens.reduce((soma,item)=>soma+(item.preco_tabela*(1-item.desconto_percentual/100))*item.quantidade,0),[itens])

  const carregar = useCallback(async()=>{
    if(!oportunidadeId)return
    setCarregando(true);setErro("")
    try{
      const [respostaItens,respostaCatalogo]=await Promise.all([
        fetch(`/api/crm-proxy/crm-documentos/oportunidades/${encodeURIComponent(oportunidadeId)}/itens`,{cache:"no-store"}),
        fetch(`/api/crm-proxy/catalogo-comercial/equipamentos`,{cache:"no-store"}),
      ])
      const payload=await respostaItens.json().catch(()=>[])
      const payloadCatalogo=await respostaCatalogo.json().catch(()=>[])
      if(!respostaItens.ok)throw new Error(texto((payload as Registro).detail)||`Falha ${respostaItens.status}`)
      if(!respostaCatalogo.ok)throw new Error(texto((payloadCatalogo as Registro).detail)||`Catálogo: falha ${respostaCatalogo.status}`)
      const lista=(Array.isArray(payload)?payload:[]).map((item:Registro):Item=>({id:texto(item.id),equipamento:texto(item.nome_comercial||item.equipamento)||"Equipamento",quantidade:Number(item.quantidade||1),preco_tabela:Number(item.preco_tabela||item.preco_unitario||0),preco_unitario:Number(item.preco_unitario||0),desconto_percentual:Number(item.desconto_percentual||0),status:texto(item.status||"EM_NEGOCIACAO")})).filter(item=>item.id)
      const listaCatalogo=(Array.isArray(payloadCatalogo)?payloadCatalogo:[]).map((item:Registro):EquipamentoCatalogo=>({codigo:texto(item.codigo),linha_produto:texto(item.linha_produto),nome_comercial:texto(item.nome_comercial||item.equipamento),configuracao:texto(item.configuracao),compressor:texto(item.compressor),preco_vigente:item.preco_vigente&&typeof item.preco_vigente==="object"?item.preco_vigente as PrecoVigente:null})).filter((item)=>item.codigo&&item.nome_comercial)
      setItens(lista);setCatalogo(listaCatalogo)
      if(!linha&&listaCatalogo.length){const primeira=listaCatalogo[0];setLinha(primeira.linha_produto);setEquipamentoCodigo(primeira.codigo)}
      const pares=await Promise.all(lista.map(async(item)=>{const r=await fetch(`/api/crm-proxy/crm-documentos/itens/${encodeURIComponent(item.id)}/propostas`,{cache:"no-store"});const p=await r.json().catch(()=>[]);return [item.id,Array.isArray(p)?p:[]] as const}))
      setPropostas(Object.fromEntries(pares))
    }catch(falha){setErro(falha instanceof Error?falha.message:"Não foi possível carregar itens e propostas.")}
    finally{setCarregando(false)}
  },[linha,oportunidadeId])

  useEffect(()=>{queueMicrotask(()=>void carregar())},[carregar])

  function trocarLinha(valor:string){setLinha(valor);setEquipamentoCodigo(catalogo.find((item)=>item.linha_produto===valor)?.codigo||"")}

  async function adicionarItem(evento:FormEvent<HTMLFormElement>){
    evento.preventDefault();if(!equipamentoSelecionado)return
    setProcessando("novo-item");setErro("");setMensagem("")
    const dados=new FormData(evento.currentTarget)
    try{
      const resposta=await fetch(`/api/crm-proxy/catalogo-comercial/oportunidades/${encodeURIComponent(oportunidadeId)}/itens`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
        equipamento_codigo:equipamentoSelecionado.codigo,
        quantidade:Math.max(1,Number(dados.get("quantidade")||1)),
        desconto_percentual:Math.max(0,Math.min(100,Number(dados.get("desconto_percentual")||0))),
        condicao_pagamento:texto(dados.get("condicao_pagamento"))||null,
        prazo_entrega:texto(dados.get("prazo_entrega"))||null,
        validade_condicao:texto(dados.get("validade_condicao"))||null,
        garantia:texto(dados.get("garantia"))||null,
        opcionais:texto(dados.get("opcionais")).split(",").map((item)=>item.trim()).filter(Boolean),
        observacoes_comerciais:texto(dados.get("observacoes_comerciais"))||null,
        observacoes_tecnicas:texto(dados.get("observacoes_tecnicas"))||null,
        ordem:itens.length,
      })})
      const payload=await resposta.json().catch(()=>({})) as Registro
      if(!resposta.ok)throw new Error(texto(payload.detail)||`Não foi possível adicionar o item (${resposta.status}).`)
      evento.currentTarget.reset();setFormularioAberto(false);setDecisaoAberta(true)
      setMensagem(`${equipamentoSelecionado.nome_comercial} foi salvo nesta oportunidade.`)
      await carregar()
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao adicionar item.")}
    finally{setProcessando("")}
  }

  async function gerar(item:Item):Promise<string|null>{
    const responsavel=texto(usuario?.id)
    if(!responsavel){setErro("Não foi possível confirmar o vendedor autenticado.");return null}
    setProcessando(item.id);setErro("");setMensagem("")
    try{
      const resposta=await fetch(`/api/crm-proxy/crm-documentos/itens/${encodeURIComponent(item.id)}/propostas`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({responsavel_id:responsavel})})
      const payload=await resposta.json().catch(()=>({}))
      if(!resposta.ok)throw new Error(texto((payload as Registro).detail)||`Não foi possível gerar a proposta (${resposta.status}).`)
      const criada=Array.isArray(payload)?payload[0]:payload
      const propostaId=criada&&typeof criada==="object"?texto((criada as Registro).id):""
      setMensagem(`Proposta criada para ${item.equipamento}.`);await carregar();return propostaId||null
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao gerar proposta.");return null}
    finally{setProcessando("")}
  }

  async function concluirCadastro(){
    if(!itens.length)return setErro("Adicione ao menos um item antes de concluir a negociação.")
    const responsavel=texto(usuario?.id);if(!responsavel)return setErro("Não foi possível confirmar o vendedor autenticado.")
    setProcessando("concluir");setErro("");setMensagem("")
    try{
      const ids:string[]=[]
      for(const item of itens){
        const atual=propostaAtual(propostas[item.id]||[])
        if(atual){ids.push(atual.id);continue}
        const resposta=await fetch(`/api/crm-proxy/crm-documentos/itens/${encodeURIComponent(item.id)}/propostas`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({responsavel_id:responsavel})})
        const payload=await resposta.json().catch(()=>({}))
        if(!resposta.ok)throw new Error(texto((payload as Registro).detail)||`Não foi possível preparar a proposta de ${item.equipamento}.`)
        const criada=Array.isArray(payload)?payload[0]:payload
        const id=criada&&typeof criada==="object"?texto((criada as Registro).id):""
        if(!id)throw new Error(`A proposta de ${item.equipamento} foi criada sem identificação.`)
        ids.push(id)
      }
      setPropostasParaEnvio(ids);setDecisaoAberta(false);setFormularioAberto(false);setFinalizacaoAberta(true)
      setMensagem(`${ids.length} proposta(s) oficial(is) preparada(s). Revise os itens e informe o destinatário para concluir o envio.`)
      await carregar()
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao preparar as propostas.")}
    finally{setProcessando("")}
  }

  async function enviarTodas(){
    const emails=destinatarios.split(/[;,\n]/).map((item)=>item.trim()).filter(Boolean)
    if(!emails.length)return setErro("Informe ao menos um e-mail de destino.")
    if(!propostasParaEnvio.length)return setErro("As propostas ainda não foram preparadas para envio.")
    setProcessando("enviar");setErro("");setMensagem("")
    try{
      const resposta=await fetch(`/api/crm-proxy/crm-app/oportunidades/${encodeURIComponent(oportunidadeId)}/enviar-propostas-email`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({proposta_ids:propostasParaEnvio,destinatarios:emails,mensagem:mensagemEmail||null})})
      const payload=await resposta.json().catch(()=>({})) as Registro
      if(!resposta.ok)throw new Error(texto(payload.detail)||`Não foi possível enviar as propostas (${resposta.status}).`)
      const protocolo=texto(payload.message_id)
      setMensagem(`Propostas enviadas com sucesso${protocolo?` · protocolo ${protocolo}`:""}.`)
      setFinalizacaoAberta(false);setDestinatarios("");setMensagemEmail("");await carregar()
    }catch(falha){setErro(falha instanceof Error?falha.message:"Falha ao enviar as propostas.")}
    finally{setProcessando("")}
  }

  return <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
    <div className="mb-4 flex items-center gap-2"><FileText className="text-cyan-300"/><div><h2 className="text-lg font-bold">Itens e propostas</h2><p className="text-xs text-slate-400">Uma oportunidade, vários itens e uma proposta oficial por equipamento</p></div></div>
    {erro&&<div className="mb-3 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200">{erro}</div>}
    {mensagem&&<div className="mb-3 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{mensagem}</div>}
    {carregando?<div className="grid min-h-28 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>:<>
      {itens.length===0?<div className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhum item comercial cadastrado. Adicione o primeiro equipamento desta negociação.</div>:<div className="space-y-3">{itens.map((item,indice)=>{const lista=propostas[item.id]||[],atual=propostaAtual(lista),precoNegociado=item.preco_tabela*(1-item.desconto_percentual/100),valorTotal=precoNegociado*item.quantidade;return <article key={item.id} className="rounded-2xl border border-[#24466f] bg-[#091a33] p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[11px] uppercase tracking-[.16em] text-cyan-400">Item {indice+1}</span><strong className="mt-1 block">{item.equipamento}</strong><p className="mt-1 text-xs text-slate-400">{item.quantidade} un. · tabela {moeda(item.preco_tabela)} · desconto {item.desconto_percentual.toLocaleString('pt-BR',{maximumFractionDigits:2})}%</p><p className="mt-1 text-sm font-semibold text-emerald-300">Negociado: {moeda(valorTotal)}</p></div><span className="rounded-full border border-[#24466f] px-2 py-1 text-[11px] text-slate-300">{atual?texto(atual.status_documento)||"RASCUNHO":"Sem proposta"}</span></div>{atual?<Link href={`/crm-app/propostas/${encodeURIComponent(atual.id)}`} className="mt-3 flex items-center justify-between rounded-xl border border-cyan-900 bg-[#061326] p-3"><span><strong className="block text-sm">{texto(atual.numero)||"Proposta comercial"}</strong><span className="text-xs text-slate-400">{moeda(atual.valor)}</span></span><span className="text-xs font-semibold text-cyan-300">Abrir →</span></Link>:<button disabled={processando===item.id} onClick={()=>void gerar(item)} className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300 disabled:opacity-50">{processando===item.id?<Loader2 size={15} className="animate-spin"/>:<FilePlus2 size={15}/>}Gerar proposta deste item</button>}</article>})}</div>}

      <div className="mt-4 rounded-2xl border border-[#24466f] bg-[#061326] p-4"><div className="flex items-center justify-between gap-3"><div><p className="text-xs text-slate-400">Resumo da negociação</p><strong className="text-lg text-emerald-300">{moeda(totalNegociado)}</strong></div><span className="text-xs text-slate-400">{itens.length} item(ns)</span></div></div>

      {!formularioAberto&&!finalizacaoAberta&&!decisaoAberta&&<div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={()=>setFormularioAberto(true)} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-4 py-3 font-semibold text-cyan-300"><Plus size={17}/>Adicionar outro item</button>{itens.length>0&&<button type="button" disabled={processando==="concluir"} onClick={()=>void concluirCadastro()} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-50">{processando==="concluir"?<Loader2 size={17} className="animate-spin"/>:<CheckCircle2 size={17}/>}Concluir e revisar propostas</button>}</div>}

      {decisaoAberta&&<div className="mt-4 rounded-2xl border border-cyan-800 bg-cyan-950/20 p-4"><h3 className="font-bold">Item salvo. O que deseja fazer agora?</h3><p className="mt-1 text-sm text-slate-400">Continue no mesmo processo comercial ou finalize o cadastro dos equipamentos.</p><div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={()=>{setDecisaoAberta(false);setFormularioAberto(true)}} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-4 py-3 font-semibold text-cyan-300"><Plus size={17}/>Cadastrar mais um item</button><button type="button" disabled={processando==="concluir"} onClick={()=>void concluirCadastro()} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-50"><CheckCircle2 size={17}/>Concluir cadastro</button></div></div>}

      {formularioAberto&&<form onSubmit={adicionarItem} className="mt-4 space-y-4 rounded-2xl border border-[#24466f] bg-[#061326] p-4"><div><h3 className="font-bold">Novo item da mesma oportunidade</h3><p className="text-xs text-slate-400">As condições abaixo pertencem somente a este equipamento e à proposta oficial dele.</p></div><div className="grid gap-3 sm:grid-cols-2"><label className="text-xs text-slate-300">Linha<select value={linha} onChange={(e)=>trocarLinha(e.target.value)} className="mt-1 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3">{linhas.map((valor)=><option key={valor}>{valor}</option>)}</select></label><label className="text-xs text-slate-300">Equipamento<select value={equipamentoCodigo} onChange={(e)=>setEquipamentoCodigo(e.target.value)} className="mt-1 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3">{equipamentos.map((item)=><option key={item.codigo} value={item.codigo}>{item.nome_comercial}</option>)}</select></label><Info label="Preço de tabela" valor={moeda(equipamentoSelecionado?.preco_vigente?.preco_cheio)}/><Info label="Configuração" valor={equipamentoSelecionado?.configuracao||"Padrão"}/><Campo name="quantidade" label="Quantidade" type="number" defaultValue="1" required/><Campo name="desconto_percentual" label="Desconto (%)" type="number" defaultValue="0" step="0.01"/><Campo name="condicao_pagamento" label="Condição de pagamento"/><Campo name="prazo_entrega" label="Prazo de entrega"/><Campo name="validade_condicao" label="Validade" type="date"/><Campo name="garantia" label="Garantia"/><Campo name="opcionais" label="Opcionais" classe="sm:col-span-2"/><Campo name="observacoes_comerciais" label="Observações comerciais" classe="sm:col-span-2"/><Campo name="observacoes_tecnicas" label="Observações técnicas" classe="sm:col-span-2"/></div><div className="grid gap-2 sm:grid-cols-2"><button type="button" onClick={()=>setFormularioAberto(false)} className="rounded-xl border border-[#24466f] px-4 py-3">Cancelar</button><button disabled={processando==="novo-item"||!equipamentoSelecionado} className="rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-50">{processando==="novo-item"?"Salvando item...":"Salvar este item"}</button></div></form>}

      {finalizacaoAberta&&<div className="mt-4 rounded-2xl border border-emerald-800 bg-emerald-950/20 p-4"><div className="flex items-center gap-2 text-emerald-300"><Send size={18}/><h3 className="font-bold">Concluir e enviar propostas</h3></div><p className="mt-1 text-sm text-slate-400">Cada item mantém sua proposta Carrier própria. O cliente receberá todas no mesmo e-mail, como PDFs separados.</p><div className="mt-4 rounded-xl border border-[#24466f] bg-[#020817] p-3 text-sm">{itens.map((item)=><div key={item.id} className="flex justify-between gap-3 border-b border-[#16325c] py-2 last:border-0"><span>{item.equipamento} · {item.quantidade} un.</span><span className="text-emerald-300">{moeda((item.preco_tabela*(1-item.desconto_percentual/100))*item.quantidade)}</span></div>)}<div className="mt-2 flex justify-between font-bold"><span>Total</span><span>{moeda(totalNegociado)}</span></div></div><label className="mt-4 block text-xs text-slate-300">Destinatários<textarea value={destinatarios} onChange={(e)=>setDestinatarios(e.target.value)} rows={2} placeholder="compras@cliente.com.br; diretor@cliente.com.br" className="mt-1 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label><label className="mt-3 block text-xs text-slate-300">Mensagem ao cliente<textarea value={mensagemEmail} onChange={(e)=>setMensagemEmail(e.target.value)} rows={3} placeholder="Seguem as propostas comerciais para sua análise." className="mt-1 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3"/></label><div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={()=>setFinalizacaoAberta(false)} className="rounded-xl border border-[#24466f] px-4 py-3">Voltar aos itens</button><button type="button" disabled={processando==="enviar"} onClick={()=>void enviarTodas()} className="flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-50">{processando==="enviar"?<Loader2 size={17} className="animate-spin"/>:<Send size={17}/>}Salvar e enviar todas</button></div></div>}
    </>}
  </section>
}

function Campo({name,label,type="text",defaultValue,step,required=false,classe=""}:{name:string;label:string;type?:string;defaultValue?:string;step?:string;required?:boolean;classe?:string}){return <label className={`text-xs text-slate-300 ${classe}`}>{label}<input name={name} type={type} defaultValue={defaultValue} step={step} required={required} className="mt-1 h-12 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3"/></label>}
function Info({label,valor}:{label:string;valor:string}){return <div className="text-xs text-slate-300">{label}<div className="mt-1 min-h-12 rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 font-semibold text-white">{valor}</div></div>}
