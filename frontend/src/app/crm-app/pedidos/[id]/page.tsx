"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { ArrowLeft, Building2, FileCheck2, Loader2, Mail, PackageCheck, Save, Send } from "lucide-react"
import { useParams } from "next/navigation"

type Registro = Record<string, unknown>
type Pacote = { pedido: Registro; proposta: Registro | null; item: Registro | null; oportunidade: Registro | null; cliente: Registro | null; envio: Registro | null; ultimo_envio: Registro | null }
type Transporte = { configurado: boolean; provedor: string; remetente: string | null }

function texto(valor: unknown, padrao = "—") { const v = String(valor ?? "").trim(); return v || padrao }
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function dataBr(valor: unknown) { const v = texto(valor, ""); if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? v : d.toLocaleString("pt-BR") }
function separarEmails(valor: string) { return valor.split(/[;,\n]+/).map((item) => item.trim()).filter(Boolean) }

export default function PedidoCrmAppPage() {
  const params = useParams<{ id: string }>()
  const id = String(params.id || "")
  const [dados, setDados] = useState<Pacote | null>(null)
  const [transporte, setTransporte] = useState<Transporte | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [editando, setEditando] = useState(false)
  const [emails, setEmails] = useState("")
  const [observacoes, setObservacoes] = useState("")

  const carregar = useCallback(async () => {
    if (!id) return
    setCarregando(true); setErro("")
    try {
      const [pedidoResposta, transporteResposta] = await Promise.all([
        fetch(`/api/crm-proxy/crm-documentos/pedidos/${encodeURIComponent(id)}`, { cache: "no-store" }),
        fetch("/api/crm-proxy/crm-documentos/pedidos/transporte/status", { cache: "no-store" }),
      ])
      const payload = await pedidoResposta.json().catch(() => ({}))
      if (!pedidoResposta.ok) throw new Error(String(payload.detail || `Não foi possível carregar o pedido (${pedidoResposta.status}).`))
      setDados(payload)
      const atuais = Array.isArray(payload?.envio?.destinatarios) ? payload.envio.destinatarios : []
      setEmails(atuais.join("\n"))
      setObservacoes(String(payload?.envio?.observacoes_envio || ""))
      const status = await transporteResposta.json().catch(() => null)
      setTransporte(transporteResposta.ok ? status : null)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar o pedido.") }
    finally { setCarregando(false) }
  }, [id])

  useEffect(() => { void carregar() }, [carregar])

  async function salvarDestinatarios() {
    const destinatarios = separarEmails(emails)
    if (!destinatarios.length) { setErro("Informe ao menos um destinatário válido."); return }
    setSalvando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/pedidos/${encodeURIComponent(id)}/destinatarios`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ destinatarios, observacoes_envio: observacoes || null }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível salvar os destinatários (${resposta.status}).`))
      setMensagem("Destinatários registrados no pedido.")
      setEditando(false)
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao salvar os destinatários.") }
    finally { setSalvando(false) }
  }

  async function enviarPedido() {
    if (!window.confirm("Confirmar o envio deste pedido para os destinatários registrados?")) return
    setEnviando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-documentos/pedidos/${encodeURIComponent(id)}/enviar`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível enviar o pedido (${resposta.status}).`))
      setMensagem("Pedido enviado aos destinatários e registrado no dossiê comercial.")
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao enviar o pedido.") }
    finally { setEnviando(false) }
  }

  const destinatarios = Array.isArray(dados?.envio?.destinatarios) ? dados?.envio?.destinatarios as string[] : []
  const statusEnvio = texto(dados?.ultimo_envio?.status_envio || dados?.envio?.status_envio, "PENDENTE")
  const cliente = texto(dados?.cliente?.razao_social || dados?.cliente?.nome || dados?.oportunidade?.cliente_nome, "Cliente não identificado no cadastro")
  const enviado = statusEnvio === "ENVIADO"

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/pedidos" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Acompanhamento do pedido</h1><p className="text-sm text-slate-400">Documento, destinatários e situação operacional</p></div></header>
    {carregando && <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {mensagem && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
    {dados && <div className="space-y-4">
      <section className="rounded-3xl border border-emerald-800 bg-gradient-to-br from-emerald-950/50 to-[#07162b] p-5"><div className="flex items-start gap-3"><span className="rounded-2xl bg-emerald-900/40 p-3 text-emerald-300"><PackageCheck size={24}/></span><div><p className="text-sm text-slate-400">Pedido comercial</p><h2 className="mt-1 text-xl font-bold">{texto(dados.pedido.numero, "Pedido gerado")}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full border border-emerald-700 px-3 py-1 text-emerald-200">{texto(dados.pedido.status, "ABERTO")}</span><span className="rounded-full border border-[#24466f] px-3 py-1">{moeda(dados.pedido.valor)}</span></div></div></div></section>
      <section className="grid gap-3 sm:grid-cols-2"><Info icone={<Building2 size={18}/>} label="Cliente" valor={cliente}/><Info icone={<PackageCheck size={18}/>} label="Equipamento" valor={texto(dados.item?.equipamento)}/><Info icone={<FileCheck2 size={18}/>} label="Proposta de origem" valor={texto(dados.proposta?.numero)}/><Info icone={<FileCheck2 size={18}/>} label="Pedido criado em" valor={dataBr(dados.pedido.created_at)}/></section>
      <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-bold">Destinatários responsáveis</h3><p className="text-sm text-slate-400">Pessoas que deverão receber o pedido</p></div><div className="flex items-center gap-2"><span className={`rounded-full border px-3 py-1 text-xs ${enviado ? "border-emerald-700 text-emerald-300" : statusEnvio === "FALHA" ? "border-red-700 text-red-300" : "border-amber-700 text-amber-300"}`}>ENVIO {statusEnvio}</span><button type="button" onClick={() => setEditando((valor) => !valor)} className="rounded-xl border border-cyan-700 px-3 py-2 text-sm text-cyan-200">{destinatarios.length ? "Editar" : "Adicionar"}</button></div></div>
        {editando ? <div className="mt-4 space-y-3"><label className="block text-sm text-slate-300">E-mails dos destinatários<textarea value={emails} onChange={(evento) => setEmails(evento.target.value)} placeholder="um@empresa.com.br\noutro@empresa.com.br" className="mt-2 min-h-28 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><label className="block text-sm text-slate-300">Observações<textarea value={observacoes} onChange={(evento) => setObservacoes(evento.target.value)} className="mt-2 min-h-20 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><button disabled={salvando} onClick={() => void salvarDestinatarios()} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"><Save className="mr-2 inline" size={18}/>{salvando ? "Salvando..." : "Salvar destinatários"}</button></div> : <div className="mt-4 space-y-2">{destinatarios.length ? destinatarios.map((email) => <div key={email} className="flex items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-3"><Mail size={18} className="text-cyan-300"/><span className="break-all text-sm">{email}</span></div>) : <p className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhum destinatário registrado. Use o botão Adicionar.</p>}</div>}
        {!editando && texto(dados.envio?.observacoes_envio, "") && <div className="mt-4 rounded-2xl bg-[#020817] p-4 text-sm text-slate-300"><strong className="block text-xs text-slate-500">Observações para o envio</strong>{texto(dados.envio?.observacoes_envio)}</div>}
        {!editando && destinatarios.length > 0 && <button disabled={enviando || !transporte?.configurado} onClick={() => void enviarPedido()} className="mt-4 w-full rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"><Send className="mr-2 inline" size={18}/>{enviando ? "Enviando..." : enviado ? "Reenviar pedido" : "Enviar pedido agora"}</button>}
        <div className="mt-4 rounded-2xl border border-[#16325c] bg-[#020817] p-3 text-xs text-slate-400">{transporte?.configurado ? <>Transporte SMTP ativo. Remetente: <strong className="text-slate-200">{transporte.remetente}</strong>.</> : <>Transporte de e-mail ainda não configurado no backend. O botão de envio permanecerá bloqueado até as credenciais SMTP serem cadastradas no Render.</>}</div>
        {dados.ultimo_envio && <div className="mt-3 rounded-2xl border border-[#16325c] p-3 text-xs text-slate-300"><strong>Última tentativa:</strong> {dataBr(dados.ultimo_envio.enviado_em || dados.ultimo_envio.tentado_em)} · {texto(dados.ultimo_envio.status_envio)}</div>}
      </section>
      <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><h3 className="font-bold">Dossiê comercial preservado</h3><p className="mt-2 text-sm leading-6 text-slate-400">O pedido mantém vínculo com a proposta aceita, o aceite registrado, a oportunidade, o item comercial e cada tentativa de envio registrada pelo CRM App.</p></section>
    </div>}
  </div></main>
}

function Info({ icone, label, valor }: { icone: React.ReactNode; label: string; valor: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="flex items-center gap-2 text-cyan-300">{icone}<span className="text-xs text-slate-400">{label}</span></div><strong className="mt-2 block">{valor}</strong></div> }
