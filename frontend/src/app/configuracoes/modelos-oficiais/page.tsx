"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import { useAuth } from "@/core/auth/AuthContext"
import { obterTokenCTI } from "@/core/auth/session"
import { API_URL } from "@/lib/api"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"
import { homologarModelos, type ModeloHomologacao } from "@/services/modelos-proposta-homologacao"

type Modelo = ModeloHomologacao & { ativo: boolean; homologado_em: string | null }
async function lerResposta(r: Response) {
  const p = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(typeof p.detail === "string" ? p.detail : `Operação não concluída (${r.status}).`)
  return p
}
async function carregar(): Promise<Modelo[]> {
  return lerResposta(await fetchCrmSeguroProxy("modelos-proposta-importacao/versoes", {}, { timeoutMs: 60000 }))
}
const botao = "rounded-xl border border-cyan-700 px-4 py-3 text-sm font-semibold text-cyan-200 disabled:opacity-40"

export default function ModelosOficiaisPage() {
  const { usuario, loading } = useAuth()
  const master = usuario?.tipo_usuario === "ADMIN_MASTER"
  const [modelos, setModelos] = useState<Modelo[]>([])
  const [equipamento, setEquipamento] = useState("")
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [conferidos, setConferidos] = useState<Record<string, boolean>>({})
  const equipamentos = useMemo(() => [...new Set(modelos.map(m => m.equipamento))], [modelos])
  const selecionado = equipamento || equipamentos[0] || ""
  const versoes = modelos.filter(m => m.equipamento === selecionado).sort((a,b) => b.versao-a.versao)
  const referencia = versoes.find(m => m.ativo) || versoes[0]

  useEffect(() => {
    if (!master) return
    let ativo = true
    carregar().then(p => { if (ativo) setModelos(p) }).catch(e => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar os modelos.") }).finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [master])

  async function executar(acao: () => Promise<void>) {
    setOcupado(true); setErro(""); setMensagem("")
    try { await acao(); setModelos(await carregar()) }
    catch (e) { setErro(e instanceof Error ? e.message : "Operação não concluída.") }
    finally { setOcupado(false) }
  }
  async function enviar() {
    if (!referencia || !arquivo) return
    if (!/\.(doc|docx)$/i.test(arquivo.name) || arquivo.size === 0 || arquivo.size > 30*1024*1024) {
      setErro("Selecione um documento Word válido de até 30 MB."); return
    }
    await executar(async () => {
      const form = new FormData(); form.append("arquivo", arquivo)
      const r = await fetch(`${API_URL}/modelos-proposta-importacao/substituir/${encodeURIComponent(referencia.id)}`, {
        method: "POST", headers: { Authorization: `Bearer ${await obterTokenCTI()}` }, body: form,
      })
      const p = await lerResposta(r)
      setArquivo(null)
      setMensagem(`Versão ${p.versao} recebida. Abra o documento, confira integralmente e homologue antes de ativar.`)
    })
  }
  async function homologar(m: Modelo) {
    await executar(async () => {
      const p = await homologarModelos([m])
      if (p.falhas) throw new Error(p.erros?.[0]?.detail || "A homologação não foi confirmada.")
      setMensagem(`Versão ${m.versao} homologada. A ativação é uma etapa separada.`)
    })
  }
  async function ativar(m: Modelo) {
    await executar(async () => {
      await lerResposta(await fetchCrmSeguroProxy(`modelos-proposta-importacao/ativar/${encodeURIComponent(m.id)}`, { method: "POST" }, { timeoutMs: 60000, tentativas: 1 }))
      setMensagem(`Versão ${m.versao} ativada para novas emissões. Documentos anteriormente emitidos preservados.`)
    })
  }
  return <main className="flex min-h-screen bg-[#020817] text-white"><Sidebar/><section className="min-w-0 flex-1"><Topbar/>
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <header><p className="text-xs uppercase tracking-widest text-cyan-400">Documentos comerciais</p><h1 className="mt-2 text-3xl font-bold">Modelos oficiais</h1><p className="mt-3 text-slate-300">Envie o novo documento integral, confira, homologue e ative a versão. Cada arquivo mantém seu conteúdo e seu histórico.</p></header>
      {loading ? <p>Validando acesso...</p> : !master ? <p role="alert">Acesso restrito ao ADMIN_MASTER.</p> : <>
        {erro && <p role="alert" className="rounded-xl border border-red-800 bg-red-950/30 p-4 text-red-200">{erro}</p>}
        {mensagem && <p role="status" className="rounded-xl border border-emerald-800 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</p>}
        {carregando ? <p>Carregando modelos...</p> : <>
          <section className="space-y-4 rounded-2xl border border-[#16325c] bg-[#07162b] p-5">
            <label className="block">Equipamento<select value={selecionado} onChange={e => {setEquipamento(e.target.value);setArquivo(null)}} disabled={ocupado} className="mt-2 block w-full rounded-xl border border-[#24466f] bg-[#020817] p-3">{equipamentos.map(e => <option key={e}>{e}</option>)}</select></label>
            <label className="block">Novo documento oficial<input key={selecionado} type="file" accept=".doc,.docx" disabled={ocupado} onChange={e => setArquivo(e.target.files?.[0] || null)} className="mt-2 block w-full rounded-xl border border-[#24466f] p-3"/></label>
            <p className="text-sm text-slate-400">O envio registra uma nova versão inativa. O modelo vigente permanece disponível até a ativação da substituição homologada.</p>
            <button type="button" onClick={() => void enviar()} disabled={ocupado || !arquivo || !referencia} className={botao}>{ocupado ? "Processando..." : "Enviar nova versão"}</button>
          </section>
          <section aria-label="Histórico de versões" className="space-y-3"><h2 className="text-xl font-bold">Versões de {selecionado || "modelo"}</h2>
            {versoes.map(m => <article key={m.id} className="rounded-2xl border border-[#16325c] bg-[#07162b] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-semibold">Versão {m.versao} · {m.ativo ? "Vigente" : m.homologado_em ? "Homologada / inativa" : "Pendente de homologação"}</h3><p className="mt-1 break-all text-sm text-slate-400">{m.arquivo_template_nome_original || "Sem arquivo"}</p></div>{m.url_temporaria && <a href={m.url_temporaria} target="_blank" rel="noreferrer" className={botao}>Abrir documento</a>}</div>
              {!m.homologado_em && m.url_temporaria && <div className="mt-4 flex flex-wrap items-center gap-4"><label className="flex items-center gap-2"><input type="checkbox" checked={!!conferidos[m.id]} disabled={ocupado} onChange={e=>setConferidos(a=>({...a,[m.id]:e.target.checked}))}/>Conferi integralmente o documento</label><button type="button" className={botao} disabled={ocupado || !conferidos[m.id]} onClick={()=>void homologar(m)}>Homologar versão {m.versao}</button></div>}
              {!m.ativo && !!m.homologado_em && <button type="button" className={`${botao} mt-4`} disabled={ocupado} onClick={()=>void ativar(m)}>Ativar versão {m.versao} para novas emissões</button>}
            </article>)}
            {!versoes.length && <p>Nenhum modelo disponível. Consulte a importação inicial.</p>}
          </section>
        </>}
        <Link href="/configuracoes/modelos-proposta" className="inline-block text-sm text-cyan-300">Importação inicial por pacote</Link>
      </>}
    </div></section></main>
}
