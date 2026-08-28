"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { ArrowLeft, Building2, CircleDollarSign, FileCheck2, Loader2, Mail, PackageCheck, Save, Send } from "lucide-react"
import { useParams } from "next/navigation"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Pacote = {
  pedido: Registro
  proposta: Registro | null
  item: Registro | null
  oportunidade: Registro | null
  cliente: Registro | null
  envio: Registro | null
  protocolo_envio: Registro | null
  transporte_email: { configurado?: boolean; remetente?: string; reply_to?: string } | null
}

function texto(valor: unknown, padrao = "—") { const v = String(valor ?? "").trim(); return v || padrao }
function moeda(valor: unknown) { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function dataBr(valor: unknown) { const v = texto(valor, ""); if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? v : d.toLocaleString("pt-BR") }
function separarEmails(valor: string) { return valor.split(/[;,\n]+/).map((item) => item.trim()).filter(Boolean) }

export default function PedidoCrmAppPage() {
  const params = useParams<{ id: string }>()
  const id = String(params.id || "")
  const [dados, setDados] = useState<Pacote | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [registrandoVenda, setRegistrandoVenda] = useState(false)
  const [vendaRegistrada, setVendaRegistrada] = useState(false)
  const [tipoVenda, setTipoVenda] = useState("EQUIPAMENTO")
  const [erro, setErro] = useState("")
  const [mensagem, setMensagem] = useState("")
  const [editando, setEditando] = useState(false)
  const [para, setPara] = useState("")
  const [cc, setCc] = useState("")
  const [cco, setCco] = useState("")
  const [observacoes, setObservacoes] = useState("")

  const carregar = useCallback(async () => {
    if (!id) return
    setCarregando(true); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/pedidos/${encodeURIComponent(id)}/pacote`, { cache: "no-store" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível carregar o pedido (${resposta.status}).`))
      setDados(payload)
      const atuais = Array.isArray(payload?.envio?.destinatarios) ? payload.envio.destinatarios : []
      const copias = Array.isArray(payload?.envio?.cc) ? payload.envio.cc : []
      const ocultas = Array.isArray(payload?.envio?.cco) ? payload.envio.cco : []
      setPara(atuais.join("\n"))
      setCc(copias.join("\n"))
      setCco(ocultas.join("\n"))
      setObservacoes(String(payload?.envio?.observacoes_envio || ""))
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao carregar o pedido.") }
    finally { setCarregando(false) }
  }, [id])

  useEffect(() => { void carregar() }, [carregar])

  async function salvarDestinatarios() {
    const destinatarios = separarEmails(para)
    if (!destinatarios.length) { setErro("Informe ao menos um endereço no campo Para."); return }
    setSalvando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/pedidos/${encodeURIComponent(id)}/destinatarios`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ destinatarios, cc: separarEmails(cc), cco: separarEmails(cco), observacoes_envio: observacoes || null }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível salvar os destinatários (${resposta.status}).`))
      setMensagem("Endereçamento do pedido registrado.")
      setEditando(false)
      await carregar()
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao salvar os destinatários.") }
    finally { setSalvando(false) }
  }

  async function enviarPedido() {
    const destinatarios = Array.isArray(dados?.envio?.destinatarios) ? dados.envio.destinatarios as string[] : []
    if (!destinatarios.length) { setErro("Registre o campo Para antes de enviar o pedido."); return }
    if (!window.confirm(`Confirma o envio definitivo deste pedido para ${destinatarios.length} destinatário(s) principal(is)?`)) return
    setEnviando(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/pedidos/${encodeURIComponent(id)}/enviar`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmar: true }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível enviar o pedido (${resposta.status}).`))
      setDados(payload)
      setMensagem("Pedido enviado e protocolo registrado no CTI.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao enviar o pedido.") }
    finally { setEnviando(false) }
  }

  async function concluirVenda() {
    if (!window.confirm("Confirma a conclusão deste pedido como venda? A venda passará a alimentar o painel gerencial do CTI.")) return
    setRegistrandoVenda(true); setErro(""); setMensagem("")
    try {
      const resposta = await fetchCrmSeguroProxy(`crm-seguro/pedidos/${encodeURIComponent(id)}/concluir-venda`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmar: true, tipo_venda: tipoVenda }),
      })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload.detail || `Não foi possível registrar a venda (${resposta.status}).`))
      setVendaRegistrada(true)
      setMensagem(payload.status === "JA_REGISTRADA" ? "Venda já estava registrada no CTI." : "Venda registrada. O painel gerencial do CTI foi alimentado.")
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha ao registrar a venda.") }
    finally { setRegistrandoVenda(false) }
  }

  const destinatarios = Array.isArray(dados?.envio?.destinatarios) ? dados?.envio?.destinatarios as string[] : []
  const copias = Array.isArray(dados?.envio?.cc) ? dados?.envio?.cc as string[] : []
  const ocultas = Array.isArray(dados?.envio?.cco) ? dados?.envio?.cco as string[] : []
  const protocolo = dados?.protocolo_envio || null
  const enviado = texto(protocolo?.status_envio || dados?.envio?.status_envio, "PENDENTE") === "ENVIADO"
  const statusEnvio = enviado ? "ENVIADO" : texto(dados?.envio?.status_envio, "PENDENTE")
  const transporteConfigurado = Boolean(dados?.transporte_email?.configurado)
  const cliente = texto(dados?.cliente?.razao_social || dados?.cliente?.nome || dados?.oportunidade?.cliente_nome, "Cliente não identificado no cadastro")

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6"><div className="mx-auto max-w-4xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app/pedidos" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Acompanhamento do pedido</h1><p className="text-sm text-slate-400">Documento, endereçamento e situação operacional</p></div></header>
    {carregando && <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>}
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
    {mensagem && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/30 p-4 text-emerald-200">{mensagem}</div>}
    {dados && <div className="space-y-4">
      <section className="rounded-3xl border border-emerald-800 bg-gradient-to-br from-emerald-950/50 to-[#07162b] p-5"><div className="flex items-start gap-3"><span className="rounded-2xl bg-emerald-900/40 p-3 text-emerald-300"><PackageCheck size={24}/></span><div><p className="text-sm text-slate-400">Pedido comercial</p><h2 className="mt-1 text-xl font-bold">{texto(dados.pedido.numero, "Pedido gerado")}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full border border-emerald-700 px-3 py-1 text-emerald-200">{texto(dados.pedido.status, "ABERTO")}</span><span className="rounded-full border border-[#24466f] px-3 py-1">{moeda(dados.pedido.valor)}</span></div></div></div></section>
      <section className="grid gap-3 sm:grid-cols-2"><Info icone={<Building2 size={18}/>} label="Cliente" valor={cliente}/><Info icone={<PackageCheck size={18}/>} label="Equipamento" valor={texto(dados.item?.equipamento)}/><Info icone={<FileCheck2 size={18}/>} label="Proposta de origem" valor={texto(dados.proposta?.numero)}/><Info icone={<FileCheck2 size={18}/>} label="Pedido criado em" valor={dataBr(dados.pedido.created_at)}/></section>

      <section className="rounded-3xl border border-cyan-800 bg-gradient-to-br from-cyan-950/30 to-[#07162b] p-5">
        <div className="flex items-start gap-3"><span className="rounded-2xl bg-cyan-900/40 p-3 text-cyan-300"><CircleDollarSign size={24}/></span><div className="flex-1"><p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Conclusão comercial</p><h3 className="mt-1 text-lg font-bold">Pedido → Venda</h3><p className="mt-1 text-sm text-slate-400">Conclua a venda pelo CRM App. O registro alimentará o acompanhamento gerencial do CTI Web.</p></div></div>
        <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
          <label className="text-sm text-slate-300">Tipo de venda<select value={tipoVenda} onChange={(evento) => setTipoVenda(evento.target.value)} disabled={vendaRegistrada || registrandoVenda} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-3 py-3 text-white"><option value="EQUIPAMENTO">Equipamento</option><option value="PECA">Peça</option><option value="SERVICO">Serviço</option><option value="OUTRA">Outra</option></select></label>
          <button disabled={vendaRegistrada || registrandoVenda} onClick={() => void concluirVenda()} className="self-end rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">{vendaRegistrada ? "Venda registrada" : registrandoVenda ? "Registrando..." : "Concluir como venda"}</button>
        </div>
      </section>

      <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-bold">Endereçamento do pedido</h3><p className="text-sm text-slate-400">Para obrigatório; CC e CCO opcionais</p></div><div className="flex items-center gap-2"><span className={`rounded-full border px-3 py-1 text-xs ${enviado ? "border-emerald-700 text-emerald-300" : "border-amber-700 text-amber-300"}`}>ENVIO {statusEnvio}</span>{!enviado && <button type="button" onClick={() => setEditando((valor) => !valor)} className="rounded-xl border border-cyan-700 px-3 py-2 text-sm text-cyan-200">{destinatarios.length ? "Editar" : "Adicionar"}</button>}</div></div>
        {editando ? <div className="mt-4 space-y-3"><label className="block text-sm text-slate-300">Para<textarea value={para} onChange={(evento) => setPara(evento.target.value)} placeholder="compras@cliente.com.br\ndiretor@cliente.com.br" className="mt-2 min-h-20 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><label className="block text-sm text-slate-300">CC — cópia<textarea value={cc} onChange={(evento) => setCc(evento.target.value)} placeholder="gestor@empresa.com.br" className="mt-2 min-h-16 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><label className="block text-sm text-slate-300">CCO — cópia oculta<textarea value={cco} onChange={(evento) => setCco(evento.target.value)} placeholder="arquivo@empresa.com.br" className="mt-2 min-h-16 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><label className="block text-sm text-slate-300">Observações<textarea value={observacoes} onChange={(evento) => setObservacoes(evento.target.value)} className="mt-2 min-h-20 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-3 text-white outline-none focus:border-cyan-600"/></label><button disabled={salvando} onClick={() => void salvarDestinatarios()} className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"><Save className="mr-2 inline" size={18}/>{salvando ? "Salvando..." : "Salvar endereçamento"}</button></div> : <div className="mt-4 space-y-3"><GrupoEmails titulo="Para" emails={destinatarios}/>{copias.length>0&&<GrupoEmails titulo="CC" emails={copias}/>} {ocultas.length>0&&<GrupoEmails titulo="CCO" emails={ocultas}/>} {!destinatarios.length&&<p className="rounded-2xl border border-dashed border-[#24466f] p-4 text-sm text-slate-400">Nenhum destinatário principal registrado. Use o botão Adicionar.</p>}</div>}
        {!editando && texto(dados.envio?.observacoes_envio, "") && <div className="mt-4 rounded-2xl bg-[#020817] p-4 text-sm text-slate-300"><strong className="block text-xs text-slate-500">Observações para o envio</strong>{texto(dados.envio?.observacoes_envio)}</div>}
        {!enviado && !editando && <div className="mt-4"><button disabled={enviando || !destinatarios.length || !transporteConfigurado} onClick={() => void enviarPedido()} className="w-full rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"><Send className="mr-2 inline" size={18}/>{enviando ? "Enviando pedido..." : "Enviar pedido"}</button><p className={`mt-3 text-xs ${transporteConfigurado ? "text-emerald-300" : "text-amber-300"}`}>{transporteConfigurado ? `Transporte confirmado: ${texto(dados.transporte_email?.remetente)}` : "Envio bloqueado até a confirmação do domínio e da chave de transporte no Render."}</p></div>}
        {enviado && protocolo && <div className="mt-4 rounded-2xl border border-emerald-800 bg-emerald-950/30 p-4"><h4 className="font-semibold text-emerald-200">Envio confirmado</h4><div className="mt-3 grid gap-2 text-sm text-slate-300 sm:grid-cols-2"><p><strong className="text-slate-500">Data:</strong> {dataBr(protocolo.enviado_em)}</p><p><strong className="text-slate-500">Provedor:</strong> {texto(protocolo.provider)}</p><p className="sm:col-span-2 break-all"><strong className="text-slate-500">Protocolo:</strong> {texto(protocolo.message_id)}</p><p className="sm:col-span-2 break-all"><strong className="text-slate-500">Remetente:</strong> {texto(protocolo.remetente)}</p></div></div>}
      </section>
      <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5"><h3 className="font-bold">Dossiê comercial preservado</h3><p className="mt-2 text-sm leading-6 text-slate-400">O pedido mantém vínculo com a proposta aceita, o aceite registrado, a oportunidade, o item comercial, o endereçamento e o protocolo de envio.</p></section>
    </div>}
  </div></main>
}

function GrupoEmails({titulo,emails}:{titulo:string;emails:string[]}) { return <div><strong className="mb-2 block text-xs uppercase tracking-[.14em] text-slate-500">{titulo}</strong><div className="space-y-2">{emails.map((email)=><div key={`${titulo}:${email}`} className="flex items-center gap-3 rounded-2xl border border-[#16325c] bg-[#091a33] p-3"><Mail size={18} className="text-cyan-300"/><span className="break-all text-sm">{email}</span></div>)}</div></div> }
function Info({ icone, label, valor }: { icone: React.ReactNode; label: string; valor: string }) { return <div className="rounded-2xl border border-[#16325c] bg-[#091a33] p-4"><div className="flex items-center gap-2 text-cyan-300">{icone}<span className="text-xs text-slate-400">{label}</span></div><strong className="mt-2 block">{valor}</strong></div> }