"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import {
  Activity,
  ArrowLeft,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Loader2,
  MapPinned,
  Plus,
  Search,
  Target,
  UserPlus,
} from "lucide-react"
import { useAuth } from "@/core/auth"
import {
  lerContextoOportunidade,
  montarDescricaoComContexto,
  textoSeguro,
} from "@/lib/crm-opportunity"

type Registro = Record<string, unknown>
type ClienteOpcao = {
  id: string
  nome: string
  codigo: string
  cidade?: string
  estado?: string
  ddd?: string
  subRegiao?: string
  segmento?: string
}
type ModuloConfig = {
  titulo: string
  endpoint: string
  icon: typeof Activity
  extrair: (payload: unknown) => Registro[]
}

const configs: Record<string, ModuloConfig> = {
  agenda: {
    titulo: "Agenda comercial",
    endpoint: "/crm/agenda",
    icon: CalendarDays,
    extrair: (payload) => (payload as { itens?: Registro[] })?.itens || [],
  },
  clientes: {
    titulo: "Clientes",
    endpoint: "/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO",
    icon: Building2,
    extrair: (payload) => (Array.isArray(payload) ? payload : []),
  },
  visitas: {
    titulo: "Visitas",
    endpoint: "/crm/atividades",
    icon: MapPinned,
    extrair: (payload) =>
      Array.isArray(payload)
        ? payload.filter((item) =>
            String(item.tipo || "").toUpperCase().includes("VISITA"),
          )
        : [],
  },
  oportunidades: {
    titulo: "Oportunidades",
    endpoint: "/crm/oportunidades?origem=CRM_APP",
    icon: BriefcaseBusiness,
    extrair: (payload) =>
      Array.isArray(payload)
        ? payload.filter(
            (item) => String(item.origem || "").toUpperCase() === "CRM_APP",
          )
        : [],
  },
  pipeline: {
    titulo: "Pipeline",
    endpoint: "/crm/oportunidades?origem=CRM_APP",
    icon: CircleDollarSign,
    extrair: (payload) =>
      Array.isArray(payload)
        ? payload.filter(
            (item) => String(item.origem || "").toUpperCase() === "CRM_APP",
          )
        : [],
  },
  atividades: {
    titulo: "Atividades",
    endpoint: "/crm/atividades",
    icon: Activity,
    extrair: (payload) => (Array.isArray(payload) ? payload : []),
  },
}

const produtosPorLinha: Record<string, string[]> = {
  TRAILER: ["X4-7500", "X4-7700", "Vector HE19", "Vector 8600MT"],
  "DIESEL TRUCK": ["Supra 1150", "Supra 850", "Supra 850MT", "Supra 750"],
  "DIRECT DRIVE": [
    "CM500",
    "CM400",
    "CM280",
    "Xarios 350",
    "Xarios 600",
    "D7",
    "D7 AE",
    "D6",
    "D6 AE",
  ],
}

const moeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
})

function codigoEstavel(nome: string): string {
  let hash = 0
  for (let indice = 0; indice < nome.length; indice += 1) {
    hash = ((hash << 5) - hash + nome.charCodeAt(indice)) | 0
  }
  return `CLI-${Math.abs(hash).toString().padStart(8, "0").slice(0, 8)}`
}

function clienteDe(item: Registro): ClienteOpcao | null {
  const nome = textoSeguro(
    item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente,
  ).trim()
  if (!nome) return null

  return {
    id: textoSeguro(item.id || item.cliente_id || item.uuid).trim() || nome,
    nome,
    codigo:
      textoSeguro(item.codigo || item.codigo_cliente || item.id).trim() ||
      codigoEstavel(nome),
    cidade: textoSeguro(item.cidade || item.municipio).trim(),
    estado: textoSeguro(item.estado || item.uf).trim().toUpperCase(),
    ddd: textoSeguro(item.ddd).trim(),
    subRegiao: textoSeguro(item.sub_regiao || item.subRegiao).trim(),
    segmento: textoSeguro(item.segmento).trim(),
  }
}

function percentualExibido(valor: unknown): number {
  const numero = Number(valor || 0)
  return Math.round(numero <= 1 ? numero * 100 : numero)
}

export default function CrmModuloPage() {
  const params = useParams<{ modulo: string[] }>()
  const { usuario } = useAuth()
  const segmentos = Array.isArray(params.modulo)
    ? params.modulo
    : [String(params.modulo || "")]
  const slug = segmentos[0]
  const novo = segmentos[1] === "nova"
  const config = configs[slug] || configs.atividades
  const Icon = config.icon

  const [registros, setRegistros] = useState<Registro[]>([])
  const [clientes, setClientes] = useState<ClienteOpcao[]>([])
  const [clienteBusca, setClienteBusca] = useState("")
  const [clienteSelecionado, setClienteSelecionado] =
    useState<ClienteOpcao | null>(null)
  const [cadastroNovo, setCadastroNovo] = useState(false)
  const [novoCliente, setNovoCliente] = useState({
    nome: "",
    segmento: "TRANSPORTADOR",
  })
  const [municipio, setMunicipio] = useState("")
  const [uf, setUf] = useState("")
  const [ddd, setDdd] = useState("")
  const [subRegiao, setSubRegiao] = useState("")
  const [linhas, setLinhas] = useState<string[]>([])
  const [equipamentos, setEquipamentos] = useState<string[]>([])
  const [quantidade, setQuantidade] = useState(1)
  const [valorCentavos, setValorCentavos] = useState(0)
  const [probabilidade, setProbabilidade] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const [busca, setBusca] = useState("")

  const api = useCallback(
    (endpoint: string, init?: RequestInit) =>
      fetch(`/api/crm-proxy${endpoint}`, { ...init, cache: "no-store" }),
    [],
  )

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const [resposta, clientesResposta] = await Promise.all([
        api(config.endpoint),
        api("/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO"),
      ])
      if (!resposta.ok) throw new Error(`Falha ${resposta.status}`)
      setRegistros(config.extrair(await resposta.json()))

      if (clientesResposta.ok) {
        const dados = await clientesResposta.json()
        const opcoes = (Array.isArray(dados) ? dados : [])
          .map(clienteDe)
          .filter(Boolean) as ClienteOpcao[]
        setClientes(opcoes.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
      }
    } catch (falha) {
      setErro(
        falha instanceof Error
          ? falha.message
          : "Não foi possível carregar os dados deste módulo.",
      )
    } finally {
      setCarregando(false)
    }
  }, [api, config])

  useEffect(() => {
    queueMicrotask(() => void carregar())
  }, [carregar])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return termo
      ? registros.filter((item) => JSON.stringify(item).toLowerCase().includes(termo))
      : registros
  }, [busca, registros])

  const sugestoesClientes = useMemo(() => {
    const termo = clienteBusca.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || clienteSelecionado) return []
    return clientes
      .filter((cliente) =>
        `${cliente.nome} ${cliente.codigo}`
          .toLocaleLowerCase("pt-BR")
          .includes(termo),
      )
      .slice(0, 12)
  }, [clienteBusca, clienteSelecionado, clientes])

  const equipamentosDisponiveis = useMemo(
    () => [...new Set(linhas.flatMap((linha) => produtosPorLinha[linha] || []))],
    [linhas],
  )
  const valorEstimado = valorCentavos / 100

  function selecionarCliente(cliente: ClienteOpcao) {
    setClienteSelecionado(cliente)
    setClienteBusca(cliente.nome)
    setCadastroNovo(false)
    setMunicipio(cliente.cidade || "")
    setUf(cliente.estado || "")
    setDdd(cliente.ddd || "")
    setSubRegiao(cliente.subRegiao || "")
  }

  function alterarValorDigitado(valor: string) {
    const digitos = valor.replace(/\D/g, "").replace(/^0+(?=\d)/, "")
    setValorCentavos(digitos ? Number(digitos.slice(0, 15)) : 0)
  }

  function alterarProbabilidade(valor: string) {
    setProbabilidade(Math.min(100, Number(valor.replace(/\D/g, "") || 0)))
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setSalvando(true)
    setErro("")
    setSucesso("")

    const formulario = evento.currentTarget
    const dados = new FormData(formulario)
    const userId = String(usuario?.id || "")

    if (!userId) {
      setErro("Não foi possível confirmar o usuário autenticado.")
      setSalvando(false)
      return
    }

    if (slug === "oportunidades") {
      const nomeCliente = (
        clienteSelecionado?.nome ||
        novoCliente.nome ||
        clienteBusca
      ).trim()

      if (
        !nomeCliente ||
        !municipio.trim() ||
        uf.trim().length !== 2 ||
        !equipamentos.length ||
        quantidade < 1
      ) {
        setErro("Preencha cliente, território, equipamento e quantidade.")
        setSalvando(false)
        return
      }

      const titulo = String(dados.get("titulo") || "").trim()
      if (!titulo) {
        setErro("Informe o título da oportunidade.")
        setSalvando(false)
        return
      }

      const descricao = montarDescricaoComContexto(
        String(dados.get("descricao") || "").trim(),
        {
          linhas,
          equipamentos,
          quantidade,
          municipio: municipio.trim(),
          uf: uf.trim().toUpperCase(),
          ddd: ddd.trim(),
          subRegiao: subRegiao.trim(),
        },
      )

      const payload = {
        cliente: {
          id: clienteSelecionado?.id || null,
          nome: nomeCliente,
          cidade: municipio.trim(),
          estado: uf.trim().toUpperCase(),
          segmento:
            clienteSelecionado?.segmento ||
            novoCliente.segmento ||
            "TRANSPORTADOR",
          ddd: ddd.trim() || null,
          sub_regiao: subRegiao.trim() || null,
        },
        oportunidade: {
          responsavel_id: userId,
          titulo,
          descricao,
          valor_estimado: valorEstimado,
          probabilidade,
          data_fechamento_prevista: String(dados.get("data") || "") || null,
          linha_equipamentos: linhas.join(", "),
          equipamento: equipamentos.join(", "),
          municipio: municipio.trim(),
          estado: uf.trim().toUpperCase(),
          ddd: ddd.trim() || null,
          sub_regiao: subRegiao.trim() || null,
        },
      }

      try {
        const resposta = await api("/crm-app/cliente-oportunidade", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
        const detalhe = await resposta.json().catch(() => ({}))
        if (!resposta.ok) {
          throw new Error(String(detalhe.detail || `Falha ${resposta.status}`))
        }

        formulario.reset()
        setClienteBusca("")
        setClienteSelecionado(null)
        setCadastroNovo(false)
        setNovoCliente({ nome: "", segmento: "TRANSPORTADOR" })
        setMunicipio("")
        setUf("")
        setDdd("")
        setSubRegiao("")
        setLinhas([])
        setEquipamentos([])
        setQuantidade(1)
        setValorCentavos(0)
        setProbabilidade(0)
        setSucesso("Oportunidade registrada no CTI e disponível no site e no App.")
        await carregar()
      } catch (falha) {
        setErro(
          falha instanceof Error
            ? falha.message
            : "Não foi possível salvar a oportunidade.",
        )
      } finally {
        setSalvando(false)
      }
      return
    }

    if (!clienteSelecionado) {
      setErro("Selecione um cliente existente.")
      setSalvando(false)
      return
    }

    const payload = {
      cliente_id: clienteSelecionado.id,
      usuario_id: userId,
      tipo:
        slug === "visitas"
          ? "VISITA"
          : String(dados.get("tipo") || "ATIVIDADE"),
      titulo: String(dados.get("titulo") || "").trim(),
      descricao: String(dados.get("descricao") || "").trim() || null,
      data: String(dados.get("data") || "") || null,
      horario: String(dados.get("horario") || "") || null,
      status: "PENDENTE",
    }

    try {
      const resposta = await api("/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) {
        throw new Error(String(detalhe.detail || `Falha ${resposta.status}`))
      }
      formulario.reset()
      setClienteBusca("")
      setClienteSelecionado(null)
      setSucesso("Registro salvo com sucesso.")
      await carregar()
    } catch (falha) {
      setErro(
        falha instanceof Error
          ? falha.message
          : "Não foi possível salvar o registro.",
      )
    } finally {
      setSalvando(false)
    }
  }

  async function concluir(id: string) {
    const resposta = await api(`/crm/atividades/${id}/concluir`, {
      method: "PUT",
    })
    if (!resposta.ok) setErro("Não foi possível concluir a atividade.")
    else await carregar()
  }

  async function atualizarOportunidade(id: string, payload: Registro) {
    const resposta = await api(`/crm/oportunidades/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!resposta.ok) {
      const detalhe = await resposta.json().catch(() => ({}))
      throw new Error(
        String(detalhe.detail || "Não foi possível atualizar a oportunidade."),
      )
    }
    await carregar()
  }

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-30 border-b border-[#16325c] bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4">
        <div className="mx-auto flex w-full max-w-[94vw] items-center gap-3">
          <Link
            href="/crm-app"
            className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"
          >
            <ArrowLeft size={20} />
          </Link>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-400">
              CTI CRM
            </p>
            <h1 className="truncate text-lg font-bold sm:text-2xl">
              {novo ? `Novo registro — ${config.titulo}` : config.titulo}
            </h1>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-[94vw] px-4 py-4 sm:px-6 sm:py-6">
        <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-4 shadow-xl sm:p-6">
          <div className="flex items-center gap-3">
            <span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">
              <Icon size={24} />
            </span>
            <div>
              <p className="text-sm text-slate-400">Operação em campo</p>
              <p className="text-xl font-bold">{config.titulo}</p>
            </div>
          </div>
        </section>

        {erro && (
          <div className="mt-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">
            {erro}
          </div>
        )}
        {sucesso && (
          <div className="mt-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">
            {sucesso}
          </div>
        )}

        {novo ? (
          <form
            onSubmit={salvar}
            className="mt-4 grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-4 sm:grid-cols-2 sm:p-6"
          >
            <label className="relative">
              <span className="mb-2 block text-sm text-slate-300">Cliente</span>
              <input
                value={clienteBusca}
                onChange={(evento) => {
                  setClienteBusca(evento.target.value)
                  setClienteSelecionado(null)
                  setNovoCliente((atual) => ({
                    ...atual,
                    nome: evento.target.value,
                  }))
                }}
                placeholder="Digite ao menos 2 letras"
                autoComplete="off"
                className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"
              />
              {sugestoesClientes.length > 0 && (
                <div className="absolute z-40 mt-2 max-h-72 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">
                  {sugestoesClientes.map((cliente) => (
                    <button
                      type="button"
                      key={`${cliente.id}-${cliente.codigo}`}
                      onClick={() => selecionarCliente(cliente)}
                      className="block w-full border-b border-[#16325c] px-4 py-3 text-left last:border-0"
                    >
                      <strong className="block">{cliente.nome}</strong>
                      <span className="text-xs text-slate-400">
                        Código CTI: {cliente.codigo}
                      </span>
                    </button>
                  ))}
                </div>
              )}
              {clienteSelecionado && (
                <span className="mt-2 block text-xs text-emerald-300">
                  Cliente selecionado • código {clienteSelecionado.codigo}
                </span>
              )}
              {clienteBusca.trim().length >= 2 &&
                !clienteSelecionado &&
                sugestoesClientes.length === 0 && (
                  <button
                    type="button"
                    onClick={() => setCadastroNovo(true)}
                    className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-cyan-300"
                  >
                    <UserPlus size={16} /> Cadastrar “{clienteBusca.trim()}” como novo
                    cliente
                  </button>
                )}
            </label>

            <Campo
              name="titulo"
              label={slug === "visitas" ? "Objetivo da visita" : "Título"}
              required
            />

            {cadastroNovo && (
              <fieldset className="grid gap-3 rounded-2xl border border-cyan-800 bg-cyan-950/20 p-4 sm:col-span-2 sm:grid-cols-3">
                <legend className="px-2 font-semibold text-cyan-300">
                  Cadastro territorial do novo cliente
                </legend>
                <input
                  value={novoCliente.nome}
                  onChange={(evento) =>
                    setNovoCliente({ ...novoCliente, nome: evento.target.value })
                  }
                  placeholder="Razão social / nome"
                  className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4 sm:col-span-2"
                />
                <select
                  value={novoCliente.segmento}
                  onChange={(evento) =>
                    setNovoCliente({ ...novoCliente, segmento: evento.target.value })
                  }
                  className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"
                >
                  <option value="TRANSPORTADOR">Transportador</option>
                  <option value="LOCADORA">Locadora</option>
                  <option value="IMPLEMENTADORA">Implementadora</option>
                  <option value="DISTRIBUIDOR">Distribuidor</option>
                  <option value="INDUSTRIA">Indústria</option>
                  <option value="OUTRO">Outro</option>
                </select>
              </fieldset>
            )}

            {slug === "oportunidades" ? (
              <>
                <label>
                  <span className="mb-2 block text-sm text-slate-300">
                    Valor estimado total
                  </span>
                  <input
                    inputMode="numeric"
                    value={valorCentavos ? moeda.format(valorEstimado) : ""}
                    onChange={(evento) => alterarValorDigitado(evento.target.value)}
                    onFocus={(evento) => evento.currentTarget.select()}
                    placeholder="R$ 0,00"
                    className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"
                  />
                </label>
                <label>
                  <span className="mb-2 block text-sm text-slate-300">
                    Chance estimada de fechamento
                  </span>
                  <input
                    inputMode="numeric"
                    value={probabilidade ? `${probabilidade}%` : ""}
                    onChange={(evento) => alterarProbabilidade(evento.target.value)}
                    onFocus={(evento) => evento.currentTarget.select()}
                    placeholder="0%"
                    className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"
                  />
                </label>
                <SelecaoMultipla
                  titulo="Linhas de produto Carrier"
                  opcoes={Object.keys(produtosPorLinha)}
                  selecionados={linhas}
                  alterar={(valor) => {
                    setLinhas(valor)
                    setEquipamentos((atuais) =>
                      atuais.filter((item) =>
                        valor.some((linha) => produtosPorLinha[linha]?.includes(item)),
                      ),
                    )
                  }}
                />
                <SelecaoMultipla
                  titulo="Equipamentos Carrier"
                  opcoes={equipamentosDisponiveis}
                  selecionados={equipamentos}
                  alterar={setEquipamentos}
                />
                <CampoControlado
                  label="Quantidade total de equipamentos"
                  value={String(quantidade)}
                  onChange={(valor) =>
                    setQuantidade(Math.max(1, Number(valor.replace(/\D/g, "") || 1)))
                  }
                />
                <CampoControlado label="Município" value={municipio} onChange={setMunicipio} />
                <CampoControlado
                  label="UF"
                  value={uf}
                  onChange={(valor) => setUf(valor.toUpperCase().slice(0, 2))}
                />
                <CampoControlado
                  label="DDD"
                  value={ddd}
                  onChange={(valor) =>
                    setDdd(valor.replace(/\D/g, "").slice(0, 3))
                  }
                />
                <CampoControlado
                  label="Sub-região"
                  value={subRegiao}
                  onChange={setSubRegiao}
                  placeholder="Ex.: Região Leste ou Oeste"
                />
                <Campo name="data" label="Fechamento previsto" type="date" />
              </>
            ) : (
              <>
                <Campo
                  name="tipo"
                  label="Tipo"
                  defaultValue={slug === "visitas" ? "VISITA" : "FOLLOW_UP"}
                />
                <Campo name="data" label="Data" type="date" />
                <Campo name="horario" label="Horário" type="time" />
              </>
            )}

            <label className="sm:col-span-2">
              <span className="mb-2 block text-sm text-slate-300">
                Descrição / resultado esperado
              </span>
              <textarea
                name="descricao"
                rows={5}
                className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"
              />
            </label>
            <button
              disabled={salvando}
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-5 font-bold text-slate-950 disabled:opacity-60 sm:col-span-2"
            >
              {salvando ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <CheckCircle2 size={20} />
              )}
              Salvar no CTI
            </button>
          </form>
        ) : (
          <section className="mt-4">
            <div className="relative">
              <Search
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                size={18}
              />
              <input
                value={busca}
                onChange={(evento) => setBusca(evento.target.value)}
                placeholder="Buscar neste módulo"
                className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"
              />
            </div>

            {carregando ? (
              <div className="grid min-h-48 place-items-center">
                <Loader2 className="animate-spin text-cyan-300" />
              </div>
            ) : filtrados.length === 0 ? (
              <div className="mt-4 rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">
                Nenhum registro encontrado.
              </div>
            ) : (
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {filtrados.map((item, indice) => (
                  <Card
                    key={String(item.id || indice)}
                    slug={slug}
                    item={item}
                    concluir={concluir}
                    atualizar={atualizarOportunidade}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 backdrop-blur">
        <div className="mx-auto grid max-w-4xl grid-cols-4 gap-2">
          <Nav href="/crm-app" label="Início" icon={Building2} />
          <Nav href="/crm-app/agenda" label="Agenda" icon={CalendarDays} />
          <Nav href="/crm-app/oportunidades" label="Negócios" icon={Target} />
          <Nav
            href="/crm-app/atividades/nova"
            label="Nova interação"
            icon={Plus}
            destaque
          />
        </div>
      </nav>
    </main>
  )
}

function Campo({
  name,
  label,
  type = "text",
  required = false,
  defaultValue,
}: {
  name: string
  label: string
  type?: string
  required?: boolean
  defaultValue?: string
}) {
  return (
    <label>
      <span className="mb-2 block text-sm text-slate-300">{label}</span>
      <input
        name={name}
        type={type}
        required={required}
        defaultValue={defaultValue}
        className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"
      />
    </label>
  )
}

function CampoControlado({
  label,
  value,
  onChange,
  placeholder = "",
}: {
  label: string
  value: string
  onChange: (valor: string) => void
  placeholder?: string
}) {
  return (
    <label>
      <span className="mb-2 block text-sm text-slate-300">{label}</span>
      <input
        value={value}
        onChange={(evento) => onChange(evento.target.value)}
        placeholder={placeholder}
        className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"
      />
    </label>
  )
}

function SelecaoMultipla({
  titulo,
  opcoes,
  selecionados,
  alterar,
}: {
  titulo: string
  opcoes: string[]
  selecionados: string[]
  alterar: (valor: string[]) => void
}) {
  return (
    <fieldset className="rounded-2xl border border-[#24466f] p-4">
      <legend className="px-2 text-sm text-slate-300">{titulo}</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {opcoes.length === 0 ? (
          <span className="text-sm text-slate-500">Selecione primeiro uma linha.</span>
        ) : (
          opcoes.map((opcao) => (
            <label
              key={opcao}
              className="flex items-center gap-2 rounded-xl bg-[#020817] px-3 py-2"
            >
              <input
                type="checkbox"
                checked={selecionados.includes(opcao)}
                onChange={(evento) =>
                  alterar(
                    evento.target.checked
                      ? [...selecionados, opcao]
                      : selecionados.filter((item) => item !== opcao),
                  )
                }
              />
              <span>{opcao}</span>
            </label>
          ))
        )}
      </div>
    </fieldset>
  )
}

function Card({
  slug,
  item,
  concluir,
  atualizar,
}: {
  slug: string
  item: Registro
  concluir: (id: string) => void
  atualizar: (id: string, payload: Registro) => Promise<void>
}) {
  const contexto = lerContextoOportunidade(item)
  const [editando, setEditando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erroEdicao, setErroEdicao] = useState("")
  const [valor, setValor] = useState(Number(item.valor_estimado || 0))
  const [chance, setChance] = useState(percentualExibido(item.probabilidade))
  const [quantidade, setQuantidade] = useState(contexto.quantidade)
  const [status, setStatus] = useState(String(item.status || "OPORTUNIDADE"))
  const [data, setData] = useState(
    String(item.data_fechamento_prevista || "").slice(0, 10),
  )

  const titulo =
    textoSeguro(item.titulo || item.nome || item.razao_social || item.oportunidade_titulo) ||
    "Registro CTI"
  const subtitulo = textoSeguro(
    item.cliente_nome || item.cliente_id || item.municipio || item.empresa || item.tipo || item.etapa,
  )
  const estado = textoSeguro(item.situacao || item.status || item.etapa) || "ATIVO"
  const dataRegistro = textoSeguro(
    item.data || item.data_fechamento_prevista || item.ultima_movimentacao,
  )
  const oportunidade = ["oportunidades", "pipeline"].includes(slug)

  async function salvarEdicao() {
    if (!item.id) return
    setSalvando(true)
    setErroEdicao("")
    try {
      const descricao = montarDescricaoComContexto(contexto.descricao, {
        linhas: contexto.linhas,
        equipamentos: contexto.equipamentos,
        quantidade,
        municipio: contexto.municipio,
        uf: contexto.uf,
        ddd: contexto.ddd,
        subRegiao: contexto.subRegiao,
      })

      await atualizar(String(item.id), {
        valor_estimado: valor,
        probabilidade: Math.max(0, Math.min(100, chance)) / 100,
        status,
        data_fechamento_prevista: data || null,
        descricao,
      })
      setEditando(false)
    } catch (falha) {
      setErroEdicao(
        falha instanceof Error
          ? falha.message
          : "Não foi possível atualizar a oportunidade.",
      )
    } finally {
      setSalvando(false)
    }
  }

  return (
    <article className="rounded-3xl border border-[#16325c] bg-[#07162b] p-4 shadow-lg sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-semibold sm:text-lg">{titulo}</h2>
          <p className="mt-1 break-all text-sm text-slate-400">{subtitulo}</p>
        </div>
        <span className="rounded-full border border-cyan-900 bg-cyan-950/40 px-2.5 py-1 text-[10px] font-semibold text-cyan-300">
          {estado}
        </span>
      </div>

      {oportunidade && !editando && (
        <div className="mt-4 space-y-2 text-sm">
          <p>
            <span className="text-slate-400">Produto:</span>{" "}
            {contexto.equipamentos.join(", ") || "A definir"}
          </p>
          <p>
            <span className="text-slate-400">Quantidade:</span>{" "}
            {contexto.quantidade} unidade(s)
          </p>
          <p>
            <span className="text-slate-400">Valor total:</span>{" "}
            <strong className="text-emerald-300">
              {moeda.format(Number(item.valor_estimado || 0))}
            </strong>
          </p>
          <p>
            <span className="text-slate-400">Chance estimada de fechamento:</span>{" "}
            {percentualExibido(item.probabilidade)}%
          </p>
          {contexto.descricao && <p className="text-slate-300">{contexto.descricao}</p>}
        </div>
      )}

      {oportunidade && editando && (
        <div className="mt-4 grid gap-3">
          <input
            type="number"
            min="0"
            step="0.01"
            value={valor}
            onChange={(evento) => setValor(Number(evento.target.value))}
            className="h-11 rounded-xl border border-[#24466f] bg-[#020817] px-3"
            placeholder="Valor total"
          />
          <input
            type="number"
            min="0"
            max="100"
            value={chance}
            onChange={(evento) => setChance(Number(evento.target.value))}
            className="h-11 rounded-xl border border-[#24466f] bg-[#020817] px-3"
            placeholder="Chance de fechamento"
          />
          <input
            type="number"
            min="1"
            value={quantidade}
            onChange={(evento) =>
              setQuantidade(Math.max(1, Number(evento.target.value)))
            }
            className="h-11 rounded-xl border border-[#24466f] bg-[#020817] px-3"
            placeholder="Quantidade"
          />
          <select
            value={status}
            onChange={(evento) => setStatus(evento.target.value)}
            className="h-11 rounded-xl border border-[#24466f] bg-[#020817] px-3"
          >
            <option value="OPORTUNIDADE">OPORTUNIDADE</option>
            <option value="PROPOSTA">PROPOSTA</option>
            <option value="NEGOCIACAO">NEGOCIAÇÃO</option>
            <option value="GANHO">GANHO</option>
            <option value="PERDIDO">PERDIDO</option>
            <option value="CANCELADO">CANCELADO</option>
          </select>
          <input
            type="date"
            value={data}
            onChange={(evento) => setData(evento.target.value)}
            className="h-11 rounded-xl border border-[#24466f] bg-[#020817] px-3"
          />
          {erroEdicao && <p className="text-sm text-red-300">{erroEdicao}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              disabled={salvando}
              onClick={() => void salvarEdicao()}
              className="flex min-h-10 flex-1 items-center justify-center gap-2 rounded-xl bg-cyan-500 font-semibold text-slate-950 disabled:opacity-60"
            >
              {salvando ? (
                <Loader2 className="animate-spin" size={16} />
              ) : (
                <CheckCircle2 size={16} />
              )}
              Salvar
            </button>
            <button
              type="button"
              onClick={() => {
                setEditando(false)
                setErroEdicao("")
              }}
              className="min-h-10 rounded-xl border border-[#24466f] px-4"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {dataRegistro && (
        <p className="mt-4 flex items-center gap-2 text-xs text-slate-400">
          <Clock3 size={14} /> {dataRegistro.slice(0, 16).replace("T", " ")}
        </p>
      )}

      {oportunidade && !editando && Boolean(item.id) && (
        <button
          type="button"
          onClick={() => setEditando(true)}
          className="mt-4 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-cyan-800 bg-cyan-950/30 text-sm text-cyan-300"
        >
          <CheckCircle2 size={16} /> Alterar oportunidade
        </button>
      )}

      {["agenda", "atividades", "visitas"].includes(slug) &&
      estado !== "CONCLUIDA" &&
      Boolean(item.id) ? (
        <button
          type="button"
          onClick={() => concluir(String(item.id))}
          className="mt-4 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-emerald-800 bg-emerald-950/30 text-sm text-emerald-300"
        >
          <CheckCircle2 size={16} /> Concluir
        </button>
      ) : null}
    </article>
  )
}

function Nav({
  href,
  label,
  icon: Icon,
  destaque = false,
}: {
  href: string
  label: string
  icon: typeof Activity
  destaque?: boolean
}) {
  return (
    <Link
      href={href}
      className={`flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-[10px] ${
        destaque ? "bg-cyan-500 font-semibold text-slate-950" : "text-slate-400"
      }`}
    >
      <Icon size={19} />
      <span>{label}</span>
    </Link>
  )
}
