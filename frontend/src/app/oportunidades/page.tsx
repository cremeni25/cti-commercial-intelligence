"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { API_URL } from "@/lib/api"
import {
  lerContextoOportunidade,
  montarDescricaoComContexto,
} from "@/lib/crm-opportunity"

type Oportunidade = {
  id: string
  titulo: string
  cliente_id?: string
  origem?: string
  status: string
  descricao?: string
  valor_estimado: number
  probabilidade: number
  data_fechamento_prevista?: string
  linha_equipamentos?: string
  equipamento?: string
  implementadora?: string
  municipio?: string
  estado?: string
  ddd?: string
  sub_regiao?: string
}

type ClienteMestre = { nome: string }

type Edicao = {
  valor: number
  chance: number
  quantidade: number
  status: string
  data: string
}

function percentual(valor?: number): number {
  const numero = Number(valor || 0)
  return Math.round(numero <= 1 ? numero * 100 : numero)
}

function fator(valor?: number): number {
  return percentual(valor) / 100
}

function moeda(valor: number): string {
  return valor.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  })
}

export default function OportunidadesPage() {
  const [dados, setDados] = useState<Oportunidade[]>([])
  const [clientes, setClientes] = useState<ClienteMestre[]>([])
  const [loading, setLoading] = useState(true)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [editando, setEditando] = useState<string | null>(null)
  const [edicao, setEdicao] = useState<Edicao>({
    valor: 0,
    chance: 0,
    quantidade: 1,
    status: "OPORTUNIDADE",
    data: "",
  })

  async function carregar() {
    setLoading(true)
    setErro("")
    try {
      const [oportunidadesResponse, clientesResponse] = await Promise.all([
        fetch(`${API_URL}/crm/oportunidades`, { cache: "no-store" }),
        fetch(
          `${API_URL}/modulos/clientes?contexto=brasil&periodo=TODO_HISTORICO`,
          { cache: "no-store" },
        ),
      ])

      if (!oportunidadesResponse.ok || !clientesResponse.ok) {
        throw new Error("Falha de carregamento")
      }

      const [oportunidadesJson, clientesJson] = await Promise.all([
        oportunidadesResponse.json(),
        clientesResponse.json(),
      ])

      setDados(Array.isArray(oportunidadesJson) ? oportunidadesJson : [])
      setClientes(Array.isArray(clientesJson) ? clientesJson : [])
    } catch {
      setErro(
        "Não foi possível carregar as oportunidades ou o Cadastro Mestre de Clientes.",
      )
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
    const linhas = String(form.get("linha_equipamentos") || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
    const equipamentos = String(form.get("equipamento") || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
    const quantidade = Math.max(1, Number(form.get("quantidade") || 1))

    const descricao = montarDescricaoComContexto(
      String(form.get("descricao") || ""),
      {
        linhas,
        equipamentos,
        quantidade,
        municipio: String(form.get("municipio") || ""),
        uf: String(form.get("estado") || ""),
        ddd: String(form.get("ddd") || ""),
        subRegiao: String(form.get("sub_regiao") || ""),
      },
    )

    const payload = {
      cliente_id: String(form.get("cliente_id") || ""),
      responsavel_id: String(form.get("responsavel_id") || ""),
      titulo: String(form.get("titulo") || ""),
      descricao,
      origem: String(form.get("origem") || "CRM"),
      linha_equipamentos: linhas.join(", ") || undefined,
      equipamento: equipamentos.join(", ") || undefined,
      implementadora: String(form.get("implementadora") || "") || undefined,
      estado: String(form.get("estado") || "") || undefined,
      municipio: String(form.get("municipio") || "") || undefined,
      ddd: String(form.get("ddd") || "") || undefined,
      sub_regiao: String(form.get("sub_regiao") || "") || undefined,
      valor_estimado: Number(form.get("valor_estimado") || 0),
      probabilidade: Number(form.get("probabilidade") || 0),
      data_fechamento_prevista:
        String(form.get("data_fechamento_prevista") || "") || undefined,
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
      setErro("Não foi possível criar a oportunidade.")
    } finally {
      setSalvando(false)
    }
  }

  function iniciarEdicao(item: Oportunidade) {
    const contexto = lerContextoOportunidade(item)
    setEditando(item.id)
    setEdicao({
      valor: Number(item.valor_estimado || 0),
      chance: percentual(item.probabilidade),
      quantidade: contexto.quantidade,
      status: item.status || "OPORTUNIDADE",
      data: String(item.data_fechamento_prevista || "").slice(0, 10),
    })
  }

  async function salvarEdicao(item: Oportunidade) {
    setSalvando(true)
    setErro("")

    const contexto = lerContextoOportunidade(item)
    const descricao = montarDescricaoComContexto(contexto.descricao, {
      linhas: contexto.linhas,
      equipamentos: contexto.equipamentos,
      quantidade: edicao.quantidade,
      municipio: contexto.municipio,
      uf: contexto.uf,
      ddd: contexto.ddd,
      subRegiao: contexto.subRegiao,
    })

    try {
      const response = await fetch(`${API_URL}/crm/oportunidades/${item.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          valor_estimado: edicao.valor,
          probabilidade: Math.max(0, Math.min(100, edicao.chance)) / 100,
          status: edicao.status,
          data_fechamento_prevista: edicao.data || null,
          descricao,
        }),
      })
      if (!response.ok) throw new Error("Falha ao atualizar oportunidade")
      setEditando(null)
      await carregar()
    } catch {
      setErro("Não foi possível atualizar a oportunidade.")
    } finally {
      setSalvando(false)
    }
  }

  const abertas = useMemo(
    () =>
      dados.filter(
        (item) =>
          !["GANHO", "PERDIDO", "CANCELADO"].includes(
            String(item.status || "").toUpperCase(),
          ),
      ),
    [dados],
  )

  const valorPipeline = abertas.reduce(
    (total, item) => total + Number(item.valor_estimado || 0),
    0,
  )
  const pipelinePonderado = abertas.reduce(
    (total, item) =>
      total + Number(item.valor_estimado || 0) * fator(item.probabilidade),
    0,
  )

  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="space-y-6 p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white">CRM • Oportunidades</h1>
              <p className="mt-2 text-gray-400">
                Mesmos registros operacionais do App CRM, com edição e análise consolidada.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setMostrarFormulario(true)}
              className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950"
            >
              Nova oportunidade
            </button>
          </div>

          {erro && (
            <div className="rounded-xl border border-red-500 p-4 text-red-300">
              {erro}
            </div>
          )}

          {mostrarFormulario && (
            <form
              onSubmit={criarOportunidade}
              className="rounded-2xl border border-cyan-700 bg-[#071226] p-6 text-gray-200"
            >
              <h2 className="text-xl font-bold text-white">
                Cadastro de nova oportunidade
              </h2>
              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
                <label className="text-sm text-gray-300">
                  Cliente da base
                  <input
                    name="cliente_id"
                    list="clientes-mestre"
                    required
                    className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white"
                  />
                  <datalist id="clientes-mestre">
                    {clientes.map((cliente) => (
                      <option key={cliente.nome} value={cliente.nome} />
                    ))}
                  </datalist>
                </label>
                <Campo nome="responsavel_id" label="Responsável comercial" obrigatorio />
                <Campo nome="titulo" label="Título" obrigatorio />
                <Campo nome="origem" label="Origem" padrao="CRM" />
                <Campo nome="linha_equipamentos" label="Linhas de produto" />
                <Campo nome="equipamento" label="Equipamentos" />
                <Campo nome="quantidade" label="Quantidade total" tipo="number" padrao="1" />
                <Campo nome="implementadora" label="Implementadora" />
                <Campo nome="estado" label="UF" />
                <Campo nome="municipio" label="Município" />
                <Campo nome="ddd" label="DDD" />
                <Campo nome="sub_regiao" label="Sub-região" />
                <Campo nome="valor_estimado" label="Valor estimado total" tipo="number" />
                <Campo
                  nome="probabilidade"
                  label="Chance estimada de fechamento (%)"
                  tipo="number"
                />
                <Campo
                  nome="data_fechamento_prevista"
                  label="Previsão de fechamento"
                  tipo="date"
                />
                <Campo nome="descricao" label="Descrição comercial" />
              </div>
              <div className="mt-5 flex gap-3">
                <button
                  disabled={salvando}
                  className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950"
                >
                  {salvando ? "Salvando..." : "Salvar oportunidade"}
                </button>
                <button
                  type="button"
                  onClick={() => setMostrarFormulario(false)}
                  className="rounded-xl border border-cyan-500 px-5 py-3 font-semibold text-cyan-300"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Kpi titulo="Clientes disponíveis" valor={clientes.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Oportunidades abertas" valor={abertas.length.toLocaleString("pt-BR")} />
            <Kpi titulo="Pipeline total" valor={moeda(valorPipeline)} />
            <Kpi titulo="Pipeline ponderado" valor={moeda(pipelinePonderado)} />
          </section>

          <div className="overflow-x-auto rounded-2xl border border-[#13203f] bg-[#091a33]">
            {loading ? (
              <div className="p-10 text-gray-400">Carregando...</div>
            ) : dados.length === 0 ? (
              <div className="p-10 text-gray-300">Nenhuma oportunidade cadastrada.</div>
            ) : (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#13203f] text-gray-400">
                    <th className="p-4">Cliente</th>
                    <th className="p-4">Oportunidade</th>
                    <th className="p-4">Produto / quantidade</th>
                    <th className="p-4">Etapa</th>
                    <th className="p-4">Valor</th>
                    <th className="p-4">Chance</th>
                    <th className="p-4">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.map((item) => {
                    const contexto = lerContextoOportunidade(item)
                    const emEdicao = editando === item.id
                    return (
                      <tr
                        key={item.id}
                        className="border-b border-[#13203f] align-top text-gray-200"
                      >
                        <td className="p-4 font-semibold text-cyan-300">
                          {item.cliente_id || "-"}
                        </td>
                        <td className="p-4">
                          <strong>{item.titulo}</strong>
                          {contexto.descricao && (
                            <p className="mt-1 max-w-sm text-xs text-gray-400">
                              {contexto.descricao}
                            </p>
                          )}
                        </td>
                        <td className="p-4">
                          {contexto.equipamentos.join(", ") || "A definir"}
                          <div className="text-xs text-gray-400">
                            {emEdicao ? (
                              <input
                                type="number"
                                min="1"
                                value={edicao.quantidade}
                                onChange={(evento) =>
                                  setEdicao({
                                    ...edicao,
                                    quantidade: Math.max(
                                      1,
                                      Number(evento.target.value),
                                    ),
                                  })
                                }
                                className="mt-2 w-24 rounded border border-[#24466f] bg-[#020817] p-2"
                              />
                            ) : (
                              `${contexto.quantidade} unidade(s)`
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          {emEdicao ? (
                            <select
                              value={edicao.status}
                              onChange={(evento) =>
                                setEdicao({ ...edicao, status: evento.target.value })
                              }
                              className="rounded border border-[#24466f] bg-[#020817] p-2"
                            >
                              <option>OPORTUNIDADE</option>
                              <option>PROPOSTA</option>
                              <option>NEGOCIACAO</option>
                              <option>GANHO</option>
                              <option>PERDIDO</option>
                              <option>CANCELADO</option>
                            </select>
                          ) : (
                            item.status
                          )}
                        </td>
                        <td className="p-4 text-green-400">
                          {emEdicao ? (
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={edicao.valor}
                              onChange={(evento) =>
                                setEdicao({
                                  ...edicao,
                                  valor: Number(evento.target.value),
                                })
                              }
                              className="w-36 rounded border border-[#24466f] bg-[#020817] p-2 text-white"
                            />
                          ) : (
                            moeda(Number(item.valor_estimado || 0))
                          )}
                        </td>
                        <td className="p-4">
                          {emEdicao ? (
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={edicao.chance}
                              onChange={(evento) =>
                                setEdicao({
                                  ...edicao,
                                  chance: Number(evento.target.value),
                                })
                              }
                              className="w-20 rounded border border-[#24466f] bg-[#020817] p-2"
                            />
                          ) : (
                            `${percentual(item.probabilidade)}%`
                          )}
                        </td>
                        <td className="p-4">
                          {emEdicao ? (
                            <div className="flex gap-2">
                              <button
                                type="button"
                                disabled={salvando}
                                onClick={() => void salvarEdicao(item)}
                                className="rounded bg-cyan-500 px-3 py-2 font-semibold text-slate-950"
                              >
                                Salvar
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditando(null)}
                                className="rounded border border-cyan-700 px-3 py-2 text-cyan-300"
                              >
                                Cancelar
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => iniciarEdicao(item)}
                              className="rounded border border-cyan-700 px-3 py-2 text-cyan-300"
                            >
                              Alterar
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}

function Campo({
  nome,
  label,
  tipo = "text",
  obrigatorio = false,
  padrao = "",
}: {
  nome: string
  label: string
  tipo?: string
  obrigatorio?: boolean
  padrao?: string
}) {
  return (
    <label className="text-sm text-gray-300">
      {label}
      <input
        name={nome}
        type={tipo}
        required={obrigatorio}
        defaultValue={padrao}
        className="mt-1 w-full rounded-lg border border-[#13203f] bg-[#020817] p-3 text-white"
      />
    </label>
  )
}

function Kpi({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="rounded-2xl border border-[#13203f] bg-[#091a33] p-6">
      <p className="text-sm text-gray-400">{titulo}</p>
      <p className="mt-2 text-3xl font-bold text-cyan-400">{valor}</p>
    </div>
  )
}
