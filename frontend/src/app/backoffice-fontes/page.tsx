/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { ChangeEvent, useEffect, useMemo, useState } from "react"
import { BrainCircuit, CheckCircle2, Database, Eye, FileSearch, FileUp, Loader2, Send, ShieldCheck, XCircle } from "lucide-react"

import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { getSupabaseClient } from "@/core/database/supabase"

type Fonte = {
  id: string
  nome_arquivo: string
  mime_type?: string | null
  extensao?: string | null
  tamanho_bytes: number
  sha256: string
  tipo_detectado: string
  classificacao_negocio: string
  classificacao_sugerida?: string | null
  confianca_classificacao?: number | null
  descricao_semantica?: string | null
  campos_semanticos?: string[] | null
  interpretado_semanticamente_em?: string | null
  status_governanca: string
  publicado_ia: boolean
  interpretacao_resumo?: Record<string, unknown>
  created_at: string
}

type Preview = {
  fonte: Fonte
  total_registros_semanticos: number
  publicavel: boolean
  preview: Array<{ indice: number; tipo_registro: string; conteudo_texto?: string | null; dados?: Record<string, unknown>; metadados?: Record<string, unknown> }>
}

type RespostaLista = { fontes: Fonte[]; total: number; por_status: Record<string, number> }

const API = "/api/crm-proxy/backoffice-fontes"
const ETAPAS = ["RECEBIDO", "INTERPRETADO", "VALIDADO", "HOMOLOGADO", "PUBLICADO_IA"]

async function tokenAtual(): Promise<string> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) throw new Error("Sessão ADMIN_MASTER não encontrada.")
  return data.session.access_token
}

async function requisitar(caminho = "", init?: RequestInit) {
  const token = await tokenAtual()
  const resposta = await fetch(`${API}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}`, ...(init?.headers || {}) },
  })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new Error(payload?.detail || `Falha ${resposta.status}`)
  return payload
}

function tamanho(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function dataHora(valor: string) {
  try { return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(valor)) }
  catch { return valor }
}

function resumoInterpretacao(fonte: Fonte) {
  const resumo = fonte.interpretacao_resumo || {}
  if (typeof resumo.paginas === "number") return `${resumo.paginas} página(s)`
  if (typeof resumo.quantidade_abas === "number") return `${resumo.quantidade_abas} aba(s)`
  if (typeof resumo.slides_xml === "number") return `${resumo.slides_xml} slide(s) estrutural(is)`
  if (typeof resumo.caracteres === "number") return `${resumo.caracteres} caractere(s)`
  if (typeof resumo.observacao === "string") return resumo.observacao
  return fonte.status_governanca === "RECEBIDO" ? "Aguardando interpretação" : "Estrutura interpretada"
}

export default function BackofficeFontesPage() {
  const [dados, setDados] = useState<RespostaLista>({ fontes: [], total: 0, por_status: {} })
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [acaoId, setAcaoId] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [preview, setPreview] = useState<Preview | null>(null)

  async function carregar() {
    const resposta = await requisitar()
    setDados({ fontes: Array.isArray(resposta.fontes) ? resposta.fontes : [], total: Number(resposta.total || 0), por_status: resposta.por_status || {} })
  }

  useEffect(() => {
    let ativo = true
    carregar().catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Falha ao carregar fontes.") }).finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [])

  const publicados = useMemo(() => dados.fontes.filter((item) => item.publicado_ia).length, [dados.fontes])

  async function enviar() {
    if (!arquivo || enviando) return
    setErro("")
    setMensagem("")
    setEnviando(true)
    try {
      const form = new FormData()
      form.append("arquivo", arquivo)
      const resposta = await requisitar("/upload", { method: "POST", body: form })
      setMensagem(resposta.duplicado ? "Esta fonte já estava registrada. Nenhuma duplicação foi criada." : "Fonte recebida e original preservado. Agora pode seguir para interpretação controlada.")
      setArquivo(null)
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao receber a fonte.")
    } finally {
      setEnviando(false)
    }
  }

  async function governanca(fonte: Fonte, status: "VALIDADO" | "HOMOLOGADO" | "REJEITADO") {
    setErro("")
    setMensagem("")
    setAcaoId(fonte.id)
    try {
      await requisitar(`/${fonte.id}/governanca`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, observacao: `Decisão registrada pelo ADMIN_MASTER: ${status}.` }),
      })
      setMensagem(`Governança atualizada para ${status}.`)
      await carregar()
      if (preview?.fonte.id === fonte.id) setPreview(await requisitar(`/${fonte.id}/preview`))
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao atualizar governança.")
    } finally { setAcaoId("") }
  }

  async function interpretar(fonte: Fonte) {
    setAcaoId(fonte.id); setErro(""); setMensagem("")
    try {
      await requisitar(`/${fonte.id}/interpretar`, { method: "POST" })
      setMensagem(`Fonte ${fonte.nome_arquivo} interpretada estruturalmente. Agora gere a leitura semântica.`)
      await carregar()
    } catch (e) { setErro(e instanceof Error ? e.message : "Falha na interpretação.") }
    finally { setAcaoId("") }
  }

  async function semantica(fonte: Fonte) {
    setAcaoId(fonte.id); setErro(""); setMensagem("")
    try {
      const resposta = await requisitar(`/${fonte.id}/semantica`, { method: "POST" })
      setMensagem(`Semântica gerada: ${resposta.total_registros_semanticos} registro(s). Revise o preview antes da homologação/publicação.`)
      await carregar()
      setPreview(await requisitar(`/${fonte.id}/preview`))
    } catch (e) { setErro(e instanceof Error ? e.message : "Falha na interpretação semântica.") }
    finally { setAcaoId("") }
  }

  async function abrirPreview(fonte: Fonte) {
    setAcaoId(fonte.id); setErro("")
    try { setPreview(await requisitar(`/${fonte.id}/preview`)) }
    catch (e) { setErro(e instanceof Error ? e.message : "Falha ao carregar preview.") }
    finally { setAcaoId("") }
  }

  async function publicar(fonte: Fonte) {
    setAcaoId(fonte.id); setErro(""); setMensagem("")
    try {
      await requisitar(`/${fonte.id}/publicar-ia`, { method: "POST" })
      setMensagem(`Fonte ${fonte.nome_arquivo} publicada para a IA Comercial. Novos documentos usarão este mesmo fluxo sem alteração de código.`)
      await carregar()
      setPreview(await requisitar(`/${fonte.id}/preview`))
    } catch (e) { setErro(e instanceof Error ? e.message : "Falha ao publicar para IA.") }
    finally { setAcaoId("") }
  }

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <div className="hidden xl:block"><Sidebar /></div>
      <section className="min-w-0 flex-1">
        <Topbar />
        <div className="mx-auto max-w-[1500px] p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">ADMIN_MASTER · GOVERNANÇA</p>
              <h1 className="mt-2 text-2xl font-bold sm:text-3xl">Back Office Universal de Fontes</h1>
              <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">Upload → interpretação estrutural → semântica → validação → homologação → publicação dinâmica para a IA. O documento só entra no universo da IA depois da sua decisão.</p>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-emerald-900/70 bg-emerald-950/20 px-3 py-2 text-xs text-emerald-300"><ShieldCheck size={16} /> Publicação automática bloqueada</div>
          </header>

          <section className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[["Fontes registradas", dados.total], ["Aguardando interpretação", dados.por_status.RECEBIDO || 0], ["Homologadas", dados.por_status.HOMOLOGADO || 0], ["Publicadas para IA", publicados]].map(([label, valor]) => (
              <div key={String(label)} className="min-w-0 rounded-2xl border border-[#13203f] bg-[#071427] p-4"><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-100">{valor}</p></div>
            ))}
          </section>

          <section className="mt-5 rounded-2xl border border-[#17345e] bg-[#071427] p-4 sm:p-5">
            <div className="flex items-center gap-3"><FileUp className="text-cyan-300" /><div><h2 className="font-semibold">Receber nova fonte</h2><p className="text-xs text-slate-500">PDF, Word, PowerPoint, planilhas, texto, dados estruturados e imagens · até 50 MB</p></div></div>
            <div className="mt-4 flex flex-col gap-3 lg:flex-row">
              <label className="flex min-h-12 flex-1 cursor-pointer items-center rounded-xl border border-dashed border-slate-600 bg-slate-950/40 px-4 text-sm text-slate-300 hover:border-cyan-600"><input className="hidden" type="file" onChange={(e: ChangeEvent<HTMLInputElement>) => setArquivo(e.target.files?.[0] || null)} />{arquivo ? `${arquivo.name} · ${tamanho(arquivo.size)}` : "Selecionar arquivo"}</label>
              <button onClick={() => void enviar()} disabled={!arquivo || enviando} className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-5 font-semibold text-slate-950 disabled:opacity-40">{enviando ? <Loader2 className="animate-spin" size={18} /> : <FileUp size={18} />} Registrar fonte</button>
            </div>
            {mensagem && <p className="mt-3 rounded-xl border border-emerald-900 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-300">{mensagem}</p>}
            {erro && <p className="mt-3 rounded-xl border border-red-900 bg-red-950/30 px-3 py-2 text-sm text-red-200">{erro}</p>}
          </section>

          {preview && (
            <section className="mt-5 rounded-2xl border border-violet-900/70 bg-violet-950/10 p-4 sm:p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div><p className="text-xs uppercase tracking-wider text-violet-300">Preview semântico</p><h2 className="mt-1 font-semibold">{preview.fonte.nome_arquivo}</h2><p className="mt-2 text-sm text-slate-400">{preview.fonte.descricao_semantica || "Sem descrição semântica."}</p></div>
                <button onClick={() => setPreview(null)} className="self-start text-xs text-slate-400">Fechar</button>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3"><div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Classificação sugerida</p><p className="mt-1 font-medium text-violet-200">{preview.fonte.classificacao_sugerida || "—"}</p></div><div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Confiança</p><p className="mt-1 font-medium">{preview.fonte.confianca_classificacao != null ? `${Math.round(Number(preview.fonte.confianca_classificacao) * 100)}%` : "—"}</p></div><div className="rounded-xl bg-[#071427] p-3"><p className="text-xs text-slate-500">Registros semânticos</p><p className="mt-1 font-medium">{preview.total_registros_semanticos}</p></div></div>
              <div className="mt-4 max-h-80 space-y-2 overflow-y-auto">{preview.preview.slice(0, 20).map((item) => <div key={`${item.indice}-${item.tipo_registro}`} className="rounded-xl border border-[#253453] bg-[#061126] p-3"><p className="text-[11px] uppercase tracking-wide text-slate-500">#{item.indice} · {item.tipo_registro}</p><p className="mt-1 whitespace-pre-wrap break-words text-xs leading-5 text-slate-300">{item.conteudo_texto || JSON.stringify(item.dados || {})}</p></div>)}</div>
            </section>
          )}

          <section className="mt-5 overflow-hidden rounded-2xl border border-[#13203f] bg-[#071427]">
            <div className="flex items-center justify-between border-b border-[#13203f] px-4 py-4 sm:px-5"><div className="flex items-center gap-2"><Database size={18} className="text-cyan-300" /><h2 className="font-semibold">Registro de fontes</h2></div><span className="text-xs text-slate-500">{dados.total} fonte(s)</span></div>
            {carregando ? <div className="flex items-center gap-2 p-6 text-sm text-slate-400"><Loader2 className="animate-spin" size={18} /> Carregando governança...</div> : dados.fontes.length === 0 ? <p className="p-6 text-sm text-slate-500">Nenhuma fonte registrada ainda.</p> : (
              <div className="overflow-x-auto"><table className="w-full min-w-[1250px] text-left text-sm"><thead className="bg-[#091a33] text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-4 py-3">Fonte</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3">Interpretação</th><th className="px-4 py-3">Semântica</th><th className="px-4 py-3">Governança</th><th className="px-4 py-3">IA</th><th className="px-4 py-3">Ações</th></tr></thead>
                <tbody>{dados.fontes.map((fonte) => { const ocupada = acaoId === fonte.id; return <tr key={fonte.id} className="border-t border-[#13203f] align-top">
                  <td className="px-4 py-4"><p className="max-w-[280px] break-words font-medium text-slate-200">{fonte.nome_arquivo}</p><p className="mt-1 text-xs text-slate-500">{tamanho(fonte.tamanho_bytes)} · SHA {fonte.sha256.slice(0, 10)}…</p></td>
                  <td className="px-4 py-4 text-slate-300">{fonte.tipo_detectado}</td>
                  <td className="max-w-[240px] px-4 py-4 text-xs leading-5 text-slate-400">{resumoInterpretacao(fonte)}</td>
                  <td className="max-w-[240px] px-4 py-4 text-xs leading-5 text-slate-400">{fonte.interpretado_semanticamente_em ? <><span className="text-violet-300">{fonte.classificacao_sugerida || "SEMÂNTICA GERADA"}</span>{fonte.campos_semanticos?.length ? <p className="mt-1 line-clamp-2">{fonte.campos_semanticos.join(", ")}</p> : null}</> : "Não gerada"}</td>
                  <td className="px-4 py-4"><span className={`rounded-full border px-2.5 py-1 text-xs ${fonte.status_governanca === "REJEITADO" || fonte.status_governanca === "ERRO" ? "border-red-900 bg-red-950/30 text-red-300" : "border-cyan-900 bg-cyan-950/30 text-cyan-300"}`}>{fonte.status_governanca}</span><div className="mt-2 flex gap-1">{ETAPAS.map((etapa) => <span key={etapa} title={etapa} className={`h-1.5 w-5 rounded-full ${ETAPAS.indexOf(etapa) <= ETAPAS.indexOf(fonte.status_governanca) ? "bg-cyan-400" : "bg-slate-800"}`} />)}</div></td>
                  <td className="px-4 py-4">{fonte.publicado_ia ? <span className="text-emerald-300">Publicado</span> : <span className="text-slate-500">Bloqueado</span>}</td>
                  <td className="px-4 py-4"><div className="flex max-w-[360px] flex-wrap gap-2">
                    {fonte.status_governanca === "RECEBIDO" && <button disabled={ocupada} onClick={() => void interpretar(fonte)} className="flex items-center gap-1 rounded-lg border border-cyan-800 px-2.5 py-1.5 text-xs text-cyan-300 disabled:opacity-40"><FileSearch size={14} /> Interpretar</button>}
                    {["INTERPRETADO", "VALIDADO", "HOMOLOGADO"].includes(fonte.status_governanca) && <button disabled={ocupada} onClick={() => void semantica(fonte)} className="flex items-center gap-1 rounded-lg border border-violet-800 px-2.5 py-1.5 text-xs text-violet-300 disabled:opacity-40"><BrainCircuit size={14} /> Gerar semântica</button>}
                    {fonte.interpretado_semanticamente_em && <button disabled={ocupada} onClick={() => void abrirPreview(fonte)} className="flex items-center gap-1 rounded-lg border border-slate-700 px-2.5 py-1.5 text-xs text-slate-300 disabled:opacity-40"><Eye size={14} /> Preview</button>}
                    {fonte.status_governanca === "INTERPRETADO" && fonte.interpretado_semanticamente_em && <button disabled={ocupada} onClick={() => void governanca(fonte, "VALIDADO")} className="flex items-center gap-1 rounded-lg border border-emerald-900 px-2.5 py-1.5 text-xs text-emerald-300 disabled:opacity-40"><CheckCircle2 size={14} /> Validar</button>}
                    {fonte.status_governanca === "VALIDADO" && <button disabled={ocupada} onClick={() => void governanca(fonte, "HOMOLOGADO")} className="flex items-center gap-1 rounded-lg border border-emerald-800 px-2.5 py-1.5 text-xs text-emerald-200 disabled:opacity-40"><ShieldCheck size={14} /> Homologar</button>}
                    {fonte.status_governanca === "HOMOLOGADO" && fonte.interpretado_semanticamente_em && <button disabled={ocupada} onClick={() => void publicar(fonte)} className="flex items-center gap-1 rounded-lg bg-emerald-500 px-2.5 py-1.5 text-xs font-semibold text-slate-950 disabled:opacity-40"><Send size={14} /> Publicar IA</button>}
                    {!["REJEITADO", "PUBLICADO_IA"].includes(fonte.status_governanca) && <button disabled={ocupada} onClick={() => void governanca(fonte, "REJEITADO")} className="flex items-center gap-1 rounded-lg border border-red-900 px-2.5 py-1.5 text-xs text-red-300 disabled:opacity-40"><XCircle size={14} /> Rejeitar</button>}
                  </div></td>
                </tr> })}</tbody></table></div>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}
