"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { FileText } from "lucide-react"
import { useI18n } from "@/core/i18n"

type Segmento = { codigo:string; segmento:string; mercado:number; carrier:number; carrier_percentual_observado:number; tk:number; nacional:number; usado_concorrente:number; usado_carrier:number; sem_contato:number; nao_classificado:number; nao_participou:number; q1:number; q2:number; q2_vs_q1_percentual:number|null }
type Mensal = { mes:string; competencia:string; trailer:number; diesel_truck:number; direct_drive:number; total:number }
type Territorio = { ddd:string; mercado:number; trailer:number; diesel_truck:number; direct_drive:number; responsavel:string }
type Prioridade = { prioridade:string; cliente:string; score_transparente:number; mercado:number; nao_carrier:number; carrier:number; nao_participou:number; sem_contato:number; tk:number; nacional:number; preco:number; relacionamento:number; gap_tecnico:number; leitura_sugerida:string; criterio_score:string }
type Implementadora = { implementadora:string; mercado_elegivel:number; trailer:number; diesel_truck:number; direct_drive:number; leitura:string }
type Tema = { tema:string; ocorrencias:number; clientes_unicos:number; observacoes_unicas:number; leitura_comercial:string; uso_no_cti:string }
type ImplementadoraForaEscopo = { implementadora:string; registros:number; percentual_mercado_anfir:number; variantes_fonte:Array<{nome:string;registros:number}> }
type MercadoViena = { mercado_anfir_total:number; mercado_fora_escopo_comercial:number; mercado_disputavel_viena:number; percentual_fora_escopo:number; percentual_disputavel:number; implementadoras_fora_escopo:ImplementadoraForaEscopo[]; regra:string }
type Payload = {
  metadata:{nome_contrato:string;competencia:string;natureza:string;market_share_oficial:boolean;escopo_usuario?:{usuario?:string};denominador_comercial?:string}
  mercado_viena:MercadoViena
  inteligencia_viena:{mercado_elegivel:number;carrier_observada:number;carrier_presenca_percentual:number;sem_contato:number;nao_participamos_proposta:number;dados_status_a_qualificar:number;q1:number;q2:number;q2_vs_q1_percentual:number|null;segmentos:Segmento[];mensal:Mensal[];territorio:Territorio[];leituras_estrategicas:string[]}
  oportunidades_prioritarias:Prioridade[]
  implementadoras_mercado:Implementadora[]
  inteligencia_observacoes:{temas:Tema[];registros_elegiveis:number;com_observacao_util:number;cobertura_observacoes_percentual:number;sem_observacao_util:number;regra:string}
}

type Tab = "viena"|"prioridades"|"implementadoras"|"observacoes"
type DrillArgs = { titulo:string; campo?:string; valor?:string; familia?:string }

const FAMILY_SLUG:Record<string,string>={TR:"trailer",DT:"diesel-truck",DD:"direct-drive"}
const BASE_DRILL={camada:"anfir",contexto:"viena-sp",periodo:"PERSONALIZADO",inicio:"2026-01-01",fim:"2026-12-31",mercado:"DISPUTAVEL_VIENA"}

function drill({titulo,campo,valor,familia}:DrillArgs){
  const q=new URLSearchParams(BASE_DRILL)
  q.set("titulo",titulo)
  q.set("subtitulo","Registros individualizados do mercado comercial efetivamente disputável pela Viena na fotografia ANFIR 2026.")
  if(campo)q.set("campo",campo)
  if(valor)q.set("valor",valor)
  if(familia)q.set("familia",familia)
  return `/detalhamento?${q.toString()}`
}

export default function AnfirWorkbookPanel({responsavelId}:{responsavelId?:string}){
  const{formatNumber}=useI18n()
  const[data,setData]=useState<Payload|null>(null)
  const[loading,setLoading]=useState(true)
  const[error,setError]=useState(false)
  const[tab,setTab]=useState<Tab>("viena")

  useEffect(()=>{
    let active=true
    queueMicrotask(()=>{
      if(!active)return
      setLoading(true);setError(false)
      const qs=responsavelId?`?responsavel_id=${encodeURIComponent(responsavelId)}`:""
      fetch(`/api/cti/analytics/anfir-workbook-2026${qs}`,{cache:"no-store"})
        .then(async response=>{if(!response.ok)throw new Error(String(response.status));return response.json() as Promise<Payload>})
        .then(payload=>{if(active)setData(payload)})
        .catch(()=>{if(active)setError(true)})
        .finally(()=>{if(active)setLoading(false)})
    })
    return()=>{active=false}
  },[responsavelId])

  if(loading)return <section className="rounded-3xl border border-[#17304d] bg-[#071427] p-6 text-sm text-slate-400">Carregando leitura ANFIR 2026...</section>
  if(error||!data)return <section className="rounded-3xl border border-amber-700/60 bg-amber-950/10 p-6 text-sm text-amber-200">Não foi possível carregar a leitura ANFIR 2026.</section>

  const v=data.inteligencia_viena,o=data.inteligencia_observacoes,m=data.mercado_viena

  return <section className="rounded-3xl border border-cyan-500/30 bg-[#061126] p-5 sm:p-6">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">{data.metadata.competencia} · Carrier/JOV</p>
        <h2 className="mt-2 text-2xl font-bold">ANFIR 2026 · Leitura estratégica Viena</h2>
        <p className="mt-2 max-w-5xl text-sm text-slate-400">Contrato funcional da auditoria Carrier/JOV. Esta leitura é fixa em 2026 e respeita o escopo comercial do usuário selecionado.</p>
        {data.metadata.escopo_usuario?.usuario&&<p className="mt-2 text-xs font-semibold text-emerald-300">Visão comercial: {data.metadata.escopo_usuario.usuario}</p>}
        <p className="mt-2 text-xs text-cyan-300">A ANFIR total permanece visível para leitura de mercado. Indicadores comerciais, presença Carrier e competitividade usam somente o mercado efetivamente disputável pela Viena.</p>
      </div>
      <Link href="/dashboard/anfir-relatorio" className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/50 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-500/20"><FileText size={16}/>Gerar relatório / PDF</Link>
    </header>

    <div className="mt-5 flex flex-wrap gap-2">
      {([["viena","Inteligência Viena"],["prioridades","Oportunidades Prioritárias"],["implementadoras","Implementadoras Mercado"],["observacoes","Inteligência Observações"]] as [Tab,string][]).map(([key,label])=><button key={key} onClick={()=>setTab(key)} className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${tab===key?"bg-cyan-400 text-slate-950":"border border-[#29456f] bg-[#09182e] text-slate-300 hover:border-cyan-500"}`}>{label}</button>)}
    </div>

    {tab==="viena"&&<div className="mt-6 space-y-6">
      <div className="grid gap-3 lg:grid-cols-3">
        <Metric title="Mercado ANFIR observado" value={formatNumber(m.mercado_anfir_total)} detail="Fotografia total do mercado no escopo selecionado."/>
        <Metric title="Mercado fora do escopo comercial" value={`${formatNumber(m.mercado_fora_escopo_comercial)} · ${m.percentual_fora_escopo.toFixed(1)}%`} detail="Fibra West, HiFlex e Planalto: permanecem visíveis, mas não entram no denominador comercial Viena."/>
        <Metric title="Mercado real disputável Viena" value={`${formatNumber(m.mercado_disputavel_viena)} · ${m.percentual_disputavel.toFixed(1)}%`} detail="Base efetiva usada nos indicadores de presença, competitividade e oportunidade."/>
      </div>

      <div className="rounded-2xl border border-amber-500/30 bg-amber-950/10 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[.16em] text-amber-300">Mercado ANFIR não atendível pela regra comercial atual</p><p className="mt-1 text-xs leading-5 text-amber-100/70">{m.regra}</p></div>
          <div className="flex flex-wrap gap-2">{m.implementadoras_fora_escopo.map(item=><span key={item.implementadora} className="rounded-lg border border-amber-500/30 bg-[#111827] px-3 py-2 text-xs text-amber-100"><strong>{item.implementadora}</strong> · {formatNumber(item.registros)}</span>)}</div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Metric title="Presença Carrier no mercado disputável" value={`${formatNumber(v.carrier_observada)} · ${v.carrier_presenca_percentual.toFixed(1)}%`} href={drill({titulo:"Presença Carrier observada · mercado disputável Viena · ANFIR 2026",campo:"categoria",valor:"CARRIER"})}/>
        <Metric title="Sem contato" value={formatNumber(v.sem_contato)} href={drill({titulo:"Sem contato · mercado disputável Viena · ANFIR 2026",campo:"categoria",valor:"SEM_CONTATO"})}/>
        <Metric title="Não participamos da proposta" value={formatNumber(v.nao_participamos_proposta)} href={drill({titulo:"Não participamos · mercado disputável Viena · ANFIR 2026",campo:"causa",valor:"COBERTURA_COMERCIAL"})}/>
        <Metric title="Status a qualificar" value={formatNumber(v.dados_status_a_qualificar)} href={drill({titulo:"Status a qualificar · mercado disputável Viena · ANFIR 2026",campo:"categoria",valor:"NAO_CLASSIFICADO"})}/>
        <Metric title="Q2 vs Q1" value={`${v.q2_vs_q1_percentual&&v.q2_vs_q1_percentual>0?"+":""}${Number(v.q2_vs_q1_percentual||0).toFixed(1)}%`} detail={`${formatNumber(v.q2)} × ${formatNumber(v.q1)}`} actions={[{label:`Q2 · ${formatNumber(v.q2)}`,href:drill({titulo:"Mercado disputável Viena · 2º trimestre",campo:"trimestre",valor:"2026-Q2"})},{label:`Q1 · ${formatNumber(v.q1)}`,href:drill({titulo:"Mercado disputável Viena · 1º trimestre",campo:"trimestre",valor:"2026-Q1"})}]}/>
      </div>

      <Table headers={["Segmento","Mercado disputável","Carrier","Carrier %","Sem contato","Não participou","Q2 vs Q1"]} rows={v.segmentos.map(s=>{const familia=FAMILY_SLUG[s.codigo];return [cellLink(s.segmento,drill({titulo:`${s.segmento} · mercado disputável ANFIR 2026`,familia})),cellLink(formatNumber(s.mercado),drill({titulo:`${s.segmento} · mercado disputável ANFIR 2026`,familia})),cellLink(formatNumber(s.carrier),drill({titulo:`${s.segmento} · Carrier observada`,familia,campo:"categoria",valor:"CARRIER"})),`${s.carrier_percentual_observado.toFixed(1)}%`,cellLink(formatNumber(s.sem_contato),drill({titulo:`${s.segmento} · Sem contato`,familia,campo:"categoria",valor:"SEM_CONTATO"})),cellLink(formatNumber(s.nao_participou),drill({titulo:`${s.segmento} · Não participamos da proposta`,familia,campo:"causa",valor:"COBERTURA_COMERCIAL"})),s.q2_vs_q1_percentual===null?"—":`${s.q2_vs_q1_percentual>0?"+":""}${s.q2_vs_q1_percentual.toFixed(1)}%`]})}/>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="Evolução mensal · mercado disputável 2026"><Table compact headers={["Mês","Trailer","Diesel Truck","Direct Drive","Total"]} rows={v.mensal.map(mes=>[cellLink(mes.mes,drill({titulo:`${mes.mes} 2026 · mercado disputável`,campo:"mes",valor:mes.competencia})),cellLink(formatNumber(mes.trailer),drill({titulo:`${mes.mes} 2026 · Trailer`,campo:"mes",valor:mes.competencia,familia:"trailer"})),cellLink(formatNumber(mes.diesel_truck),drill({titulo:`${mes.mes} 2026 · Diesel Truck`,campo:"mes",valor:mes.competencia,familia:"diesel-truck"})),cellLink(formatNumber(mes.direct_drive),drill({titulo:`${mes.mes} 2026 · Direct Drive`,campo:"mes",valor:mes.competencia,familia:"direct-drive"})),cellLink(formatNumber(mes.total),drill({titulo:`${mes.mes} 2026 · total disputável`,campo:"mes",valor:mes.competencia}))])}/></Card>
        <Card title="Território por DDD · mercado disputável"><Table compact headers={["DDD","Mercado","Trailer","Diesel Truck","Direct Drive","Responsável"]} rows={v.territorio.map(d=>[cellLink(d.ddd,drill({titulo:`DDD ${d.ddd} · mercado disputável ANFIR 2026`,campo:"ddd",valor:d.ddd})),cellLink(formatNumber(d.mercado),drill({titulo:`DDD ${d.ddd} · mercado disputável`,campo:"ddd",valor:d.ddd})),cellLink(formatNumber(d.trailer),drill({titulo:`DDD ${d.ddd} · Trailer`,campo:"ddd",valor:d.ddd,familia:"trailer"})),cellLink(formatNumber(d.diesel_truck),drill({titulo:`DDD ${d.ddd} · Diesel Truck`,campo:"ddd",valor:d.ddd,familia:"diesel-truck"})),cellLink(formatNumber(d.direct_drive),drill({titulo:`DDD ${d.ddd} · Direct Drive`,campo:"ddd",valor:d.ddd,familia:"direct-drive"})),d.responsavel])}/></Card>
      </div>
      <Card title="Leituras estratégicas — mercado disputável"><ol className="space-y-3">{v.leituras_estrategicas.map((r,i)=><li key={r} className="flex gap-3 text-sm leading-6 text-slate-300"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-500/15 text-xs font-bold text-cyan-300">{i+1}</span><span>{r}</span></li>)}</ol></Card>
    </div>}

    {tab==="prioridades"&&<div className="mt-6"><Table headers={["Prioridade","Cliente","Score transparente","Mercado","Não Carrier","Carrier","Não participou","Sem contato","Preço","Relacionamento","Gap técnico","Leitura sugerida"]} rows={data.oportunidades_prioritarias.map(r=>[r.prioridade,cellLink(r.cliente,drill({titulo:`Cliente · ${r.cliente} · ANFIR 2026`,campo:"empresa",valor:r.cliente})),formatNumber(r.score_transparente),formatNumber(r.mercado),formatNumber(r.nao_carrier),formatNumber(r.carrier),formatNumber(r.nao_participou),formatNumber(r.sem_contato),formatNumber(r.preco),formatNumber(r.relacionamento),formatNumber(r.gap_tecnico),r.leitura_sugerida])}/></div>}

    {tab==="implementadoras"&&<div className="mt-6 space-y-5"><div className="rounded-xl border border-amber-500/30 bg-amber-950/10 p-4 text-xs text-amber-100/80"><strong>Fora do denominador comercial:</strong> Fibra West, HiFlex e Planalto aparecem no bloco separado da Inteligência Viena e não compõem o ranking abaixo.</div><Table headers={["Implementadora normalizada","Mercado disputável","Trailer","Diesel Truck","Direct Drive","Leitura sugerida"]} rows={data.implementadoras_mercado.map(r=>[cellLink(r.implementadora,drill({titulo:`Implementadora · ${r.implementadora} · mercado disputável ANFIR 2026`,campo:"implementadora",valor:r.implementadora})),cellLink(formatNumber(r.mercado_elegivel),drill({titulo:`${r.implementadora} · mercado disputável ANFIR`,campo:"implementadora",valor:r.implementadora})),cellLink(formatNumber(r.trailer),drill({titulo:`${r.implementadora} · Trailer`,campo:"implementadora",valor:r.implementadora,familia:"trailer"})),cellLink(formatNumber(r.diesel_truck),drill({titulo:`${r.implementadora} · Diesel Truck`,campo:"implementadora",valor:r.implementadora,familia:"diesel-truck"})),cellLink(formatNumber(r.direct_drive),drill({titulo:`${r.implementadora} · Direct Drive`,campo:"implementadora",valor:r.implementadora,familia:"direct-drive"})),r.leitura])}/></div>}

    {tab==="observacoes"&&<div className="mt-6 space-y-5">
      <div className="grid gap-3 sm:grid-cols-4"><Metric title="Mercado disputável analisado" value={formatNumber(o.registros_elegiveis)} href={drill({titulo:"Registros disputáveis · Inteligência de Observações"})}/><Metric title="Com observação útil" value={formatNumber(o.com_observacao_util)} href={drill({titulo:"Com observação útil · ANFIR 2026",campo:"observacao",valor:"COM_OBSERVACAO"})}/><Metric title="Cobertura de observações" value={`${o.cobertura_observacoes_percentual.toFixed(1)}%`} href={drill({titulo:"Registros com observação útil · ANFIR 2026",campo:"observacao",valor:"COM_OBSERVACAO"})}/><Metric title="Sem observação útil" value={formatNumber(o.sem_observacao_util)} href={drill({titulo:"Sem observação útil · ANFIR 2026",campo:"observacao",valor:"SEM_OBSERVACAO"})}/></div>
      <Table headers={["Tema","Ocorrências","Clientes únicos","Observações únicas","Leitura comercial","Uso no CTI"]} rows={o.temas.map(r=>[cellLink(r.tema,drill({titulo:`Tema · ${r.tema} · ANFIR 2026`,campo:"tema",valor:r.tema})),cellLink(formatNumber(r.ocorrencias),drill({titulo:`Tema · ${r.tema} · ocorrências`,campo:"tema",valor:r.tema})),formatNumber(r.clientes_unicos),formatNumber(r.observacoes_unicas),r.leitura_comercial,r.uso_no_cti])}/>
      <div className="rounded-xl border border-cyan-900 bg-cyan-950/10 p-4 text-xs text-cyan-100/80"><strong>Regra:</strong> {o.regra}</div>
    </div>}
  </section>
}

function cellLink(label:string,href:string){return <Link href={href} className="font-semibold text-cyan-300 underline-offset-4 hover:text-cyan-200 hover:underline">{label}</Link>}
function Metric({title,value,detail,href,actions}:{title:string;value:string;detail?:string;href?:string;actions?:Array<{label:string;href:string}>}){const body=<><p className="text-[11px] uppercase tracking-wide text-slate-500">{title}</p><p className="mt-2 text-xl font-bold text-cyan-300">{value}</p>{detail&&<p className="mt-1 text-xs text-slate-500">{detail}</p>}{href&&<p className="mt-3 text-[11px] text-cyan-400">Clique para detalhar</p>}</>;return <div className="rounded-xl border border-[#193354] bg-[#08162d] p-4">{href?<Link href={href} className="block rounded-lg outline-none transition hover:bg-[#0b1d38] focus:ring-2 focus:ring-cyan-500/60">{body}</Link>:body}{actions&&<div className="mt-3 flex flex-wrap gap-2">{actions.map(action=><Link key={action.href} href={action.href} className="rounded-lg border border-cyan-700/60 px-2.5 py-1.5 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-500/10">{action.label}</Link>)}</div>}</div>}
function Card({title,children}:{title:string;children:React.ReactNode}){return <div className="rounded-2xl border border-[#17304d] bg-[#071427] p-4"><h3 className="mb-3 font-semibold">{title}</h3>{children}</div>}
function Table({headers,rows,compact=false}:{headers:string[];rows:React.ReactNode[][];compact?:boolean}){return <div className="overflow-x-auto rounded-2xl border border-[#17304d] bg-[#071427]"><table className={`w-full text-left ${compact?"min-w-[650px]":"min-w-[950px]"}`}><thead className="bg-[#091a33] text-[11px] uppercase text-slate-400"><tr>{headers.map(h=><th key={h} className="px-3 py-3 font-semibold">{h}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i} className="border-t border-[#13203f] text-sm text-slate-300 hover:bg-[#08162d]/70">{row.map((cell,j)=><td key={`${i}-${j}`} className="px-3 py-3 align-top">{cell}</td>)}</tr>)}</tbody></table></div>}
