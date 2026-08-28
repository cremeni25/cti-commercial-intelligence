"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { ArrowLeft, CheckCircle2, FileText, Loader2, Mail, PackageCheck, Send } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import { useAuth } from "@/core/auth"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Pacote = { proposta: Registro; item: Registro | null; oportunidade: Registro | null; cliente: Registro | null; aceites: Registro[]; pedidos: Registro[] }

function texto(valor: unknown, padrao = "—") { const v = String(valor ?? "").trim(); return v || padrao }
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function emails(valor: string) { return valor.split(/[;,\n]+/).map((item) => item.trim()).filter(Boolean) }

export default function PropostaCrmAppPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { usuario } = useAuth()
  const id = String(params.id || "")
  const [dados, setDados] = useState<Pacote | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [revisaoAberta, setRevisaoAberta] = useState(false)
  const [envioAberto, setEnvioAberto] = useState(false)
  const [paraPedido, setParaPedido] = useState("")
  const [ccPedido, setCcPedido] = useState("")
  const [ccoPedido, setCcoPedido] = useState("")
  const [observacoes, setObservacoes] = useState("")
  const [paraProposta, setParaProposta] = useState("")
  const [ccProposta, setCcProposta] = useState("")
  const [ccoProposta, setCcoProposta] = useState("")
  const [mensagemEmail, setMensagemEmail] = useState("Segue a proposta comercial para sua análise.")

  async function carregar() {
    setCarregando(true); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/pacote`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível carregar a proposta (${resposta.status}).`))
      setDados(payload)
      const emailCliente = texto(payload?.cliente?.email, "")
      if (emailCliente) {
        setParaProposta((atual) => atual || emailCliente)
        setParaPedido((atual) => atual || emailCliente)
      }
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar a proposta.") }
    finally { setCarregando(false) }
  }

  useEffect(() => { if (id) void carregar() }, [id])

  async function executar(sufixo: string, body: Registro = {}) {
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}${sufixo}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Operação não concluída (${resposta.status}).`))
      setMensagem("Operação registrada com sucesso.")
      await carregar()
      return payload
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha na operação.") }
    finally { setProcessando(false) }
  }

  async function enviarProposta() {
    const destinatarios = emails(paraProposta)
    if (!destinatarios.length) return setErro("Informe ao menos um endereço no campo Para.")
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/enviar-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destinatarios,
          cc: emails(ccProposta),
          cco: emails(ccoProposta),
          mensagem: mensagemEmail.trim() || null,
        }),
      })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(payload.detail) || `Não foi possível enviar a proposta (${resposta.status}).`)
      setMensagem(`Proposta enviada por e-mail. Protocolo: ${texto(payload.message_id, "confirmado")}.`)
      setEnvioAberto(false)
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao enviar a proposta.") }
    finally { setProcessando(false) }
  }

  async function aceite(metodo: "PRESENCIAL_TELA" | "REMOTO_LINK") {
    const nome = window.prompt("Nome completo do cliente/signatário:")?.trim()
    if (!nome) return
    const email = window.prompt("E-mail do cliente, quando disponível:")?.trim() || null

    if (metodo === "PRESENCIAL_TELA") {
      const confirmado = window.confirm(`Confirmar que ${nome} aceitou presencialmente os termos desta proposta?`)
      if (!confirmado) return
    }

    setProcessando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/aceites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metodo, nome_signatario: nome, email_signatario: email }),
      })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível registrar o aceite (${resposta.status}).`))

      const aceiteCriado = payload.aceite && typeof payload.aceite === "object" ? payload.aceite as Registro : null
      const aceiteId = texto(aceiteCriado?.id, "")

      if (metodo === "PRESENCIAL_TELA") {
        if (!aceiteId) throw new Error("A solicitação de aceite foi criada sem identificação válida.")
        const confirmacao = await fetch(`/api/crm-proxy/crm-documentos/aceites/${encodeURIComponent(aceiteId)}/confirmar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            aceite_termos: true,
            user_agent: navigator.userAgent,
            evidencias: { origem: "CRM_APP", modalidade: "PRESENCIAL_TELA" },
          }),
        })
        const confirmacaoPayload = await confirmacao.json().catch(() => ({})) as Registro
        if (!confirmacao.ok) throw new Error(String(confirmacaoPayload.detail || `Não foi possível confirmar o aceite (${confirmacao.status}).`))
        setMensagem("Aceite presencial confirmado. A proposta está liberada para conversão em pedido.")
      } else {
        const token = String(payload.link_token || "")
        if (!token) throw new Error("O link de aceite foi criado sem token válido.")
        const link = `${window.location.origin}/aceite/${token}`
        await navigator.clipboard?.writeText(link)
        setMensagem(`Link de aceite copiado: ${link}`)
      }

      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao registrar o aceite.") }
    finally { setProcessando(false) }
  }

  async function converterPedido() {
    const destinatarios = emails(paraPedido)
    if (!destinatarios.length) { setErro("Informe ao menos um endereço no campo Para do pedido."); return }
    setProcessando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/propostas/${encodeURIComponent(id)}/converter-pedido-operacional`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destinatarios,
          cc: emails(ccPedido),
          cco: emails(ccoPedido),
          observacoes_envio: observacoes || null,
          responsavel_id: usuario?.id ? String(usuario.id) : null,
        }),
      })
      const payload = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível gerar o pedido (${resposta.status}).`))
      const pedidoId = String(payload.id || "")
      if (!pedidoId) throw new Error("Pedido gerado sem identificação válida.")
      router.push(`/crm-app/pedidos/${pedidoId}`)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao gerar o pedido.") }
    finally { setProcessando(false) }
  }

  const status = texto(dados?.proposta.status_documento, "RASCUNHO").toUpperCase()
  const podeEmitir = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"].includes(status)
  const podeEnviar = ["RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA", "EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podeAceite = ["EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO"].includes(status)
  const podePedido = status === "ACEITA"
  const pedido = dados?.pedidos?.[0]
  const precoTabela = dados?.item?.preco_tabela ?? dados?.item?.preco_unitario
  const desconto = Number(dados?.item?.desconto_percentual || 0)

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-28 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/propostas" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Proposta, envio, aceite e pedido</h1></div></header>
    {carregando && <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {mensagem && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
    {dados && <div className="space-y-4">
      <section className="rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><p className="text-sm text-slate-400">Proposta comercial</p><h2 className="mt-1 text-xl font-bold">{texto(dados.proposta.numero, "Proposta em elaboração")}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full border border-cyan-800 px-3 py-1 text-cyan-200">{status.replaceAll("_", " ")}</span><span className="rounded-full border border-[#24466f] px-3 py-1 text-slate-300">{moeda(dados.proposta.valor)}</span></div></section>
      <section className="grid gap-3 sm:grid-cols-2"><Info label="Cliente" valor={texto(dados.cliente?.razao_social || dados.cliente?.nome || dados.oportunidade?.cliente_nome)}/><Info label="Equipamento" valor={texto(dados.item?.equipamento)}/><Info label="Quantidade" valor={texto(dados.item?.quantidade, "1")}/><Info label="Preço de tabela" valor={moeda(precoTabela)}/><Info label="Desconto" valor={`${desconto.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`}/><Info label="Valor negociado" valor={moeda(dados.proposta.valor)}/></section>
      <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><h3 className="font-bold">Ações comerciais</h3><p className="mt-1 text-sm text-slate-400">Emita, envie ao cliente, registre aceite e converta em pedido sem sair do aplicativo.</p><div className="mt-4 grid gap-3">
        {podeEmitir && <button disabled={processando} onClick={() => void executar("/emitir")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40"><FileText className="mr-2 inline" size={18}/>Emitir proposta</button>}
        {podeEnviar && !envioAberto && <button disabled={processando} onClick={() => setEnvioAberto(true)} className="rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-40"><Mail className="mr-2 inline" size={18}/>Enviar proposta por e-mail</button>}
        {podeAceite && <><button disabled={processando} onClick={() => void aceite("PRESENCIAL_TELA")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40"><CheckCircle2 className="mr-2 inline" size={18}/>Aceite presencial</button><button disabled={processando} onClick={() => void aceite("REMOTO_LINK")} className="rounded-xl border border-cyan-700 px-4 py-3 text-cyan-200 disabled:opacity-40">Gerar link de aceite</button></>}
        {podePedido && !revisaoAberta && <button disabled={processando} onClick={() => setRevisaoAberta(true)} className="rounded-xl border border-emerald-700 px-4 py-3 text-emerald-300 disabled:opacity-40"><PackageCheck className="mr-2 inline" size={18}/>Revisar e converter em pedido</button>}
        {pedido && <Link href={`/crm-app/pedidos/${String(pedido.id)}`} className="rounded-xl border border-emerald-700 px-4 py-3 text-center font-semibold text-emerald-300">Abrir pedido</Link>}
      </div></section>

      {envioAberto && <section className="rounded-3xl border border-cyan-800 bg-cyan-950/15 p-5"><h3 className="text-lg font-bold">Enviar proposta ao cliente</h3><p className="mt-1 text-sm text-slate-400">O aplicativo gera o PDF oficial e usa o mesmo endereçamento de um e-mail convencional.</p><div className="mt-4 space-y-3"><CampoEmail titulo="Para" valor={paraProposta} alterar={setParaProposta} obrigatorio placeholder="cliente@empresa.com.br"/><CampoEmail titulo="CC — cópia" valor={ccProposta} alterar={setCcProposta} placeholder="gestor@empresa.com.br"/><CampoEmail titulo="CCO — cópia oculta" valor={ccoProposta} alterar={setCcoProposta} placeholder="arquivo@empresa.com.br"/><label className="block"><span className="mb-2 block text-sm">Mensagem</span><textarea value={mensagemEmail} onChange={(e) => setMensagemEmail(e.target.value)} rows={4} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label></div><div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={() => setEnvioAberto(false)} className="rounded-xl border border-[#24466f] px-4 py-3">Cancelar</button><button type="button" disabled={processando || !emails(paraProposta).length} onClick={() => void enviarProposta()} className="rounded-xl bg-cyan-500 px-4 py-3 font-bold text-slate-950 disabled:opacity-40">{processando ? <Loader2 className="mr-2 inline animate-spin" size={18}/> : <Send className="mr-2 inline" size={18}/>}Enviar PDF oficial</button></div></section>}

      {podePedido && revisaoAberta && <section className="rounded-3xl border border-emerald-800 bg-emerald-950/20 p-5"><h3 className="text-lg font-bold">Revisão e endereçamento do pedido</h3><p className="mt-1 text-sm text-slate-400">Defina agora Para, CC e CCO. O pedido será criado já com esse envelope registrado.</p><div className="mt-4 space-y-3"><CampoEmail titulo="Para" valor={paraPedido} alterar={setParaPedido} obrigatorio placeholder="compras@cliente.com.br"/><CampoEmail titulo="CC — cópia" valor={ccPedido} alterar={setCcPedido} placeholder="gestor@empresa.com.br"/><CampoEmail titulo="CCO — cópia oculta" valor={ccoPedido} alterar={setCcoPedido} placeholder="arquivo@empresa.com.br"/><label className="block"><span className="mb-2 block text-sm">Observações do pedido</span><textarea value={observacoes} onChange={(e) => setObservacoes(e.target.value)} rows={3} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/></label></div><div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={() => setRevisaoAberta(false)} className="rounded-xl border border-[#24466f] px-4 py-3">Cancelar</button><button type="button" disabled={processando || !emails(paraPedido).length} onClick={() => void converterPedido()} className="rounded-xl bg-emerald-600 px-4 py-3 font-bold disabled:opacity-40"><Send className="mr-2 inline" size={18}/>Gerar pedido</button></div></section>}
    </div>}
  </div></main>
}

function CampoEmail({ titulo, valor, alterar, obrigatorio = false, placeholder }: { titulo: string; valor: string; alterar: (valor: string) => void; obrigatorio?: boolean; placeholder: string }) {
  return <label className="block"><span className="mb-2 block text-sm">{titulo}{obrigatorio ? " *" : ""}</span><textarea value={valor} onChange={(e) => alterar(e.target.value)} rows={2} placeholder={placeholder} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 py-3"/><small className="text-slate-500">Separe múltiplos endereços por vírgula, ponto e vírgula ou nova linha.</small></label>
}

function Info({ label, valor }: { label: string; valor: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><p className="text-xs text-slate-400">{label}</p><strong className="mt-1 block">{valor}</strong></div> }