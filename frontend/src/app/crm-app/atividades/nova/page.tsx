"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, ClipboardCheck, Loader2, MapPinned } from "lucide-react"
import { useAuth } from "@/core/auth"

type Cliente = { id: string; nome: string; codigo?: string }

const tipos = [
  ["VISITA_PRESENCIAL", "Visita presencial"],
  ["VISITA_REMOTA", "Visita remota"],
  ["LIGACAO", "Ligação"],
  ["WHATSAPP", "WhatsApp"],
  ["EMAIL", "E-mail"],
  ["FOLLOW_UP", "Follow-up"],
  ["REUNIAO", "Reunião"],
  ["APRESENTACAO", "Apresentação"],
  ["PROSPECCAO", "Prospecção"],
  ["POS_VENDA", "Pós-venda"],
  ["OUTRO", "Outro"],
] as const

export default function NovaAtividadePage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteBusca, setClienteBusca] = useState("")
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [tipo, setTipo] = useState("FOLLOW_UP")
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  useEffect(() => {
    fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" })
      .then((r) => r.ok ? r.json() : [])
      .then((dados) => setClientes((Array.isArray(dados) ? dados : []).map((item) => ({
        id: String(item.id || item.cliente_id || ""),
        nome: String(item.razao_social || item.nome_fantasia || item.nome || item.empresa || "").trim(),
        codigo: String(item.codigo || item.codigo_cliente || "").trim(),
      })).filter((item) => item.id && item.nome)))
      .catch(() => setClientes([]))
  }, [])

  const sugestoes = useMemo(() => {
    const termo = clienteBusca.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || cliente) return []
    return clientes.filter((item) => `${item.nome} ${item.codigo || ""}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 12)
  }, [clienteBusca, cliente, clientes])

  const visita = tipo.startsWith("VISITA")

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setErro("")
    setSucesso("")
    if (!cliente) return setErro("Selecione um cliente existente.")
    if (!usuario?.id) return setErro("Não foi possível confirmar o usuário autenticado.")

    const dados = new FormData(evento.currentTarget)
    const detalhes = [
      `Descrição: ${String(dados.get("descricao") || "").trim()}`,
      visita ? `Local: ${String(dados.get("local") || "").trim()}` : "",
      visita ? `Participantes: ${String(dados.get("participantes") || "").trim()}` : "",
      visita ? `Resultado esperado: ${String(dados.get("resultado_esperado") || "").trim()}` : "",
      `Próxima ação: ${String(dados.get("proxima_acao") || "").trim()}`,
    ].filter(Boolean).join("\n")

    setSalvando(true)
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: cliente.id,
          usuario_id: usuario.id,
          tipo,
          titulo: String(dados.get("titulo") || "").trim(),
          descricao: detalhes || null,
          data: String(dados.get("data") || "") || null,
          horario: String(dados.get("horario") || "") || null,
          status: "PENDENTE",
        }),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(detalhe.detail || `Falha ${resposta.status}`))
      evento.currentTarget.reset()
      setCliente(null)
      setClienteBusca("")
      setTipo("FOLLOW_UP")
      setSucesso("Atividade registrada com sucesso.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar a atividade.")
    } finally {
      setSalvando(false)
    }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6">
    <div className="mx-auto max-w-3xl">
      <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Nova atividade</h1></div></header>
      <section className="mb-4 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><div className="flex items-center gap-3"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">{visita ? <MapPinned/> : <ClipboardCheck/>}</span><div><strong className="block text-lg">Uma única criação para todas as interações</strong><span className="text-sm text-slate-400">Visita é um tipo de atividade. Os campos específicos aparecem automaticamente.</span></div></div></section>
      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">{sucesso}</div>}
      <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
        <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Cliente</span><input value={clienteBusca} onChange={(e) => { setClienteBusca(e.target.value); setCliente(null) }} placeholder="Digite ao menos 2 letras" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/>{sugestoes.length > 0 && <div className="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((item) => <button type="button" key={item.id} onClick={() => { setCliente(item); setClienteBusca(item.nome) }} className="block w-full border-b border-[#16325c] px-4 py-3 text-left last:border-0"><strong>{item.nome}</strong>{item.codigo && <span className="ml-2 text-xs text-slate-400">{item.codigo}</span>}</button>)}</div>}</label>
        <label><span className="mb-2 block text-sm text-slate-300">Tipo de atividade</span><select value={tipo} onChange={(e) => setTipo(e.target.value)} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4">{tipos.map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}</select></label>
        <Campo name="titulo" label={visita ? "Objetivo da visita" : "Título"} required />
        <Campo name="data" label="Data" type="date" required />
        <Campo name="horario" label="Horário" type="time" />
        {visita && <><Campo name="local" label="Endereço / local" required /><Campo name="participantes" label="Participantes" /><Campo name="resultado_esperado" label="Resultado esperado" /></>}
        <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição</span><textarea name="descricao" rows={5} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4" /></label>
        <Campo name="proxima_acao" label="Próxima ação" />
        <button disabled={salvando} className="h-12 rounded-2xl bg-cyan-500 font-semibold text-slate-950 disabled:opacity-60">{salvando ? <span className="inline-flex items-center gap-2"><Loader2 className="animate-spin" size={18}/>Salvando...</span> : "Salvar atividade"}</button>
      </form>
    </div>
  </main>
}

function Campo({ name, label, type = "text", required = false }: { name: string; label: string; type?: string; required?: boolean }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4" /></label>
}
