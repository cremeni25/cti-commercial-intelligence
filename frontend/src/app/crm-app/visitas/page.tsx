"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Loader2,
  MapPinned,
  Play,
  Plus,
  Search,
  Target,
  X,
} from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; cidade: string; uf: string }
type Oportunidade = { id: string; clienteId: string; cliente: string; titulo: string }
type Visita = {
  id: string
  clienteId: string
  cliente: string
  oportunidadeId: string
  oportunidade: string
  titulo: string
  descricao: string
  data: string
  horario: string
  status: string
}

type Encerramento = {
  visita: Visita
  resultado: string
  desfecho: string
  proximaAcao: string
  proximaData: string
}

const STATUS_CONCLUIDOS = new Set(["CONCLUIDA", "CONCLUÍDA", "REALIZADA"])

function texto(valor: unknown) {
  return String(valor || "").trim()
}

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["dados", "itens", "resultado", "atividades", "oportunidades"]) {
      if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
    }
  }
  return []
}

function dataHoje() {
  return new Date().toISOString().slice(0, 10)
}

function dataBr(data: string) {
  if (!data) return "Data não informada"
  return new Date(`${data}T12:00:00`).toLocaleDateString("pt-BR")
}

function clienteDe(item: Registro): Cliente | null {
  const nome = texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente)
  if (!nome) return null
  return {
    id: texto(item.id || item.cliente_id || item.uuid) || nome,
    nome,
    cidade: texto(item.cidade || item.municipio),
    uf: texto(item.estado || item.uf).toUpperCase(),
  }
}

function statusOperacional(visita: Visita) {
  const status = visita.status.toUpperCase()
  if (STATUS_CONCLUIDOS.has(status)) return "CONCLUIDA"
  if (status === "EM_ANDAMENTO" || status === "INICIADA") return "EM_ANDAMENTO"
  if (visita.data && visita.data < dataHoje()) return "ATRASADA"
  return "AGENDADA"
}

function descricaoEstruturada(objetivo: string, resultado?: string, desfecho?: string, proximaAcao?: string) {
  const linhas = [`[OBJETIVO]\n${objetivo.trim() || "Não informado"}`]
  if (resultado) linhas.push(`[RESULTADO]\n${resultado.trim()}`)
  if (desfecho) linhas.push(`[DESFECHO]\n${desfecho.trim()}`)
  if (proximaAcao) linhas.push(`[PRÓXIMA AÇÃO]\n${proximaAcao.trim()}`)
  return linhas.join("\n\n")
}

export default function VisitasPage() {
  const { usuario } = useAuth()
  const [visitas, setVisitas] = useState<Visita[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [busca, setBusca] = useState("")
  const [filtro, setFiltro] = useState("TODAS")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [novaAberta, setNovaAberta] = useState(false)
  const [clienteId, setClienteId] = useState("")
  const [encerramento, setEncerramento] = useState<Encerramento | null>(null)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const [atividadesResposta, clientesResposta, oportunidadesResposta] = await Promise.all([
        fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }),
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }),
        fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
      ])
      if (!atividadesResposta.ok) throw new Error(`Não foi possível carregar as visitas (${atividadesResposta.status}).`)

      const atividadesPayload = await atividadesResposta.json()
      const clientesPayload = clientesResposta.ok ? await clientesResposta.json() : []
      const oportunidadesPayload = oportunidadesResposta.ok ? await oportunidadesResposta.json() : []

      const clientesNormalizados = lista(clientesPayload)
        .map(clienteDe)
        .filter(Boolean) as Cliente[]
      const clientesUnicos = new Map(clientesNormalizados.map((cliente) => [cliente.id, cliente]))
      setClientes([...clientesUnicos.values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))

      const oportunidadesNormalizadas = lista(oportunidadesPayload).map((item) => ({
        id: texto(item.id || item.oportunidade_id),
        clienteId: texto(item.cliente_id),
        cliente: texto(item.cliente_nome || item.cliente || item.empresa),
        titulo: texto(item.titulo || item.equipamento) || "Oportunidade",
      })).filter((item) => item.id)
      setOportunidades(oportunidadesNormalizadas)

      const nomesClientes = new Map(clientesNormalizados.map((cliente) => [cliente.id, cliente.nome]))
      const nomesOportunidades = new Map(oportunidadesNormalizadas.map((item) => [item.id, item.titulo]))
      const visitasNormalizadas = lista(atividadesPayload)
        .filter((item) => texto(item.tipo || item.tipo_atividade).toUpperCase().includes("VISITA"))
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
        })
        .filter((item) => item.id)
        .sort((a, b) => `${a.data}${a.horario}`.localeCompare(`${b.data}${b.horario}`))
      setVisitas(visitasNormalizadas)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o módulo de visitas.")
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => { void carregar() }, [carregar])

  const resumo = useMemo(() => {
    const estados = visitas.map(statusOperacional)
    return {
      hoje: visitas.filter((visita) => visita.data === dataHoje() && !STATUS_CONCLUIDOS.has(visita.status)).length,
      atrasadas: estados.filter((estado) => estado === "ATRASADA").length,
      andamento: estados.filter((estado) => estado === "EM_ANDAMENTO").length,
      concluidas: estados.filter((estado) => estado === "CONCLUIDA").length,
    }
  }, [visitas])

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return visitas.filter((visita) => {
      const estado = statusOperacional(visita)
      const atendeFiltro = filtro === "TODAS" || estado === filtro
      const atendeBusca = !termo || `${visita.cliente} ${visita.titulo} ${visita.oportunidade}`.toLocaleLowerCase("pt-BR").includes(termo)
      return atendeFiltro && atendeBusca
    })
  }, [busca, filtro, visitas])

  const oportunidadesDoCliente = useMemo(
    () => oportunidades.filter((oportunidade) => !clienteId || oportunidade.clienteId === clienteId),
    [clienteId, oportunidades],
  )

  async function criarVisita(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const clienteSelecionado = texto(dados.get("cliente_id"))
    const titulo = texto(dados.get("titulo"))
    const objetivo = texto(dados.get("objetivo"))
    if (!clienteSelecionado || !titulo || !objetivo || !usuario?.id) {
      setErro("Informe cliente, título, objetivo e confirme o usuário autenticado.")
      setSalvando(false)
      return
    }
    const payload = {
      cliente_id: clienteSelecionado,
      oportunidade_id: texto(dados.get("oportunidade_id")) || null,
      usuario_id: String(usuario.id),
      tipo: "VISITA",
      titulo,
      descricao: descricaoEstruturada(objetivo),
      data: texto(dados.get("data")),
      horario: texto(dados.get("horario")),
      status: "PENDENTE",
    }
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const detalhe = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      evento.currentTarget.reset()
      setClienteId("")
      setNovaAberta(false)
      setSucesso("Visita agendada e sincronizada com o CTI.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível agendar a visita.")
    } finally {
      setSalvando(false)
    }
  }

  async function iniciar(visita: Visita) {
    setErro(""); setSucesso("")
    const resposta = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(visita.id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "EM_ANDAMENTO" }),
    })
    const detalhe = await resposta.json().catch(() => ({})) as Registro
    if (!resposta.ok) return setErro(texto(detalhe.detail) || "Não foi possível iniciar a visita.")
    setSucesso("Visita iniciada. Registre o resultado ao final.")
    await carregar()
  }

  async function concluirVisita(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!encerramento || !usuario?.id) return
    setSalvando(true); setErro(""); setSucesso("")
    const dados = new FormData(evento.currentTarget)
    const resultado = texto(dados.get("resultado"))
    const desfecho = texto(dados.get("desfecho"))
    const proximaAcao = texto(dados.get("proxima_acao"))
    const proximaData = texto(dados.get("proxima_data"))
    if (!resultado || !desfecho) {
      setErro("Informe o resultado e o desfecho da visita.")
      setSalvando(false)
      return
    }
    try {
      const atualizar = await fetch(`/api/crm-proxy/crm/atividades/${encodeURIComponent(encerramento.visita.id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: "CONCLUIDA",
          descricao: descricaoEstruturada(encerramento.visita.descricao, resultado, desfecho, proximaAcao),
        }),
      })
      const detalhe = await atualizar.json().catch(() => ({})) as Registro
      if (!atualizar.ok) throw new Error(texto(detalhe.detail) || `Falha ${atualizar.status}`)

      if (proximaAcao && proximaData) {
        const proxima = await fetch("/api/crm-proxy/crm/atividades", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cliente_id: encerramento.visita.clienteId,
            oportunidade_id: encerramento.visita.oportunidadeId || null,
            usuario_id: String(usuario.id),
            tipo: "FOLLOW_UP",
            titulo: proximaAcao,
            descricao: `Próxima ação definida após a visita: ${encerramento.visita.titulo}`,
            data: proximaData,
            horario: null,
            status: "PENDENTE",
          }),
        })
        if (!proxima.ok) throw new Error("A visita foi concluída, mas a próxima ação não pôde ser criada.")
      }

      setEncerramento(null)
      setSucesso("Resultado registrado. Histórico e próxima ação sincronizados com o CTI.")
      await carregar()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir a visita.")
    } finally {
      setSalvando(false)
    }
  }

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
            <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Visitas comerciais</h1><p className="text-sm text-slate-400">Prepare, execute, registre o resultado e defina a próxima ação</p></div>
          </div>
          <button onClick={() => setNovaAberta(true)} className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-500 px-4 font-bold text-slate-950"><Plus size={18}/>Nova visita</button>
        </header>

        {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
        {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-emerald-200">{sucesso}</div>}

        <section className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Resumo valor={resumo.hoje} label="Hoje" />
          <Resumo valor={resumo.atrasadas} label="Atrasadas" />
          <Resumo valor={resumo.andamento} label="Em andamento" />
          <Resumo valor={resumo.concluidas} label="Concluídas" />
        </section>

        <section className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto]">
          <label className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, oportunidade ou objetivo" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label>
          <select value={filtro} onChange={(e) => setFiltro(e.target.value)} className="h-12 rounded-2xl border border-[#16325c] bg-[#07162b] px-4"><option value="TODAS">Todas</option><option value="AGENDADA">Agendadas</option><option value="ATRASADA">Atrasadas</option><option value="EM_ANDAMENTO">Em andamento</option><option value="CONCLUIDA">Concluídas</option></select>
        </section>

        {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : visiveis.length === 0 ? (
          <section className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center"><MapPinned className="mx-auto text-cyan-300"/><h2 className="mt-3 text-lg font-bold">Nenhuma visita neste filtro</h2><p className="mt-1 text-sm text-slate-400">Agende a primeira visita ou altere o filtro para consultar o histórico.</p><button onClick={() => setNovaAberta(true)} className="mt-4 rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950">Agendar visita</button></section>
        ) : <div className="space-y-3">{visiveis.map((visita) => {
          const estado = statusOperacional(visita)
          return <article key={visita.id} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:p-5">
            <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold text-cyan-300">{estado.replace("_", " ")}</p><h2 className="mt-1 text-lg font-bold">{visita.cliente}</h2><p className="text-sm text-slate-300">{visita.titulo}</p>{visita.oportunidade && <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-400"><BriefcaseBusiness size={14}/>{visita.oportunidade}</p>}</div><div className="text-right text-xs text-slate-400"><span className="inline-flex items-center gap-1"><CalendarDays size={14}/>{dataBr(visita.data)}</span>{visita.horario && <span className="mt-1 flex items-center justify-end gap-1"><Clock3 size={14}/>{visita.horario}</span>}</div></div>
            {visita.descricao && <p className="mt-4 whitespace-pre-line rounded-2xl bg-[#020817]/70 p-3 text-sm leading-6 text-slate-300">{visita.descricao}</p>}
            <div className="mt-4 grid gap-2 sm:grid-cols-3"><Link href={visita.oportunidadeId ? `/crm-app/historico/${visita.oportunidadeId}?origem=visitas` : `/crm-app/clientes?busca=${encodeURIComponent(visita.cliente)}`} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#24466f] px-3 py-3 text-sm"><Target size={16}/>Preparar visita</Link>{estado !== "CONCLUIDA" && estado !== "EM_ANDAMENTO" && <button onClick={() => void iniciar(visita)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-3 py-3 text-sm font-semibold text-cyan-200"><Play size={16}/>Iniciar visita</button>}{estado !== "CONCLUIDA" && <button onClick={() => setEncerramento({ visita, resultado: "", desfecho: "", proximaAcao: "", proximaData: "" })} className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-3 text-sm font-bold"><CheckCircle2 size={16}/>Registrar resultado</button>}</div>
          </article>
        })}</div>}
      </div>

      {novaAberta && <Modal titulo="Agendar nova visita" fechar={() => setNovaAberta(false)}><form onSubmit={criarVisita} className="grid gap-4 sm:grid-cols-2"><CampoSelect name="cliente_id" label="Cliente" valor={clienteId} alterar={setClienteId} opcoes={clientes.map((cliente) => ({ valor: cliente.id, texto: `${cliente.nome}${cliente.cidade ? ` · ${cliente.cidade}/${cliente.uf}` : ""}` }))}/><CampoSelect name="oportunidade_id" label="Oportunidade relacionada" opcoes={[{ valor: "", texto: "Sem oportunidade vinculada" }, ...oportunidadesDoCliente.map((oportunidade) => ({ valor: oportunidade.id, texto: `${oportunidade.cliente} · ${oportunidade.titulo}` }))]}/><Campo name="titulo" label="Objetivo resumido" placeholder="Ex.: Apresentar proposta Supra 750"/><Campo name="data" label="Data" type="date" valor={dataHoje()}/><Campo name="horario" label="Horário" type="time"/><label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Preparação e objetivo da visita</span><textarea name="objetivo" rows={5} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3" placeholder="O que precisa ser confirmado, apresentado ou negociado?"/></label><button disabled={salvando} className="sm:col-span-2 inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-cyan-500 font-bold text-slate-950">{salvando ? <Loader2 className="animate-spin"/> : <CalendarDays size={18}/>}Agendar visita</button></form></Modal>}

      {encerramento && <Modal titulo="Registrar resultado da visita" fechar={() => setEncerramento(null)}><form onSubmit={concluirVisita} className="grid gap-4"><div className="rounded-2xl bg-[#020817] p-4"><p className="font-bold">{encerramento.visita.cliente}</p><p className="text-sm text-slate-400">{encerramento.visita.titulo}</p></div><label><span className="mb-2 block text-sm text-slate-300">Resultado obtido</span><textarea name="resultado" rows={4} required className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3" placeholder="Registre fatos, necessidades, objeções e decisões."/></label><CampoSelect name="desfecho" label="Desfecho" opcoes={[{ valor: "", texto: "Selecione" }, { valor: "AVANÇOU", texto: "Avançou" }, { valor: "MANTEVE", texto: "Manteve estágio" }, { valor: "SEM INTERESSE", texto: "Sem interesse" }, { valor: "PERDIDA PARA CONCORRENTE", texto: "Perdida para concorrente" }, { valor: "PEDIDO / FECHAMENTO", texto: "Pedido / fechamento" }]}/><Campo name="proxima_acao" label="Próxima ação" placeholder="Ex.: Enviar revisão da proposta"/><Campo name="proxima_data" label="Data da próxima ação" type="date"/><button disabled={salvando} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-emerald-600 font-bold">{salvando ? <Loader2 className="animate-spin"/> : <CheckCircle2 size={18}/>}Concluir e sincronizar</button></form></Modal>}
    </main>
  )
}

function Resumo({ valor, label }: { valor: number; label: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><strong className="text-2xl text-cyan-300">{valor}</strong><span className="mt-1 block text-xs text-slate-400">{label}</span></div>
}

function Modal({ titulo, fechar, children }: { titulo: string; fechar: () => void; children: React.ReactNode }) {
  return <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 p-4"><div className="mx-auto my-6 max-w-2xl rounded-3xl border border-[#24466f] bg-[#07162b] p-5 text-white shadow-2xl"><header className="mb-5 flex items-center justify-between"><h2 className="text-xl font-bold">{titulo}</h2><button onClick={fechar} className="rounded-xl border border-[#24466f] p-2 text-slate-300"><X size={18}/></button></header>{children}</div></div>
}

function Campo({ name, label, type = "text", valor, placeholder }: { name: string; label: string; type?: string; valor?: string; placeholder?: string }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} defaultValue={valor} placeholder={placeholder} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label>
}

function CampoSelect({ name, label, opcoes, valor, alterar }: { name: string; label: string; opcoes: { valor: string; texto: string }[]; valor?: string; alterar?: (valor: string) => void }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><select name={name} value={alterar ? valor : undefined} defaultValue={alterar ? undefined : valor} onChange={alterar ? (evento) => alterar(evento.target.value) : undefined} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"><option value="">Selecione</option>{opcoes.filter((opcao, indice, todos) => todos.findIndex((item) => item.valor === opcao.valor) === indice).map((opcao) => <option key={`${name}-${opcao.valor}-${opcao.texto}`} value={opcao.valor}>{opcao.texto}</option>)}</select></label>
}
