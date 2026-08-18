/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react"
import { Bot, Loader2, MessageSquarePlus, Paperclip, Send, ShieldCheck, X } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import IaArtefatos from "@/components/ia/IaArtefatos"
import { getSupabaseClient } from "@/core/database/supabase"

type Conversa = { id: string; titulo: string; updated_at?: string }
type ArtefatoMensagem = {
  tipo: string
  formato?: string
  titulo?: string
  dados?: Array<{ label: string; valor: number; unidade?: string }>
  status?: string
  mensagem?: string
}
type AnexoMensagem = {
  nome: string
  tipo?: string
  tamanho_bytes?: number
  sha256?: string
  temporario?: boolean
  publicado_cti?: boolean
}
type Mensagem = {
  id?: string
  papel: "user" | "assistant" | "system"
  conteudo: string
  fontes?: Array<{ tipo?: string; descricao?: string }>
  metadados?: { artefatos?: ArtefatoMensagem[]; anexos?: AnexoMensagem[] }
  created_at?: string
}

const API = "/api/crm-proxy/ia-comercial-cti"
const MARGEM_RENOVACAO_SEGUNDOS = 60
const EXTENSOES_ACEITAS = ".pdf,.xlsx,.xlsm,.csv,.docx,.pptx,.txt,.md,.json,.xml"
const MAX_ANEXOS = 5

async function tokenAtual(forcarRenovacao = false): Promise<string> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error) throw new Error("Não foi possível validar a sessão autenticada.")

  const sessao = data.session
  if (!sessao) throw new Error("Sessão autenticada não encontrada.")

  const agora = Math.floor(Date.now() / 1000)
  const expiraEm = sessao.expires_at || 0
  const deveRenovar = forcarRenovacao || !expiraEm || expiraEm <= agora + MARGEM_RENOVACAO_SEGUNDOS

  if (!deveRenovar) return sessao.access_token

  const renovacao = await supabase.auth.refreshSession()
  const tokenRenovado = renovacao.data.session?.access_token
  if (renovacao.error || !tokenRenovado) {
    await supabase.auth.signOut({ scope: "local" }).catch(() => undefined)
    throw new Error("Sessão expirada. Entre novamente no CTI.")
  }
  return tokenRenovado
}

async function tratarResposta(resposta: Response) {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    if (resposta.status === 401) {
      const supabase = getSupabaseClient()
      await supabase.auth.signOut({ scope: "local" }).catch(() => undefined)
      throw new Error("Sessão expirada. Entre novamente no CTI.")
    }
    throw new Error(payload?.detail || "Falha na comunicação com a IA Comercial CTI.")
  }
  return payload
}

async function requisitar(caminho: string, init?: RequestInit) {
  const executar = async (token: string) => fetch(`${API}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
  })

  let resposta = await executar(await tokenAtual())
  if (resposta.status === 401) resposta = await executar(await tokenAtual(true))
  return tratarResposta(resposta)
}

async function requisitarMultipart(caminho: string, formulario: FormData) {
  const executar = async (token: string) => fetch(`${API}${caminho}`, {
    method: "POST",
    body: formulario,
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  })

  let resposta = await executar(await tokenAtual())
  if (resposta.status === 401) resposta = await executar(await tokenAtual(true))
  return tratarResposta(resposta)
}

function tamanhoLegivel(bytes?: number) {
  if (!bytes) return ""
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function IaComercialPage() {
  const [conversas, setConversas] = useState<Conversa[]>([])
  const [conversaId, setConversaId] = useState("")
  const [mensagens, setMensagens] = useState<Mensagem[]>([])
  const [entrada, setEntrada] = useState("")
  const [anexos, setAnexos] = useState<File[]>([])
  const [carregando, setCarregando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const fimConversaRef = useRef<HTMLDivElement | null>(null)
  const inputArquivoRef = useRef<HTMLInputElement | null>(null)

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
    setAnexos([])
  }

  useEffect(() => {
    const prompt = new URLSearchParams(window.location.search).get("prompt")
    if (prompt?.trim()) setEntrada(prompt.trim())
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

  function selecionarArquivos(evento: ChangeEvent<HTMLInputElement>) {
    const recebidos = Array.from(evento.target.files || [])
    if (!recebidos.length) return
    setErro("")
    setAnexos((atuais) => {
      const combinados = [...atuais, ...recebidos]
      if (combinados.length > MAX_ANEXOS) {
        setErro(`Envie no máximo ${MAX_ANEXOS} arquivos por interação.`)
        return combinados.slice(0, MAX_ANEXOS)
      }
      return combinados
    })
    evento.target.value = ""
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    const texto = entrada.trim()
    if (!texto || enviando) return
    setErro("")
    setEntrada("")
    setEnviando(true)

    const anexosEnvio = [...anexos]
    setAnexos([])

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

      const anexosMensagem: AnexoMensagem[] = anexosEnvio.map((arquivo) => ({
        nome: arquivo.name,
        tamanho_bytes: arquivo.size,
        temporario: true,
        publicado_cti: false,
      }))
      setMensagens((atuais) => [...atuais, { papel: "user", conteudo: texto, metadados: anexosMensagem.length ? { anexos: anexosMensagem } : undefined }])

      let resposta
      if (anexosEnvio.length) {
        const formulario = new FormData()
        formulario.append("mensagem", texto)
        anexosEnvio.forEach((arquivo) => formulario.append("arquivos", arquivo, arquivo.name))
        resposta = await requisitarMultipart(`/conversas/${id}/mensagens-anexos`, formulario)
      } else {
        resposta = await requisitar(`/conversas/${id}/mensagens`, {
          method: "POST",
          body: JSON.stringify({ mensagem: texto }),
        })
      }
      setMensagens((atuais) => [...atuais, resposta])
      await carregarConversas()
    } catch (falha) {
      setAnexos(anexosEnvio)
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir a resposta.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex h-[100dvh] overflow-hidden bg-[#020817] text-white">
      <div className="hidden xl:block">
        <Sidebar />
      </div>
      <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar />
        <div className="grid min-h-0 flex-1 grid-rows-[minmax(0,1fr)] overflow-hidden xl:grid-cols-[280px_minmax(0,1fr)] xl:grid-rows-1">
          <aside className="hidden min-h-0 overflow-y-auto border-r border-[#13203f] bg-[#061126] p-4 xl:block">
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
            <header className="shrink-0 border-b border-[#13203f] bg-[#091a33] px-4 py-3 sm:px-5 sm:py-4 md:px-6">
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-cyan-500/10 text-cyan-300 sm:size-11 sm:rounded-2xl"><Bot size={20} /></div>
                  <div className="min-w-0"><p className="truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-400 sm:text-xs">Assistente exclusivo do CTI</p><h1 className="text-lg font-bold sm:text-xl">IA Comercial CTI</h1></div>
                </div>
                <button type="button" onClick={() => void criarConversa()} className="flex shrink-0 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-3 py-2.5 text-sm font-semibold text-slate-950 sm:px-4 xl:hidden">
                  <MessageSquarePlus size={18} /> <span className="hidden sm:inline">Nova conversa</span>
                </button>
              </div>
              <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-400 sm:mt-3 sm:text-xs"><ShieldCheck size={14} className="shrink-0 text-emerald-400" /> <span className="line-clamp-1 sm:line-clamp-none">Análise auditável, anexos temporários e ações controladas. Nenhuma alteração ocorre sem confirmação explícita.</span></div>
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3 sm:p-5 md:p-6">
              <div className="mx-auto w-full max-w-5xl space-y-4">
                {mensagens.length === 0 && (
                  <div className="rounded-3xl border border-[#18345e] bg-[#071427] p-5 text-center sm:p-7">
                    <Bot className="mx-auto text-cyan-300" size={34} />
                    <h2 className="mt-4 text-xl font-bold sm:text-2xl">Como posso apoiar a operação comercial?</h2>
                    <p className="mt-3 text-sm leading-6 text-slate-400 md:text-[15px]">Pergunte sobre clientes, oportunidades, mercado frigorífico, cadeia fria ou anexe planilhas, PDFs, Word e apresentações para análise e cruzamento.</p>
                  </div>
                )}

                {mensagens.map((mensagem, indice) => (
                  <article key={mensagem.id || `${mensagem.papel}-${indice}`} className={`max-w-[96%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[92%] md:px-5 md:py-4 md:text-[15px] xl:max-w-[88%] ${mensagem.papel === "user" ? "ml-auto bg-cyan-500 text-slate-950" : "border border-[#18345e] bg-[#091a33] text-slate-200"}`}>
                    <div className="whitespace-pre-wrap break-words">{mensagem.conteudo}</div>
                    {mensagem.metadados?.anexos?.length ? (
                      <div className={`mt-3 flex flex-wrap gap-2 ${mensagem.papel === "user" ? "text-slate-900" : "text-slate-300"}`}>
                        {mensagem.metadados.anexos.map((anexo, anexoIndice) => (
                          <span key={`${anexo.nome}-${anexoIndice}`} className={`inline-flex max-w-full items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs ${mensagem.papel === "user" ? "border-cyan-700/30 bg-cyan-100/60" : "border-slate-700 bg-slate-950/40"}`}>
                            <Paperclip size={13} /> <span className="truncate">{anexo.nome}</span>{anexo.tamanho_bytes ? <span className="opacity-60">{tamanhoLegivel(anexo.tamanho_bytes)}</span> : null}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    {mensagem.papel === "assistant" ? (
                      <IaArtefatos mensagemId={mensagem.id} artefatos={mensagem.metadados?.artefatos} />
                    ) : null}
                    {mensagem.papel === "assistant" && mensagem.fontes?.length ? (
                      <div className="mt-3 border-t border-[#18345e] pt-2 text-xs text-slate-500">Fonte: {mensagem.fontes.map((fonte) => fonte.descricao || fonte.tipo).join(" · ")}</div>
                    ) : null}
                  </article>
                ))}

                {enviando && <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 className="animate-spin" size={17} /> Analisando o contexto CTI{anexos.length ? " e anexos" : ""}...</div>}
                {erro && <div className="rounded-xl border border-red-900 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</div>}
                <div ref={fimConversaRef} aria-hidden="true" />
              </div>
            </div>

            <form onSubmit={enviar} className="shrink-0 border-t border-[#13203f] bg-[#061126] p-3 sm:p-4">
              <div className="mx-auto w-full max-w-5xl">
                {anexos.length ? (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {anexos.map((arquivo, indice) => (
                      <span key={`${arquivo.name}-${indice}`} className="inline-flex max-w-full items-center gap-2 rounded-lg border border-cyan-900 bg-cyan-950/30 px-2.5 py-1.5 text-xs text-cyan-100">
                        <Paperclip size={13} /> <span className="max-w-48 truncate sm:max-w-72">{arquivo.name}</span><span className="text-cyan-400">{tamanhoLegivel(arquivo.size)}</span>
                        <button type="button" aria-label={`Remover ${arquivo.name}`} onClick={() => setAnexos((atuais) => atuais.filter((_, i) => i !== indice))} className="rounded p-0.5 hover:bg-cyan-900/60"><X size={13} /></button>
                      </span>
                    ))}
                  </div>
                ) : null}
                <div className="flex gap-2 sm:gap-3">
                  <input ref={inputArquivoRef} type="file" multiple accept={EXTENSOES_ACEITAS} onChange={selecionarArquivos} className="hidden" />
                  <button type="button" onClick={() => inputArquivoRef.current?.click()} disabled={enviando || anexos.length >= MAX_ANEXOS} aria-label="Anexar arquivos" title="Anexar arquivos temporários" className="grid size-12 shrink-0 place-items-center rounded-2xl border border-slate-700 bg-slate-900/80 text-slate-300 hover:border-cyan-600 hover:text-cyan-300 disabled:opacity-40 sm:size-14">
                    <Paperclip size={20} />
                  </button>
                  <textarea value={entrada} onChange={(event) => setEntrada(event.target.value)} placeholder={anexos.length ? "Diga o que a IA deve fazer com os anexos..." : "Pergunte à IA Comercial CTI..."} rows={1} className="min-h-12 max-h-28 flex-1 resize-none rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-500 md:text-[15px]" />
                  <button disabled={!entrada.trim() || enviando} className="grid size-12 shrink-0 place-items-center rounded-2xl bg-cyan-500 text-slate-950 disabled:opacity-40 sm:size-14"><Send size={20} /></button>
                </div>
                <p className="mt-2 px-1 text-[10px] text-slate-600 sm:text-[11px]">Anexos desta conversa são temporários e não entram no conhecimento oficial do CTI sem homologação no Back Office.</p>
              </div>
            </form>
          </section>
        </div>
      </section>
    </main>
  )
}