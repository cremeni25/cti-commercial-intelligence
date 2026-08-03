"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ArrowLeft, Building2, ChevronRight, Loader2, Search } from "lucide-react"

type Registro = Record<string, unknown>
type Cliente = { id: string; chave: string; nome: string; codigo: string; cidade: string; estado: string; negocios: number }

function texto(valor: unknown) { return String(valor ?? "").trim() }
function lista(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["dados", "itens", "resultado", "oportunidades"]) if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
  }
  return []
}
function chaveNome(valor: unknown) { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }
function primeiro(valor: unknown) { return Array.isArray(valor) ? texto(valor[0]) : texto(valor) }

export default function ClientesCrmAppPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")

  useEffect(() => {
    let ativo = true
    async function carregar() {
      setCarregando(true); setErro(""); setAviso("")
      const [cadastroResultado, nucleoResultado] = await Promise.allSettled([
        fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }).then(async (r) => { if (!r.ok) throw new Error(`Clientes: HTTP ${r.status}`); return r.json() }),
        fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }).then(async (r) => { if (!r.ok) throw new Error(`Núcleo comercial: HTTP ${r.status}`); return r.json() }),
      ])
      if (!ativo) return
      if (nucleoResultado.status === "rejected") { setErro("Não foi possível carregar o núcleo comercial. Tente novamente em instantes."); setCarregando(false); return }

      const registrosNucleo = lista(nucleoResultado.value)
      const mapa = new Map<string, Cliente>()
      if (cadastroResultado.status === "fulfilled") {
        for (const item of lista(cadastroResultado.value)) {
          const nome = texto(item.nome || item.empresa || item.razao_social || item.nome_fantasia || item.cliente)
          if (!nome) continue
          const chave = chaveNome(nome)
          mapa.set(chave, {
            id: texto(item.id || item.cliente_id || item.codigo || item.codigo_cliente) || nome,
            chave,
            nome,
            codigo: texto(item.codigo || item.codigo_cliente || item.id) || nome,
            cidade: texto(item.cidade || item.municipio) || primeiro(item.municipios),
            estado: (texto(item.estado || item.uf) || primeiro(item.estados)).toUpperCase(),
            negocios: 0,
          })
        }
      } else setAviso("Cadastro histórico temporariamente indisponível. Exibindo clientes encontrados no núcleo comercial.")

      for (const item of registrosNucleo) {
        const nome = texto(item.cliente_nome || item.razao_social || item.nome_cliente || item.cliente)
        if (!nome) continue
        const chave = chaveNome(nome)
        const existente = mapa.get(chave)
        mapa.set(chave, {
          id: texto(item.cliente_id) || existente?.id || nome,
          chave,
          nome: existente?.nome || nome,
          codigo: existente?.codigo || texto(item.cliente_codigo || item.codigo_cliente || item.cliente_id) || nome,
          cidade: existente?.cidade || texto(item.cliente_cidade || item.municipio || item.cidade),
          estado: existente?.estado || texto(item.cliente_estado || item.estado || item.uf).toUpperCase(),
          negocios: (existente?.negocios || 0) + 1,
        })
      }
      setClientes([...mapa.values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
      setCarregando(false)
    }
    void carregar()
    return () => { ativo = false }
  }, [])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return clientes
    return clientes.filter((item) => `${item.nome} ${item.codigo} ${item.cidade} ${item.estado}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, clientes])

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-5xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Carteira de clientes</h1>{!carregando && !erro && <p className="mt-1 text-sm text-slate-400">{clientes.length} clientes · abra o dossiê para consultar histórico e próximos passos</p>}</div></header>
    <label className="relative mb-4 block"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, código ou cidade" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></label>
    {aviso && <div className="mb-4 rounded-2xl border border-amber-900 bg-amber-950/30 p-4 text-sm text-amber-100">{aviso}</div>}
    {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {carregando ? <div className="grid min-h-64 place-items-center gap-3 text-slate-400"><Loader2 className="animate-spin text-cyan-300"/><span>Carregando carteira comercial...</span></div> : erro ? null : filtrados.length === 0 ? <div className="grid min-h-64 place-items-center rounded-3xl border border-dashed border-[#24466f] p-8 text-center"><div><AlertCircle className="mx-auto mb-3 text-cyan-300"/><p className="font-semibold">Nenhum cliente encontrado</p><p className="mt-1 text-sm text-slate-400">A busca não encontrou clientes correspondentes.</p></div></div> : <div className="grid gap-4 md:grid-cols-2">{filtrados.map((cliente) => <Link key={cliente.chave} href={`/crm-app/clientes/${encodeURIComponent(cliente.id)}?nome=${encodeURIComponent(cliente.nome)}`} className="group rounded-3xl border border-[#16325c] bg-[#07162b] p-5 transition hover:border-cyan-700"><div className="flex items-center gap-3"><span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Building2 size={22}/></span><div className="min-w-0 flex-1"><h2 className="truncate font-bold">{cliente.nome}</h2><p className="text-xs text-slate-400">{cliente.codigo}{cliente.cidade ? ` · ${cliente.cidade}${cliente.estado ? `/${cliente.estado}` : ""}` : ""}</p><p className="mt-2 text-xs font-semibold text-cyan-300">{cliente.negocios} {cliente.negocios === 1 ? "negociação" : "negociações"} · abrir dossiê comercial</p></div><ChevronRight size={20} className="text-cyan-300 transition group-hover:translate-x-1"/></div></Link>)}</div>}
  </div></main>
}
