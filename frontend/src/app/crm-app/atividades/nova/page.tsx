"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, ClipboardCheck, Loader2, MapPinned } from "lucide-react"
import { useAuth } from "@/core/auth"

type Cliente = { id: string; nome: string; codigo?: string }
type Negociacao = {
  oportunidade_id: string
  cliente_id: string
  titulo: string
  etapa: string
  proposta_id?: string | null
  proposta_numero?: string | null
  pedido_id?: string | null
  pedido_numero?: string | null
  encerrada?: boolean
}

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

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

export default function NovaAtividadePage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [negociacoes, setNegociacoes] = useState<Negociacao[]>([])
  const [clienteBusca, setClienteBusca] = useState("")
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [oportunidadeId, setOportunidadeId] = useState("")
  const [tipo, setTipo] = useState("FOLLOW_UP")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  useEffect(() => {
    let ativo = true

    async function carregar() {
      setCarregando(true)
      try {
        const [clientesResposta, nucleoResposta] = await Promise.all([
          fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" }),
          fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
        ])

        const clientesDados = clientesResposta.ok ? await clientesResposta.json() : []
        const nucleoDados = nucleoResposta.ok ? await nucleoResposta.json() : []
        if (!ativo) return

        const mapaClientes = new Map<string, Cliente>()
        for (const item of Array.isArray(clientesDados) ? clientesDados : []) {
          const id = texto(item.id || item.cliente_id)
          const nome = texto(item.razao_social || item.nome_fantasia || item.nome || item.empresa)
          if (id && nome) mapaClientes.set(id, { id, nome, codigo: texto(item.codigo || item.codigo_cliente) })
        }

        const listaNegociacoes: Negociacao[] = []
        for (const item of Array.isArray(nucleoDados) ? nucleoDados : []) {
          const oportunidade_id = texto(item.oportunidade_id)
          const cliente_id = texto(item.cliente_id)
          if (!oportunidade_id || !cliente_id) continue
          listaNegociacoes.push({
            oportunidade_id,
            cliente_id,
            titulo: texto(item.titulo) || "Oportunidade comercial",
            etapa: texto(item.etapa) || "OPORTUNIDADE",
            proposta_id: texto(item.proposta_id) || null,
            proposta_numero: texto(item.proposta_numero) || null,
            pedido_id: texto(item.pedido_id) || null,
            pedido_numero: texto(item.pedido_numero) || null,
            encerrada: Boolean(item.encerrada),
          })
          const clienteNome = texto(item.cliente_nome)
          if (!mapaClientes.has(cliente_id) && clienteNome) mapaClientes.set(cliente_id, { id: cliente_id, nome: clienteNome })
        }

        setClientes([...mapaClientes.values()].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
        setNegociacoes(listaNegociacoes)
      } catch {
        if (ativo) setErro("Não foi possível carregar clientes e negociações.")
      } finally {
        if (ativo) setCarregando(false)
      }
    }

    void carregar()
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = clienteBusca.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || cliente) return []
    return clientes.filter((item) => `${item.nome} ${item.codigo || ""}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 12)
  }, [clienteBusca, cliente, clientes])

  const negociacoesDoCliente = useMemo(
    () => negociacoes.filter((item) => item.cliente_id === cliente?.id && !item.encerrada),
    [cliente?.id, negociacoes],
  )

  const negociacaoSelecionada = useMemo(
    () => negociacoes.find((item) => item.oportunidade_id === oportunidadeId) || null,
    [negociacoes, oportunidadeId],
  )

  const visita = tipo.startsWith("VISITA")

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setErro("")
    setSucesso("")
    if (!cliente) return setErro("Selecione um cliente existente.")
    if (!usuario?.id) return setErro("Não foi possível confirmar o usuário autenticado.")

    const dados = new FormData(evento.currentTarget)
    const detalhes = [
      `Descrição: ${texto(dados.get("descricao"))}`,
      visita ? `Local: ${texto(dados.get("local"))}` : "",
      visita ? `Participantes: ${texto(dados.get("participantes"))}` : "",
      visita ? `Resultado esperado: ${texto(dados.get("resultado_esperado"))}` : "",
      `Próxima ação: ${texto(dados.get("proxima_acao"))}`,
    ].filter((linha) => linha && !linha.endsWith(": ")).join("\n")

    setSalvando(true)
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: cliente.id,
          oportunidade_id: negociacaoSelecionada?.oportunidade_id || null,
          proposta_id: negociacaoSelecionada?.proposta_id || null,
          pedido_id: negociacaoSelecionada?.pedido_id || null,
          usuario_id: usuario.id,
          tipo,
          titulo: texto(dados.get("titulo")),
          descricao: detalhes || null,
          data: texto(dados.get("data")) || null,
          horario: texto(dados.get("horario")) || null,
          status: "PENDENTE",
        }),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      evento.currentTarget.reset()
      setCliente(null)
      setClienteBusca("")
      setOportunidadeId("")
      setTipo("FOLLOW_UP")
      setSucesso(negociacaoSelecionada
        ? "Atividade registrada e vinculada à oportunidade, proposta e pedido disponíveis."
        : "Atividade registrada no histórico do cliente.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar a atividade.")
    } finally {
      setSalvando(false)
    }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6">
    <div className="mx-auto max-w-3xl">
      <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Nova atividade</h1></div></header>
      <section className="mb-4 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><div className="flex items-center gap-3"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">{visita ? <MapPinned/> : <ClipboardCheck/>}</span><div><strong className="block text-lg">Uma única criação para todas as interações</strong><span className="text-sm text-slate-400">A atividade pode ser vinculada ao cliente e à negociação completa.</span></div></div></section>
      {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">{sucesso}</div>}
      {carregando ? <div className="grid min-h-72 place-items-center"><Loader2 className="animate-spin text-cyan-300" /></div> : <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
        <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Cliente</span><input value={clienteBusca} onChange={(e) => { setClienteBusca(e.target.value); setCliente(null); setOportunidadeId("") }} placeholder="Digite ao menos 2 letras" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/>{sugestoes.length > 0 && <div className="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((item) => <button type="button" key={item.id} onClick={() => { setCliente(item); setClienteBusca(item.nome); setOportunidadeId("") }} className="block w-full border-b border-[#16325c] px-4 py-3 text-left last:border-0"><strong>{item.nome}</strong>{item.codigo && <span className="ml-2 text-xs text-slate-400">{item.codigo}</span>}</button>)}</div>}</label>
        <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Negociação relacionada</span><select value={oportunidadeId} onChange={(e) => setOportunidadeId(e.target.value)} disabled={!cliente} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4 disabled:opacity-60"><option value="">Interação geral com o cliente</option>{negociacoesDoCliente.map((item) => <option key={item.oportunidade_id} value={item.oportunidade_id}>{item.titulo} — {item.etapa}{item.proposta_numero ? ` — proposta ${item.proposta_numero}` : ""}{item.pedido_numero ? ` — pedido ${item.pedido_numero}` : ""}</option>)}</select>{cliente && negociacoesDoCliente.length === 0 && <span className="mt-2 block text-xs text-slate-400">Sem negociação aberta; a atividade será vinculada somente ao cliente.</span>}</label>
        <label><span className="mb-2 block text-sm text-slate-300">Tipo de atividade</span><select value={tipo} onChange={(e) => setTipo(e.target.value)} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4">{tipos.map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}</select></label>
        <Campo name="titulo" label={visita ? "Objetivo da visita" : "Título"} required />
        <Campo name="data" label="Data" type="date" required />
        <Campo name="horario" label="Horário" type="time" />
        {visita && <><Campo name="local" label="Endereço / local" required /><Campo name="participantes" label="Participantes" /><Campo name="resultado_esperado" label="Resultado esperado" /></>}
        <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição</span><textarea name="descricao" rows={5} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4" /></label>
        <Campo name="proxima_acao" label="Próxima ação" />
        <button disabled={salvando} className="h-12 rounded-2xl bg-cyan-500 font-semibold text-slate-950 disabled:opacity-60">{salvando ? <span className="inline-flex items-center gap-2"><Loader2 className="animate-spin" size={18}/>Salvando...</span> : "Salvar atividade"}</button>
      </form>}
    </div>
  </main>
}

function Campo({ name, label, type = "text", required = false }: { name: string; label: string; type?: string; required?: boolean }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4" /></label>
}
