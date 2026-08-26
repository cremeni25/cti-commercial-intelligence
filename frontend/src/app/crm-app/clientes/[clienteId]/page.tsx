"use client"

import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Loader2,
  MapPin,
  MessageSquarePlus,
  Pencil,
  Plus,
  Target,
} from "lucide-react"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; codigo: string; cidade: string; uf: string }
type Negocio = { id: string; titulo: string; etapa: string; valor: number; fechamento: string }
type Atividade = { id: string; tipo: string; titulo: string; descricao: string; data: string; status: string; oportunidadeId: string }

function texto(valor: unknown) { return String(valor ?? "").trim() }
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
function chave(valor: unknown) {
  return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR")
}
function dataIso(valor: unknown) { return texto(valor).slice(0, 10) }
function dataBr(valor: string) {
  if (!valor) return "Não informada"
  const data = new Date(`${valor}T12:00:00`)
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleDateString("pt-BR")
}
function concluida(status: string) { return ["CONCLUIDA", "CONCLUÍDA", "REALIZADA"].includes(status.toUpperCase()) }

export default function DossieClientePage() {
  const params = useParams<{ clienteId: string }>()
  const search = useSearchParams()
  const clienteId = decodeURIComponent(String(params.clienteId || ""))
  const nomeEsperado = search.get("nome") || ""
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [negocios, setNegocios] = useState<Negocio[]>([])
  const [atividades, setAtividades] = useState<Atividade[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    async function carregar() {
      setCarregando(true); setErro("")
      try {
        const [clientesResposta, nucleoResposta, atividadesResposta] = await Promise.all([
          fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }),
          fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
          fetch("/api/crm-proxy/crm/atividades", { cache: "no-store" }),
        ])
        if (!nucleoResposta.ok) throw new Error(`Não foi possível carregar o núcleo comercial (${nucleoResposta.status}).`)
        const clientesPayload = clientesResposta.ok ? await clientesResposta.json() : []
        const nucleoPayload = await nucleoResposta.json()
        const atividadesPayload = atividadesResposta.ok ? await atividadesResposta.json() : []
        if (!ativo) return

        const clientes = lista(clientesPayload)
        const alvoNome = chave(nomeEsperado)
        const cadastro = clientes.find((item) => {
          const id = texto(item.id || item.cliente_id || item.codigo || item.codigo_cliente)
          const nome = chave(item.nome || item.empresa || item.razao_social || item.nome_fantasia || item.cliente)
          return id === clienteId || (!!alvoNome && nome === alvoNome)
        })
        const registrosNucleo = lista(nucleoPayload)
        const negocioBase = registrosNucleo.find((item) => texto(item.cliente_id) === clienteId || (!!alvoNome && chave(item.cliente_nome || item.razao_social || item.nome_cliente || item.cliente) === alvoNome))
        const nome = texto(cadastro?.nome || cadastro?.empresa || cadastro?.razao_social || cadastro?.nome_fantasia || negocioBase?.cliente_nome || negocioBase?.cliente || nomeEsperado) || "Cliente"
        const clienteNormalizado = {
          id: texto(cadastro?.id || cadastro?.cliente_id || negocioBase?.cliente_id) || clienteId,
          nome,
          codigo: texto(cadastro?.codigo || cadastro?.codigo_cliente),
          cidade: texto(cadastro?.cidade || cadastro?.municipio || negocioBase?.cliente_cidade || negocioBase?.municipio),
          uf: texto(cadastro?.estado || cadastro?.uf || negocioBase?.cliente_estado || negocioBase?.uf).toUpperCase(),
        }
        setCliente(clienteNormalizado)
        const nomeChave = chave(nome)

        setNegocios(registrosNucleo.filter((item) => texto(item.cliente_id) === clienteNormalizado.id || chave(item.cliente_nome || item.razao_social || item.nome_cliente || item.cliente) === nomeChave).map((item) => ({
          id: texto(item.oportunidade_id || item.id),
          titulo: texto(item.titulo || item.equipamento) || "Oportunidade comercial",
          etapa: texto(item.etapa || item.status_oportunidade || item.status) || "OPORTUNIDADE",
          valor: Number(item.valor || item.valor_estimado || 0),
          fechamento: dataIso(item.data_fechamento_prevista || item.fechamento_previsto),
        })).filter((item) => item.id))

        setAtividades(lista(atividadesPayload).filter((item) => texto(item.cliente_id) === clienteNormalizado.id || chave(item.cliente_nome || item.cliente) === nomeChave).map((item) => ({
          id: texto(item.id || item.atividade_id),
          tipo: texto(item.tipo || item.tipo_atividade) || "ATIVIDADE",
          titulo: texto(item.titulo || item.assunto) || "Registro comercial",
          descricao: texto(item.descricao),
          data: dataIso(item.data || item.data_atividade || item.inicio),
          status: texto(item.status || item.situacao) || "PENDENTE",
          oportunidadeId: texto(item.oportunidade_id),
        })).sort((a, b) => b.data.localeCompare(a.data)))
      } catch (falha) {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o dossiê comercial.")
      } finally { if (ativo) setCarregando(false) }
    }
    void carregar()
    return () => { ativo = false }
  }, [clienteId, nomeEsperado])

  const hoje = new Date().toISOString().slice(0, 10)
  const realizadas = useMemo(() => atividades.filter((item) => concluida(item.status)), [atividades])
  const pendentes = useMemo(() => atividades.filter((item) => !concluida(item.status)), [atividades])
  const ultimaVisita = useMemo(() => realizadas.find((item) => item.tipo.toUpperCase().includes("VISITA")), [realizadas])
  const proximaAcao = useMemo(() => [...pendentes].filter((item) => item.data).sort((a, b) => a.data.localeCompare(b.data))[0], [pendentes])
  const atrasadas = useMemo(() => pendentes.filter((item) => item.data && item.data < hoje).length, [pendentes, hoje])
  const pipeline = useMemo(() => negocios.reduce((soma, item) => soma + item.valor, 0), [negocios])

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-5xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app/clientes" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Dossiê comercial do cliente</h1><p className="text-sm text-slate-400">Uma visão única da carteira, histórico e próximos passos</p></div>
      </header>

      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-72 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : cliente && <>
        <section className="mb-4 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5">
          <div className="flex items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2/></span><div><h2 className="text-xl font-bold">{cliente.nome}</h2>{cliente.codigo && <p className="mt-1 text-sm text-slate-400">{cliente.codigo}</p>}{cliente.cidade && <p className="mt-1 flex items-center gap-1 text-sm text-slate-300"><MapPin size={15}/>{cliente.cidade}{cliente.uf ? `/${cliente.uf}` : ""}</p>}</div></div><Link href={`/crm-app/clientes/${encodeURIComponent(cliente.id)}/editar`} className="flex shrink-0 items-center gap-2 rounded-xl border border-cyan-800 px-3 py-2 text-xs font-semibold text-cyan-200"><Pencil size={15}/>Editar cadastro</Link></div>
          <div className="mt-5 grid gap-2 sm:grid-cols-3"><Link href={`/crm-app/visitas?cliente=${encodeURIComponent(cliente.id)}`} className="flex items-center justify-center gap-2 rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200"><CalendarClock size={16}/>Agendar visita</Link><Link href={`/crm-app/atividades/nova?cliente=${encodeURIComponent(cliente.id)}&origem=clientes`} className="flex items-center justify-center gap-2 rounded-xl border border-[#24466f] px-4 py-3 text-sm font-semibold"><MessageSquarePlus size={16}/>Registrar atividade</Link><Link href={`/crm-app/oportunidades/nova?cliente=${encodeURIComponent(cliente.id)}&nome=${encodeURIComponent(cliente.nome)}`} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950"><Plus size={16}/>Nova oportunidade</Link></div>
        </section>

        <section className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Resumo label="Negócios" valor={String(negocios.length)} />
          <Resumo label="Pipeline" valor={pipeline.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
          <Resumo label="Pendências" valor={String(pendentes.length)} />
          <Resumo label="Atrasadas" valor={String(atrasadas)} alerta={atrasadas > 0} />
        </section>

        <section className="mb-4 grid gap-3 sm:grid-cols-2">
          <Situacao titulo="Última visita" icone={<CheckCircle2 size={18}/>} principal={ultimaVisita ? ultimaVisita.titulo : "Nenhuma visita concluída"} detalhe={ultimaVisita ? dataBr(ultimaVisita.data) : "O histórico ainda não possui visita realizada."} />
          <Situacao titulo="Próxima ação" icone={proximaAcao && proximaAcao.data < hoje ? <AlertTriangle size={18}/> : <Clock3 size={18}/>} principal={proximaAcao ? proximaAcao.titulo : "Nenhuma próxima ação"} detalhe={proximaAcao ? `${dataBr(proximaAcao.data)} · ${proximaAcao.status}` : "Defina uma atividade para manter o cliente em acompanhamento."} alerta={!!proximaAcao && proximaAcao.data < hoje} />
        </section>

        <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="mb-4 flex items-center gap-2"><Target className="text-cyan-300"/><h2 className="text-lg font-bold">Negociações</h2></div>{negocios.length === 0 ? <p className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhuma oportunidade vinculada. Use “Nova oportunidade” para iniciar uma negociação.</p> : <div className="space-y-2">{negocios.map((item) => <Link key={item.id} href={`/crm-app/historico/${item.id}?origem=clientes`} className="flex items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="min-w-0 flex-1"><strong className="block truncate">{item.titulo}</strong><span className="text-xs text-slate-400">{item.etapa} · {item.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}{item.fechamento ? ` · ${dataBr(item.fechamento)}` : ""}</span></div><ChevronRight className="text-cyan-300" size={18}/></Link>)}</div>}</section>

        <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="mb-4 flex items-center gap-2"><FileText className="text-cyan-300"/><h2 className="text-lg font-bold">Histórico comercial do cliente</h2></div>{atividades.length === 0 ? <p className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhuma atividade registrada para este cliente.</p> : <div className="space-y-3">{atividades.map((item) => <article key={item.id} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><span className="text-xs font-semibold text-cyan-300">{item.tipo}</span><h3 className="mt-1 font-bold">{item.titulo}</h3></div><span className="text-xs text-slate-400">{dataBr(item.data)}</span></div>{item.descricao && <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-300">{item.descricao}</p>}<div className="mt-3 flex flex-wrap items-center justify-between gap-2"><span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">{item.status}</span>{item.oportunidadeId && <Link href={`/crm-app/historico/${item.oportunidadeId}?origem=clientes`} className="text-xs font-semibold text-cyan-300">Abrir negociação →</Link>}</div></article>)}</div>}</section>
      </>}
    </div>
  </main>
}

function Resumo({ label, valor, alerta = false }: { label: string; valor: string; alerta?: boolean }) {
  return <div className={`rounded-2xl border p-4 ${alerta ? "border-amber-800 bg-amber-950/30" : "border-[#16325c] bg-[#07162b]"}`}><strong className={alerta ? "text-xl text-amber-200" : "text-xl text-cyan-300"}>{valor}</strong><span className="mt-1 block text-xs text-slate-400">{label}</span></div>
}
function Situacao({ titulo, icone, principal, detalhe, alerta = false }: { titulo: string; icone: React.ReactNode; principal: string; detalhe: string; alerta?: boolean }) {
  return <div className={`rounded-2xl border p-4 ${alerta ? "border-amber-800 bg-amber-950/30" : "border-[#16325c] bg-[#07162b]"}`}><div className={`mb-2 flex items-center gap-2 text-sm font-semibold ${alerta ? "text-amber-200" : "text-cyan-300"}`}>{icone}{titulo}</div><strong className="block">{principal}</strong><p className="mt-1 text-xs text-slate-400">{detalhe}</p></div>
}
