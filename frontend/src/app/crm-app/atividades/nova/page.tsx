"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { ArrowLeft, Check, ClipboardCheck, Loader2, MapPinned, Search } from "lucide-react"
import { useAuth } from "@/core/auth"
import { ControlledSelect } from "@/components/crm-app/ControlledSelect"

type Cliente = { id: string; nome: string; cidade?: string; estado?: string }
type Negociacao = {
  oportunidade_id: string
  cliente_id: string
  cliente_nome?: string
  titulo: string
  etapa: string
  proposta_id?: string | null
  proposta_numero?: string | null
  pedido_id?: string | null
  pedido_numero?: string | null
  encerrada?: boolean
}
type Registro = Record<string, unknown>

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

const tiposParceiro = [
  ["PESSOA_FISICA", "Pessoa física / contato"],
  ["EMPRESA", "Empresa / parceiro de negócio"],
  ["IMPLEMENTADORA", "Implementadora"],
  ["AUTORIZADA_CARRIER", "Autorizada Carrier"],
  ["FORNECEDOR", "Fornecedor"],
  ["OUTRO", "Outro"],
] as const

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function chave(valor: unknown): string {
  return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR")
}

export default function NovaAtividadePage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [negociacoes, setNegociacoes] = useState<Negociacao[]>([])
  const [clienteBusca, setClienteBusca] = useState("")
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [parceiroNome, setParceiroNome] = useState("")
  const [parceiroTipo, setParceiroTipo] = useState("PESSOA_FISICA")
  const [parceiroOrganizacao, setParceiroOrganizacao] = useState("")
  const [oportunidadeId, setOportunidadeId] = useState("")
  const [tipo, setTipo] = useState("FOLLOW_UP")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")
  const envioEmCursoRef = useRef(false)

  useEffect(() => {
    let ativo = true
    void (async () => {
      setCarregando(true)
      setErro("")
      try {
        const params = new URLSearchParams(window.location.search)
        const clienteContexto = texto(params.get("cliente"))
        const oportunidadeContexto = texto(params.get("oportunidade"))
        const tipoContexto = texto(params.get("tipo")).toUpperCase()
        const [clientesResposta, nucleoResposta] = await Promise.all([
          fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }),
          fetch("/api/crm-proxy/crm/nucleo-comercial", { cache: "no-store" }),
        ])
        const clientesDados = await clientesResposta.json().catch(() => [])
        const nucleoDados = await nucleoResposta.json().catch(() => [])
        if (!clientesResposta.ok) throw new Error(String((clientesDados as Registro).detail || `Clientes: HTTP ${clientesResposta.status}`))
        if (!nucleoResposta.ok) throw new Error(String((nucleoDados as Registro).detail || `Núcleo: HTTP ${nucleoResposta.status}`))
        if (!ativo) return

        const listaClientes = (Array.isArray(clientesDados) ? clientesDados : [])
          .map((item: Registro) => ({
            id: texto(item.id),
            nome: texto(item.nome || item.razao_social || item.nome_fantasia),
            cidade: texto(item.cidade || item.municipio),
            estado: texto(item.estado || item.uf),
          }))
          .filter((item) => item.id && item.nome)
          .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))

        const listaNegociacoes = (Array.isArray(nucleoDados) ? nucleoDados : [])
          .map((item: Registro) => ({
            oportunidade_id: texto(item.oportunidade_id),
            cliente_id: texto(item.cliente_id),
            cliente_nome: texto(item.cliente_nome),
            titulo: texto(item.titulo) || "Oportunidade comercial",
            etapa: texto(item.etapa) || "OPORTUNIDADE",
            proposta_id: texto(item.proposta_id) || null,
            proposta_numero: texto(item.proposta_numero) || null,
            pedido_id: texto(item.pedido_id) || null,
            pedido_numero: texto(item.pedido_numero) || null,
            encerrada: Boolean(item.encerrada),
          }))
          .filter((item) => item.oportunidade_id)

        setClientes(listaClientes)
        setNegociacoes(listaNegociacoes)
        if (tipoContexto && tipos.some(([valor]) => valor === tipoContexto)) setTipo(tipoContexto)

        const negociacaoInicial = oportunidadeContexto
          ? listaNegociacoes.find((item) => item.oportunidade_id === oportunidadeContexto)
          : undefined
        const idClienteInicial = clienteContexto || negociacaoInicial?.cliente_id || ""
        const nomeClienteInicial = negociacaoInicial?.cliente_nome || ""
        const clienteInicial = listaClientes.find((item) => item.id === idClienteInicial)
          || listaClientes.find((item) => nomeClienteInicial && chave(item.nome) === chave(nomeClienteInicial))
        if (clienteInicial) {
          setCliente(clienteInicial)
          setClienteBusca(clienteInicial.nome)
        }
        if (negociacaoInicial) setOportunidadeId(negociacaoInicial.oportunidade_id)
      } catch (falha) {
        if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar clientes e negociações.")
      } finally {
        if (ativo) setCarregando(false)
      }
    })()
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = clienteBusca.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || cliente) return []
    return clientes
      .filter((item) => `${item.nome} ${item.cidade || ""} ${item.estado || ""}`.toLocaleLowerCase("pt-BR").includes(termo))
      .slice(0, 12)
  }, [clienteBusca, cliente, clientes])

  const negociacoesDoCliente = useMemo(
    () => negociacoes.filter((item) => !item.encerrada && (
      item.cliente_id === cliente?.id
      || item.cliente_nome?.toLocaleLowerCase("pt-BR") === cliente?.nome.toLocaleLowerCase("pt-BR")
    )),
    [cliente, negociacoes],
  )

  const opcoesNegociacao = useMemo(
    () => [
      ["", cliente ? "Interação geral com o cliente" : "Sem negociação relacionada"],
      ...negociacoesDoCliente.map((item) => [item.oportunidade_id, `${item.titulo} — ${item.etapa}`] as const),
    ] as const,
    [cliente, negociacoesDoCliente],
  )

  const negociacaoSelecionada = useMemo(
    () => negociacoes.find((item) => item.oportunidade_id === oportunidadeId) || null,
    [negociacoes, oportunidadeId],
  )
  const visita = tipo.startsWith("VISITA")
  const contextoValido = Boolean(cliente || parceiroNome.trim())

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (envioEmCursoRef.current) return
    setErro("")
    setSucesso("")
    if (!contextoValido) return setErro("Selecione um cliente ou informe um parceiro/contato externo.")
    if (!usuario?.id) return setErro("Não foi possível confirmar o usuário autenticado.")

    envioEmCursoRef.current = true
    setSalvando(true)
    const dados = new FormData(evento.currentTarget)
    try {
      const resposta = await fetch("/api/crm-proxy/crm/atividades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: cliente?.id || null,
          parceiro_nome: cliente ? null : parceiroNome.trim(),
          parceiro_tipo: cliente ? null : parceiroTipo,
          parceiro_organizacao: cliente ? null : parceiroOrganizacao.trim() || null,
          oportunidade_id: cliente ? negociacaoSelecionada?.oportunidade_id || null : null,
          proposta_id: cliente ? negociacaoSelecionada?.proposta_id || null : null,
          pedido_id: cliente ? negociacaoSelecionada?.pedido_id || null : null,
          usuario_id: usuario.id,
          tipo,
          titulo: texto(dados.get("titulo")),
          descricao: texto(dados.get("descricao")) || null,
          data: texto(dados.get("data")) || null,
          horario: texto(dados.get("horario")) || null,
          status: "PENDENTE",
        }),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      setSucesso("Atividade registrada com sucesso. Redirecionando para a Central de Atividades...")
      window.location.href = "/crm-app/atividades"
    } catch (falha) {
      envioEmCursoRef.current = false
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar a atividade.")
    } finally {
      setSalvando(false)
    }
  }

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 text-white sm:px-6"><div className="mx-auto max-w-3xl">
    <header className="mb-5 flex items-center gap-3"><Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link><div><p className="text-xs uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">Nova atividade</h1></div></header>
    <section className="mb-4 rounded-3xl border border-[#16325c] bg-gradient-to-br from-[#0a2242] to-[#07162b] p-5"><div className="flex items-center gap-3"><span className="grid size-12 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">{visita ? <MapPinned/> : <ClipboardCheck/>}</span><div><strong className="block text-lg">Uma única criação para todas as interações</strong><span className="text-sm text-slate-400">A atividade pode estar ligada a um cliente/negociação ou a um parceiro de negócio sem cadastro de cliente.</span></div></div></section>
    {erro && <div className="mb-4 rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>}
    {sucesso && <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm text-emerald-200">{sucesso}</div>}
    {carregando ? <div className="grid min-h-72 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : <form onSubmit={salvar} className="grid gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:grid-cols-2">
      <label className="relative sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Cliente cadastrado</span><div className="relative"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={clienteBusca} onChange={(e) => { setClienteBusca(e.target.value); setCliente(null); setOportunidadeId("") }} placeholder="Opcional: digite pelo menos 2 letras do nome" className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-11 pr-4"/></div>{sugestoes.length > 0 && <div className="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((item) => <button type="button" key={item.id} onClick={() => { setCliente(item); setClienteBusca(item.nome); setParceirolimpar(); setOportunidadeId("") }} className="flex w-full items-center justify-between border-b border-[#16325c] px-4 py-3 text-left last:border-0"><span><strong className="block">{item.nome}</strong><small className="text-slate-400">{[item.cidade, item.estado].filter(Boolean).join("/") || "Cliente cadastrado"}</small></span><Check size={16} className="text-cyan-300"/></button>)}</div>}</label>
      <div className="sm:col-span-2 rounded-2xl border border-[#24466f] bg-[#020817]/60 p-4"><div className="mb-3 text-sm text-slate-300">Ou registre a atividade para parceiro de negócio / contato externo</div><div className="grid gap-3 sm:grid-cols-2"><input value={parceiroNome} onChange={(e) => { setParceiroNome(e.target.value); if (e.target.value.trim()) { setCliente(null); setClienteBusca(""); setOportunidadeId("") } }} placeholder="Nome da pessoa ou parceiro" className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4"/><ControlledSelect value={parceiroTipo} onChange={setParceiroTipo} options={tiposParceiro}/><input value={parceiroOrganizacao} onChange={(e) => setParceiroOrganizacao(e.target.value)} placeholder="Empresa/organização (opcional)" className="h-12 rounded-2xl border border-[#24466f] bg-[#020817] px-4 sm:col-span-2"/></div></div>
      {cliente && <div className="sm:col-span-2 rounded-xl border border-emerald-900 bg-emerald-950/20 p-3 text-sm text-emerald-200">Cliente selecionado: <strong>{cliente.nome}</strong>{oportunidadeId ? " · negociação preservada" : ""}</div>}
      {!cliente && parceiroNome.trim() && <div className="sm:col-span-2 rounded-xl border border-cyan-900 bg-cyan-950/20 p-3 text-sm text-cyan-200">Parceiro/contato: <strong>{parceiroNome.trim()}</strong>{parceiroOrganizacao.trim() ? ` · ${parceiroOrganizacao.trim()}` : ""}</div>}
      <div className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Negociação relacionada</span><ControlledSelect value={oportunidadeId} onChange={setOportunidadeId} disabled={!cliente} options={opcoesNegociacao}/><small className="mt-1 block text-slate-500">Para parceiro/contato externo, a atividade segue sem vínculo obrigatório com negociação.</small></div>
      <div><span className="mb-2 block text-sm text-slate-300">Tipo de atividade</span><ControlledSelect value={tipo} onChange={setTipo} options={tipos}/></div>
      <Campo name="titulo" label={visita ? "Objetivo da visita" : "Título"} required/>
      <Campo name="data" label="Data" type="date" required/>
      <Campo name="horario" label="Horário" type="time"/>
      <label className="sm:col-span-2"><span className="mb-2 block text-sm text-slate-300">Descrição</span><textarea name="descricao" rows={5} className="w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4"/></label>
      <button disabled={salvando || !contextoValido} className="sm:col-span-2 h-12 rounded-2xl bg-cyan-500 font-semibold text-slate-950 disabled:opacity-60">{salvando ? "Salvando..." : "Salvar atividade"}</button>
    </form>}
  </div></main>

  function setParceirolimpar() {
    setParceiroNome("")
    setParceiroOrganizacao("")
  }
}

function Campo({ name, label, type = "text", required = false }: { name: string; label: string; type?: string; required?: boolean }) {
  return <label><span className="mb-2 block text-sm text-slate-300">{label}</span><input name={name} type={type} required={required} className="h-12 w-full rounded-2xl border border-[#24466f] bg-[#020817] px-4"/></label>
}
