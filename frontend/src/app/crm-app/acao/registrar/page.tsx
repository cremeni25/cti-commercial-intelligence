"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { ArrowLeft, Check, ChevronRight, Loader2, Search } from "lucide-react"
import { useAuth } from "@/core/auth"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; cidade?: string; estado?: string }
type Negociacao = { oportunidade_id: string; cliente_id: string; cliente_nome?: string; titulo: string; etapa: string; encerrada?: boolean }

const TIPOS = [
  ["VISITA_PRESENCIAL", "Visita"],
  ["LIGACAO", "Ligação"],
  ["WHATSAPP", "WhatsApp"],
  ["EMAIL", "E-mail"],
  ["REUNIAO", "Reunião"],
  ["FOLLOW_UP", "Follow-up"],
] as const

function texto(v: unknown) { return String(v ?? "").trim() }
function chave(v: unknown) { return texto(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase() }
function abertas(lista: Negociacao[]) { return lista.filter((i) => !i.encerrada && !["GANHO", "PERDIDO", "CANCELADO", "ENCERRADO", "FATURADO"].includes(chave(i.etapa))) }

export default function RegistroRapidoPage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [negociacoes, setNegociacoes] = useState<Negociacao[]>([])
  const [busca, setBusca] = useState("")
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [tipo, setTipo] = useState("FOLLOW_UP")
  const [oportunidadeId, setOportunidadeId] = useState("")
  const [descricao, setDescricao] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const envioRef = useRef(false)

  useEffect(() => {
    const agora = new URLSearchParams(window.location.search)
    const inicial = chave(agora.get("tipo"))
    if (TIPOS.some(([valor]) => valor === inicial)) setTipo(inicial)
    let ativo = true
    void (async () => {
      try {
        const [cr, nr] = await Promise.all([
          fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }),
          fetchCrmSeguroProxy("crm-seguro/nucleo-comercial", { cache: "no-store" }),
        ])
        const cd = await cr.json().catch(() => [])
        const nd = await nr.json().catch(() => [])
        if (!cr.ok || !nr.ok) throw new Error("Não foi possível carregar os dados do CRM.")
        if (!ativo) return
        setClientes((Array.isArray(cd) ? cd : []).map((i: Registro) => ({
          id: texto(i.id),
          nome: texto(i.nome || i.razao_social || i.nome_fantasia),
          cidade: texto(i.cidade || i.municipio),
          estado: texto(i.estado || i.uf),
        })).filter((i: Cliente) => i.id && i.nome))
        setNegociacoes((Array.isArray(nd) ? nd : []).map((i: Registro) => ({
          oportunidade_id: texto(i.oportunidade_id || i.id),
          cliente_id: texto(i.cliente_id),
          cliente_nome: texto(i.cliente_nome),
          titulo: texto(i.titulo || i.equipamento) || "Negociação comercial",
          etapa: texto(i.etapa || i.status_oportunidade),
          encerrada: Boolean(i.encerrada),
        })).filter((i: Negociacao) => i.oportunidade_id))
      } catch (falha) {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o CRM.")
      } finally {
        if (ativo) setCarregando(false)
      }
    })()
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (cliente || termo.length < 2) return []
    return clientes.filter((i) => `${i.nome} ${i.cidade || ""} ${i.estado || ""}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 10)
  }, [busca, cliente, clientes])

  const negociacoesCliente = useMemo(() => {
    if (!cliente) return []
    return abertas(negociacoes.filter((i) => i.cliente_id === cliente.id || (i.cliente_nome && chave(i.cliente_nome) === chave(cliente.nome))))
  }, [cliente, negociacoes])

  useEffect(() => {
    queueMicrotask(() => {
      if (negociacoesCliente.length === 1) setOportunidadeId(negociacoesCliente[0].oportunidade_id)
      else setOportunidadeId("")
    })
  }, [negociacoesCliente])

  async function salvar(e: FormEvent) {
    e.preventDefault()
    if (envioRef.current || !cliente || !usuario?.id) return
    if (negociacoesCliente.length > 1 && !oportunidadeId) {
      setErro("Este cliente possui mais de uma negociação aberta. Escolha qual processo deve receber esta interação.")
      return
    }
    envioRef.current = true
    setSalvando(true)
    setErro("")
    try {
      const agora = new Date()
      const data = agora.toISOString().slice(0, 10)
      const horario = agora.toTimeString().slice(0, 5)
      const negocio = negociacoesCliente.find((i) => i.oportunidade_id === oportunidadeId)
      const rotulo = TIPOS.find(([valor]) => valor === tipo)?.[1] || "Interação"
      const resposta = await fetchCrmSeguroProxy("crm-seguro/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: cliente.id,
          oportunidade_id: negocio?.oportunidade_id || null,
          usuario_id: usuario.id,
          tipo,
          titulo: `${rotulo} · ${cliente.nome}`,
          descricao: descricao.trim() || null,
          data,
          horario,
          status: "PENDENTE",
        }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto(payload?.detail) || `HTTP ${resposta.status}`)
      const qs = new URLSearchParams({ cliente: cliente.nome })
      if (negocio?.oportunidade_id) qs.set("oportunidade", negocio.oportunidade_id)
      window.location.href = `/crm-app/acao/concluida?${qs.toString()}`
    } catch (falha) {
      envioRef.current = false
      setErro(falha instanceof Error ? falha.message : "Não foi possível registrar a interação.")
    } finally {
      setSalvando(false)
    }
  }

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
      <form onSubmit={salvar} className="mx-auto max-w-3xl">
        <header className="mb-5 flex items-start gap-3">
          <Link href="/crm-app/acao" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={21} /></Link>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Registro rápido</p>
            <h1 className="mt-1 text-3xl font-bold">O que aconteceu?</h1>
            <p className="mt-1 text-sm leading-6 text-slate-400">Três passos. O restante o CTI completa automaticamente.</p>
          </div>
        </header>

        {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}

        <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">1 · Cliente</span>
          {carregando ? <div className="mt-4 flex min-h-16 items-center text-slate-400"><Loader2 className="mr-2 animate-spin" size={19}/>Carregando...</div> : cliente ? (
            <div className="mt-4 flex items-center justify-between gap-3 rounded-2xl border border-emerald-900 bg-emerald-950/20 p-4">
              <div><strong className="block text-lg">{cliente.nome}</strong><span className="text-sm text-slate-400">{[cliente.cidade, cliente.estado].filter(Boolean).join(" · ")}</span></div>
              <button type="button" onClick={() => { setCliente(null); setBusca(""); setOportunidadeId("") }} className="min-h-10 rounded-xl border border-[#24466f] px-3 text-sm text-slate-300">Trocar</button>
            </div>
          ) : (
            <div className="relative mt-4">
              <Search className="absolute left-4 top-4 text-slate-500" size={20}/>
              <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Digite o nome do cliente" className="min-h-14 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-12 pr-4 text-base outline-none focus:border-cyan-500" />
              {sugestoes.length > 0 && <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((item) => <button key={item.id} type="button" onClick={() => { setCliente(item); setBusca(item.nome) }} className="flex min-h-14 w-full items-center justify-between border-b border-[#16325c] px-4 text-left last:border-0"><span><strong className="block">{item.nome}</strong><span className="text-xs text-slate-500">{[item.cidade, item.estado].filter(Boolean).join(" · ")}</span></span><ChevronRight size={18} className="text-cyan-400"/></button>)}</div>}
            </div>
          )}

          {cliente && negociacoesCliente.length > 0 && <div className="mt-4 rounded-2xl border border-[#24466f] bg-[#020817] p-4">
            <span className="text-xs font-semibold uppercase tracking-[.16em] text-slate-500">Negociação</span>
            {negociacoesCliente.length === 1 ? <div className="mt-2 flex items-center gap-2 text-sm text-emerald-300"><Check size={17}/>{negociacoesCliente[0].titulo} vinculada automaticamente</div> : <div className="mt-3 grid gap-2">{negociacoesCliente.map((item) => <button key={item.oportunidade_id} type="button" onClick={() => setOportunidadeId(item.oportunidade_id)} className={`min-h-12 rounded-xl border px-4 text-left text-sm ${oportunidadeId === item.oportunidade_id ? "border-cyan-500 bg-cyan-950/40 text-cyan-200" : "border-[#24466f] text-slate-300"}`}>{item.titulo}</button>)}</div>}
          </div>}
        </section>

        <section className="mt-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">2 · Tipo</span>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">{TIPOS.map(([valor, label]) => <button key={valor} type="button" onClick={() => setTipo(valor)} className={`min-h-14 rounded-2xl border px-3 text-sm font-semibold ${tipo === valor ? "border-cyan-400 bg-cyan-500 text-slate-950" : "border-[#24466f] bg-[#020817] text-slate-300"}`}>{label}</button>)}</div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <span className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">3 · Resumo</span>
          <textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} rows={5} placeholder="Descreva em poucas palavras o que aconteceu e qual é o próximo passo." className="mt-4 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4 text-base leading-6 outline-none placeholder:text-slate-600 focus:border-cyan-500" />
        </section>

        <button type="submit" disabled={!cliente || salvando} className="mt-5 flex min-h-16 w-full items-center justify-center rounded-2xl bg-cyan-500 px-5 text-lg font-bold text-slate-950 disabled:opacity-50">
          {salvando ? <><Loader2 className="mr-2 animate-spin" size={20}/>Salvando...</> : "Registrar e continuar"}
        </button>
        <Link href="/crm-app/atividades/nova" className="mt-3 flex min-h-12 items-center justify-center text-sm font-semibold text-slate-500">Preciso de opções avançadas</Link>
      </form>
    </main>
  )
}
