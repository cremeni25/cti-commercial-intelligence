"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ArrowLeft, Building2, ChevronRight, Loader2, Search } from "lucide-react"

type Registro = Record<string, unknown>
type Cliente = { id: string; chave: string; nome: string; codigo: string; cidade: string; estado: string }
type Negocio = { oportunidade_id: string; cliente_id: string; cliente_chave: string; titulo: string; etapa: string; valor: number }

function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const item = payload as Registro
    for (const chave of ["dados", "itens", "resultado", "oportunidades"]) {
      if (Array.isArray(item[chave])) return item[chave] as Registro[]
    }
  }
  return []
}

function texto(valor: unknown) {
  return String(valor || "").trim()
}

function chaveNome(valor: unknown) {
  return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR")
}

function primeiro(valor: unknown) {
  return Array.isArray(valor) ? texto(valor[0]) : texto(valor)
}

function clienteDoCadastro(item: Registro): Cliente | null {
  const nome = texto(item.nome || item.empresa || item.razao_social || item.nome_fantasia || item.cliente)
  if (!nome) return null
  const id = texto(item.id || item.cliente_id || item.codigo || item.codigo_cliente) || nome
  return {
    id,
    chave: chaveNome(nome),
    nome,
    codigo: texto(item.codigo || item.codigo_cliente || item.id) || nome,
    cidade: texto(item.cidade || item.municipio) || primeiro(item.municipios),
    estado: (texto(item.estado || item.uf) || primeiro(item.estados)).toUpperCase(),
  }
}

function clienteDoNegocio(item: Registro): Cliente | null {
  const nome = texto(item.cliente_nome || item.razao_social || item.nome_cliente || item.cliente)
  if (!nome) return null
  const id = texto(item.cliente_id || item.cliente_codigo || item.codigo_cliente) || nome
  return {
    id,
    chave: chaveNome(nome),
    nome,
    codigo: texto(item.cliente_codigo || item.codigo_cliente || item.cliente_id) || nome,
    cidade: texto(item.cliente_cidade || item.municipio || item.cidade),
    estado: texto(item.cliente_estado || item.estado || item.uf).toUpperCase(),
  }
}

export default function ClientesCrmAppPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [negocios, setNegocios] = useState<Negocio[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")

  useEffect(() => {
    let ativo = true

    async function carregar() {
      setCarregando(true)
      setErro("")
      setAviso("")

      const [clientesResultado, negociosResultado] = await Promise.allSettled([
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" })
          .then(async (resposta) => {
            if (!resposta.ok) throw new Error(`Clientes: HTTP ${resposta.status}`)
            return resposta.json()
          }),
        fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" })
          .then(async (resposta) => {
            if (!resposta.ok) throw new Error(`Núcleo comercial: HTTP ${resposta.status}`)
            return resposta.json()
          }),
      ])

      if (!ativo) return

      if (negociosResultado.status === "rejected") {
        setErro("Não foi possível carregar o núcleo comercial. Tente novamente em instantes.")
        setCarregando(false)
        return
      }

      const registrosNegocios = lista(negociosResultado.value)
      const negociosDados = registrosNegocios.map((item) => ({
        oportunidade_id: texto(item.oportunidade_id || item.id),
        cliente_id: texto(item.cliente_id),
        cliente_chave: chaveNome(item.cliente_nome || item.razao_social || item.nome_cliente || item.cliente),
        titulo: texto(item.titulo || item.equipamento || "Oportunidade comercial"),
        etapa: texto(item.etapa || item.status_oportunidade || item.status || "OPORTUNIDADE"),
        valor: Number(item.valor || item.valor_estimado || 0),
      })).filter((item) => item.oportunidade_id)

      const mapaClientes = new Map<string, Cliente>()

      if (clientesResultado.status === "fulfilled") {
        for (const item of lista(clientesResultado.value)) {
          const cliente = clienteDoCadastro(item)
          if (cliente) mapaClientes.set(cliente.chave, cliente)
        }
      } else {
        setAviso("Cadastro histórico temporariamente indisponível. Exibindo clientes encontrados no núcleo comercial.")
      }

      for (const item of registrosNegocios) {
        const cliente = clienteDoNegocio(item)
        if (!cliente) continue
        const existente = mapaClientes.get(cliente.chave)
        mapaClientes.set(cliente.chave, existente ? { ...existente, id: texto(item.cliente_id) || existente.id } : cliente)
      }

      setClientes([...mapaClientes.values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
      setNegocios(negociosDados)
      setCarregando(false)
    }

    void carregar()
    return () => { ativo = false }
  }, [])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return clientes
    return clientes.filter((cliente) =>
      `${cliente.nome} ${cliente.codigo} ${cliente.cidade} ${cliente.estado}`
        .toLocaleLowerCase("pt-BR")
        .includes(termo),
    )
  }, [busca, clientes])

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6">
      <div className="mx-auto max-w-5xl">
        <header className="mb-5 flex items-center gap-3">
          <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p>
            <h1 className="text-2xl font-bold">Clientes e histórico comercial</h1>
            {!carregando && !erro ? <p className="mt-1 text-sm text-slate-400">{clientes.length} clientes na mesma carteira exibida na tela inicial</p> : null}
          </div>
        </header>

        <div className="relative mb-4">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar cliente, código ou cidade"
            className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"
          />
        </div>

        {aviso && <div className="mb-4 rounded-2xl border border-amber-900 bg-amber-950/30 p-4 text-sm text-amber-100">{aviso}</div>}
        {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}

        {carregando ? (
          <div className="grid min-h-64 place-items-center gap-3 text-slate-400">
            <Loader2 className="animate-spin text-cyan-300" />
            <span>Carregando carteira comercial...</span>
          </div>
        ) : erro ? null : filtrados.length === 0 ? (
          <div className="grid min-h-64 place-items-center rounded-3xl border border-dashed border-[#24466f] p-8 text-center">
            <div>
              <AlertCircle className="mx-auto mb-3 text-cyan-300" />
              <p className="font-semibold">Nenhum cliente encontrado</p>
              <p className="mt-1 text-sm text-slate-400">
                {busca ? "A busca não encontrou clientes correspondentes." : "Ainda não há clientes disponíveis na carteira comercial."}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {filtrados.map((cliente) => {
              const relacionados = negocios.filter((negocio) =>
                (negocio.cliente_id && negocio.cliente_id === cliente.id) ||
                (negocio.cliente_chave && negocio.cliente_chave === cliente.chave),
              )
              return (
                <section key={cliente.chave} className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
                  <div className="flex items-start gap-3">
                    <span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22} /></span>
                    <div className="min-w-0">
                      <h2 className="font-bold">{cliente.nome}</h2>
                      <p className="text-xs text-slate-400">
                        {cliente.codigo}{cliente.cidade ? ` · ${cliente.cidade}${cliente.estado ? `/${cliente.estado}` : ""}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    {relacionados.length === 0 ? (
                      <p className="rounded-2xl border border-dashed border-[#24466f] p-3 text-sm text-slate-500">Nenhuma negociação vinculada.</p>
                    ) : relacionados.map((negocio) => (
                      <Link
                        key={negocio.oportunidade_id}
                        href={`/crm-app/historico/${negocio.oportunidade_id}`}
                        className="flex items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-3"
                      >
                        <div className="min-w-0 flex-1">
                          <strong className="block truncate text-sm">{negocio.titulo}</strong>
                          <span className="text-xs text-slate-400">
                            {negocio.etapa} · {negocio.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                          </span>
                        </div>
                        <ChevronRight size={18} className="text-cyan-300" />
                      </Link>
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
