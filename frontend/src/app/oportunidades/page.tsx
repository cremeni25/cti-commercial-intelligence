"use client"

import { FormEvent, useEffect, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"

type Oportunidade = {
  id: string
  titulo: string
  cliente_id?: string
  origem?: string
  status: string
  valor_estimado: number
  probabilidade: number
  data_fechamento_prevista?: string
  equipamento?: string
  implementadora?: string
}

type ClienteMestre = {
  nome: string
  chassis?: string[]
  placas?: string[]
  equipamentos?: string[]
  implementadoras?: string[]
  estados?: string[]
  municipios?: string[]
}

function fatorProbabilidade(valor?: number) {
  const numero = Number(valor || 0)
  if (numero <= 0) return 0
  return numero <= 1 ? numero : numero / 100
}

export default function OportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [clientes, setClientes] = useState<ClienteMestre[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")

  async function carregar() {
    setLoading(true)
    try {
      const [oportunidadesResponse, clientesResponse] = await Promise.all([
        fetch(`${API_URL}/crm/oportunidades`),
        fetch(`${API_URL}/modulos/clientes?contexto=brasil&periodo=TODO_HISTORICO`),
      ])
      if (!oportunidadesResponse.ok || !clientesResponse.ok) throw new Error("Falha de carregamento")
      const [oportunidadesJson, clientesJson] = await Promise.all([oportunidadesResponse.json(), clientesResponse.json()])
      setDados(Array.isArray(oportunidadesJson) ? oportunidadesJson : [])
      setClientes(Array.isArray(clientesJson) ? clientesJson : [])
    } catch {
      setErro("Não foi possível carregar as oportunidades ou o Cadastro Mestre de Clientes.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      if (new URLSearchParams(window.location.search).get("novo") === "1") {
        setMostrarFormulario(true)
      }
      void carregar()
    })
  }, [])

  async function criarOportunidade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSalvando(true)
    setErro("")
    const form = new FormData(event.currentTarget)
    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      responsavel_id: String(form.get("responsavel_id") || ""),
      titulo: String(form.get("titulo") || ""),
      descricao: String(form.get("descricao") || "") || undefined,
      origem: String(form.get("origem") || "CRM"),
      linha_equipamentos: String(form.get("linha_equipamentos") || "") || undefined,
      equipamento: String(form.get("equipamento") || "") || undefined,
      implementadora: String(form.get("implementadora") || "") || undefined,
      estado: String(form.get("estado") || "") || undefined,
      municipio: String(form.get("municipio") || "") || undefined,
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
      await carregar()
    } catch {
      setErro("Não foi possível criar a oportunidade. Verifique os campos obrigatórios e a estrutura do CRM no banco.")
    } finally {
      setSalvando(false)
    }
  }

  const valorPipeline = dados.reduce((total, item) => total + Number(item.valor_estimado || 0), 0)
  const pipelinePonderado = dados.reduce((total, item) => total + Number(item.valor_estimado || 0) * fatorProbabilidade(item.probabilidade), 0)

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div><h1 className="text-4xl font-bold text-white">CRM • Oportunidades</h1><p className="mt-2 text-gray-400">Operações futuras vinculadas ao Cadastro Mestre de Clientes.</p></div>
            <button type="button" onClick={() => setMostrarFormulario(true)} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">Nova oportunidade</button>
          </div>

          {erro && <div className="rounded-xl border border-red-500 p-4 text-red-300">{erro}</div>}

          {mostrarFormulario && (
            <form onSubmit={criarOportunidade} className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200">
              <h2 className="text-xl font-bold text-white">Cadastro de nova oportunidade</h2>
              <p className="mt-2 text-sm text-gray-400">Selecione um cliente já identificado na base importada. Equipamentos e implementadoras permanecem associados à oportunidade específica.</p>
              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
                <label className="text-sm text-gray-300">Cliente da base<input name="cliente_id" list="clientes-mestre" required className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white" /><datalist id="clientes-mestre">{clientes.map((cliente) => <option key={cliente.nome} value={cliente.nome} />)}</datalist></label>
                <Campo nome="responsavel_id" label="Responsável comercial" obrigatorio />
                <Campo nome="titulo" label="Título" obrigatorio />
                <Campo nome="origem" label="Origem" padrao="CRM" />
                <Campo nome="linha_equipamentos" label="Linha de equipamentos" />
                <Campo nome="equipamento" label="Equipamento" />
                <Campo nome="implementadora" label="Implementadora desta venda" />
                <Campo nome="estado" label="Estado" />
                <Campo nome="municipio" label="Município" />
                <Campo nome="valor_estimado" label="Valor estimado" tipo="number" />
                <Campo nome="probabilidade" label="Probabilidade (%)" tipo="number" />
                <Campo nome="data_fechamento_prevista" label="Previsão de fechamento" tipo="date" />
                <Campo nome="descricao" label="Descrição" />
                <Campo nome="observacoes" label="Observações" />
              </div>
              <div className="mt-5 flex gap-3"><button disabled={salvando} className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950">{salvando ? "Salvando..." : "Salvar oportunidade"}</button><button type="button" onClick={() => setMostrarFormulario(false)} className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300">Cancelar</button></div>
            </form>
          )}

          <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Kpi titulo="Clientes disponíveis" valor={clientes.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Oportunidades" valor={dados.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Pipeline total" valor={valorPipeline.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
            <Kpi titulo="Pipeline ponderado" valor={pipelinePonderado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} />
          </section>

          <div className="overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">
            {loading ? <div className="p-10 text-gray-400">Carregando...</div> : dados.length === 0 ? <div className="p-10 text-gray-300">Nenhuma oportunidade cadastrada.</div> : (
              <table className="w-full text-left"><thead><tr className="border-b border-[#13203f] text-gray-400"><th className="p-4">Cliente</th><th className="p-4">Oportunidade</th><th className="p-4">Etapa</th><th className="p-4">Equipamento</th><th className="p-4">Implementadora</th><th className="p-4">Valor</th><th className="p-4">Probabilidade</th></tr></thead><tbody>{dados.map((item) => <tr key={item.id} className="border-b border-[#13203f] text-gray-200"><td className="p-4 font-semibold text-cyan-300">{item.cliente_id || "-"}</td><td className="p-4">{item.titulo}</td><td className="p-4">{item.status}</td><td className="p-4">{item.equipamento || "-"}</td><td className="p-4">{item.implementadora || "-"}</td><td className="p-4 text-green-400">{Number(item.valor_estimado || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</td><td className="p-4">{Math.round(fatorProbabilidade(item.probabilidade) * 100)}%</td></tr>)}</tbody></table>
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

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6"><p className="text-sm text-gray-400">{titulo}</p><p className="mt-2 text-3xl font-bold text-cyan-400">{valor}</p></div>
}
