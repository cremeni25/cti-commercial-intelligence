"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { Archive, ArrowLeft, CalendarClock, CheckCircle2, CircleAlert, ClipboardCheck, Eye, Filter, Loader2, Pencil, Plus, RefreshCw, X } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type ClienteOpcao = { id: string; nome: string }
type Atividade = {
  id: string; titulo: string; tipo: string; status: string; data: string; horario: string
  clienteId: string; cliente: string; oportunidadeId: string; descricao: string
  arquivada: boolean; motivoArquivamento: string
}

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["atividades", "itens", "dados", "resultado"]) if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
  }
  return []
}
function normalizarStatus(valor: unknown): string { return texto(valor).toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") || "PENDENTE" }
function concluida(status: string): boolean { return ["CONCLUIDA", "CONCLUIDO", "REALIZADA", "FINALIZADA"].includes(status) }
function cancelada(status: string): boolean { return ["CANCELADA", "CANCELADO"].includes(status) }
function hojeIso(): string { return new Date().toISOString().slice(0, 10) }

export default function AtividadesPage() {
  const { usuario } = useAuth()
  const master = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [atividades, setAtividades] = useState<Atividade[]>([])
  const [clientes, setClientes] = useState<ClienteOpcao[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [statusFiltro, setStatusFiltro] = useState("TODAS")
  const [tipoFiltro, setTipoFiltro] = useState("TODOS")
  const [busca, setBusca] = useState("")
  const [mostrarArquivadas, setMostrarArquivadas] = useState(false)
  const [editando, setEditando] = useState<Atividade | null>(null)
  const [arquivando, setArquivando] = useState<Atividade | null>(null)
  const [encerrando, setEncerrando] = useState<Atividade | null>(null)
  const [detalhando, setDetalhando] = useState<Atividade | null>(null)
  const [salvando, setSalvando] = useState(false)

  function normalizar(item: Registro): Atividade {
    return {
      id: texto(item.id || item.atividade_id), titulo: texto(item.titulo || item.assunto || item.descricao) || "Atividade comercial",
      tipo: texto(item.tipo || item.tipo_atividade).toUpperCase() || "ATIVIDADE", status: normalizarStatus(item.status),
      data: texto(item.data || item.data_atividade || item.inicio).slice(0, 10), horario: texto(item.horario || item.hora || item.inicio).slice(11, 16),
      clienteId: texto(item.cliente_id), cliente: texto(item.cliente_nome || item.cliente), oportunidadeId: texto(item.oportunidade_id),
      descricao: texto(item.descricao), arquivada: Boolean(item.arquivado_em), motivoArquivamento: texto(item.motivo_arquivamento),
    }
  }

  async function carregar(arquivadas = mostrarArquivadas) {
    setCarregando(true); setErro("")
    try {
      const endpoint = arquivadas ? `/api/crm-proxy/crm/atividades/arquivadas?usuario_id=${encodeURIComponent(usuario?.id || "")}` : "/api/crm-proxy/crm/atividades"
      const [atividadesResposta, clientesResposta] = await Promise.all([
        fetch(endpoint, { cache: "no-store" }), fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }),
      ])
      const payload = await atividadesResposta.json().catch(() => ([]))
      if (!atividadesResposta.ok) throw new Error(texto((payload as Registro).detail) || `Falha ${atividadesResposta.status}`)
      setAtividades(lista(payload).map(normalizar).filter((item) => item.id).sort((a, b) => `${b.data}${b.horario}`.localeCompare(`${a.data}${a.horario}`)))
      const clientesPayload = clientesResposta.ok ? await clientesResposta.json().catch(() => []) : []
      setClientes(lista(clientesPayload).map((item) => ({ id: texto(item.id || item.cliente_id), nome: texto(item.nome || item.razao_social || item.nome_fantasia || item.cliente) })).filter((item) => item.id && item.nome).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as atividades.") }
    finally { setCarregando(false) }
  }

  useEffect(() => { if (!mostrarArquivadas || usuario?.id) void carregar(mostrarArquivadas) }, [mostrarArquivadas, usuario?.id])

  const resumo = useMemo(() => {
    const hoje = hojeIso()
    return {
      pendentes: atividades.filter((a) => !a.arquivada && !concluida(a.status) && !cancelada(a.status)).length,
      concluidas: atividades.filter((a) => !a.arquivada && concluida(a.status)).length,
      atrasadas: atividades.filter((a) => !a.arquivada && !concluida(a.status) && !cancelada(a.status) && a.data && a.data < hoje).length,
    }
  }, [atividades])

  const tipos = useMemo(() => [...new Set(atividades.map((a) => a.tipo).filter(Boolean))].sort(), [atividades])
  const filtradas = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR"); const hoje = hojeIso()
    return atividades.filter((a) => {
      if (!mostrarArquivadas && a.arquivada) return false
      if (statusFiltro === "PENDENTES" && (concluida(a.status) || cancelada(a.status))) return false
      if (statusFiltro === "CONCLUIDAS" && !concluida(a.status)) return false
      if (statusFiltro === "ATRASADAS" && (concluida(a.status) || cancelada(a.status) || !a.data || a.data >= hoje)) return false
      if (tipoFiltro !== "TODOS" && a.tipo !== tipoFiltro) return false
      if (termo && !`${a.titulo} ${a.cliente} ${a.tipo} ${a.descricao}`.toLocaleLowerCase("pt-BR").includes(termo)) return false
      return true
    })
  }, [atividades, busca, statusFiltro, tipoFiltro, mostrarArquivadas])

  async function registrarEncerramento(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!encerrando || !usuario?.id) return
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const resultado = texto(dados.get("resultado")); const desfecho = texto(dados.get("desfecho"))
    const proximaAcao = texto(dados.get("proxima_acao")); const proximaData = texto(dados.get("proxima_data"))
    if (!resultado || !desfecho) { setErro("Informe o resultado e o desfecho da atividade."); setSalvando(false); return }
    if ((proximaAcao && !proximaData) || (!proximaAcao && proximaData)) { setErro("Informe a próxima ação e a data em conjunto."); setSalvando(false); return }
    try {
      const resposta = await fetch("/api/crm-atividades/concluir", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          atividade_id: encerrando.id, cliente_id: encerrando.clienteId || null, oportunidade_id: encerrando.oportunidadeId || null,
          usuario_id: String(usuario.id), status_anterior: encerrando.status, descricao_original: encerrando.descricao,
          resultado, desfecho, proxima_acao: proximaAcao, proxima_data: proximaData,
        }),
      })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(payload.detail) || `Falha ${resposta.status}`)
      setEncerrando(null)
      setSucesso(proximaAcao ? "Atividade concluída; resultado preservado e próxima ação criada." : "Atividade concluída com resultado e desfecho preservados no histórico.")
      await carregar(false)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível registrar o resultado.") }
    finally { setSalvando(false) }
  }

  async function salvarEdicao(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!editando || !usuario?.id) return
    setSalvando(true); setErro(""); setSucesso(""); const dados = new FormData(evento.currentTarget)
    try {
      const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(editando.id)}/administrar`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
          administrador_id: usuario.id, cliente_id: texto(dados.get("cliente_id")) || null, tipo: texto(dados.get("tipo")), titulo: texto(dados.get("titulo")),
          descricao: texto(dados.get("descricao")), data: texto(dados.get("data")) || null, horario: texto(dados.get("horario")) || null, status: texto(dados.get("status")),
        }),
      })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(payload.detail) || `Falha ${resposta.status}`)
      setEditando(null); setSucesso("Atividade corrigida no mesmo registro. Nenhuma nova atividade foi criada."); await carregar(false)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível corrigir a atividade.") }
    finally { setSalvando(false) }
  }

  async function confirmarArquivamento(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!arquivando || !usuario?.id) return
    setSalvando(true); setErro(""); setSucesso(""); const dados = new FormData(evento.currentTarget)
    try {
      const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(arquivando.id)}/arquivar`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ administrador_id: usuario.id, motivo: texto(dados.get("motivo")) }) })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(payload.detail) || `Falha ${resposta.status}`)
      setArquivando(null); setSucesso("Atividade arquivada e preservada para auditoria."); await carregar(false)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível arquivar a atividade.") }
    finally { setSalvando(false) }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Central de Atividades</h1><p className="text-sm text-slate-400">Planeje, execute, registre o resultado e defina a próxima ação</p></div></div><div className="flex flex-wrap gap-2">{master && <button onClick={() => { setMostrarArquivadas((valor) => !valor); setStatusFiltro("TODAS"); setBusca("") }} className="flex items-center gap-2 rounded-2xl border border-amber-800 px-3 py-3 text-sm text-amber-200"><Archive size={17}/>{mostrarArquivadas ? "Voltar às ativas" : "Arquivadas"}</button>}<button onClick={() => void carregar(mostrarArquivadas)} className="grid size-12 place-items-center rounded-2xl border border-[#24466f] text-cyan-300"><RefreshCw size={18}/></button>{!mostrarArquivadas && <Link href="/crm-app/atividades/nova" className="flex items-center gap-2 rounded-2xl bg-cyan-500 px-4 py-3 font-bold text-slate-950"><Plus size={18}/>Nova atividade</Link>}</div></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}{sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    {!mostrarArquivadas && <section className="mb-5 grid grid-cols-3 gap-3"><Indicador icone={<ClipboardCheck size={18}/>} valor={resumo.pendentes} rotulo="Pendentes"/><Indicador icone={<CheckCircle2 size={18}/>} valor={resumo.concluidas} rotulo="Concluídas"/><Indicador icone={<CircleAlert size={18}/>} valor={resumo.atrasadas} rotulo="Atrasadas"/></section>}
    <section className="mb-5 grid gap-3 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:grid-cols-[1fr_auto_auto]"><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar por cliente, título, tipo ou histórico" className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"/><label className="relative"><Filter className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16}/><select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] pl-9 pr-8"><option value="TODAS">Todos os status</option><option value="PENDENTES">Pendentes</option><option value="CONCLUIDAS">Concluídas</option><option value="ATRASADAS">Atrasadas</option></select></label><select value={tipoFiltro} onChange={(e) => setTipoFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option value="TODOS">Todos os tipos</option>{tipos.map((tipo) => <option key={tipo} value={tipo}>{tipo.replaceAll("_", " ")}</option>)}</select></section>
    {carregando ? <div className="grid min-h-52 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : filtradas.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-10 text-center text-slate-400">Nenhuma atividade encontrada.</div> : <div className="space-y-3">{filtradas.map((atividade) => { const aberta = !atividade.arquivada && !concluida(atividade.status) && !cancelada(atividade.status); const atrasada = aberta && Boolean(atividade.data) && atividade.data < hojeIso(); return <article key={atividade.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="flex items-start justify-between gap-4"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-[#24466f] px-3 py-1 text-[11px] text-cyan-200">{atividade.tipo.replaceAll("_", " ")}</span>{atrasada && <span className="rounded-full border border-amber-700 px-3 py-1 text-[11px] text-amber-200">ATRASADA</span>}</div><h2 className="mt-3 text-lg font-bold">{atividade.titulo}</h2><p className="mt-1 text-sm text-slate-400">{atividade.cliente || "Cliente não informado"}</p>{atividade.descricao && <p className="mt-3 line-clamp-4 whitespace-pre-line text-sm leading-6 text-slate-300">{atividade.descricao}</p>}</div><span className={`shrink-0 rounded-full px-3 py-1 text-xs ${concluida(atividade.status) ? "bg-emerald-950/50 text-emerald-300" : "bg-cyan-950/50 text-cyan-300"}`}>{atividade.status}</span></div><div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-400">{atividade.data && <span className="inline-flex items-center gap-1"><CalendarClock size={14}/>{new Date(`${atividade.data}T12:00:00`).toLocaleDateString("pt-BR")}{atividade.horario ? ` · ${atividade.horario}` : ""}</span>}{atividade.oportunidadeId && <Link href={`/crm-app/oportunidades/${encodeURIComponent(atividade.oportunidadeId)}`} className="rounded-lg border border-[#24466f] px-2 py-1 text-cyan-300">Abrir negociação</Link>}{atividade.clienteId && <Link href={`/crm-app/clientes/${encodeURIComponent(atividade.clienteId)}`} className="rounded-lg border border-[#24466f] px-2 py-1 text-cyan-300">Abrir cliente</Link>}</div>{!atividade.arquivada && <div className="mt-4 flex flex-wrap gap-2">{aberta ? <button onClick={() => setEncerrando(atividade)} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Registrar resultado</button> : <button onClick={() => setDetalhando(atividade)} className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-emerald-800 px-4 py-3 text-sm font-semibold text-emerald-200"><Eye size={16}/>Ver resultado / histórico</button>}{master && <button onClick={() => setEditando(atividade)} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-800 px-4 py-3 text-sm font-semibold text-cyan-200"><Pencil size={16}/>Corrigir</button>}{master && <button onClick={() => setArquivando(atividade)} className="flex items-center justify-center gap-2 rounded-xl border border-amber-800 px-4 py-3 text-sm font-semibold text-amber-200"><Archive size={16}/>Arquivar</button>}</div>}</article> })}</div>}
  </div>

  {encerrando && <Modal titulo="Registrar resultado da atividade" fechar={() => setEncerrando(null)}><form onSubmit={registrarEncerramento} className="grid gap-4"><div className="rounded-2xl bg-[#020817] p-4"><p className="font-bold">{encerrando.titulo}</p><p className="text-sm text-slate-400">{encerrando.cliente || "Cliente não informado"}</p>{encerrando.descricao && <p className="mt-3 whitespace-pre-line text-sm text-slate-300"><strong>Planejamento original:</strong><br/>{encerrando.descricao}</p>}</div><label><span className="mb-2 block text-sm text-slate-300">Resultado obtido</span><textarea name="resultado" rows={4} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><CampoSelect name="desfecho" label="Desfecho" opcoes={[{valor:"AVANÇOU",texto:"Avançou"},{valor:"MANTEVE",texto:"Manteve estágio"},{valor:"SEM INTERESSE",texto:"Sem interesse"},{valor:"PERDIDA PARA CONCORRENTE",texto:"Perdida para concorrente"},{valor:"PEDIDO / FECHAMENTO",texto:"Pedido / fechamento"},{valor:"INFORMATIVA / ENCERRADA",texto:"Informativa / encerrada"}]}/><CampoEdicao name="proxima_acao" label="Próxima ação" valor=""/><CampoEdicao name="proxima_data" label="Data da próxima ação" valor="" type="date"/><p className="text-xs text-slate-400">O planejamento original será preservado. Resultado, desfecho e próxima ação serão acrescentados ao histórico; se houver próxima ação, um follow-up será criado automaticamente.</p><button disabled={salvando} className="min-h-12 rounded-2xl bg-emerald-600 font-bold disabled:opacity-60">{salvando ? "Salvando..." : "Concluir e registrar histórico"}</button></form></Modal>}

  {detalhando && <Modal titulo="Resultado e histórico" fechar={() => setDetalhando(null)}><div className="grid gap-4"><div><p className="font-bold">{detalhando.titulo}</p><p className="text-sm text-slate-400">{detalhando.cliente || "Cliente não informado"}</p></div><div className="whitespace-pre-line rounded-2xl border border-[#24466f] bg-[#020817] p-4 text-sm leading-6 text-slate-200">{detalhando.descricao || "Nenhum histórico textual registrado."}</div></div></Modal>}

  {editando && <Modal titulo="Corrigir atividade" fechar={() => setEditando(null)}><form onSubmit={salvarEdicao} className="grid gap-3 sm:grid-cols-2"><label className="sm:col-span-2"><span className="mb-1 block text-xs text-slate-400">Cliente vinculado</span><select name="cliente_id" defaultValue={editando.clienteId} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3"><option value="">Sem cliente</option>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select></label><CampoEdicao name="tipo" label="Tipo" valor={editando.tipo}/><CampoEdicao name="status" label="Status" valor={editando.status}/><CampoEdicao name="titulo" label="Título" valor={editando.titulo} classe="sm:col-span-2"/><CampoEdicao name="data" label="Data" valor={editando.data} type="date"/><CampoEdicao name="horario" label="Horário" valor={editando.horario} type="time"/><label className="sm:col-span-2"><span className="mb-1 block text-xs text-slate-400">Descrição</span><textarea name="descricao" defaultValue={editando.descricao} rows={4} className="w-full rounded-xl border border-[#24466f] bg-[#020817] p-3"/></label><p className="sm:col-span-2 text-xs text-slate-400">Correção administrativa do mesmo registro, preservada na auditoria.</p><button disabled={salvando} className="sm:col-span-2 h-11 rounded-xl bg-cyan-500 font-bold text-slate-950">Salvar correção</button></form></Modal>}

  {arquivando && <Modal titulo="Arquivar atividade" fechar={() => setArquivando(null)}><form onSubmit={confirmarArquivamento} className="grid gap-3"><p className="text-sm text-slate-300"><strong>{arquivando.titulo}</strong><br/>{arquivando.cliente || "Cliente não informado"}</p><label><span className="mb-1 block text-xs text-slate-400">Motivo obrigatório</span><textarea name="motivo" required minLength={5} rows={4} className="w-full rounded-xl border border-amber-800 bg-[#020817] p-3"/></label><button disabled={salvando} className="h-11 rounded-xl bg-amber-600 font-bold text-slate-950">Confirmar arquivamento</button></form></Modal>}
  </main>
}

function Indicador({icone, valor, rotulo}:{icone:React.ReactNode;valor:number;rotulo:string}) { return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><div className="text-cyan-300">{icone}</div><strong className="mt-2 block text-2xl text-white">{valor}</strong><span className="text-xs text-slate-400">{rotulo}</span></div> }
function Modal({titulo, fechar, children}:{titulo:string;fechar:()=>void;children:React.ReactNode}) { return <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 p-4"><section className="mx-auto my-6 max-h-[90dvh] w-full max-w-xl overflow-auto rounded-3xl border border-[#24466f] bg-[#07162b] p-5 shadow-2xl"><header className="mb-4 flex items-center justify-between gap-3"><h2 className="text-lg font-bold">{titulo}</h2><button type="button" onClick={fechar} className="grid size-9 place-items-center rounded-xl border border-[#24466f] text-slate-300"><X size={18}/></button></header>{children}</section></div> }
function CampoEdicao({name,label,valor,type="text",classe=""}:{name:string;label:string;valor:string;type?:string;classe?:string}) { return <label className={classe}><span className="mb-1 block text-xs text-slate-400">{label}</span><input name={name} type={type} defaultValue={valor} className="h-11 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3"/></label> }
function CampoSelect({name,label,opcoes}:{name:string;label:string;opcoes:{valor:string;texto:string}[]}) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><select name={name} required className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option value="">Selecione</option>{opcoes.map((opcao) => <option key={opcao.valor} value={opcao.valor}>{opcao.texto}</option>)}</select></label> }
