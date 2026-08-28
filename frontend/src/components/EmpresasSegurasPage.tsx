"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import {
  getClientes,
  getClientesCanonicosSeguros,
  getCrmResumoEmpresasSeguro,
  type ClienteCanonicoSeguro,
  type CrmResumoEmpresaSeguro,
  type EmpresaResumoItem,
} from "@/services/modulos-api"

type Oportunidade = { id?: string; cliente_id?: string; titulo?: string; status?: string; valor_estimado?: number }
type Proposta = { id?: string; cliente_id?: string; numero?: string; status?: string; valor?: number }
type Pedido = { id?: string; cliente_id?: string; numero?: string; status?: string; status_ciclo?: string; valor?: number }
type Atividade = { id?: string; cliente_id?: string; titulo?: string; status?: string; data?: string; data_atividade?: string }

const ENCERRADOS = new Set(["GANHO", "PERDIDO", "CANCELADO", "ENCERRADO"])

function normalizar(valor?: string) {
  return String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim()
}
function digitos(valor?: string) { return String(valor || "").replace(/\D/g, "") }
function moeda(valor?: number) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function cnpj(valor?: string) {
  const d = digitos(valor)
  return d.length === 14 ? d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5") : String(valor || "")
}

export default function EmpresasSegurasPage() {
  const { contextoAtual, queryString } = useOperationalContext()
  const [historico, setHistorico] = useState<EmpresaResumoItem[]>([])
  const [clientes, setClientes] = useState<ClienteCanonicoSeguro[]>([])
  const [crm, setCrm] = useState<CrmResumoEmpresaSeguro>({ oportunidades: [], propostas: [], pedidos: [], atividades: [] })
  const [busca, setBusca] = useState("")
  const [selecionada, setSelecionada] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    void (async () => {
      setLoading(true); setErro("")
      try {
        const [h, c, r] = await Promise.all([
          getClientes(queryString),
          getClientesCanonicosSeguros(),
          getCrmResumoEmpresasSeguro(),
        ])
        if (!ativo) return
        setHistorico(Array.isArray(h) ? h : [])
        setClientes(Array.isArray(c) ? c : [])
        setCrm(r || { oportunidades: [], propostas: [], pedidos: [], atividades: [] })
      } catch (e) {
        if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar Empresas.")
      } finally { if (ativo) setLoading(false) }
    })()
    return () => { ativo = false }
  }, [queryString])

  const clientePorId = useMemo(() => new Map(clientes.map(item => [String(item.id), item])), [clientes])
  const clientePorNome = useMemo(() => new Map(clientes.map(item => [normalizar(item.nome), item])), [clientes])

  const oportunidades = (crm.oportunidades || []) as Oportunidade[]
  const propostas = (crm.propostas || []) as Proposta[]
  const pedidos = (crm.pedidos || []) as Pedido[]
  const atividades = (crm.atividades || []) as Atividade[]

  const mapaCrm = useMemo(() => {
    const mapa = new Map<string, { oportunidades: Oportunidade[]; propostas: Proposta[]; pedidos: Pedido[]; atividades: Atividade[] }>()
    const obter = (clienteId?: string) => {
      const cliente = clienteId ? clientePorId.get(String(clienteId)) : undefined
      if (!cliente) return null
      const chave = normalizar(cliente.nome)
      if (!mapa.has(chave)) mapa.set(chave, { oportunidades: [], propostas: [], pedidos: [], atividades: [] })
      return mapa.get(chave)!
    }
    oportunidades.forEach(item => obter(item.cliente_id)?.oportunidades.push(item))
    propostas.forEach(item => obter(item.cliente_id)?.propostas.push(item))
    pedidos.forEach(item => obter(item.cliente_id)?.pedidos.push(item))
    atividades.forEach(item => obter(item.cliente_id)?.atividades.push(item))
    return mapa
  }, [atividades, clientePorId, oportunidades, pedidos, propostas])

  const lista = useMemo(() => historico.filter(item => {
    const cliente = clientePorNome.get(normalizar(item.nome))
    const texto = normalizar([item.nome, cliente?.razao_social, cliente?.nome_fantasia, cliente?.cnpj, ...(item.chassis || []), ...(item.placas || []), ...(item.implementadoras || [])].filter(Boolean).join(" "))
    const termo = normalizar(busca)
    const termoCnpj = digitos(busca)
    return texto.includes(termo) || (!!termoCnpj && digitos(cliente?.cnpj).includes(termoCnpj))
  }), [busca, clientePorNome, historico])

  const abertas = oportunidades.filter(item => !ENCERRADOS.has(String(item.status || "").toUpperCase()))
  const pipeline = abertas.reduce((s, item) => s + Number(item.valor_estimado || 0), 0)
  const selecionadaHistorico = selecionada ? historico.find(item => normalizar(item.nome) === normalizar(selecionada)) : undefined
  const selecionadaCliente = selecionada ? clientePorNome.get(normalizar(selecionada)) : undefined
  const selecionadaCrm = selecionada ? mapaCrm.get(normalizar(selecionada)) : undefined

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
      <header><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Cadastro Mestre de Clientes</p><h1 className="mt-2 text-3xl font-bold">Empresas</h1><p className="mt-2 text-sm text-slate-400">Pesquisa cadastral e histórica permanece disponível. O quadro comercial em curso respeita o responsável autenticado.</p><p className="mt-2 text-sm text-cyan-300">Contexto: {contextoAtual.label}</p></header>
      {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi titulo="Empresas históricas" valor={loading ? "..." : historico.length.toLocaleString("pt-BR")} />
        <Kpi titulo="Negócios em curso" valor={loading ? "..." : abertas.length.toLocaleString("pt-BR")} />
        <Kpi titulo="Pipeline autorizado" valor={loading ? "..." : moeda(pipeline)} />
        <Kpi titulo="Clientes cadastrados" valor={loading ? "..." : clientes.length.toLocaleString("pt-BR")} />
      </section>
      <section className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5 sm:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><h2 className="text-xl font-bold">Empresas — mercado × responsabilidade comercial</h2><p className="mt-1 text-sm text-slate-400">Buscar uma empresa não transfere sua propriedade comercial. O vendedor pode localizar qualquer cadastro necessário para iniciar uma nova negociação.</p></div><input value={busca} onChange={e => setBusca(e.target.value)} placeholder="Buscar empresa, CNPJ, chassi, placa ou implementadora" className="rounded-xl border border-[#13203f] bg-[#071028] px-4 py-3 text-white" /></div>
        {loading ? <p className="mt-8 text-slate-400">Carregando dados reais...</p> : <div className="mt-6 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead><tr className="border-b border-[#13203f] text-slate-400"><th className="p-3">Empresa</th><th className="p-3">REALIZADO</th><th className="p-3">EM CURSO</th><th className="p-3">Ação</th></tr></thead><tbody>{lista.map(item => {
          const cliente = clientePorNome.get(normalizar(item.nome)); const atual = mapaCrm.get(normalizar(item.nome)); const ops = atual?.oportunidades.filter(o => !ENCERRADOS.has(String(o.status || "").toUpperCase())) || []; const valor = ops.reduce((s,o) => s + Number(o.valor_estimado || 0), 0)
          return <tr key={item.nome} className="border-b border-[#13203f] hover:bg-cyan-500/5"><td className="p-3"><strong>{item.nome}</strong>{cliente?.cnpj && <div className="mt-1 text-xs text-cyan-300">CNPJ {cnpj(cliente.cnpj)}</div>}<div className="text-xs text-slate-500">{cliente?.cidade || ""}{cliente?.estado ? ` / ${cliente.estado}` : ""}</div></td><td className="p-3"><div className="text-cyan-200">{item.quantidade_registros} registros</div><div className="text-xs text-slate-500">{moeda(item.valor_total)}</div></td><td className="p-3"><div>{ops.length} negócio(s)</div><div className="text-xs text-emerald-300">{moeda(valor)}</div></td><td className="p-3"><button onClick={() => setSelecionada(item.nome)} className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-300">Abrir empresa</button></td></tr>
        })}</tbody></table></div>}
      </section>
      {selecionada && <section className="rounded-2xl border border-cyan-800 bg-[#071427] p-5 sm:p-6"><div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[.16em] text-cyan-400">Empresa selecionada</p><h2 className="mt-1 text-2xl font-bold">{selecionada}</h2>{selecionadaCliente?.cnpj && <p className="mt-1 text-sm text-cyan-300">CNPJ {cnpj(selecionadaCliente.cnpj)}</p>}</div><button onClick={() => setSelecionada(null)} className="rounded-lg border border-slate-700 px-3 py-2 text-xs">Fechar</button></div><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4"><Kpi titulo="Histórico" valor={`${selecionadaHistorico?.quantidade_registros || 0} registros`} /><Kpi titulo="Oportunidades autorizadas" valor={String(selecionadaCrm?.oportunidades.length || 0)} /><Kpi titulo="Propostas autorizadas" valor={String(selecionadaCrm?.propostas.length || 0)} /><Kpi titulo="Pedidos / atividades" valor={`${selecionadaCrm?.pedidos.length || 0} / ${selecionadaCrm?.atividades.length || 0}`} /></div><div className="mt-5 flex flex-wrap gap-3">{(selecionadaCrm?.oportunidades || []).map(op => op.id && <Link key={op.id} href={`/oportunidades/${op.id}`} className="rounded-lg border border-cyan-800 px-3 py-2 text-xs text-cyan-200">{op.titulo || "Abrir oportunidade"}</Link>)}</div></section>}
    </div></section>
  </main>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-xl font-bold text-cyan-300">{valor}</p></div>
}
