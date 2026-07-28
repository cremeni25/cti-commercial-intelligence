"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { Activity, ArrowLeft, BriefcaseBusiness, Building2, CalendarDays, CheckCircle2, CircleDollarSign, Clock3, Loader2, MapPinned, Plus, RefreshCw, Search, Target } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type ClienteOpcao = { id: string; nome: string; codigo: string }
type ModuloConfig = { titulo: string; endpoint: string; icon: typeof Activity; extrair: (payload: unknown) => Registro[] }

const configs: Record<string, ModuloConfig> = {
  agenda: { titulo: "Agenda comercial", endpoint: "/crm/agenda", icon: CalendarDays, extrair: (p) => ((p as { itens?: Registro[] })?.itens || []) },
  clientes: { titulo: "Clientes", endpoint: "/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", icon: Building2, extrair: (p) => Array.isArray(p) ? p : [] },
  visitas: { titulo: "Visitas", endpoint: "/crm/atividades", icon: MapPinned, extrair: (p) => Array.isArray(p) ? p.filter((i) => String(i.tipo || "").toUpperCase().includes("VISITA")) : [] },
  oportunidades: { titulo: "Oportunidades", endpoint: "/crm/oportunidades", icon: BriefcaseBusiness, extrair: (p) => Array.isArray(p) ? p.filter((i) => String(i.origem || "").toUpperCase() === "CRM_APP") : [] },
  pipeline: { titulo: "Pipeline", endpoint: "/crm/oportunidades", icon: CircleDollarSign, extrair: (p) => Array.isArray(p) ? p.filter((i) => String(i.origem || "").toUpperCase() === "CRM_APP") : [] },
  atividades: { titulo: "Atividades", endpoint: "/crm/atividades", icon: Activity, extrair: (p) => Array.isArray(p) ? p : [] },
}

const produtosPorLinha: Record<string, string[]> = {
  TRAILER: ["X4-7500", "X4-7700", "Vector HE19"],
  "DIESEL TRUCK": ["Supra 1150", "Supra 850", "Supra 750"],
  "DIRECT DRIVE": ["CM600", "CM500", "CM400", "CM280", "Xarios 350", "Xarios 600", "D7", "D7 AE"],
}

function texto(valor: unknown): string {
  if (valor == null) return ""
  if (typeof valor === "string" || typeof valor === "number") return String(valor)
  if (typeof valor === "object") {
    const o = valor as Registro
    return texto(o.nome || o.razao_social || o.nome_fantasia || o.empresa || o.codigo || o.id)
  }
  return ""
}

function codigoEstavel(nome: string): string {
  let hash = 0
  for (let i = 0; i < nome.length; i += 1) hash = ((hash << 5) - hash + nome.charCodeAt(i)) | 0
  return `CLI-${Math.abs(hash).toString().padStart(8, "0").slice(0, 8)}`
}

function clienteDe(item: Registro): ClienteOpcao | null {
  const nome = texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente).trim()
  if (!nome) return null
  const codigo = texto(item.codigo || item.codigo_cliente || item.id).trim() || codigoEstavel(nome)
  const id = texto(item.id || item.cliente_id || item.uuid).trim() || nome
  return { id, nome, codigo }
}

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 })

export default function CrmModuloPage() {
  const params = useParams<{ modulo: string[] }>()
  const { usuario } = useAuth()
  const segmentos = Array.isArray(params.modulo) ? params.modulo : [String(params.modulo || "")]
  const slug = segmentos[0]
  const novo = segmentos[1] === "nova"
  const config = configs[slug] || configs.atividades
  const Icon = config.icon

  const [registros, setRegistros] = useState<Registro[]>([])
  const [clientes, setClientes] = useState<ClienteOpcao[]>([])
  const [clienteBusca, setClienteBusca] = useState("")
  const [clienteSelecionado, setClienteSelecionado] = useState<ClienteOpcao | null>(null)
  const [linhas, setLinhas] = useState<string[]>([])
  const [equipamentos, setEquipamentos] = useState<string[]>([])
  const [valorEstimado, setValorEstimado] = useState(0)
  const [probabilidade, setProbabilidade] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [busca, setBusca] = useState("")

  const api = useCallback((endpoint: string, init?: RequestInit) => fetch(`/api/crm-proxy${endpoint}`, { ...init, cache: "no-store" }), [])

  const carregar = useCallback(async () => {
    setCarregando(true); setErro("")
    try {
      const [resposta, clientesResposta] = await Promise.all([api(config.endpoint), api("/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO")])
      if (!resposta.ok) throw new Error(`Falha ${resposta.status}`)
      setRegistros(config.extrair(await resposta.json()))
      if (clientesResposta.ok) {
        const dados = await clientesResposta.json()
        const opcoes = (Array.isArray(dados) ? dados : []).map(clienteDe).filter(Boolean) as ClienteOpcao[]
        setClientes(opcoes.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
      }
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível carregar os dados deste módulo.") }
    finally { setCarregando(false) }
  }, [api, config])

  useEffect(() => { void carregar() }, [carregar])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return termo ? registros.filter((item) => JSON.stringify(item).toLowerCase().includes(termo)) : registros
  }, [busca, registros])

  const sugestoesClientes = useMemo(() => {
    const termo = clienteBusca.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || clienteSelecionado) return []
    return clientes.filter((c) => `${c.nome} ${c.codigo}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 12)
  }, [clienteBusca, clienteSelecionado, clientes])

  const equipamentosDisponiveis = useMemo(() => [...new Set(linhas.flatMap((linha) => produtosPorLinha[linha] || []))], [linhas])

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const userId = String(usuario?.id || usuario?.auth_id || "")
    if (!clienteSelecionado || !userId) { setErro("Selecione um cliente da lista e confirme o usuário autenticado."); setSalvando(false); return }

    let endpoint = "/crm/atividades"
    let payload: Record<string, unknown> = {
      cliente_id: clienteSelecionado.id, usuario_id: userId,
      tipo: slug === "visitas" ? "VISITA" : String(dados.get("tipo") || "ATIVIDADE"),
      titulo: String(dados.get("titulo") || "").trim(), descricao: String(dados.get("descricao") || "").trim() || null,
      data: String(dados.get("data") || "") || null, horario: String(dados.get("horario") || "") || null, status: "PENDENTE",
    }
    if (slug === "oportunidades") {
      endpoint = "/crm/oportunidades"
      payload = {
        cliente_id: clienteSelecionado.id, responsavel_id: userId, titulo: String(dados.get("titulo") || "").trim(),
        descricao: String(dados.get("descricao") || "").trim() || null, valor_estimado: valorEstimado, probabilidade,
        data_fechamento_prevista: String(dados.get("data") || "") || null, linha_equipamentos: linhas.join(", "), equipamento: equipamentos.join(", "),
        municipio: String(dados.get("municipio") || "").trim() || null, estado: String(dados.get("estado") || "").trim() || null,
        origem: "CRM_APP", status: "OPORTUNIDADE",
      }
    }
    if (!payload.titulo) { setErro("Informe o título ou objetivo do registro."); setSalvando(false); return }
    try {
      const resposta = await api(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(detalhe.detail || `Falha ${resposta.status}`))
      evento.currentTarget.reset(); setClienteBusca(""); setClienteSelecionado(null); setLinhas([]); setEquipamentos([]); setValorEstimado(0); setProbabilidade(0)
      setSucesso(slug === "oportunidades" ? "Oportunidade registrada e inserida no pipeline." : "Registro salvo com sucesso.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível salvar o registro.") }
    finally { setSalvando(false) }
  }

  async function concluir(id: string) {
    const resposta = await api(`/crm/atividades/${id}/concluir`, { method: "PUT" })
    if (!resposta.ok) setErro("Não foi possível concluir a atividade."); else await carregar()
  }

  return <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
    <header className="sticky top-0 z-30 border-b border-[#16325c] bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4"><div className="mx-auto flex w-full max-w-[94vw] items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20} /></Link><div className="min-w-0 flex-1"><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="truncate text-lg font-bold sm:text-2xl">{novo ? `Novo registro — ${config.titulo}` : config.titulo}</h1></div><button onClick={() => void carregar()} className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><RefreshCw size={19} /></button></div></header>
    <div className="mx-auto w-full max-w-[94vw] px-4 py-4 sm:px-6 sm:py-6">
      <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-4 shadow-xl sm:p-6"><div className="flex items-center gap-3"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300"><Icon size={24} /></span><div><p className="text-sm text-slate-400">Operação em campo</p><p className="text-xl font-bold">{config.titulo}</p></div></div></section>
      {erro && <div className="mt-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
      {sucesso && <div className="mt-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">{sucesso}</div>}
      {novo ? <form onSubmit={salvar} className="mt-4 grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:grid-cols-2 sm:p-6">
        <label className="relative"><span className="mb-2 block text-sm text-slate-300">Cliente</span><input value={clienteBusca} onChange={(e) => { setClienteBusca(e.target.value); setClienteSelecionado(null) }} placeholder="Digite ao menos 2 letras" autoComplete="off" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 outline-none focus:border-cyan-500" />{clienteBusca.length >= 2 && !clienteSelecionado && sugestoesClientes.length === 0 && <span className="mt-2 block text-xs text-amber-300">Nenhum cliente localizado com este texto.</span>}{sugestoesClientes.length > 0 && <div className="absolute z-40 mt-2 max-h-72 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoesClientes.map((c) => <button type="button" key={`${c.id}-${c.codigo}`} onClick={() => { setClienteSelecionado(c); setClienteBusca(c.nome) }} className="block w-full border-b border-[#16325c] px-4 py-3 text-left last:border-0"><strong className="block">{c.nome}</strong><span className="text-xs text-slate-400">Código CTI: {c.codigo}</span></button>)}</div>}{clienteSelecionado && <span className="mt-2 block text-xs text-emerald-300">Cliente selecionado • código {clienteSelecionado.codigo}</span>}</label>
        <Campo name="titulo" label={slug === "visitas" ? "Objetivo da visita" : "Título"} required />
        {slug === "oportunidades" ? <>
          <label><span className="mb-2 block text-sm text-slate-300">Valor estimado</span><input inputMode="numeric" value={valorEstimado ? moeda.format(valorEstimado) : ""} onChange={(e) => setValorEstimado(Number(e.target.value.replace(/\D/g, "")))} placeholder="R$ 0,00" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 outline-none focus:border-cyan-500" /></label>
          <label><span className="mb-2 block text-sm text-slate-300">Probabilidade</span><input inputMode="numeric" value={probabilidade ? `${probabilidade}%` : ""} onChange={(e) => setProbabilidade(Math.min(100, Number(e.target.value.replace(/\D/g, ""))))} placeholder="0%" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 outline-none focus:border-cyan-500" /></label>
          <SelecaoMultipla titulo="Linhas de produto Carrier" opcoes={Object.keys(produtosPorLinha)} selecionados={linhas} alterar={(valor) => { setLinhas(valor); setEquipamentos((atuais) => atuais.filter((item) => valor.some((linha) => produtosPorLinha[linha]?.includes(item)))) }} />
          <SelecaoMultipla titulo="Equipamentos Carrier" opcoes={equipamentosDisponiveis} selecionados={equipamentos} alterar={setEquipamentos} />
          <Campo name="municipio" label="Município" /><Campo name="estado" label="UF" /><Campo name="data" label="Fechamento previsto" type="date" />
        </> : <><Campo name="tipo" label="Tipo" defaultValue={slug === "visitas" ? "VISITA" : "FOLLOW_UP"} /><Campo name="data" label="Data" type="date" /><Campo name="horario" label="Horário" type="time" /></>}
        <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição / resultado esperado</span><textarea name="descricao" rows={5} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3 outline-none focus:border-cyan-500" /></label>
        <button disabled={salvando} className="sm:col-span-2 inline-flex min-h-13 items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-5 font-bold text-slate-950 disabled:opacity-60">{salvando ? <Loader2 className="animate-spin" size={20} /> : <CheckCircle2 size={20} />} Salvar no CTI</button>
      </form> : <section className="mt-4"><div className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} /><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar neste módulo" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4 outline-none focus:border-cyan-500" /></div>{carregando ? <div className="grid min-h-48 place-items-center"><Loader2 className="animate-spin text-cyan-300" /></div> : filtrados.length === 0 ? <div className="mt-4 rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum registro encontrado.</div> : <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{filtrados.map((item, indice) => <Card key={String(item.id || indice)} slug={slug} item={item} concluir={concluir} />)}</div>}</section>}
    </div>
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 backdrop-blur"><div className="mx-auto grid max-w-4xl grid-cols-4 gap-2"><Nav href="/crm-app" label="Início" icon={Building2} /><Nav href="/crm-app/agenda" label="Agenda" icon={CalendarDays} /><Nav href="/crm-app/oportunidades" label="Negócios" icon={Target} /><Nav href="/crm-app/atividades/nova" label="Nova interação" icon={Plus} destaque /></div></nav>
  </main>
}

function Campo({ name, label, type = "text", required = false, defaultValue }: { name: string; label: string; type?: string; required?: boolean; defaultValue?: string }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} defaultValue={defaultValue} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 outline-none focus:border-cyan-500" /></label> }
function SelecaoMultipla({ titulo, opcoes, selecionados, alterar }: { titulo: string; opcoes: string[]; selecionados: string[]; alterar: (valor: string[]) => void }) { return <fieldset className="rounded-2xl border border-[#24466f] p-4"><legend className="px-2 text-sm text-slate-300">{titulo}</legend><div className="grid gap-2 sm:grid-cols-2">{opcoes.length === 0 ? <span className="text-sm text-slate-500">Selecione primeiro uma linha.</span> : opcoes.map((opcao) => <label key={opcao} className="flex items-center gap-2 rounded-xl bg-[#020817] px-3 py-2"><input type="checkbox" checked={selecionados.includes(opcao)} onChange={(e) => alterar(e.target.checked ? [...selecionados, opcao] : selecionados.filter((item) => item !== opcao))} /><span>{opcao}</span></label>)}</div></fieldset> }
function Card({ slug, item, concluir }: { slug: string; item: Registro; concluir: (id: string) => void }) { const titulo = texto(item.titulo || item.nome || item.razao_social || item.oportunidade_titulo) || "Registro CTI"; const subtitulo = texto(item.cliente_nome || item.cliente_id || item.municipio || item.empresa || item.tipo || item.etapa); const status = texto(item.situacao || item.status || item.etapa) || "ATIVO"; const data = texto(item.data || item.data_fechamento_prevista || item.ultima_movimentacao); return <article className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4 shadow-lg sm:p-5"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate font-semibold sm:text-lg">{titulo}</h2><p className="mt-1 truncate text-sm text-slate-400">{subtitulo}</p></div><span className="rounded-full border border-cyan-900 bg-cyan-950/40 px-2.5 py-1 text-[10px] font-semibold text-cyan-300">{status}</span></div>{data && <p className="mt-4 flex items-center gap-2 text-xs text-slate-400"><Clock3 size={14} /> {data.slice(0, 16).replace("T", " ")}</p>}{slug === "pipeline" && <p className="mt-3 text-lg font-bold text-emerald-300">{moeda.format(Number(item.valor_estimado || 0))}</p>}{["agenda", "atividades", "visitas"].includes(slug) && status !== "CONCLUIDA" && item.id ? <button onClick={() => concluir(String(item.id))} className="mt-4 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-emerald-800 bg-emerald-950/30 text-sm text-emerald-300"><CheckCircle2 size={16} /> Concluir</button> : null}</article> }
function Nav({ href, label, icon: Icon, destaque = false }: { href: string; label: string; icon: typeof Activity; destaque?: boolean }) { return <Link href={href} className={`flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-[10px] ${destaque ? "bg-cyan-500 font-semibold text-slate-950" : "text-slate-400"}`}><Icon size={19} /><span>{label}</span></Link> }
