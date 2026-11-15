"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { ArrowRight, Building2, Loader2, Package, Search, Sparkles, X } from "lucide-react"
import { useAuth } from "@/core/auth"
import { rotaAutorizadaCTI } from "@/core/rbac/route-access"
import { buscarNoCTI, perguntarAoCTI, type AcaoAssistente, type RespostaAssistente, type ResultadoBusca } from "@/services/assistente-cti"

const ROTAS_PUBLICAS = ["/", "/login", "/redefinir-senha", "/crm-app/login", "/solicitar-acesso", "/primeiro-acesso", "/aceite"]
const PERFIS_EXTERNOS = ["AUTORIZADO_CARRIER", "GESTOR_AUTORIZADO_CARRIER"]
const EXEMPLOS = [
  "Clientes com frota grande que usam concorrente",
  "Clientes inativos",
  "Prospects com frota em Campinas",
  "Onde vejo as propostas?",
]

export default function AssistenteCTI() {
  const pathname = usePathname() || "/"
  const router = useRouter()
  const { usuario } = useAuth()
  const [aberto, setAberto] = useState(false)
  const [texto, setTexto] = useState("")
  const [busca, setBusca] = useState<ResultadoBusca | null>(null)
  const [resposta, setResposta] = useState<RespostaAssistente | null>(null)
  const [pensando, setPensando] = useState(false)
  const [erro, setErro] = useState("")
  const pedido = useRef(0)
  const campo = useRef<HTMLInputElement>(null)

  const visivel = Boolean(usuario) && !ROTAS_PUBLICAS.includes(pathname) && !PERFIS_EXTERNOS.includes(String(usuario?.tipo_usuario || "").toUpperCase())
  const permitido = useCallback((href: string) => Boolean(usuario && rotaAutorizadaCTI(href.split("?")[0], usuario)), [usuario])

  useEffect(() => {
    if (!visivel) return
    function atalho(evento: KeyboardEvent) {
      if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === "k") {
        evento.preventDefault()
        setAberto((atual) => !atual)
      } else if (evento.key === "Escape") {
        setAberto(false)
      }
    }
    window.addEventListener("keydown", atalho)
    return () => window.removeEventListener("keydown", atalho)
  }, [visivel])

  useEffect(() => {
    if (aberto) campo.current?.focus()
  }, [aberto])

  // Busca enquanto digita (telas, empresas, modelos).
  useEffect(() => {
    const termo = texto.trim()
    if (!aberto || termo.length < 2) return
    const controle = new AbortController()
    const id = window.setTimeout(() => {
      buscarNoCTI(termo, controle.signal).then(setBusca).catch(() => undefined)
    }, 250)
    return () => { window.clearTimeout(id); controle.abort() }
  }, [texto, aberto])

  function ir(href: string) {
    setAberto(false)
    router.push(href)
  }

  async function perguntar(pergunta = texto) {
    const limpa = pergunta.trim()
    if (limpa.length < 2) return
    const meu = ++pedido.current
    setTexto(limpa)
    setPensando(true)
    setErro("")
    try {
      const r = await perguntarAoCTI(limpa)
      if (meu === pedido.current) setResposta(r)
    } catch (falha) {
      if (meu === pedido.current) setErro(falha instanceof Error ? falha.message : "Não foi possível responder agora.")
    } finally {
      if (meu === pedido.current) setPensando(false)
    }
  }

  if (!visivel) return null
  const noApp = pathname.startsWith("/crm-app")
  const termoValido = texto.trim().length >= 2
  const acoes = (resposta?.acoes || []).filter((a) => permitido(a.href))
  const telas = termoValido ? (busca?.telas || []).filter((t) => permitido(t.href)) : []
  const empresas = termoValido && permitido("/carteira") ? busca?.empresas || [] : []
  const equipamentos = termoValido && permitido("/catalogo") ? busca?.equipamentos || [] : []

  const Linha = ({ acao, icone }: { acao: AcaoAssistente; icone?: React.ReactNode }) => (
    <li>
      <button type="button" onClick={() => ir(acao.href)} className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left text-sm hover:bg-[#0f2340]">
        <span className="flex min-w-0 items-center gap-2">{icone}<span className="truncate">{acao.titulo}</span></span>
        <ArrowRight size={14} className="shrink-0 text-cyan-400"/>
      </button>
    </li>
  )

  return (
    <>
      <button type="button" onClick={() => setAberto(true)} aria-label="Pergunte ao CTI (Ctrl+K)" className={`fixed right-4 z-40 inline-flex items-center gap-2 rounded-full bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-cyan-950/50 ${noApp ? "bottom-24" : "bottom-5"}`}>
        <Sparkles size={18}/><span className="hidden sm:inline">Pergunte ao CTI</span>
      </button>

      {aberto && (
        <div className="fixed inset-0 z-[60] flex items-start justify-center bg-black/60 p-3 pt-[8vh]" onClick={() => setAberto(false)}>
          <section role="dialog" aria-modal="true" aria-label="Pergunte ao CTI" onClick={(e) => e.stopPropagation()} className="w-full max-w-2xl overflow-hidden rounded-3xl border border-[#1d3a63] bg-[#061126] text-white shadow-2xl">
            <form onSubmit={(e) => { e.preventDefault(); void perguntar() }} className="flex items-center gap-2 border-b border-[#13203f] px-4">
              <Search size={18} className="shrink-0 text-cyan-400"/>
              <input ref={campo} value={texto} onChange={(e) => { pedido.current += 1; setTexto(e.target.value); setResposta(null); setErro(""); setPensando(false) }} placeholder="Pergunte ou procure: cliente, tela, modelo..." aria-label="Pergunta ou busca" maxLength={500} className="min-h-14 w-full bg-transparent text-base outline-none"/>
              <button type="submit" disabled={!termoValido || pensando} className="shrink-0 rounded-xl bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950 disabled:opacity-40">{pensando ? <Loader2 size={14} className="animate-spin"/> : "Perguntar"}</button>
              <button type="button" onClick={() => setAberto(false)} aria-label="Fechar" className="shrink-0 rounded-lg p-2 text-slate-400"><X size={18}/></button>
            </form>

            <div className="max-h-[65vh] space-y-4 overflow-y-auto p-4">
              {erro && <p role="alert" className="rounded-xl border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</p>}

              {resposta && (
                <div role="status" className="space-y-3 rounded-2xl border border-cyan-900 bg-[#081a32] p-4">
                  <p className="text-sm leading-relaxed">{resposta.resposta}</p>
                  {resposta.destaques.length > 0 && (
                    <ul className="flex flex-wrap gap-2">{resposta.destaques.map((d) => (
                      <li key={d.cliente_id}><button type="button" onClick={() => ir(`/carteira?empresa=${encodeURIComponent(d.cliente_id)}`)} className="rounded-full border border-[#24466f] px-3 py-1 text-xs text-slate-200 hover:border-cyan-500">{d.nome}{d.cidade ? ` · ${d.cidade}` : ""}</button></li>
                    ))}</ul>
                  )}
                  <ul aria-label="Para onde ir">{acoes.map((a) => <Linha key={a.href} acao={a}/>)}</ul>
                </div>
              )}

              {!resposta && termoValido && (
                <>
                  {telas.length > 0 && <div><p className="px-3 text-[11px] uppercase tracking-widest text-slate-500">Telas</p><ul>{telas.map((t) => <Linha key={t.href} acao={t}/>)}</ul></div>}
                  {empresas.length > 0 && <div><p className="px-3 text-[11px] uppercase tracking-widest text-slate-500">Empresas</p><ul>{empresas.map((e) => <Linha key={e.cliente_id} acao={{ href: e.href, titulo: `${e.nome}${e.cidade ? ` · ${e.cidade}` : ""}` }} icone={<Building2 size={14} className="text-cyan-400"/>}/>)}</ul></div>}
                  {equipamentos.length > 0 && <div><p className="px-3 text-[11px] uppercase tracking-widest text-slate-500">Equipamentos</p><ul>{equipamentos.map((e) => <Linha key={e.modelo} acao={{ href: e.href, titulo: `${e.modelo}${e.linha ? ` · ${e.linha}` : ""}` }} icone={<Package size={14} className="text-cyan-400"/>}/>)}</ul></div>}
                  <p className="px-3 text-xs text-slate-500">Tecle Enter para o CTI responder à pergunta.</p>
                </>
              )}

              {!resposta && !termoValido && (
                <div>
                  <p className="px-1 pb-2 text-xs text-slate-400">Exemplos do que você pode perguntar:</p>
                  <div className="flex flex-wrap gap-2">{EXEMPLOS.map((ex) => <button key={ex} type="button" onClick={() => void perguntar(ex)} className="rounded-full border border-[#24466f] px-3 py-1.5 text-xs text-slate-200 hover:border-cyan-500">{ex}</button>)}</div>
                  <p className="px-1 pt-3 text-[11px] text-slate-500">Atalho: Ctrl+K (ou ⌘K) em qualquer tela.</p>
                </div>
              )}
            </div>
          </section>
        </div>
      )}
    </>
  )
}
