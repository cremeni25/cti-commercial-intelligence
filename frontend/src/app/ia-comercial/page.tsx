/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { Bot, Loader2, MessageSquarePlus, Send, ShieldCheck } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"

type Conversa = { id: string; titulo: string; updated_at?: string }
type Mensagem = {
  id?: string
  papel: "user" | "assistant" | "system"
  conteudo: string
  fontes?: Array<{ tipo?: string; descricao?: string }>
  created_at?: string
}

const API = "/api/crm-proxy/ia-comercial-cti"

async function tokenAtual(): Promise<string> {
  const supabase = getSupabaseClient()
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error("Sessão autenticada não encontrada.")
  return token
}

async function requisitar(caminho: string, init?: RequestInit) {
  const token = await tokenAtual()
  const resposta = await fetch(`${API}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
  })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new Error(payload?.detail || "Falha na comunicação com a IA Comercial CTI.")
  return payload
}

export default function IaComercialPage() {
  const [conversas, setConversas] = useState<Conversa[]>([])
  const [conversaId, setConversaId] = useState("")
  const [mensagens, setMensagens] = useState<Mensagem[]>([])
  const [entrada, setEntrada] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const fimConversaRef = useRef<HTMLDivElement | null>(null)

  const conversaAtual = useMemo(
    () => conversas.find((item) => item.id === conversaId),
    [conversas, conversaId],
  )

  async function carregarConversas() {
    const lista = await requisitar("/conversas")
    const normalizada = Array.isArray(lista) ? lista : []
    setConversas(normalizada)
    if (!conversaId && normalizada[0]?.id) setConversaId(normalizada[0].id)
  }

  async function criarConversa() {
    setErro("")
    const criada = await requisitar("/conversas", {
      method: "POST",
      body: JSON.stringify({ titulo: "Nova conversa" }),
    })
    setConversas((atuais) => [criada, ...atuais])
    setConversaId(criada.id)
    setMensagens([])
  }

  useEffect(() => {
    let ativo = true
    carregarConversas()
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar conversas.") })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [])

  useEffect(() => {
    if (!conversaId) { setMensagens([]); return }
    let ativo = true
    requisitar(`/conversas/${conversaId}/mensagens`)
      .then((lista) => { if (ativo) setMensagens(Array.isArray(lista) ? lista : []) })
      .catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Falha ao carregar mensagens.") })
    return () => { ativo = false }
  }, [conversaId])

  useEffect(() => {
    fimConversaRef.current?.scrollIntoView({
      behavior: enviando ? "smooth" : "auto",
      block: "end",
    })
  }, [mensagens, enviando, conversaId])

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    const texto = entrada.trim()
    if (!texto || enviando) return
    setErro("")
    setEntrada("")
    setEnviando(true)

    try {
      let id = conversaId
      if (!id) {
        const criada = await requisitar("/conversas", {
          method: "POST",
          body: JSON.stringify({ titulo: "Nova conversa" }),
        })
        id = criada.id
        setConversaId(id)
        setConversas((atuais) => [criada, ...atuais])
      }

      setMensagens((atuais) => [...atuais, { papel: "user", conteudo: texto }])
      const resposta = await requisitar(`/conversas/${id}/mensagens`, {
        method: "POST",
        body: JSON.stringify({ mensagem: texto }),
      })
      setMensagens((atuais) => [...atuais, resposta])
      await carregarConversas()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir a resposta.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex h-screen overflow-hidden bg-[#020817] text-white">
      <Sidebar />
      <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar />
        <div className="grid min-h-0 flex-1 overflow-hidden lg:grid-cols-[300px_1fr]">
          <aside className="min-h-0 overflow-y-auto border-r border-[#13203f] bg-[#061126] p-4">
            <button onClick={() => void criarConversa()} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950">
              <MessageSquarePlus size={18} /> Nova conversa
            </button>
            <div className="mt-4 space-y-2">
              {carregando ? <p className="text-sm text-slate-500">Carregando...</p> : conversas.map((item) => (
                <button key={item.id} onClick={() => setConversaId(item.id)} className={`w-full rounded-xl border px-3 py-3 text-left text-sm ${item.id === conversaId ? "border-cyan-500 bg-cyan-950/30 text-cyan-200" : "border-[#13203f] bg-[#091a33] text-slate-300"}`}>
                  <span className="line-clamp-2">{item.titulo || "Nova conversa"}</span>
                </button>
              ))}
            </div>
          </aside>

          <section className="flex min-h-0 min-w-0 flex-col overflow-hidden">
            <header className="shrink-0 border-b border-[#13203f] bg-[#091a33] px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="grid size-11 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-300"><Bot /></div>
                <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Assistente exclusivo do CTI</p><h1 className="text-xl font-bold">IA Comercial CTI</h1></div>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-400"><ShieldCheck size={15} className="text-emerald-400" /> Fase inicial: leitura, análise e respostas auditáveis. Nenhum registro é alterado.</div>
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-6">
              <div className="mx-auto max-w-4xl space-y-4">
                {mensagens.length === 0 && (
                  <div className="rounded-3xl border border-[#18345e] bg-[#071427] p-7 text-center">
                    <Bot className="mx-auto text-cyan-300" size={38} />
                    <h2 className="mt-4 text-2xl font-bold">Como posso apoiar a operação comercial?</h2>
                    <p className="mt-3 text-sm leading-6 text-slate-400">Pergunte sobre clientes, oportunidades, propostas, pedidos, prioridades, riscos ou próximos encaminhamentos registrados no CTI.</p>
                  </div>
                )}

                {mensagens.map((mensagem, indice) => (
                  <article key={mensagem.id || `${mensagem.papel}-${indice}`} className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${mensagem.papel === "user" ? "ml-auto bg-cyan-500 text-slate-950" : "border border-[#18345e] bg-[#091a33] text-slate-200"}`}>
                    <div className="whitespace-pre-wrap">{mensagem.conteudo}</div>
                    {mensagem.papel === "assistant" && mensagem.fontes?.length ? (
                      <div className="mt-3 border-t border-[#18345e] pt-2 text-xs text-slate-500">Fonte: {mensagem.fontes.map((fonte) => fonte.descricao || fonte.tipo).join(" · ")}</div>
                    ) : null}
                  </article>
                ))}

                {enviando && <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 className="animate-spin" size={17} /> Analisando o contexto CTI...</div>}
                {erro && <div className="rounded-xl border border-red-900 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</div>}
                <div ref={fimConversaRef} aria-hidden="true" />
              </div>
            </div>

            <form onSubmit={enviar} className="shrink-0 border-t border-[#13203f] bg-[#061126] p-4">
              <div className="mx-auto flex max-w-4xl gap-3">
                <textarea value={entrada} onChange={(event) => setEntrada(event.target.value)} placeholder={`Pergunte à ${conversaAtual?.titulo || "IA Comercial CTI"}...`} rows={2} className="min-h-14 flex-1 resize-none rounded-2xl border border-[#28507c] bg-[#020d1f] px-4 py-3 text-sm outline-none focus:border-cyan-400" />
                <button disabled={!entrada.trim() || enviando} className="grid size-14 place-items-center rounded-2xl bg-cyan-500 text-slate-950 disabled:opacity-40"><Send size={20} /></button>
              </div>
            </form>
          </section>
        </div>
      </section>
    </main>
  )
}
