"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Copy, Download, Loader2, Megaphone, MessageCircle, ShieldCheck } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import {
  baixarCampanhaCsv,
  buscarCampanha,
  buscarPainelCampanhas,
  marcarEnviado,
  registrarAutorizacao,
  salvarCampanha,
  type ClienteCampanha,
  type DetalheCampanha,
  type PainelCampanhas,
} from "@/services/campanhas-comerciais"

const numero = (valor: number) => valor.toLocaleString("pt-BR")
const ROTULO_AUTORIZACAO: Record<ClienteCampanha["autorizacao"], string> = { AUTORIZADO: "Autorizou", RECUSADO: "Pediu para sair", PENDENTE: "Autorização pendente" }

function Copiar({ texto, rotulo }: { texto: string; rotulo: string }) {
  const [copiado, setCopiado] = useState<"" | "ok" | "falhou">("")
  async function copiar() {
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado("ok")
    } catch {
      setCopiado("falhou")
    }
    setTimeout(() => setCopiado(""), 2500)
  }
  return (
    <button type="button" onClick={() => void copiar()} aria-label={rotulo} className="inline-flex min-h-9 items-center gap-2 rounded-xl border border-[#24466f] px-3 text-xs font-semibold text-cyan-200">
      <Copy size={14}/>{copiado === "ok" ? "Copiado" : copiado === "falhou" ? "Selecione e copie" : "Copiar"}
    </button>
  )
}

function Campanha({ codigo, onAlterada }: { codigo: string; onAlterada: () => void }) {
  const [dados, setDados] = useState<DetalheCampanha | null>(null)
  const [mensagem, setMensagem] = useState("")
  const [erro, setErro] = useState("")
  const [aviso, setAviso] = useState("")
  const [salvando, setSalvando] = useState(false)

  const carregar = useCallback(async () => {
    try {
      const detalhe = await buscarCampanha(codigo)
      setDados(detalhe)
      setMensagem(detalhe.mensagem)
      setErro("")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível abrir a campanha.")
    }
  }, [codigo])

  useEffect(() => {
    let ativo = true
    buscarCampanha(codigo)
      .then((detalhe) => { if (ativo) { setDados(detalhe); setMensagem(detalhe.mensagem) } })
      .catch((falha: unknown) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível abrir a campanha.") })
    return () => { ativo = false }
  }, [codigo])

  async function salvar(aprovar: boolean) {
    setSalvando(true)
    setAviso("")
    try {
      await salvarCampanha(codigo, mensagem, aprovar)
      setAviso(aprovar ? "Campanha aprovada. Já pode enviar pelo WhatsApp Business." : "Rascunho salvo.")
      await carregar()
      onAlterada()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar.")
    } finally {
      setSalvando(false)
    }
  }

  async function enviar(cliente: ClienteCampanha) {
    if (!cliente.link_whatsapp) return
    window.open(cliente.link_whatsapp, "_blank", "noopener")
    try {
      await marcarEnviado(codigo, cliente.cliente_id)
      setDados((atual) => atual && { ...atual, clientes: atual.clientes.map((c) => c.cliente_id === cliente.cliente_id ? { ...c, enviado_em: new Date().toISOString() } : c) })
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "O envio não foi registrado.")
    }
  }

  async function autorizacao(cliente: ClienteCampanha, status: "AUTORIZADO" | "RECUSADO") {
    try {
      await registrarAutorizacao(cliente.cliente_id, status)
      await carregar()
      onAlterada()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível registrar a autorização.")
    }
  }

  if (!dados) return erro ? <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p> : <div className="grid min-h-32 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>
  const aprovada = dados.status === "APROVADA" && mensagem === dados.mensagem
  const enviaveis = dados.clientes.filter((c) => c.link_whatsapp)

  return (
    <section aria-label={`Campanha ${dados.titulo}`} className="space-y-4 rounded-3xl border border-[#13203f] bg-[#061126] p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">{dados.titulo}</h2>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${aprovada ? "border-emerald-700 text-emerald-200" : "border-amber-700 text-amber-200"}`}>{aprovada ? "Aprovada" : "Rascunho aguardando aprovação"}</span>
      </div>
      <label className="block text-sm text-slate-300">
        Mensagem (o agente troca <code>{"{contato}"}</code>, <code>{"{empresa}"}</code> e <code>{"{frota}"}</code> pelos dados de cada cliente)
        <textarea value={mensagem} onChange={(e) => setMensagem(e.target.value)} rows={5} maxLength={1500} className="mt-2 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-sm text-white"/>
      </label>
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={salvando} onClick={() => void salvar(false)} className="min-h-10 rounded-xl border border-[#24466f] px-4 text-sm font-semibold disabled:opacity-60">Salvar rascunho</button>
        <button type="button" disabled={salvando} onClick={() => void salvar(true)} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950 disabled:opacity-60"><CheckCircle2 size={16}/>{salvando ? "Salvando..." : "Aprovar campanha"}</button>
        <button type="button" onClick={() => void baixarCampanhaCsv(codigo).catch((f: unknown) => setErro(f instanceof Error ? f.message : "Falha na exportação."))} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-[#24466f] px-4 text-sm font-semibold"><Download size={16}/>Exportar lista</button>
      </div>
      {aviso && <p role="status" className="text-sm text-emerald-300">{aviso}</p>}
      {erro && <p role="alert" className="text-sm text-red-300">{erro}</p>}
      <p className="text-sm text-slate-400">{numero(dados.clientes.length)} clientes · {numero(enviaveis.length)} com WhatsApp · {numero(Object.keys(dados.enviados || {}).length)} já enviados. Quem ainda não autorizou recebe junto o pedido de autorização (LGPD).</p>
      <ul className="divide-y divide-[#13203f]">
        {dados.clientes.slice(0, 200).map((cliente) => (
          <li key={cliente.cliente_id} className="flex flex-col gap-2 py-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <p className="font-semibold">{cliente.nome}</p>
              <p className="text-xs text-slate-400">{[cliente.cidade, cliente.responsavel_nome, cliente.telefone ? `+${cliente.telefone}` : "sem WhatsApp", ROTULO_AUTORIZACAO[cliente.autorizacao]].filter(Boolean).join(" · ")}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {cliente.link_whatsapp && (
                <button type="button" disabled={!aprovada} title={aprovada ? "" : "Aprove a campanha antes de enviar"} onClick={() => void enviar(cliente)} className="inline-flex min-h-9 items-center gap-2 rounded-xl bg-emerald-600 px-3 text-xs font-bold text-white disabled:opacity-40">
                  <MessageCircle size={14}/>{cliente.enviado_em ? "Enviar de novo" : "Enviar no WhatsApp"}
                </button>
              )}
              {cliente.autorizacao !== "AUTORIZADO" && <button type="button" onClick={() => void autorizacao(cliente, "AUTORIZADO")} className="min-h-9 rounded-xl border border-emerald-800 px-3 text-xs text-emerald-200">Respondeu SIM</button>}
              {cliente.autorizacao !== "RECUSADO" && <button type="button" onClick={() => void autorizacao(cliente, "RECUSADO")} className="min-h-9 rounded-xl border border-red-900 px-3 text-xs text-red-200">Pediu para sair</button>}
            </div>
          </li>
        ))}
      </ul>
      {dados.clientes.length > 200 && <p className="text-xs text-slate-500">Mostrando os 200 primeiros por prioridade. A lista completa está na exportação.</p>}
    </section>
  )
}

export default function CampanhasPage() {
  const [painel, setPainel] = useState<PainelCampanhas | null>(null)
  const [erro, setErro] = useState("")
  const [aberta, setAberta] = useState("")

  const carregar = useCallback(async () => {
    try {
      setPainel(await buscarPainelCampanhas())
      setErro("")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as campanhas.")
    }
  }, [])

  useEffect(() => {
    let ativo = true
    buscarPainelCampanhas()
      .then((dados) => { if (ativo) setPainel(dados) })
      .catch((falha: unknown) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar as campanhas.") })
    return () => { ativo = false }
  }, [])

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Gestão</p>
            <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Campanhas e Canal CTI Viena SP</h1>
            <p className="mt-2 max-w-3xl text-gray-400">O agente monta cada campanha pelo grupo da carteira e escreve a mensagem de cada cliente. Você aprova e envia pelo seu WhatsApp Business. Quando a API oficial for conectada, o envio passa a ser automático.</p>
          </header>

          {erro && <p role="alert" className="rounded-2xl border border-red-900/60 bg-red-950/30 px-5 py-4 text-sm text-red-200">{erro}</p>}
          {!painel && !erro && <div className="grid min-h-40 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}

          {painel && (
            <>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {painel.campanhas.map((c) => (
                  <button key={c.codigo} type="button" aria-pressed={aberta === c.codigo} onClick={() => setAberta(aberta === c.codigo ? "" : c.codigo)} className={`rounded-2xl border p-4 text-left ${aberta === c.codigo ? "border-cyan-500 bg-[#0b2342]" : "border-[#163356] bg-[#081a32]"}`}>
                    <span className="flex items-center justify-between gap-2"><strong className="flex items-center gap-2"><Megaphone size={16} className="text-cyan-300"/>{c.titulo}</strong><span className={`text-xs ${c.rascunho.status === "APROVADA" ? "text-emerald-300" : "text-amber-300"}`}>{c.rascunho.status === "APROVADA" ? "Aprovada" : "Rascunho"}</span></span>
                    <span className="mt-1 block text-xs text-slate-400">{c.publico_descricao}</span>
                    <span className="mt-3 block text-sm"><b className="text-2xl">{numero(c.total)}</b> clientes · {numero(c.com_whatsapp)} com WhatsApp · {numero(c.autorizados)} autorizaram</span>
                  </button>
                ))}
              </div>

              {aberta && <Campanha key={aberta} codigo={aberta} onAlterada={() => void carregar()}/>}

              <section aria-label="Posts do Canal" className="space-y-3 rounded-3xl border border-[#13203f] bg-[#061126] p-5">
                <h2 className="flex items-center gap-2 text-lg font-semibold"><Megaphone size={20} className="text-cyan-300"/> Posts da semana para o Canal CTI Viena SP</h2>
                <p className="text-sm text-slate-400">Copie e publique no Canal pelo WhatsApp Business. O agente renova os textos toda semana.</p>
                {painel.posts_canal.map((post) => (
                  <article key={post.tema} className="rounded-2xl border border-[#163356] bg-[#081a32] p-4">
                    <div className="flex items-center justify-between gap-2"><p className="text-xs uppercase tracking-wider text-cyan-400">{post.tema}</p><Copiar texto={post.texto} rotulo={`Copiar post ${post.tema}`}/></div>
                    <p className="mt-2 whitespace-pre-line text-sm">{post.texto}</p>
                  </article>
                ))}
              </section>

              <section aria-label="Autorização LGPD" className="space-y-3 rounded-3xl border border-[#13203f] bg-[#061126] p-5">
                <h2 className="flex items-center gap-2 text-lg font-semibold"><ShieldCheck size={20} className="text-emerald-300"/> Autorização de contato (LGPD)</h2>
                <p className="text-sm text-slate-400">Vai junto na primeira mensagem de quem ainda não autorizou. Quem responde SAIR deixa de receber campanhas.</p>
                <div className="flex items-start justify-between gap-3 rounded-2xl border border-[#163356] bg-[#081a32] p-4"><p className="text-sm">{painel.texto_autorizacao}</p><Copiar texto={painel.texto_autorizacao} rotulo="Copiar texto de autorização"/></div>
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  )
}
