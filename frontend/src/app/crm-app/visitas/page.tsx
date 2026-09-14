"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ArrowLeft, BriefcaseBusiness, CalendarDays, CheckCircle2, Clock3, Loader2, MapPinned, Plus, Search, XCircle } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; cidade: string; uf: string }
type Oportunidade = { id: string; clienteId: string; cliente: string; titulo: string }
type Visita = { id: string; clienteId: string; cliente: string; oportunidadeId: string; oportunidade: string; titulo: string; descricao: string; data: string; horario: string; status: string }

type EstadoVisita = "AGENDADA" | "A_CONFIRMAR" | "REALIZADA" | "NAO_REALIZADA"

const REALIZADAS = new Set(["CONCLUIDA", "CONCLUÍDA", "REALIZADA"])
const NAO_REALIZADAS = new Set(["CANCELADA", "CANCELADO", "NAO_REALIZADA", "NÃO_REALIZADA"])

function texto(valor: unknown) { return String(valor ?? "").trim() }
function chave(valor: unknown) { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }
function hoje() { return new Date().toISOString().slice(0, 10) }
function dataBr(data: string) { return data ? new Date(`${data}T12:00:00`).toLocaleDateString("pt-BR") : "Data não informada" }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const k of ["dados", "itens", "resultado", "atividades", "oportunidades"]) {
      if (Array.isArray(objeto[k])) return objeto[k] as Registro[]
    }
  }
  return []
}
function estado(visita: Visita): EstadoVisita {
  const status = chave(visita.status)
  if (REALIZADAS.has(status)) return "REALIZADA"
  if (NAO_REALIZADAS.has(status)) return "NAO_REALIZADA"
  if (visita.data && visita.data > hoje()) return "AGENDADA"
  return "A_CONFIRMAR"
}
function rotuloEstado(valor: EstadoVisita) {
  if (valor === "REALIZADA") return "REALIZADA"
  if (valor === "NAO_REALIZADA") return "NÃO REALIZADA"
  if (valor === "A_CONFIRMAR") return "A CONFIRMAR"
  return "AGENDADA"
}
function descricaoObjetivo(objetivo: string) {
  return `[OBJETIVO]\n${objetivo.trim() || "Não informado"}`
}

export default function VisitasPage() {
  const { usuario } = useAuth()
  const router = useRouter()
  const contextoAplicado = useRef(false)
  const [visitas, setVisitas] = useState<Visita[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [busca, setBusca] = useState("")
  const [filtro, setFiltro] = useState("ATIVAS")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [novaAberta, setNovaAberta] = useState(false)
  const [clienteId, setClienteId] = useState("")
  const [clienteBusca, setClienteBusca] = useState("")
  const [oportunidadeId, setOportunidadeId] = useState("")
  const [oportunidadeBusca, setOportunidadeBusca] = useState("")
  const [decisao, setDecisao] = useState<Visita | null>(null)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const params = new URLSearchParams(window.location.search)
      const clienteContexto = texto(params.get("cliente"))
      const oportunidadeContexto = texto(params.get("oportunidade"))
      const [atividadesResposta, clientesResposta, oportunidadesResposta] = await Promise.all([
        fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }),
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }),
        fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
      ])
      if (!atividadesResposta.ok) throw new Error(`Não foi possível carregar as visitas (${atividadesResposta.status}).`)
      const atividadesPayload = await atividadesResposta.json()
      const clientesPayload = clientesResposta.ok ? await clientesResposta.json() : []
      const oportunidadesPayload = oportunidadesResposta.ok ? await oportunidadesResposta.json() : []

      const clientesNormalizados = lista(clientesPayload).map((item) => {
        const nome = texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente)
        if (!nome) return null
        return {
          id: texto(item.id || item.cliente_id || item.uuid) || nome,
          nome,
          cidade: texto(item.cidade || item.municipio),
          uf: texto(item.estado || item.uf).toUpperCase(),
        }
      }).filter(Boolean) as Cliente[]
      const clientesUnicos = [...new Map(clientesNormalizados.map((item) => [item.id, item])).values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
      setClientes(clientesUnicos)

      const oportunidadesNormalizadas = lista(oportunidadesPayload).map((item) => ({
        id: texto(item.id || item.oportunidade_id),
        clienteId: texto(item.cliente_id),
        cliente: texto(item.cliente_nome || item.cliente || item.empresa),
        titulo: texto(item.titulo || item.equipamento) || "Oportunidade",
      })).filter((item) => item.id)
      setOportunidades(oportunidadesNormalizadas)

      if (!contextoAplicado.current && (clienteContexto || oportunidadeContexto)) {
        const oportunidadeInicial = oportunidadeContexto ? oportunidadesNormalizadas.find((item) => item.id === oportunidadeContexto) : undefined
        const clienteInicial = clientesUnicos.find((item) => clienteContexto && item.id === clienteContexto)
          || clientesUnicos.find((item) => oportunidadeInicial?.clienteId && item.id === oportunidadeInicial.clienteId)
          || clientesUnicos.find((item) => oportunidadeInicial?.cliente && chave(item.nome) === chave(oportunidadeInicial.cliente))
        if (clienteInicial) {
          setClienteId(clienteInicial.id)
          setClienteBusca(clienteInicial.nome)
          setNovaAberta(true)
        }
        if (oportunidadeInicial) {
          setOportunidadeId(oportunidadeInicial.id)
          setOportunidadeBusca(oportunidadeInicial.titulo)
          setNovaAberta(true)
        }
        contextoAplicado.current = true
      }

      const nomesClientes = new Map(clientesNormalizados.map((item) => [item.id, item.nome]))
      const nomesOportunidades = new Map(oportunidadesNormalizadas.map((item) => [item.id, item.titulo]))
      setVisitas(lista(atividadesPayload)
        .filter((item) => chave(item.tipo || item.tipo_atividade).includes("VISITA"))
        .map((item) => {
          const idCliente = texto(item.cliente_id)
          const idOportunidade = texto(item.oportunidade_id)
          return {
            id: texto(item.id || item.atividade_id),
            clienteId: idCliente,
            cliente: texto(item.cliente_nome || item.cliente) || nomesClientes.get(idCliente) || "Cliente não identificado",
            oportunidadeId: idOportunidade,
            oportunidade: texto(item.oportunidade_titulo) || nomesOportunidades.get(idOportunidade) || "",
            titulo: texto(item.titulo || item.assunto) || "Visita comercial",
            descricao: texto(item.descricao),
            data: texto(item.data || item.data_atividade || item.inicio).slice(0, 10),
            horario: texto(item.horario || item.hora || item.inicio).slice(11, 16),
            status: texto(item.status || item.situacao).toUpperCase() || "PENDENTE",
          }
        }).filter((item) => item.id)
        .sort((a, b) => `${b.data}${b.horario}`.localeCompare(`${a.data}${a.horario}`)))
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as visitas.")
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => { void carregar() }, [carregar])

  const resumo = useMemo(() => ({
    hoje: visitas.filter((item) => item.data === hoje() && estado(item) === "A_CONFIRMAR").length,
    agendadas: visitas.filter((item) => estado(item) === "AGENDADA").length,
    confirmar: visitas.filter((item) => estado(item) === "A_CONFIRMAR").length,
    realizadas: visitas.filter((item) => estado(item) === "REALIZADA").length,
  }), [visitas])

  const visiveis = useMemo(() => visitas.filter((item) => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    const e = estado(item)
    const porFiltro = filtro === "TODAS" || (filtro === "ATIVAS" ? e === "AGENDADA" || e === "A_CONFIRMAR" : e === filtro)
    return porFiltro && (!termo || `${item.cliente} ${item.titulo} ${item.oportunidade}`.toLocaleLowerCase("pt-BR").includes(termo))
  }), [busca, filtro, visitas])

  const clientesFiltrados = useMemo(() => {
    const termo = chave(clienteBusca)
    if (!termo || clienteId) return []
    return clientes.filter((item) => chave(`${item.nome} ${item.cidade} ${item.uf}`).includes(termo)).slice(0, 8)
  }, [clienteBusca, clienteId, clientes])

  const oportunidadesDoCliente = useMemo(() => oportunidades.filter((item) => !clienteId || item.clienteId === clienteId), [clienteId, oportunidades])
  const oportunidadesFiltradas = useMemo(() => {
    const termo = chave(oportunidadeBusca)
    if (!termo || oportunidadeId) return []
    return oportunidadesDoCliente.filter((item) => chave(`${item.titulo} ${item.cliente}`).includes(termo)).slice(0, 8)
  }, [oportunidadeBusca, oportunidadeId, oportunidadesDoCliente])

  function fecharNovaVisita() {
    setNovaAberta(false)
    setClienteId("")
    setClienteBusca("")
    setOportunidadeId("")
    setOportunidadeBusca("")
  }

  async function criarVisita(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true)
    setErro("")
    setSucesso("")
    const dados = new FormData(evento.currentTarget)
    if (!usuario?.id || !clienteId || !texto(dados.get("titulo")) || !texto(dados.get("objetivo")) || !texto(dados.get("data"))) {
      setErro("Informe cliente, objetivo e data da visita.")
      setSalvando(false)
      return
    }
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: clienteId,
          oportunidade_id: oportunidadeId || null,
          usuario_id: String(usuario.id),
          tipo: "VISITA",
          titulo: texto(dados.get("titulo")),
          descricao: descricaoObjetivo(texto(dados.get("objetivo"))),
          data: texto(dados.get("data")),
          horario: texto(dados.get("horario")),
          status: "PENDENTE",
        }),
      })
      const detalhe = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      evento.currentTarget.reset()
      fecharNovaVisita()
      setSucesso("Visita agendada.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível agendar a visita.")
    } finally {
      setSalvando(false)
    }
  }

  async function atualizarStatus(visita: Visita, status: string) {
    setSalvando(true)
    setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(visita.id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      const detalhe = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      await carregar()
    } finally {
      setSalvando(false)
    }
  }

  async function confirmarRealizada(visita: Visita) {
    try {
      await atualizarStatus(visita, "CONCLUIDA")
      if (visita.oportunidadeId) {
        router.push(`/crm-app/historico/${encodeURIComponent(visita.oportunidadeId)}?origem=visitas`)
        return
      }
      setDecisao(visita)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível confirmar a visita.")
    }
  }

  async function confirmarNaoRealizada(visita: Visita) {
    try {
      await atualizarStatus(visita, "CANCELADA")
      setSucesso("Visita marcada como não realizada.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível atualizar a visita.")
    }
  }

  function abrirOportunidade(visita: Visita) {
    const params = new URLSearchParams({ cliente: visita.clienteId, nome: visita.cliente, origem: "visita", visita: visita.id })
    router.push(`/crm-app/oportunidades/nova?${params.toString()}`)
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-6xl">
    <header className="mb-5 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Visitas</h1><p className="text-sm text-slate-400">Agende. Confirme se ocorreu. Se houver negócio, acompanhe o ciclo comercial.</p></div></div><button onClick={() => setNovaAberta(true)} className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-500 px-4 font-bold text-slate-950"><Plus size={18}/>Agendar visita</button></header>

    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}

    <section className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4"><Resumo valor={resumo.hoje} label="Hoje"/><Resumo valor={resumo.agendadas} label="Futuras"/><Resumo valor={resumo.confirmar} label="A confirmar"/><Resumo valor={resumo.realizadas} label="Realizadas"/></section>

    <section className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto]"><label className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente ou objetivo" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label><select value={filtro} onChange={(e) => setFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#16325c] bg-[#07162b] px-4"><option value="ATIVAS">Pendentes</option><option value="AGENDADA">Futuras</option><option value="A_CONFIRMAR">A confirmar</option><option value="REALIZADA">Realizadas</option><option value="NAO_REALIZADA">Não realizadas</option><option value="TODAS">Todas</option></select></section>

    {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? <section className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center"><MapPinned className="mx-auto text-cyan-300"/><h2 className="mt-3 text-lg font-bold">Nenhuma visita neste filtro</h2><p className="mt-1 text-sm text-slate-400">O histórico permanece no dossiê do cliente.</p></section> : <div className="space-y-3">{visiveis.map((visita) => {
      const e = estado(visita)
      const finalizada = e === "REALIZADA" || e === "NAO_REALIZADA"
      return <article key={visita.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold text-cyan-300">{rotuloEstado(e)}</p><h2 className="mt-1 text-lg font-bold">{visita.cliente}</h2><p className="text-sm text-slate-300">{visita.titulo}</p>{visita.oportunidade && <p className="mt-1 text-xs text-slate-400">Negócio: {visita.oportunidade}</p>}</div><div className="text-right text-xs text-slate-400"><span className="inline-flex items-center gap-1"><CalendarDays size={14}/>{dataBr(visita.data)}</span>{visita.horario && <span className="mt-1 flex items-center justify-end gap-1"><Clock3 size={14}/>{visita.horario}</span>}</div></div>{visita.descricao && <p className="mt-4 whitespace-pre-line rounded-2xl bg-[#020817]/70 p-3 text-sm leading-6 text-slate-300">{visita.descricao}</p>}<div className="mt-4 flex flex-wrap gap-2">
        {e === "A_CONFIRMAR" && <><button disabled={salvando} onClick={() => void confirmarRealizada(visita)} className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 text-sm font-bold"><CheckCircle2 size={16}/>Visita realizada</button><button disabled={salvando} onClick={() => void confirmarNaoRealizada(visita)} className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl border border-slate-600 px-3 text-sm font-semibold text-slate-200"><XCircle size={16}/>Não realizada</button></>}
        {visita.oportunidadeId && <Link href={`/crm-app/historico/${encodeURIComponent(visita.oportunidadeId)}?origem=visitas`} className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl border border-cyan-700 px-3 text-sm font-semibold text-cyan-200"><BriefcaseBusiness size={16}/>Acompanhar negócio</Link>}
        {finalizada && !visita.oportunidadeId && visita.clienteId && <Link href={`/crm-app/clientes/${encodeURIComponent(visita.clienteId)}?nome=${encodeURIComponent(visita.cliente)}`} className="inline-flex min-h-11 flex-1 items-center justify-center rounded-xl border border-[#24466f] px-3 text-sm font-semibold">Ver cliente</Link>}
      </div></article>
    })}</div>}
  </div>

  {novaAberta && <Modal titulo="Agendar visita" fechar={fecharNovaVisita}><form onSubmit={criarVisita} className="grid gap-4 sm:grid-cols-2">
    <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Cliente</span><input value={clienteBusca} onChange={(e) => { setClienteBusca(e.target.value); setClienteId(""); setOportunidadeId(""); setOportunidadeBusca("") }} placeholder="Digite nome ou cidade" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/>{clientesFiltrados.length > 0 && <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{clientesFiltrados.map((item) => <button type="button" key={item.id} onClick={() => { setClienteId(item.id); setClienteBusca(item.nome) }} className="block min-h-12 w-full border-b border-[#16325c] px-4 text-left last:border-0"><strong>{item.nome}</strong><span className="ml-2 text-xs text-slate-400">{[item.cidade,item.uf].filter(Boolean).join("/")}</span></button>)}</div>}</label>
    <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Negócio existente (opcional)</span><input disabled={!clienteId} value={oportunidadeBusca} onChange={(e) => { setOportunidadeBusca(e.target.value); setOportunidadeId("") }} placeholder={clienteId ? "Digite o nome do negócio" : "Selecione o cliente primeiro"} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 disabled:opacity-50"/>{oportunidadesFiltradas.length > 0 && <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{oportunidadesFiltradas.map((item) => <button type="button" key={item.id} onClick={() => { setOportunidadeId(item.id); setOportunidadeBusca(item.titulo) }} className="block min-h-12 w-full border-b border-[#16325c] px-4 text-left last:border-0"><strong>{item.titulo}</strong></button>)}</div>}</label>
    <Campo name="titulo" label="Objetivo resumido"/><Campo name="data" label="Data" type="date" valor={hoje()}/><Campo name="horario" label="Horário" type="time"/><label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Contexto da visita</span><textarea name="objetivo" rows={4} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label><button disabled={salvando || !clienteId} className="sm:col-span-2 min-h-12 rounded-2xl bg-cyan-500 font-bold text-slate-950 disabled:opacity-50">Agendar</button>
  </form></Modal>}

  {decisao && <Modal titulo="Visita realizada" fechar={() => setDecisao(null)}><div className="space-y-4"><div className="rounded-2xl bg-[#020817] p-4"><p className="font-bold">{decisao.cliente}</p><p className="mt-1 text-sm text-slate-400">A visita já está registrada como realizada.</p></div><p className="text-sm leading-6 text-slate-300">Existe possibilidade comercial que precisa ser acompanhada até ganho ou perda?</p><div className="grid gap-2 sm:grid-cols-2"><button onClick={() => { setDecisao(null); setSucesso("Visita encerrada sem oportunidade comercial.") }} className="min-h-12 rounded-2xl border border-[#24466f] font-semibold">Não. Encerrar aqui</button><button onClick={() => abrirOportunidade(decisao)} className="min-h-12 rounded-2xl bg-cyan-500 font-bold text-slate-950">Sim. Abrir oportunidade</button></div></div></Modal>}
  </main>
}

function Resumo({ valor, label }: { valor: number; label: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><strong className="text-2xl text-cyan-300">{valor}</strong><span className="mt-1 block text-xs text-slate-400">{label}</span></div>
}

function Campo({ name, label, type = "text", valor }: { name: string; label: string; type?: string; valor?: string }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} defaultValue={valor} required={name !== "horario"} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label>
}

function Modal({ titulo, fechar, children }: { titulo: string; fechar: () => void; children: React.ReactNode }) {
  return <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-slate-950/85 p-4"><section className="my-6 w-full max-w-2xl rounded-3xl border border-[#24466f] bg-[#07162b] p-5 shadow-2xl"><div className="mb-5 flex items-center justify-between gap-3"><h2 className="text-xl font-bold">{titulo}</h2><button type="button" onClick={fechar} className="grid size-10 place-items-center rounded-xl border border-[#24466f]">×</button></div>{children}</section></div>
}
