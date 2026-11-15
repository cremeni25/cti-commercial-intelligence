"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { BookOpen, Building2, Loader2, Search, X } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import {
  buscarFichaEmpresa,
  buscarGlossario,
  buscarSetorizacao,
  type FichaEmpresa,
  type PerfilCliente,
  type Setorizacao,
  type TermoGlossario,
} from "@/services/carteira-setorizada"

const COR_GRUPO: Record<string, string> = {
  CLIENTE_ATIVO: "border-emerald-700 text-emerald-200",
  CLIENTE_INATIVO: "border-amber-700 text-amber-200",
  PROSPECT_COM_FROTA: "border-cyan-700 text-cyan-200",
  PROSPECT: "border-slate-600 text-slate-300",
}
const ROTULO_CURTO: Record<string, string> = {
  CLIENTE_ATIVO: "Cliente ativo",
  CLIENTE_INATIVO: "Cliente inativo",
  PROSPECT_COM_FROTA: "Prospect com frota",
  PROSPECT: "Prospect",
  GRANDE: "Frota grande",
  MEDIO: "Frota média",
  PEQUENO: "Frota pequena",
  SEM_DADO: "Frota não identificada",
  RECORRENTE: "Recorrente",
  JANELA_RENOVACAO: "Janela de renovação",
  USA_CONCORRENTE: "Usa concorrente",
  NEGOCIO_ABERTO: "Negócio aberto",
  SEM_RESPONSAVEL: "Sem responsável",
}
const numero = (valor: number) => valor.toLocaleString("pt-BR")
const moeda = (valor: number | null | undefined) => (valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })
function dataCurta(valor?: string | null) {
  if (!valor) return "—"
  const [a, m, d] = valor.slice(0, 10).split("-")
  return a && m && d ? `${d}/${m}/${a}` : valor
}

function Ficha({ clienteId, onFechar }: { clienteId: string; onFechar: () => void }) {
  const [ficha, setFicha] = useState<FichaEmpresa | null>(null)
  const [erro, setErro] = useState("")
  useEffect(() => {
    let ativo = true
    buscarFichaEmpresa(clienteId).then((f) => { if (ativo) setFicha(f) }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível abrir a ficha.") })
    return () => { ativo = false }
  }, [clienteId])

  return (
    <div role="dialog" aria-modal="true" aria-label="Ficha da empresa" className="fixed inset-0 z-50 flex justify-end bg-black/60">
      <section className="h-full w-full max-w-2xl overflow-y-auto border-l border-[#163356] bg-[#061126] p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[.2em] text-cyan-400">Ficha da empresa</p>
            <h2 className="mt-1 text-2xl font-bold">{ficha?.nome || "..."}</h2>
            {ficha && <p className="text-sm text-slate-400">{[ficha.cnpj, [ficha.cidade, ficha.estado].filter(Boolean).join("/"), ficha.segmento].filter(Boolean).join(" · ")}</p>}
          </div>
          <button type="button" onClick={onFechar} aria-label="Fechar ficha" className="grid size-10 place-items-center rounded-xl border border-[#24466f]"><X size={18}/></button>
        </div>
        {erro && <p role="alert" className="mt-4 text-sm text-red-300">{erro}</p>}
        {!ficha && !erro && <Loader2 className="mt-6 animate-spin text-cyan-300"/>}
        {ficha && (
          <div className="mt-4 space-y-4 text-sm">
            <div className="flex flex-wrap gap-2">
              <span className={`rounded-full border px-3 py-1 text-xs ${COR_GRUPO[ficha.grupo] || ""}`}>{ROTULO_CURTO[ficha.grupo]}</span>
              <span className="rounded-full border border-slate-600 px-3 py-1 text-xs">{ROTULO_CURTO[ficha.porte]}</span>
              {ficha.sinais.map((s) => <span key={s} className="rounded-full border border-cyan-900 px-3 py-1 text-xs text-cyan-200">{ROTULO_CURTO[s] || s}</span>)}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-3"><p className="text-xs text-slate-500">Frota registrada</p><strong className="text-xl">{numero(ficha.frota_registrada)}</strong><p className="text-xs text-slate-400">{ficha.frota_carrier} Carrier · {ficha.frota_concorrencia} concorrência</p></div>
              <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-3"><p className="text-xs text-slate-500">Última compra</p><strong className="text-xl">{dataCurta(ficha.ultima_compra)}</strong><p className="text-xs text-slate-400">{ficha.unidades_compradas} unidades na planilha de vendas</p></div>
              <div className="rounded-2xl border border-[#163356] bg-[#081a32] p-3"><p className="text-xs text-slate-500">Em negociação</p><strong className="text-xl">{ficha.negocios_abertos}</strong><p className="text-xs text-slate-400">{moeda(ficha.valor_negocios_abertos)}</p></div>
            </div>
            <section><h3 className="font-semibold text-cyan-200">Responsável comercial</h3><p className="mt-1">{ficha.responsavel_nome || "Sem responsável (fica com a gestão)"}{ficha.responsavel_nome && !ficha.responsavel_ativo ? " · desativado" : ""}</p>
              {ficha.responsaveis_anteriores.length > 0 && <ul className="mt-1 text-xs text-slate-400">{ficha.responsaveis_anteriores.map((h, i) => <li key={i}>{dataCurta(h.quando)}: {h.de || "—"} → {h.para || "—"}{h.motivo ? ` (${h.motivo})` : ""}</li>)}</ul>}
            </section>
            <section><h3 className="font-semibold text-cyan-200">Frota por implementadora</h3>
              {Object.keys(ficha.frota_por_implementadora).length ? <p className="mt-1 text-slate-300">{Object.entries(ficha.frota_por_implementadora).map(([k, v]) => `${k} (${v})`).join(" · ")}</p> : <p className="mt-1 text-slate-500">Sem registros na base de mercado.</p>}
            </section>
            <section><h3 className="font-semibold text-cyan-200">Negócios</h3>
              {ficha.negocios.length ? <ul className="mt-1 space-y-1">{ficha.negocios.map((n) => <li key={n.id} className="flex flex-wrap justify-between gap-2"><span>{n.titulo || "Negócio"} <span className="text-slate-500">· {n.status}</span></span><span className="text-slate-400">{moeda(n.valor)} · {n.responsavel || "—"}</span></li>)}</ul> : <p className="mt-1 text-slate-500">Nenhum negócio registrado.</p>}
            </section>
            <section><h3 className="font-semibold text-cyan-200">Atividades recentes</h3>
              {ficha.atividades_recentes.length ? <ul className="mt-1 space-y-1">{ficha.atividades_recentes.map((a, i) => <li key={i} className="flex flex-wrap justify-between gap-2"><span>{dataCurta(a.data)} · {a.titulo || a.tipo}</span><span className="text-slate-400">{a.autor || "—"} · {a.feita ? "feita" : a.status}</span></li>)}</ul> : <p className="mt-1 text-slate-500">Nenhuma atividade registrada.</p>}
            </section>
            {ficha.compras_planilha.length > 0 && <section><h3 className="font-semibold text-cyan-200">Compras (planilha de vendas)</h3><ul className="mt-1 space-y-1">{ficha.compras_planilha.map((c, i) => <li key={i} className="flex flex-wrap justify-between gap-2"><span>{dataCurta(c.mes)} · {c.equipamento}</span><span className="text-slate-400">{c.quantidade} un · {c.vendedor || "—"}</span></li>)}</ul></section>}
            <section><h3 className="font-semibold text-cyan-200">Cadastro</h3><p className="mt-1 text-slate-300">{[ficha.cadastro.endereco, ficha.cadastro.bairro, ficha.cadastro.cep].filter(Boolean).join(", ") || "Endereço não informado"}</p><p className="text-slate-400">{[ficha.cadastro.contato, ficha.cadastro.fone, ficha.cadastro.email].filter(Boolean).join(" · ") || "Contato não informado"}</p></section>
          </div>
        )}
      </section>
    </div>
  )
}

export default function CarteiraPage() {
  return <Suspense fallback={<main className="grid min-h-screen place-items-center bg-[#020817]"><Loader2 className="animate-spin text-cyan-300"/></main>}><CarteiraComFiltros/></Suspense>
}

function CarteiraComFiltros() {
  const params = useSearchParams()
  // Remonta quando o endereço muda (ex.: o "Pergunte ao CTI" abre a carteira já filtrada).
  return <CarteiraConteudo key={params.toString()} inicial={params}/>
}

function CarteiraConteudo({ inicial }: { inicial: URLSearchParams }) {
  const router = useRouter()
  const [dados, setDados] = useState<Setorizacao | null>(null)
  const [erro, setErro] = useState("")
  const [grupo, setGrupo] = useState(inicial.get("grupo") || "")
  const [sinal, setSinal] = useState(inicial.get("sinal") || "")
  const [porte, setPorte] = useState(inicial.get("porte") || "")
  const [cidade, setCidade] = useState(inicial.get("cidade") || "")
  const [busca, setBusca] = useState(inicial.get("busca") || "")
  const [aberta, setAberta] = useState<string | null>(inicial.get("empresa"))
  const [glossario, setGlossario] = useState<TermoGlossario[]>([])

  useEffect(() => {
    let ativo = true
    buscarSetorizacao({ grupo, sinal, porte, cidade }).then((r) => { if (ativo) { setDados(r); setErro("") } }).catch((e: unknown) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar a carteira.") })
    return () => { ativo = false }
  }, [grupo, sinal, porte, cidade])
  useEffect(() => { void buscarGlossario().then(setGlossario).catch(() => setGlossario([])) }, [])

  const lista = useMemo(() => {
    const alvo = busca.trim().toLowerCase()
    return (dados?.clientes || []).filter((c: PerfilCliente) => !alvo || [c.nome, c.cnpj, c.cidade, c.responsavel_nome].some((v) => String(v || "").toLowerCase().includes(alvo)))
  }, [dados, busca])

  const chip = (ativo: boolean) => `shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold ${ativo ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-5 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Inteligência de carteira</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Carteira setorizada</h1>
            <p className="mt-2 max-w-3xl text-gray-400">Cada cliente cruzado com a frota registrada no mercado, as compras, os negócios e o responsável. Toque em um cliente para abrir a ficha completa da empresa.</p>
          </header>
          {erro && <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>}
          {!dados && !erro && <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
          {dados && (
            <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" role="group" aria-label="Grupos de clientes">
                {Object.entries(dados.rotulos.grupos).map(([codigo, rotulo]) => (
                  <button key={codigo} type="button" aria-pressed={grupo === codigo} onClick={() => setGrupo(grupo === codigo ? "" : codigo)} className={`rounded-2xl border p-4 text-left ${grupo === codigo ? "border-cyan-500 bg-cyan-950/40" : "border-[#163356] bg-[#081a32]"}`}>
                    <strong className="block text-2xl">{numero(dados.por_grupo[codigo] || 0)}</strong>
                    <span className="text-xs text-slate-400">{rotulo}</span>
                  </button>
                ))}
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Sinais">
                <button type="button" onClick={() => setSinal("")} className={chip(!sinal)}>Todos os sinais</button>
                {Object.keys(dados.rotulos.sinais).map((s) => <button key={s} type="button" aria-pressed={sinal === s} onClick={() => setSinal(sinal === s ? "" : s)} title={dados.rotulos.sinais[s]} className={chip(sinal === s)}>{ROTULO_CURTO[s]} ({numero(dados.por_sinal[s] || 0)})</button>)}
              </div>
              {(porte || cidade) && (
                <div className="flex flex-wrap gap-2" role="group" aria-label="Filtros aplicados">
                  {porte && <button type="button" onClick={() => setPorte("")} className={chip(true)}>{ROTULO_CURTO[porte] || porte} ✕</button>}
                  {cidade && <button type="button" onClick={() => setCidade("")} className={chip(true)}>Cidade: {cidade} ✕</button>}
                </div>
              )}
              <label className="flex items-center gap-2 rounded-2xl border border-[#24466f] bg-[#061126] px-4">
                <Search size={18} className="text-slate-500"/><span className="sr-only">Buscar cliente</span>
                <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar por nome, CNPJ, cidade ou responsável" className="min-h-12 w-full bg-transparent text-sm outline-none"/>
              </label>
              <p className="text-xs text-slate-500">{numero(lista.length)} de {numero(dados.total_clientes)} clientes · ordenados por janela de renovação, inativos e prospects com frota primeiro</p>
              <ul className="space-y-2" aria-label="Clientes">
                {lista.map((c) => (
                  <li key={c.cliente_id}>
                    <button type="button" onClick={() => setAberta(c.cliente_id)} className="w-full rounded-2xl border border-[#163356] bg-[#081a32] p-4 text-left hover:border-cyan-700">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="flex items-center gap-2 font-semibold"><Building2 size={16} className="text-cyan-400"/>{c.nome}</span>
                        <span className={`rounded-full border px-2 py-0.5 text-[11px] ${COR_GRUPO[c.grupo] || ""}`}>{ROTULO_CURTO[c.grupo]}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">{[c.cidade && `${c.cidade}${c.estado ? `/${c.estado}` : ""}`, `frota ${c.frota_registrada} (${c.frota_concorrencia} concorrência)`, `última compra ${dataCurta(c.ultima_compra)}`, c.responsavel_nome || "sem responsável"].filter(Boolean).join(" · ")}</p>
                      {c.sinais.length > 0 && <p className="mt-2 flex flex-wrap gap-1">{c.sinais.map((s) => <span key={s} className="rounded-full border border-cyan-900 px-2 py-0.5 text-[11px] text-cyan-200">{ROTULO_CURTO[s] || s}</span>)}</p>}
                    </button>
                  </li>
                ))}
              </ul>
              {dados.filtrados > dados.clientes.length && <p className="text-xs text-slate-500">Mostrando os {dados.clientes.length} mais prioritários. Use os filtros para ver os demais.</p>}
            </>
          )}
          {glossario.length > 0 && (
            <details className="rounded-3xl border border-[#13203f] bg-[#061126] p-5">
              <summary className="flex cursor-pointer items-center gap-2 font-semibold"><BookOpen size={18} className="text-cyan-400"/> Dicionário de termos do CTI</summary>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">{glossario.map((g) => <div key={g.termo}><dt className="font-semibold text-cyan-200">{g.termo}</dt><dd className="text-sm text-slate-300">{g.definicao}<span className="block text-xs text-slate-500">Também chamado de: {g.sinonimos.join(", ")}</span></dd></div>)}</dl>
            </details>
          )}
        </div>
      </section>
      {aberta && <Ficha clienteId={aberta} onFechar={() => { setAberta(null); if (inicial.get("empresa")) router.replace("/carteira") }}/>}
    </main>
  )
}
