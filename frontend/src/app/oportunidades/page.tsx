"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

interface Oportunidade {
  id: string
  titulo: string
  origem?: string
  status: string
  valor_estimado: number
  probabilidade: number
  data_abertura?: string
  data_fechamento_prevista?: string
  created_at?: string
  responsavel_id?: string
  cliente_id?: string
}

const contexto = {
  origem: "CRM Operacional",
  periodo: "Oportunidades abertas e atualizadas no CRM operacional.",
  significado: "Representa operações futuras em andamento, sem conversão automática da base histórica.",
  criterio: "Pipeline total soma valor_estimado; pipeline ponderado aplica a probabilidade normalizada da oportunidade.",
  finalidade: "Criar, acompanhar e priorizar oportunidades comerciais futuras.",
}

function fatorProbabilidade(valor?: number) {
  const probabilidade = Number(valor || 0)
  if (probabilidade <= 0) return 0
  if (probabilidade <= 1) return probabilidade
  return probabilidade / 100
}

export default function OportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")

  async function carregarOportunidades() {
    try {
      const response = await fetch(`${API_URL}/crm/oportunidades`)
      const json = await response.json()
      setDados(Array.isArray(json) ? json : [])
    } catch (error) {
      console.error(error)
      setErro("Não foi possível carregar as oportunidades operacionais.")
    } finally {
      setLoading(false)
    }
  }

  async function criarOportunidade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSalvando(true)
    setErro("")
    const form = new FormData(event.currentTarget)
    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      contato_id: String(form.get("contato_id") || "") || undefined,
      responsavel_id: String(form.get("responsavel_id") || ""),
      titulo: String(form.get("titulo") || ""),
      descricao: String(form.get("descricao") || "") || undefined,
      origem: String(form.get("origem") || "CRM"),
      linha_equipamentos: String(form.get("linha_equipamentos") || "") || undefined,
      equipamento: String(form.get("equipamento") || "") || undefined,
      implementadora: String(form.get("implementadora") || "") || undefined,
      locadora: String(form.get("locadora") || "") || undefined,
      estado: String(form.get("estado") || "") || undefined,
      ddd: String(form.get("ddd") || "") || undefined,
      sub_regiao: String(form.get("sub_regiao") || "") || undefined,
      municipio: String(form.get("municipio") || "") || undefined,
      bairro: String(form.get("bairro") || "") || undefined,
      valor_estimado: Number(form.get("valor_estimado") || 0),
      probabilidade: Number(form.get("probabilidade") || 0),
      data_fechamento_prevista: String(form.get("data_fechamento_prevista") || "") || undefined,
      observacoes: String(form.get("observacoes") || "") || undefined,
      status: "OPORTUNIDADE",
    }

    try {
      const response = await fetch(`${API_URL}/crm/oportunidades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!response.ok) throw new Error("Falha ao criar oportunidade")
      setMostrarFormulario(false)
      await carregarOportunidades()
    } catch (error) {
      console.error(error)
      setErro("Não foi possível criar a oportunidade. Verifique os campos obrigatórios.")
    } finally {
      setSalvando(false)
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      if (new URLSearchParams(window.location.search).get("novo") === "1") {
        setMostrarFormulario(true)
      }
      void carregarOportunidades()
    })
  }, [])

  const valorPipeline = dados.reduce((acc, item) => acc + (item.valor_estimado || 0), 0)
  const pipelinePonderado = dados.reduce((acc, item) => acc + ((item.valor_estimado || 0) * fatorProbabilidade(item.probabilidade)), 0)
  const probabilidadeMedia = dados.length
    ? Math.round((dados.reduce((acc, item) => acc + fatorProbabilidade(item.probabilidade), 0) / dados.length) * 100)
    : 0

  function formatarData(data?: string) {
    if (!data) return "-"
    return new Date(data).toLocaleDateString("pt-BR")
  }

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="flex-1">
        <Topbar />
        <div className="p-8 space-y-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white">CRM • Oportunidades</h1>
              <p className="text-gray-400 mt-2">Operações futuras do CRM Operacional.</p>
            </div>
            <button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova oportunidade</button>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          {mostrarFormulario && (
            <form onSubmit={criarOportunidade} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200">
              <h2 className="text-xl font-bold text-white">Cadastro de nova oportunidade</h2>
              <p className="mt-2 text-sm text-gray-400">Ao salvar, o backend cria automaticamente a primeira movimentação do pipeline, histórico, auditoria, forecast e indicadores do CRM.</p>
              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
                <Campo nome="cliente_id" label="Empresa" obrigatorio />
                <Campo nome="contato_id" label="Contato" />
                <Campo nome="responsavel_id" label="Responsável" obrigatorio />
                <Campo nome="titulo" label="Título" obrigatorio />
                <Campo nome="origem" label="Origem" padrao="CRM" />
                <Campo nome="linha_equipamentos" label="Linha de equipamentos" />
                <Campo nome="equipamento" label="Equipamento" />
                <Campo nome="implementadora" label="Implementadora" />
                <Campo nome="locadora" label="Locadora" />
                <Campo nome="estado" label="Estado" />
                <Campo nome="ddd" label="DDD" />
                <Campo nome="sub_regiao" label="Sub-Região" />
                <Campo nome="municipio" label="Município" />
                <Campo nome="bairro" label="Bairro" />
                <Campo nome="valor_estimado" label="Valor estimado" tipo="number" />
                <Campo nome="probabilidade" label="Probabilidade" tipo="number" />
                <Campo nome="data_fechamento_prevista" label="Previsão de fechamento" tipo="date" />
                <Campo nome="descricao" label="Descrição" />
                <Campo nome="observacoes" label="Observações" />
              </div>
              <div className="mt-5 flex gap-3">
                <button disabled={salvando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">{salvando ? "Salvando..." : "Salvar oportunidade"}</button>
                <button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button>
              </div>
            </form>
          )}

          <section className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-5">
            <Kpi titulo="Oportunidades" valor={dados.length} />
            <Kpi titulo="Pipeline Total" valor={`R$ ${valorPipeline.toLocaleString("pt-BR")}`} />
            <Kpi titulo="Pipeline Ponderado" valor={`R$ ${pipelinePonderado.toLocaleString("pt-BR")}`} />
            <Kpi titulo="Probabilidade Média" valor={`${probabilidadeMedia}%`} />
            <Kpi titulo="Backend CRM" valor="ONLINE" />
          </section>

          <Contexto />

          <div className="bg-[#091a33] rounded-2xl border border-[#13203f] overflow-hidden">
            <div className="p-6 border-b border-[#13203f]"><h2 className="text-white text-xl font-semibold">Oportunidades Comerciais</h2></div>
            {loading ? (
              <div className="p-10 text-gray-400">Carregando...</div>
            ) : dados.length === 0 ? (
              <EstadoVazio onNova={() => setMostrarFormulario(true)} />
            ) : (
              <table className="w-full">
                <thead><tr className="text-left border-b border-[#13203f]"><th className="p-4 text-gray-400">Título</th><th className="p-4 text-gray-400">Origem</th><th className="p-4 text-gray-400">Status</th><th className="p-4 text-gray-400">Valor</th><th className="p-4 text-gray-400">Probabilidade</th><th className="p-4 text-gray-400">Fechamento</th></tr></thead>
                <tbody>{dados.map((item) => (<tr key={item.id} className="border-b border-[#13203f]"><td className="p-4 text-white">{item.titulo}</td><td className="p-4 text-gray-300">{item.origem || "CRM"}</td><td className="p-4 text-cyan-400">{item.status}</td><td className="p-4 text-green-400">R$ {(item.valor_estimado || 0).toLocaleString("pt-BR")}</td><td className="p-4 text-yellow-400">{Math.round(fatorProbabilidade(item.probabilidade) * 100)}%</td><td className="p-4 text-white">{formatarData(item.data_fechamento_prevista || item.data_abertura || item.created_at)}</td></tr>))}</tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}

function Campo({ nome, label, tipo = "text", obrigatorio = false, padrao = "" }: { nome: string; label: string; tipo?: string; obrigatorio?: boolean; padrao?: string }) {
  return <label className="text-sm text-gray-300">{label}<input name={nome} type={tipo} required={obrigatorio} defaultValue={padrao} className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /></label>
}

function Kpi({ titulo, valor }: { titulo: string; valor: string | number }) {
  return <div className="bg-[#091a33] p-6 rounded-2xl border border-[#13203f]"><p className="text-gray-400 text-sm">{titulo}</p><h2 className="text-3xl text-cyan-400 font-bold mt-2">{valor}</h2></div>
}

function Contexto() {
  return <div className="rounded-2xl border border-[#13203f] bg-[#071226] p-5 text-sm text-gray-300"><h2 className="text-white font-semibold mb-2">Contexto dos indicadores</h2><p><strong>Origem dos indicadores:</strong> {contexto.origem}</p><p><strong>Período considerado:</strong> {contexto.periodo}</p><p><strong>Significado operacional:</strong> {contexto.significado}</p><p><strong>Critério de cálculo:</strong> {contexto.criterio}</p><p><strong>Finalidade operacional:</strong> {contexto.finalidade}</p></div>
}

function EstadoVazio({ onNova }: { onNova: () => void }) {
  return <div className="p-10 text-gray-300 space-y-4"><p><strong>Por que não existem registros:</strong> nenhuma oportunidade operacional foi cadastrada no CRM para este contexto.</p><p><strong>O que esta tela representa:</strong> a carteira futura de oportunidades comerciais, separada da base histórica.</p><p><strong>Próximo passo esperado:</strong> iniciar o cadastro da primeira oportunidade.</p><button type="button" onClick={onNova} className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950">Nova oportunidade</button></div>
}
