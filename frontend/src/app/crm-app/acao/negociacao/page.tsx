"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, ChevronRight, Loader2, Search } from "lucide-react"
import { useAuth } from "@/core/auth"
import { pertenceAoEscopoDoUsuario } from "@/core/rbac/commercial-scope"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>

const FINAIS = new Set(["GANHO", "PERDIDO", "CANCELADO", "FATURADO", "ENCERRADO", "CONCLUIDO", "CONCLUÍDO"])

function texto(valor: unknown) {
  return String(valor ?? "").trim()
}

function etapa(item: Registro) {
  return texto(item.etapa || item.status || item.status_oportunidade).toUpperCase()
}

function etapaLegivel(valor: string) {
  const mapa: Record<string, string> = {
    OPORTUNIDADE: "Interesse",
    NEGOCIACAO: "Negociação",
    NEGOCIAÇÃO: "Negociação",
    PROPOSTA: "Proposta",
    ACEITA: "Aceite",
    ACEITE: "Aceite",
    PEDIDO: "Pedido",
    GANHO: "Concluído",
  }
  return mapa[valor] || valor.replaceAll("_", " ") || "Em andamento"
}

export default function SelecionarNegociacaoPage() {
  const { usuario } = useAuth()
  const [itens, setItens] = useState<Registro[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true
    void (async () => {
      setCarregando(true)
      setErro("")
      try {
        const resposta = await fetchCrmSeguroProxy("crm-seguro/nucleo-comercial", { cache: "no-store" })
        const payload = await resposta.json().catch(() => [])
        if (!resposta.ok) throw new Error(texto(payload?.detail) || `HTTP ${resposta.status}`)
        if (!ativo) return
        const lista = (Array.isArray(payload) ? payload : [])
          .filter((item: Registro) => pertenceAoEscopoDoUsuario(texto(item.responsavel_id), usuario))
          .filter((item: Registro) => !FINAIS.has(etapa(item)))
        setItens(lista)
      } catch (falha) {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar suas negociações.")
      } finally {
        if (ativo) setCarregando(false)
      }
    })()
    return () => { ativo = false }
  }, [usuario])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return itens
    return itens.filter((item) => `${texto(item.cliente_nome)} ${texto(item.titulo)} ${texto(item.equipamento)}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, itens])

  return (
    <main className="min-h-[100dvh] bg-[#020817] px-4 pb-28 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-5 flex items-start gap-3">
          <Link href="/crm-app/acao" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={21} /></Link>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Próxima ação</p>
            <h1 className="mt-1 text-3xl font-bold">Qual negociação?</h1>
            <p className="mt-1 text-sm leading-6 text-slate-400">Escolha o cliente. O CTI abre o processo existente e preserva todo o histórico.</p>
          </div>
        </header>

        <div className="relative mb-4">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
          <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, negociação ou equipamento" className="min-h-14 w-full rounded-2xl border border-[#24466f] bg-[#07162b] pl-12 pr-4 text-base outline-none placeholder:text-slate-600 focus:border-cyan-600" />
        </div>

        {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
        {carregando && <div className="flex min-h-40 items-center justify-center text-slate-400"><Loader2 className="mr-2 animate-spin" size={20} />Carregando suas negociações...</div>}

        {!carregando && !erro && filtrados.length === 0 && (
          <div className="rounded-3xl border border-[#16325c] bg-[#07162b] p-6 text-center">
            <strong className="text-lg">Nenhuma negociação aberta encontrada</strong>
            <p className="mt-2 text-sm text-slate-400">Você pode registrar uma nova ação ou iniciar uma oportunidade.</p>
            <Link href="/crm-app/acao" className="mt-4 inline-flex min-h-12 items-center rounded-xl bg-cyan-500 px-5 font-bold text-slate-950">Nova ação</Link>
          </div>
        )}

        <div className="grid gap-3">
          {filtrados.map((item) => {
            const id = texto(item.oportunidade_id || item.id)
            const cliente = texto(item.cliente_nome) || "Cliente em identificação"
            const titulo = texto(item.titulo || item.equipamento) || "Negociação comercial"
            const fase = etapaLegivel(etapa(item))
            return (
              <Link key={id} href={`/crm-app/historico/${encodeURIComponent(id)}?origem=campo`} className="flex min-h-24 items-center gap-4 rounded-3xl border border-[#1b3c65] bg-[#091a33] p-5 active:scale-[.99]">
                <div className="min-w-0 flex-1">
                  <span className="block truncate text-lg font-bold">{cliente}</span>
                  <span className="mt-1 block truncate text-sm text-slate-300">{titulo}</span>
                  <span className="mt-2 inline-flex rounded-full border border-cyan-900 bg-cyan-950/50 px-3 py-1 text-xs font-semibold text-cyan-300">{fase}</span>
                </div>
                <span className="flex min-h-11 shrink-0 items-center gap-1 rounded-xl bg-cyan-500 px-3 text-sm font-bold text-slate-950">Continuar <ChevronRight size={17} /></span>
              </Link>
            )
          })}
        </div>
      </div>
    </main>
  )
}
