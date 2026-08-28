"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ArrowLeft, CalendarDays, CheckCircle2, Clock3, Eye, Loader2, MapPinned, Play, Plus, Search, Target, X } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; cidade: string; uf: string }
type Oportunidade = { id: string; clienteId: string; cliente: string; titulo: string }
type Visita = { id: string; clienteId: string; cliente: string; oportunidadeId: string; oportunidade: string; titulo: string; descricao: string; data: string; horario: string; status: string }
type OpcaoBusca = { valor: string; titulo: string; complemento?: string }

const CONCLUIDOS = new Set(["CONCLUIDA", "CONCLUÍDA", "REALIZADA"])
function texto(valor: unknown) { return String(valor ?? "").trim() }
function chave(valor: unknown) { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }
function hoje() { return new Date().toISOString().slice(0, 10) }
function dataBr(data: string) { return data ? new Date(`${data}T12:00:00`).toLocaleDateString("pt-BR") : "Data não informada" }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const campo of ["dados", "itens", "resultado", "atividades", "oportunidades"]) if (Array.isArray(objeto[campo])) return objeto[campo] as Registro[]
  }
  return []
}
function estado(visita: Visita) {
  const status = visita.status.toUpperCase()
  if (CONCLUIDOS.has(status)) return "CONCLUIDA"
  if (["EM_ANDAMENTO", "INICIADA"].includes(status)) return "EM_ANDAMENTO"
  if (visita.data && visita.data < hoje()) return "ATRASADA"
  return "AGENDADA"
}
function descricao(objetivo: string, resultado?: string, desfecho?: string, proxima?: string) {
  const linhas = [`[OBJETIVO]\n${objetivo.trim() || "Não informado"}`]
  if (resultado) linhas.push(`[RESULTADO]\n${resultado.trim()}`)
  if (desfecho) linhas.push(`[DESFECHO]\n${desfecho.trim()}`)
  if (proxima) linhas.push(`[PRÓXIMA AÇÃO]\n${proxima.trim()}`)
  return linhas.join("\n\n")
}
function objetivoDa(descricaoAtual: string) {
  const marcador = "[OBJETIVO]"; const inicio = descricaoAtual.indexOf(marcador)
  if (inicio < 0) return descricaoAtual
  const restante = descricaoAtual.slice(inicio + marcador.length).trim(); const proximo = restante.search(/\n\n\[[A-ZÁÉÍÓÚÇ ]+\]/)
  return proximo >= 0 ? restante.slice(0, proximo).trim() : restante
}

export default function VisitasPage() {
  const { usuario } = useAuth()
  const contextoAplicado = useRef(false)
  const [visitas, setVisitas] = useState<Visita[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [busca, setBusca] = useState(""); const [filtro, setFiltro] = useState("TODAS")
  const [carregando, setCarregando] = useState(true); const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState(""); const [sucesso, setSucesso] = useState("")
  const [novaAberta, setNovaAberta] = useState(false); const [clienteId, setClienteId] = useState(""); const [clienteBusca, setClienteBusca] = useState("")
  const [oportunidadeId, setOportunidadeId] = useState(""); const [oportunidadeBusca, setOportunidadeBusca] = useState("")
  const [encerramento, setEncerramento] = useState<Visita | null>(null); const [detalhe, setDetalhe] = useState<Visita | null>(null)

  const carregar = useCallback(async () => {
    setCarregando(true); setErro("")
    try {
      const params = new URLSearchParams(window.location.search); const clienteContexto = texto(params.get("cliente")); const oportunidadeContexto = texto(params.get("oportunidade"))
      const [atividadesResposta, clientesResposta, oportunidadesResposta] = await Promise.all([
        fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }),
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }),
        fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
      ])
      if (!atividadesResposta.ok) throw new Error(`Não foi possível carregar as visitas (${atividadesResposta.status}).`)
      const atividadesPayload = await atividadesResposta.json(); const clientesPayload = clientesResposta.ok ? await clientesResposta.json() : []; const oportunidadesPayload = oportunidadesResposta.ok ? await oportunidadesResposta.json() : []
      const clientesNormalizados = lista(clientesPayload).map((item) => {
        const nome = texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente); if (!nome) return null
        return { id: texto(item.id || item.cliente_id || item.uuid) || nome, nome, cidade: texto(item.cidade || item.municipio), uf: texto(item.estado || item.uf).toUpperCase() }
      }).filter(Boolean) as Cliente[]
      const clientesUnicos = [...new Map(clientesNormalizados.map((item) => [item.id, item])).values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")); setClientes(clientesUnicos)
      const oportunidadesNormalizadas = lista(oportunidadesPayload).map((item) => ({ id: texto(item.id || item.oportunidade_id), clienteId: texto(item.cliente_id), cliente: texto(item.cliente_nome || item.cliente || item.empresa), titulo: texto(item.titulo || item.equipamento) || "Oportunidade" })).filter((item) => item.id); setOportunidades(oportunidadesNormalizadas)
      if (!contextoAplicado.current && (clienteContexto || oportunidadeContexto)) {
        const oportunidadeInicial = oportunidadeContexto ? oportunidadesNormalizadas.find((item) => item.id === oportunidadeContexto) : undefined
        const clienteInicial = clientesUnicos.find((item) => clienteContexto && item.id === clienteContexto) || clientesUnicos.find((item) => oportunidadeInicial?.clienteId && item.id === oportunidadeInicial.clienteId) || clientesUnicos.find((item) => oportunidadeInicial?.cliente && chave(item.nome) === chave(oportunidadeInicial.cliente))
        if (clienteInicial) { setClienteId(clienteInicial.id); setClienteBusca(clienteInicial.nome); setNovaAberta(true) }
        if (oportunidadeInicial) { setOportunidadeId(oportunidadeInicial.id); setOportunidadeBusca(oportunidadeInicial.titulo); setNovaAberta(true) }
        contextoAplicado.current = true
      }
      const nomesClientes = new Map(clientesNormalizados.map((item) => [item.id, item.nome])); const nomesOportunidades = new Map(oportunidadesNormalizadas.map((item) => [item.id, item.titulo]))
      setVisitas(lista(atividadesPayload).filter((item) => texto(item.tipo || item.tipo_atividade).toUpperCase().includes("VISITA")).map((item) => {
        const idCliente = texto(item.cliente_id); const idOportunidade = texto(item.oportunidade_id)
        return { id: texto(item.id || item.atividade_id), clienteId: idCliente, cliente: texto(item.cliente_nome || item.cliente) || nomesClientes.get(idCliente) || "Cliente não identificado", oportunidadeId: idOportunidade, oportunidade: texto(item.oportunidade_titulo) || nomesOportunidades.get(idOportunidade) || "", titulo: texto(item.titulo || item.assunto) || "Visita comercial", descricao: texto(item.descricao), data: texto(item.data || item.data_atividade || item.inicio).slice(0, 10), horario: texto(item.horario || item.hora || item.inicio).slice(11, 16), status: texto(item.status || item.situacao).toUpperCase() || "PENDENTE" }
      }).filter((item) => item.id).sort((a, b) => `${a.data}${a.horario}`.localeCompare(`${b.data}${b.horario}`)))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o módulo de visitas.") }
    finally { setCarregando(false) }
  }, [])

  useEffect(() => { void carregar() }, [carregar])
  const resumo = useMemo(() => ({ hoje: visitas.filter((item) => item.data === hoje() && estado(item) !== "CONCLUIDA").length, atrasadas: visitas.filter((item) => estado(item) === "ATRASADA").length, andamento: visitas.filter((item) => estado(item) === "EM_ANDAMENTO").length, concluidas: visitas.filter((item) => estado(item) === "CONCLUIDA").length }), [visitas])
  const visiveis = useMemo(() => visitas.filter((item) => { const termo = busca.trim().toLocaleLowerCase("pt-BR"); return (filtro === "TODAS" || estado(item) === filtro) && (!termo || `${item.cliente} ${item.titulo} ${item.oportunidade}`.toLocaleLowerCase("pt-BR").includes(termo)) }), [busca, filtro, visitas])
  const clientesBusca = useMemo<OpcaoBusca[]>(() => clientes.map((item) => ({ valor: item.id, titulo: item.nome, complemento: [item.cidade, item.uf].filter(Boolean).join("/") || item.id })), [clientes])
  const oportunidadesDoCliente = useMemo<OpcaoBusca[]>(() => oportunidades.filter((item) => !clienteId || item.clienteId === clienteId).map((item) => ({ valor: item.id, titulo: item.titulo, complemento: item.cliente || "Negociação comercial" })), [clienteId, oportunidades])

  function fecharNovaVisita() { setNovaAberta(false); setClienteId(""); setClienteBusca(""); setOportunidadeId(""); setOportunidadeBusca("") }
  async function criarVisita(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setSalvando(true); setErro(""); setSucesso(""); const dados = new FormData(evento.currentTarget)
    if (!usuario?.id || !clienteId || !texto(dados.get("titulo")) || !texto(dados.get("objetivo"))) { setErro("Informe cliente, título, objetivo e confirme o usuário autenticado."); setSalvando(false); return }
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cliente_id: clienteId, oportunidade_id: oportunidadeId || null, usuario_id: String(usuario.id), tipo: "VISITA", titulo: texto(dados.get("titulo")), descricao: descricao(texto(dados.get("objetivo"))), data: texto(dados.get("data")), horario: texto(dados.get("horario")), status: "PENDENTE" }) })
      const detalheResposta = await resposta.json().catch(() => ({})) as Registro; if (!resposta.ok) throw new Error(texto(detalheResposta.detail) || `Falha ${resposta.status}`)
      evento.currentTarget.reset(); fecharNovaVisita(); setSucesso("Visita agendada e sincronizada com o CTI."); await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível agendar a visita.") } finally { setSalvando(false) }
  }
  async function iniciar(visita: Visita) {
    setErro(""); setSucesso(""); const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(visita.id)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "EM_ANDAMENTO" }) }); const corpo = await resposta.json().catch(() => ({})) as Registro
    if (!resposta.ok) return setErro(texto(corpo.detail) || "Não foi possível iniciar a visita."); setSucesso("Visita iniciada. Registre o resultado ao final."); await carregar()
  }
  async function concluir(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!encerramento || !usuario?.id) return
    setSalvando(true); setErro(""); setSucesso(""); const dados = new FormData(evento.currentTarget); const resultado = texto(dados.get("resultado")); const desfecho = texto(dados.get("desfecho")); const proxima = texto(dados.get("proxima_acao")); const proximaData = texto(dados.get("proxima_data"))
    if (!resultado || !desfecho) { setErro("Informe o resultado e o desfecho da visita."); setSalvando(false); return }
    if ((proxima && !proximaData) || (!proxima && proximaData)) { setErro("Informe a próxima ação e sua data em conjunto."); setSalvando(false); return }
    try {
      const resposta = await fetch("/api/crm-visitas/concluir", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ visita_id: encerramento.id, cliente_id: encerramento.clienteId, oportunidade_id: encerramento.oportunidadeId || null, usuario_id: String(usuario.id), descricao: descricao(objetivoDa(encerramento.descricao), resultado, desfecho, proxima), proxima_acao: proxima, proxima_data: proximaData }) }); const corpo = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(corpo.detail) || `Falha ${resposta.status}`); setEncerramento(null); setSucesso("Visita concluída. Histórico e próxima ação sincronizados com o CTI."); await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível concluir a visita.") } finally { setSalvando(false) }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-6xl">
    <header className="mb-5 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Visitas comerciais</h1><p className="text-sm text-slate-400">Prepare, execute, registre o resultado e defina a próxima ação</p></div></div><button onClick={() => setNovaAberta(true)} className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-500 px-4 font-bold text-slate-950"><Plus size={18}/>Nova visita</button></header>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}{sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}
    <section className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4"><Resumo valor={resumo.hoje} label="Hoje"/><Resumo valor={resumo.atrasadas} label="Atrasadas"/><Resumo valor={resumo.andamento} label="Em andamento"/><Resumo valor={resumo.concluidas} label="Concluídas"/></section>
    <section className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto]"><label className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, oportunidade ou objetivo" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label><select value={filtro} onChange={(e) => setFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#16325c] bg-[#07162b] px-4"><option value="TODAS">Todas</option><option value="AGENDADA">Agendadas</option><option value="ATRASADA">Atrasadas</option><option value="EM_ANDAMENTO">Em andamento</option><option value="CONCLUIDA">Concluídas</option></select></section>
    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? <section className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center"><MapPinned className="mx-auto text-cyan-300"/><h2 className="mt-3 text-lg font-bold">Nenhuma visita neste filtro</h2></section> : <div className="space-y-3">{visiveis.map((visita) => { const concluidaVisita = CONCLUIDOS.has(visita.status); const prepararHref = visita.oportunidadeId ? `/crm-app/historico/${visita.oportunidadeId}?origem=visitas` : visita.clienteId ? `/crm-app/clientes/${encodeURIComponent(visita.clienteId)}` : ""; return <article key={visita.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold text-cyan-300">{estado(visita).replace("_", " ")}</p><h2 className="mt-1 text-lg font-bold">{visita.cliente}</h2><p className="text-sm text-slate-300">{visita.titulo}</p>{visita.oportunidade && <p className="mt-1 text-xs text-slate-400">Negociação: {visita.oportunidade}</p>}</div><div className="text-right text-xs text-slate-400"><span className="inline-flex items-center gap-1"><CalendarDays size={14}/>{dataBr(visita.data)}</span>{visita.horario && <span className="mt-1 flex items-center justify-end gap-1"><Clock3 size={14}/>{visita.horario}</span>}</div></div>{visita.descricao && <p className="mt-4 line-clamp-5 whitespace-pre-line rounded-2xl bg-[#020817]/70 p-3 text-sm leading-6 text-slate-300">{visita.descricao}</p>}<div className="mt-4 grid gap-2 sm:grid-cols-3">{concluidaVisita ? <button onClick={() => setDetalhe(visita)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-800 px-3 py-3 text-sm font-semibold text-emerald-200"><Eye size={16}/>Ver resultado / histórico</button> : prepararHref ? <Link href={prepararHref} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#24466f] px-3 py-3 text-sm"><Target size={16}/>Preparar visita</Link> : null}{!concluidaVisita && estado(visita) !== "EM_ANDAMENTO" && <button onClick={() => void iniciar(visita)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-3 py-3 text-sm font-semibold text-cyan-200"><Play size={16}/>Iniciar visita</button>}{!concluidaVisita && <button onClick={() => setEncerramento(visita)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Registrar resultado</button>}</div></article> })}</div>}
  </div>

  {novaAberta && <Modal titulo="Agendar nova visita" fechar={fecharNovaVisita}><form onSubmit={criarVisita} className="grid gap-4 sm:grid-cols-2"><CampoBusca name="cliente_id" label="Cliente" placeholder="Digite nome, código ou cidade" valor={clienteId} busca={clienteBusca} opcoes={clientesBusca} obrigatorio onBuscar={(valor) => { setClienteBusca(valor); setClienteId(""); setOportunidadeId(""); setOportunidadeBusca("") }} onSelecionar={(opcao) => { setClienteId(opcao.valor); setClienteBusca(opcao.titulo); setOportunidadeId(""); setOportunidadeBusca("") }}/><CampoBusca name="oportunidade_id" label="Oportunidade relacionada" placeholder={clienteId ? "Digite o título da oportunidade" : "Selecione primeiro o cliente"} valor={oportunidadeId} busca={oportunidadeBusca} opcoes={oportunidadesDoCliente} desabilitado={!clienteId} permitirVazio onBuscar={(valor) => { setOportunidadeBusca(valor); setOportunidadeId("") }} onSelecionar={(opcao) => { setOportunidadeId(opcao.valor); setOportunidadeBusca(opcao.titulo) }}/><Campo name="titulo" label="Objetivo resumido"/><Campo name="data" label="Data" type="date" valor={hoje()}/><Campo name="horario" label="Horário" type="time"/><label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Preparação e objetivo da visita</span><textarea name="objetivo" rows={5} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><button disabled={salvando} className="sm:col-span-2 min-h-12 rounded-2xl bg-cyan-500 font-bold text-slate-950">Agendar visita</button></form></Modal>}
  {encerramento && <Modal titulo="Registrar resultado da visita" fechar={() => setEncerramento(null)}><form onSubmit={concluir} className="grid gap-4"><div className="rounded-2xl bg-[#020817] p-4"><p className="font-bold">{encerramento.cliente}</p><p className="text-sm text-slate-400">{encerramento.titulo}</p></div><label><span className="mb-2 block text-sm text-slate-300">Resultado obtido</span><textarea name="resultado" rows={4} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><CampoSelect name="desfecho" label="Desfecho" opcoes={[{ valor: "AVANÇOU", texto: "Avançou" }, { valor: "MANTEVE", texto: "Manteve estágio" }, { valor: "SEM INTERESSE", texto: "Sem interesse" }, { valor: "PERDIDA PARA CONCORRENTE", texto: "Perdida para concorrente" }, { valor: "PEDIDO / FECHAMENTO", texto: "Pedido / fechamento" }]}/><Campo name="proxima_acao" label="Próxima ação"/><Campo name="proxima_data" label="Data da próxima ação" type="date"/><button disabled={salvando} className="min-h-12 rounded-2xl bg-emerald-600 font-bold">Concluir e sincronizar</button></form></Modal>}
  {detalhe && <Modal titulo="Resultado e histórico da visita" fechar={() => setDetalhe(null)}><div className="grid gap-4"><div><p className="font-bold">{detalhe.cliente}</p><p className="text-sm text-slate-400">{detalhe.titulo}</p></div><div className="whitespace-pre-line rounded-2xl border border-[#24466f] bg-[#020817] p-4 text-sm leading-6 text-slate-200">{detalhe.descricao || "Nenhum resultado textual registrado."}</div>{detalhe.oportunidadeId && <Link href={`/crm-app/historico/${detalhe.oportunidadeId}?origem=visitas`} className="rounded-xl border border-cyan-800 px-4 py-3 text-center text-cyan-200">Abrir histórico da negociação</Link>}</div></Modal>}
  </main>
}

function Resumo({ valor, label }: { valor: number; label: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><strong className="text-2xl text-cyan-300">{valor}</strong><span className="mt-1 block text-xs text-slate-400">{label}</span></div> }
function Modal({ titulo, fechar, children }: { titulo: string; fechar: () => void; children: React.ReactNode }) { return <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 p-4"><div className="mx-auto my-6 max-w-2xl rounded-3xl border border-[#24466f] bg-[#07162b] p-5 text-white"><header className="mb-5 flex items-center justify-between"><h2 className="text-xl font-bold">{titulo}</h2><button type="button" onClick={fechar} className="rounded-xl border border-[#24466f] p-2"><X size={18}/></button></header>{children}</div></div> }
function Campo({ name, label, type = "text", valor }: { name: string; label: string; type?: string; valor?: string }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} defaultValue={valor} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label> }
function CampoSelect({ name, label, opcoes }: { name: string; label: string; opcoes: { valor: string; texto: string }[] }) { return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><select name={name} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option value="">Selecione</option>{opcoes.map((opcao) => <option key={`${name}-${opcao.valor}`} value={opcao.valor}>{opcao.texto}</option>)}</select></label> }
function CampoBusca({ name, label, placeholder, valor, busca, opcoes, onBuscar, onSelecionar, obrigatorio = false, permitirVazio = false, desabilitado = false }: { name: string; label: string; placeholder: string; valor: string; busca: string; opcoes: OpcaoBusca[]; onBuscar: (valor: string) => void; onSelecionar: (opcao: OpcaoBusca) => void; obrigatorio?: boolean; permitirVazio?: boolean; desabilitado?: boolean }) {
  const termo = busca.trim().toLocaleLowerCase("pt-BR"); const resultados = termo.length < 2 ? [] : opcoes.filter((opcao) => `${opcao.titulo} ${opcao.complemento || ""} ${opcao.valor}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 12); const mostrarResultados = !valor && termo.length >= 2 && !desabilitado
  return <label className="relative"><span className="mb-2 block text-sm text-slate-300">{label}</span><input type="hidden" name={name} value={valor}/><div className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={17}/><input value={busca} disabled={desabilitado} required={obrigatorio} onChange={(evento) => onBuscar(evento.target.value)} placeholder={placeholder} autoComplete="off" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-11 pr-4 disabled:opacity-50"/></div>{valor && <button type="button" onClick={() => onBuscar("")} className="mt-2 text-xs font-semibold text-cyan-300">Alterar seleção</button>}{mostrarResultados && <div className="absolute left-0 right-0 z-40 mt-2 max-h-72 overflow-y-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{permitirVazio && <button type="button" onClick={() => { onBuscar(""); onSelecionar({ valor: "", titulo: "" }) }} className="block w-full px-4 py-3 text-left text-sm text-slate-400">Sem vínculo</button>}{resultados.length ? resultados.map((opcao) => <button key={opcao.valor} type="button" onClick={() => onSelecionar(opcao)} className="block w-full border-t border-[#16325c] px-4 py-3 text-left"><strong className="block text-sm text-white">{opcao.titulo}</strong>{opcao.complemento && <span className="text-xs text-slate-400">{opcao.complemento}</span>}</button>) : <div className="px-4 py-3 text-sm text-slate-400">Nenhum resultado encontrado.</div>}</div>}</label>
}
