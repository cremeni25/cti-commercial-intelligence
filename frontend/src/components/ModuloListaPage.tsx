"use client"

import Link from "next/link"
import { useEffect, useMemo, useState, type ReactNode } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { API_URL } from "@/lib/api"
import { type EmpresaResumoItem } from "@/services/modulos-api"

type ClienteCanonico = { id: string; nome: string; razao_social?: string; nome_fantasia?: string; cnpj?: string; cidade?: string; estado?: string; segmento?: string; categoria?: string; status?: string }
type OportunidadeCRM = { id: string; cliente_id?: string; titulo?: string; status?: string; valor_estimado?: number; descricao?: string; data_fechamento_prevista?: string }
type PropostaCRM = { id: string; cliente_id?: string; oportunidade_id?: string; numero?: string; status?: string; valor?: number }
type PedidoCRM = { id: string; cliente_id?: string; proposta_id?: string; numero?: string; status?: string; status_ciclo?: string; valor?: number }
type AtividadeCRM = { id: string; cliente_id?: string; oportunidade_id?: string; titulo?: string; descricao?: string; status?: string; data?: string; data_atividade?: string; horario?: string }
type CrmEmpresa = { oportunidades: OportunidadeCRM[]; propostas: PropostaCRM[]; pedidos: PedidoCRM[]; atividades: AtividadeCRM[]; categoria?: string }

const STATUS_NEGOCIO_ENCERRADO = new Set(["GANHO", "PERDIDO", "CANCELADO", "ENCERRADO"])
const STATUS_PROPOSTA_ENCERRADA = new Set(["APROVADA", "RECUSADA", "EXPIRADA", "CANCELADA"])

function normalizar(valor: string) { return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim() }
function somenteDigitos(valor?: string) { return String(valor || "").replace(/\D/g, "") }
function formatarCnpj(valor?: string) { const d = somenteDigitos(valor); return d.length === 14 ? d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5") : String(valor || "") }
function moeda(valor?: number) { return `R$ ${(valor ?? 0).toLocaleString("pt-BR")}` }
function negocioEmCurso(item: OportunidadeCRM) { return !STATUS_NEGOCIO_ENCERRADO.has(String(item.status || "").toUpperCase()) }
function propostaVigente(item: PropostaCRM) { return !STATUS_PROPOSTA_ENCERRADA.has(String(item.status || "").toUpperCase()) }
function pedidoEmCurso(item: PedidoCRM) { return String(item.status_ciclo || item.status || "").toUpperCase() !== "ENCERRADO" }
function drill(camada: "anfir" | "crm", titulo: string, queryString = "", campo?: string, valor?: string) {
  const query = new URLSearchParams(queryString)
  query.set("camada", camada)
  query.set("titulo", titulo)
  query.set("subtitulo", camada === "anfir" ? "Registros individualizados do realizado no contexto e período ativos" : "Oportunidades em curso que formam este indicador")
  if (campo) query.set("campo", campo)
  if (valor) query.set("valor", valor)
  return `/detalhamento?${query.toString()}`
}
async function buscarJson<T>(endpoint: string): Promise<T> {
  const resposta = await fetch(`${API_URL}${endpoint}`, { cache: "no-store" })
  if (!resposta.ok) throw new Error(`${resposta.status}`)
  return resposta.json() as Promise<T>
}

export default function ModuloListaPage({ titulo, subtitulo, carregar, cadastroMestre = false }: { titulo: string; subtitulo: string; carregar: (query: string) => Promise<EmpresaResumoItem[]>; cadastroMestre?: boolean }) {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dados, setDados] = useState<EmpresaResumoItem[]>([])
  const [busca, setBusca] = useState("")
  const [categoria, setCategoria] = useState("TODAS")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [detalheNome, setDetalheNome] = useState<string | null>(null)
  const [clientesCanonicos, setClientesCanonicos] = useState<ClienteCanonico[]>([])
  const [oportunidades, setOportunidades] = useState<OportunidadeCRM[]>([])
  const [propostas, setPropostas] = useState<PropostaCRM[]>([])
  const [pedidos, setPedidos] = useState<PedidoCRM[]>([])
  const [atividades, setAtividades] = useState<AtividadeCRM[]>([])

  useEffect(() => {
    let ativo = true
    queueMicrotask(async () => {
      setLoading(true); setErro(""); setDetalheNome(null)
      try {
        const historico = await carregar(queryString)
        if (!ativo) return
        setDados(historico)
        if (cadastroMestre) {
          const [clientes, ops, props, peds, atvs] = await Promise.all([
            buscarJson<ClienteCanonico[]>("/clientes"), buscarJson<OportunidadeCRM[]>("/crm/oportunidades"), buscarJson<PropostaCRM[]>("/crm/propostas"), buscarJson<PedidoCRM[]>("/crm/pedidos"), buscarJson<AtividadeCRM[]>("/crm/atividades"),
          ])
          if (!ativo) return
          setClientesCanonicos(clientes); setOportunidades(ops); setPropostas(props); setPedidos(peds); setAtividades(atvs)
        }
      } catch { if (ativo) setErro("Erro ao carregar dados reais do módulo.") }
      finally { if (ativo) setLoading(false) }
    })
    return () => { ativo = false }
  }, [cadastroMestre, carregar, queryString])

  useEffect(() => {
    if (!detalheNome) return
    const anterior = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => { document.body.style.overflow = anterior }
  }, [detalheNome])

  const clientePorId = useMemo(() => new Map(clientesCanonicos.map((item) => [String(item.id), item])), [clientesCanonicos])
  const clientePorNome = useMemo(() => new Map(clientesCanonicos.map((item) => [normalizar(item.nome), item])), [clientesCanonicos])
  const categoriaPorNome = useMemo(() => new Map(clientesCanonicos.map((item) => [normalizar(item.nome), item.categoria || item.segmento || ""])), [clientesCanonicos])
  const crmPorNome = useMemo(() => {
    const mapa = new Map<string, CrmEmpresa>()
    clientesCanonicos.forEach((cliente) => mapa.set(normalizar(cliente.nome), { oportunidades: [], propostas: [], pedidos: [], atividades: [], categoria: cliente.categoria || cliente.segmento }))
    const obter = (id?: string) => { const cliente = id ? clientePorId.get(String(id)) : undefined; return cliente ? mapa.get(normalizar(cliente.nome)) || null : null }
    oportunidades.forEach((item) => obter(item.cliente_id)?.oportunidades.push(item))
    propostas.forEach((item) => obter(item.cliente_id)?.propostas.push(item))
    pedidos.forEach((item) => obter(item.cliente_id)?.pedidos.push(item))
    atividades.forEach((item) => obter(item.cliente_id)?.atividades.push(item))
    return mapa
  }, [atividades, clientePorId, clientesCanonicos, oportunidades, pedidos, propostas])

  const categorias = useMemo(() => Array.from(new Set(clientesCanonicos.map((item) => item.categoria || item.segmento).filter(Boolean) as string[])).sort(), [clientesCanonicos])
  const lista = useMemo(() => dados.filter((item) => {
    const clienteCanonico = clientePorNome.get(normalizar(item.nome))
    const categoriaEmpresa = categoriaPorNome.get(normalizar(item.nome)) || ""
    const conteudo = [item.nome, clienteCanonico?.razao_social, clienteCanonico?.nome_fantasia, clienteCanonico?.cnpj, ...(item.chassis ?? []), ...(item.placas ?? []), ...(item.implementadoras ?? []), categoriaEmpresa].filter(Boolean).join(" ")
    const termo = normalizar(busca)
    const termoCnpj = somenteDigitos(busca)
    const corresponde = normalizar(conteudo).includes(termo) || (termoCnpj.length > 0 && somenteDigitos(clienteCanonico?.cnpj).includes(termoCnpj))
    return corresponde && (categoria === "TODAS" || normalizar(categoriaEmpresa) === normalizar(categoria))
  }), [busca, categoria, categoriaPorNome, clientePorNome, dados])

  const valorHistorico = dados.reduce((total, item) => total + (item.valor_total ?? 0), 0)
  const totalChassis = dados.reduce((total, item) => total + (item.quantidade_chassis ?? 0), 0)
  const negociosEmCurso = oportunidades.filter(negocioEmCurso)
  const pipelineAtual = negociosEmCurso.reduce((total, item) => total + Number(item.valor_estimado || 0), 0)
  const propostasVigentes = propostas.filter(propostaVigente)
  const pedidosEmCurso = pedidos.filter(pedidoEmCurso)
  const periodoExibido = periodo === "TODO_HISTORICO" ? "Todo o histórico" : periodo === "PERSONALIZADO" ? `${dataInicio || "?"} a ${dataFim || "?"}` : periodo.replaceAll("_", " ")
  const detalheHistorico = detalheNome ? dados.find((item) => normalizar(item.nome) === normalizar(detalheNome)) || null : null
  const detalheCrm = detalheNome ? crmPorNome.get(normalizar(detalheNome)) || { oportunidades: [], propostas: [], pedidos: [], atividades: [] } : null
  const realizadoHref = drill("anfir", "Empresas · todos os registros realizados", queryString)
  const emCursoHref = drill("crm", "Empresas · negócios em curso")

  return <main className="flex min-h-screen bg-[#020817] text-white">
    <Sidebar />
    <section className="min-w-0 flex-1"><Topbar /><div className="space-y-6 p-4 sm:p-6 lg:p-8">
      <header><p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Leitura temporal por empresa</p><h1 className="mt-2 text-3xl font-bold">{titulo}</h1><p className="mt-2 text-sm text-slate-400">{subtitulo}</p><p className="mt-2 text-sm text-cyan-300">Contexto: {contextoAtual.label} • Período histórico: {periodoExibido}</p></header>
      {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}
      {cadastroMestre && <section className="grid gap-5 xl:grid-cols-2">
        <PainelTempo titulo="REALIZADO" subtitulo="O que estas empresas já representaram." destaque="Histórico confirmado"><div className="grid gap-3 sm:grid-cols-2"><Kpi titulo="Empresas históricas" valor={dados.length.toLocaleString("pt-BR")} /><Kpi titulo="Registros" valor={dados.reduce((s, i) => s + i.quantidade_registros, 0).toLocaleString("pt-BR")} href={realizadoHref} /><Kpi titulo="Chassis identificados" valor={totalChassis.toLocaleString("pt-BR")} /><Kpi titulo="Valor registrado na base" valor={moeda(valorHistorico)} href={realizadoHref} /></div></PainelTempo>
        <PainelTempo titulo="EM CURSO" subtitulo="O que está sendo construído agora." destaque="CRM atual"><div className="grid gap-3 sm:grid-cols-2"><Kpi titulo="Empresas com negócio em curso" valor={new Set(negociosEmCurso.map((item) => item.cliente_id).filter(Boolean)).size.toLocaleString("pt-BR")} /><Kpi titulo="Negócios em curso" valor={negociosEmCurso.length.toLocaleString("pt-BR")} href={emCursoHref} /><Kpi titulo="Pipeline atual" valor={moeda(pipelineAtual)} href={emCursoHref} /><Kpi titulo="Propostas vigentes / Pedidos em curso" valor={`${propostasVigentes.length} / ${pedidosEmCurso.length}`} /></div></PainelTempo>
      </section>}
      <section className="rounded-2xl border border-[#13203f] bg-[#091a33] p-5 sm:p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><h2 className="text-xl font-bold">{cadastroMestre ? "Empresas — histórico e situação atual" : "Dados operacionais"}</h2><p className="mt-1 text-sm text-slate-400">Abra uma empresa para confrontar REALIZADO × EM CURSO. Os totais de registros podem ser abertos até a linha de origem.</p></div><div className="flex flex-col gap-2 sm:flex-row">{cadastroMestre && <select value={categoria} onChange={(e) => setCategoria(e.target.value)} className="rounded-xl border border-[#13203f] bg-[#071028] px-4 py-3 text-white"><option value="TODAS">Todas as categorias</option>{categorias.map((item) => <option key={item} value={item}>{item}</option>)}</select>}<input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder={cadastroMestre ? "Buscar empresa, CNPJ, chassi, placa ou implementadora" : "Buscar empresa"} className="rounded-xl border border-[#13203f] bg-[#071028] px-4 py-3 text-white" /></div></div>
        {loading ? <p className="mt-8 text-slate-400">Carregando dados reais...</p> : lista.length === 0 ? <p className="mt-8 text-slate-400">Nenhuma empresa encontrada para os filtros selecionados.</p> : <div className="mt-6 overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-[#13203f] text-slate-400"><th className="p-3">Empresa</th><th className="p-3">REALIZADO</th>{cadastroMestre && <th className="p-3">EM CURSO</th>}<th className="p-3">Linhas</th>{cadastroMestre && <th className="p-3">Ação</th>}</tr></thead><tbody>{lista.map((item) => { const crm = crmPorNome.get(normalizar(item.nome)); const clienteCanonico = clientePorNome.get(normalizar(item.nome)); const categoriaEmpresa = categoriaPorNome.get(normalizar(item.nome)) || "Categoria não classificada"; const opsEmCurso = crm?.oportunidades.filter(negocioEmCurso) ?? []; const realizadoEmpresa = drill("anfir", `Empresa · ${item.nome} · realizado`, queryString, "empresa", item.nome); const crmEmpresa = drill("crm", `Empresa · ${item.nome} · negócios em curso`, "", "empresa", item.nome); return <tr key={item.nome} className="border-b border-[#13203f] text-slate-200 hover:bg-cyan-500/5"><td className="p-3"><p className="font-semibold text-white">{item.nome}</p>{clienteCanonico?.cnpj && <p className="text-xs text-cyan-300">CNPJ {formatarCnpj(clienteCanonico.cnpj)}</p>}<p className="text-xs text-slate-500">{categoriaEmpresa}</p></td><td className="p-3"><Link href={realizadoEmpresa} className="block rounded-lg p-2 transition hover:bg-cyan-500/10"><p className="font-semibold text-cyan-200">{item.quantidade_registros} registros</p><p className="text-xs text-slate-500">{item.quantidade_chassis ?? 0} chassis • {moeda(item.valor_total)} na base</p><p className="mt-1 text-[11px] text-cyan-400">Clique para detalhar</p></Link></td>{cadastroMestre && <td className="p-3">{opsEmCurso.length > 0 ? <Link href={crmEmpresa} className="block rounded-lg p-2 transition hover:bg-emerald-500/10"><p className="font-semibold text-emerald-200">{opsEmCurso.length} negócio(s)</p><p className="text-xs text-emerald-300">{moeda(opsEmCurso.reduce((s, op) => s + Number(op.valor_estimado || 0), 0))} em pipeline</p><p className="mt-1 text-[11px] text-emerald-400">Clique para detalhar</p></Link> : <div className="p-2"><p>0 negócio(s)</p><p className="text-xs text-slate-500">R$ 0 em pipeline</p></div>}</td>}<td className="p-3">{item.linhas?.join(", ") || "-"}</td>{cadastroMestre && <td className="p-3"><button type="button" onClick={() => setDetalheNome(item.nome)} className="rounded-lg border border-cyan-500 px-3 py-2 text-cyan-300 hover:bg-cyan-500/10">Abrir visão temporal</button></td>}</tr> })}</tbody></table></div>}
      </section>
    </div></section>
    {detalheNome && detalheHistorico && detalheCrm && <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 p-3" role="dialog" aria-modal="true"><div className="max-h-[94vh] w-full max-w-6xl overflow-y-auto rounded-2xl border border-cyan-700 bg-[#071427] shadow-2xl"><EmpresaTemporal nome={detalheNome} historico={detalheHistorico} crm={detalheCrm} categoria={categoriaPorNome.get(normalizar(detalheNome)) || "Categoria não classificada"} queryString={queryString} fechar={() => setDetalheNome(null)} /></div></div>}
  </main>
}

function EmpresaTemporal({ nome, historico, crm, categoria, queryString, fechar }: { nome: string; historico: EmpresaResumoItem; crm: CrmEmpresa; categoria: string; queryString: string; fechar: () => void }) {
  const opsEmCurso = crm.oportunidades.filter(negocioEmCurso)
  const pipeline = opsEmCurso.reduce((s, item) => s + Number(item.valor_estimado || 0), 0)
  const propsVigentes = crm.propostas.filter(propostaVigente)
  const pedsEmCurso = crm.pedidos.filter(pedidoEmCurso)
  const proximaAtividade = [...crm.atividades].filter((item) => !["CONCLUIDA", "CANCELADA"].includes(String(item.status || "").toUpperCase())).sort((a, b) => String(a.data || a.data_atividade || "9999").localeCompare(String(b.data || b.data_atividade || "9999")))[0]
  const realizadoEmpresa = drill("anfir", `Empresa · ${nome} · realizado`, queryString, "empresa", nome)
  const crmEmpresa = drill("crm", `Empresa · ${nome} · negócios em curso`, "", "empresa", nome)
  return <section className="space-y-5 p-5 sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Visão temporal da empresa</p><h2 className="mt-1 text-3xl font-bold">{nome}</h2><p className="mt-1 text-sm text-slate-400">{categoria} • {historico.municipios?.join(", ") || "Município não identificado"} • {historico.estados?.join(", ") || "UF não identificada"}</p></div><button type="button" onClick={fechar} className="rounded-lg border border-[#28456f] px-4 py-2 text-slate-300 hover:border-cyan-500">Fechar</button></div><div className="grid gap-5 lg:grid-cols-2"><PainelTempo titulo="REALIZADO" subtitulo="Histórico confirmado desta empresa." destaque="Passado"><div className="grid gap-3 sm:grid-cols-2"><Kpi titulo="Registros históricos" valor={historico.quantidade_registros.toLocaleString("pt-BR")} href={realizadoEmpresa} /><Kpi titulo="Valor registrado na base" valor={moeda(historico.valor_total)} href={realizadoEmpresa} /><Kpi titulo="Chassis / Placas" valor={`${historico.quantidade_chassis ?? 0} / ${historico.quantidade_placas ?? 0}`} /><Kpi titulo="Linhas" valor={historico.linhas?.join(" • ") || "-"} /></div><Painel titulo="Ativos e parceiros"><p>Equipamentos: {historico.equipamentos?.join(", ") || "-"}</p><p>Implementadoras: {historico.implementadoras?.join(", ") || "-"}</p></Painel></PainelTempo><PainelTempo titulo="EM CURSO" subtitulo="Negócios e ações ainda em movimento." destaque="Presente / futuro"><div className="grid gap-3 sm:grid-cols-2"><Kpi titulo="Negócios em curso" valor={opsEmCurso.length.toLocaleString("pt-BR")} href={opsEmCurso.length ? crmEmpresa : undefined} /><Kpi titulo="Pipeline" valor={moeda(pipeline)} href={opsEmCurso.length ? crmEmpresa : undefined} /><Kpi titulo="Propostas vigentes" valor={propsVigentes.length.toLocaleString("pt-BR")} /><Kpi titulo="Pedidos em curso" valor={pedsEmCurso.length.toLocaleString("pt-BR")} /></div><Painel titulo="Próxima ação"><p className="font-semibold text-white">{proximaAtividade?.titulo || proximaAtividade?.descricao || "Nenhuma ação programada"}</p><p>{proximaAtividade?.data || proximaAtividade?.data_atividade || "Sem data"}</p></Painel></PainelTempo></div><section className="grid gap-5 lg:grid-cols-2"><Painel titulo={`Histórico comercial CRM (${crm.oportunidades.length})`}>{crm.oportunidades.length ? crm.oportunidades.map((item) => <div key={item.id} className="border-b border-[#13203f] py-3"><p className="font-semibold text-white">{item.titulo || "Oportunidade"}</p><p>{item.status || "Sem status"} • {moeda(Number(item.valor_estimado || 0))}</p></div>) : <p>Nenhum negócio vinculado.</p>}</Painel><Painel titulo={`Propostas / Pedidos (${crm.propostas.length} / ${crm.pedidos.length})`}><p>Propostas: {crm.propostas.map((item) => item.numero || item.status || item.id).join(", ") || "-"}</p><p className="mt-2">Pedidos: {crm.pedidos.map((item) => `${item.numero || item.id}${item.status_ciclo ? ` • ${item.status_ciclo}` : ""}`).join(", ") || "-"}</p></Painel></section></section>
}

function PainelTempo({ titulo, subtitulo, destaque, children }: { titulo: string; subtitulo: string; destaque: string; children: ReactNode }) { return <section className="rounded-3xl border border-[#13203f] bg-[#071427] p-5 sm:p-6"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">{titulo}</p><h3 className="mt-1 text-xl font-bold text-white">{subtitulo}</h3></div><span className="rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-300">{destaque}</span></div>{children}</section> }
function Painel({ titulo, children }: { titulo: string; children: ReactNode }) { return <div className="mt-4 rounded-xl border border-[#13203f] bg-[#071028] p-5 text-sm text-slate-300"><h3 className="mb-3 text-lg font-bold text-white">{titulo}</h3>{children}</div> }
function Kpi({ titulo, valor, href }: { titulo: string; valor: string; href?: string }) { const body = <><p className="text-sm text-slate-400">{titulo}</p><p className="mt-2 text-xl font-bold text-cyan-300">{valor}</p>{href && <p className="mt-2 text-[11px] text-cyan-400">Clique para detalhar</p>}</>; return href ? <Link href={href} className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4 transition hover:border-cyan-500/70 hover:bg-[#0b1d38]">{body}</Link> : <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4">{body}</div> }
