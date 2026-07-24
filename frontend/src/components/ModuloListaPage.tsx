"use client"

import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useOperationalContext } from "@/context/OperationalContext"
import { getClienteDetalhe, type ClienteDetalheComercial, type EmpresaResumoItem } from "@/services/modulos-api"

function normalizar(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}

export default function ModuloListaPage({
  titulo,
  subtitulo,
  carregar,
  cadastroMestre = false,
}: {
  titulo: string
  subtitulo: string
  carregar: (query: string) => Promise<EmpresaResumoItem[]>
  cadastroMestre?: boolean
}) {
  const { contextoAtual, periodo, dataInicio, dataFim, queryString } = useOperationalContext()
  const [dados, setDados] = useState<EmpresaResumoItem[]>([])
  const [busca, setBusca] = useState("")
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState("")
  const [detalhe, setDetalhe] = useState<ClienteDetalheComercial | null>(null)
  const [detalheLoading, setDetalheLoading] = useState(false)

  useEffect(() => {
    let ativo = true
    queueMicrotask(() => {
      if (!ativo) return
      setLoading(true)
      setErro("")
      setDetalhe(null)
      carregar(queryString)
        .then((resultado) => { if (ativo) setDados(resultado) })
        .catch(() => { if (ativo) setErro("Erro ao carregar dados reais do módulo.") })
        .finally(() => { if (ativo) setLoading(false) })
    })
    return () => { ativo = false }
  }, [carregar, queryString])

  const abrirCliente = async (nome: string) => {
    if (!cadastroMestre) return
    setDetalheLoading(true)
    setErro("")
    try {
      setDetalhe(await getClienteDetalhe(nome, queryString))
    } catch {
      setErro("Não foi possível abrir a visão comercial do cliente.")
    } finally {
      setDetalheLoading(false)
    }
  }

  const lista = useMemo(() => dados.filter((item) => {
    const conteudo = [item.nome, ...(item.chassis ?? []), ...(item.placas ?? []), ...(item.implementadoras ?? [])].join(" ")
    return normalizar(conteudo).includes(normalizar(busca))
  }), [dados, busca])
  const valorTotal = dados.reduce((total, item) => total + (item.valor_total ?? 0), 0)
  const estados = new Set(dados.flatMap((item) => item.estados ?? []))
  const totalChassis = dados.reduce((total, item) => total + (item.quantidade_chassis ?? 0), 0)
  const periodoExibido = periodo === "TODO_HISTORICO" ? "Todo o histórico" : periodo === "PERSONALIZADO" ? `${dataInicio || "?"} a ${dataFim || "?"}` : periodo.replaceAll("_", " ")

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1 min-w-0">
        <Topbar />
        <div className="p-8 space-y-8">
          <div>
            <h1 className="text-4xl font-bold text-white">{titulo}</h1>
            <p className="text-gray-400 mt-2">{subtitulo}</p>
            <p className="text-cyan-300 text-sm mt-2">Contexto: {contextoAtual.label} • Período: {periodoExibido}</p>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          <div className={`grid grid-cols-1 ${cadastroMestre ? "md:grid-cols-4" : "md:grid-cols-3"} gap-4`}>
            <Kpi titulo="Registros" valor={dados.reduce((total, item) => total + item.quantidade_registros, 0).toLocaleString("pt-BR")} />
            <Kpi titulo={cadastroMestre ? "Clientes" : "Entidades"} valor={dados.length.toLocaleString("pt-BR")} />
            {cadastroMestre && <Kpi titulo="Chassis identificados" valor={totalChassis.toLocaleString("pt-BR")} />}
            <Kpi titulo="Valor total" valor={`R$ ${valorTotal.toLocaleString("pt-BR")}`} />
          </div>

          <section className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div><h2 className="text-2xl font-bold text-white">{cadastroMestre ? "Visão consolidada dos clientes" : "Dados operacionais"}</h2><p className="text-gray-400">{estados.size} estados encontrados após os filtros globais.</p></div>
              <input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder={cadastroMestre ? "Buscar cliente, chassi, placa ou implementadora" : "Buscar empresa"} className="rounded-xl bg-[#071028] border border-[#13203f] px-4 py-3 text-white" />
            </div>

            {loading ? <p className="text-gray-400 mt-8">Carregando dados reais...</p> : lista.length === 0 ? <p className="text-gray-400 mt-8">Nenhuma empresa encontrada para o território e período selecionados.</p> : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-left">
                  <thead><tr className="border-b border-[#13203f] text-gray-400"><th className="p-3">Nome</th><th className="p-3">Registros</th>{cadastroMestre && <><th className="p-3">Chassis</th><th className="p-3">Placas</th><th className="p-3">Origem comercial</th></>}<th className="p-3">Valor</th><th className="p-3">Estados</th><th className="p-3">Linhas</th>{cadastroMestre && <th className="p-3">Ação</th>}</tr></thead>
                  <tbody>{lista.map((item) => <tr key={item.nome} className="border-b border-[#13203f] text-gray-200"><td className="p-3 font-semibold">{item.nome}</td><td className="p-3">{item.quantidade_registros}</td>{cadastroMestre && <><td className="p-3">{item.quantidade_chassis ?? 0}</td><td className="p-3">{item.quantidade_placas ?? 0}</td><td className="p-3">{item.implementadoras?.join(", ") || "-"}</td></>}<td className="p-3">R$ {(item.valor_total ?? 0).toLocaleString("pt-BR")}</td><td className="p-3">{item.estados?.join(", ") || "-"}</td><td className="p-3">{item.linhas?.join(", ") || "-"}</td>{cadastroMestre && <td className="p-3"><button onClick={() => abrirCliente(item.nome)} className="rounded-lg border border-cyan-500 px-3 py-2 text-cyan-300 hover:bg-cyan-500/10">Abrir visão comercial</button></td>}</tr>)}</tbody>
                </table>
              </div>
            )}
          </section>

          {detalheLoading && <section className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6 text-gray-400">Carregando visão comercial...</section>}
          {detalhe && <ClienteComercial detalhe={detalhe} fechar={() => setDetalhe(null)} />}
        </div>
      </section>
    </main>
  )
}

function ClienteComercial({ detalhe, fechar }: { detalhe: ClienteDetalheComercial; fechar: () => void }) {
  const { cliente, inteligencia, oportunidades, atividades } = detalhe
  return (
    <section className="rounded-2xl bg-[#091a33] border border-cyan-700 p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div><p className="text-cyan-300 text-sm">Visão comercial 360</p><h2 className="text-3xl font-bold text-white">{cliente.nome}</h2><p className="text-gray-400 mt-1">{cliente.municipios?.join(", ") || "Município não identificado"} • {cliente.estados?.join(", ") || "UF não identificada"}</p></div>
        <button onClick={fechar} className="text-gray-400 hover:text-white">Fechar</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Kpi titulo="Prioridade" valor={inteligencia.prioridade} />
        <Kpi titulo="Oportunidades abertas" valor={String(inteligencia.oportunidades_abertas)} />
        <Kpi titulo="Atividades atrasadas" valor={String(inteligencia.atividades_atrasadas)} />
        <Kpi titulo="Pipeline" valor={`R$ ${inteligencia.valor_pipeline.toLocaleString("pt-BR")}`} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Painel titulo="Ativos e histórico"><p>Chassis: {cliente.chassis?.join(", ") || "-"}</p><p>Placas: {cliente.placas?.join(", ") || "-"}</p><p>Equipamentos: {cliente.equipamentos?.join(", ") || "-"}</p><p>Implementadoras: {cliente.implementadoras?.join(", ") || "-"}</p></Painel>
        <Painel titulo="Próxima ação"><p className="text-white font-semibold">{inteligencia.proxima_acao?.titulo || inteligencia.proxima_acao?.descricao || "Nenhuma ação programada"}</p><p>{inteligencia.proxima_acao?.data || "Sem data"} {inteligencia.proxima_acao?.horario || ""}</p><p className="text-cyan-300">{inteligencia.proxima_acao?.situacao || "AGENDAR"}</p></Painel>
        <Painel titulo={`Oportunidades (${oportunidades.length})`}>{oportunidades.length ? oportunidades.map((item, index) => <div key={item.id || index} className="border-b border-[#13203f] py-3"><p className="text-white font-semibold">{item.titulo || "Oportunidade"}</p><p>{item.status || "Sem status"} • R$ {(item.valor_estimado || 0).toLocaleString("pt-BR")}</p></div>) : <p>Nenhuma oportunidade vinculada.</p>}</Painel>
        <Painel titulo={`Agenda (${atividades.length})`}>{atividades.length ? atividades.slice(0, 8).map((item, index) => <div key={item.id || index} className="border-b border-[#13203f] py-3"><p className="text-white font-semibold">{item.titulo || item.descricao || "Atividade"}</p><p>{item.data || "Sem data"} • {item.situacao || item.status || "PENDENTE"}</p></div>) : <p>Nenhuma atividade vinculada.</p>}</Painel>
      </div>
    </section>
  )
}

function Painel({ titulo, children }: { titulo: string; children: React.ReactNode }) { return <div className="rounded-xl bg-[#071028] border border-[#13203f] p-5 text-gray-300"><h3 className="text-lg font-bold text-white mb-3">{titulo}</h3>{children}</div> }
function Kpi({ titulo, valor }: { titulo: string; valor: string }) { return <div className="rounded-2xl bg-[#091a33] border border-[#13203f] p-6"><p className="text-gray-400 text-sm">{titulo}</p><p className="text-3xl text-cyan-400 font-bold mt-2">{valor}</p></div> }
