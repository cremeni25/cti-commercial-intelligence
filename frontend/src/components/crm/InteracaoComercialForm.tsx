"use client"

import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { Building2, Check, Loader2, Search, UserRound } from "lucide-react"
import { useAuth } from "@/core/auth"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Contexto = "CLIENTE" | "PARCEIRO"
type Resultado = "LEAD" | "OPORTUNIDADE" | "SEM_CONTINUIDADE"
type Cliente = { id: string; nome: string; cidade: string; estado: string; cnpj: string }
type Props = { superficie: "app" | "web"; tipoInicial?: string }

const TIPOS = [
  ["VISITA_PRESENCIAL", "Visita"],
  ["LIGACAO", "Ligação"],
  ["WHATSAPP", "WhatsApp"],
  ["EMAIL", "E-mail"],
  ["REUNIAO", "Reunião"],
  ["FOLLOW_UP", "Follow-up"],
] as const

function texto(v: unknown) { return String(v ?? "").trim() }
function chave(v: unknown) { return texto(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase() }
function digitos(v: unknown) { return texto(v).replace(/\D/g, "") }

export default function InteracaoComercialForm({ superficie, tipoInicial = "FOLLOW_UP" }: Props) {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [contexto, setContexto] = useState<Contexto>("CLIENTE")
  const [busca, setBusca] = useState("")
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [tipo, setTipo] = useState(tipoInicial)
  const [parceiroNome, setParceiroNome] = useState("")
  const [parceiroTipo, setParceiroTipo] = useState("PARCEIRO_COMERCIAL")
  const [parceiroOrganizacao, setParceiroOrganizacao] = useState("")
  const [descricao, setDescricao] = useState("")
  const [resultado, setResultado] = useState<Resultado>("LEAD")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [cadastroAberto, setCadastroAberto] = useState(false)
  const [consultandoCnpj, setConsultandoCnpj] = useState(false)
  const [novoCnpj, setNovoCnpj] = useState("")
  const [novoNome, setNovoNome] = useState("")
  const [novaCidade, setNovaCidade] = useState("")
  const [novoEstado, setNovoEstado] = useState("")
  const envioRef = useRef(false)

  async function carregarClientes() {
    const resposta = await fetchCrmSeguroProxy("crm-seguro/clientes", { cache: "no-store" })
    const dados = await resposta.json().catch(() => [])
    if (!resposta.ok) throw new Error(texto((dados as Registro).detail) || "Não foi possível carregar os clientes.")
    const lista = (Array.isArray(dados) ? dados : []).map((i: Registro) => ({
      id: texto(i.id),
      nome: texto(i.nome || i.razao_social || i.nome_fantasia),
      cidade: texto(i.cidade || i.municipio),
      estado: texto(i.estado || i.uf).toUpperCase(),
      cnpj: texto(i.cnpj || i.cnpj_cpf || i.documento),
    })).filter((i: Cliente) => i.id && i.nome)
    setClientes(lista)
    return lista
  }

  useEffect(() => {
    let ativo = true
    const params = new URLSearchParams(window.location.search)
    const tipoUrl = chave(params.get("tipo"))
    const clienteUrl = texto(params.get("cliente"))
    queueMicrotask(() => { if (TIPOS.some(([codigo]) => codigo === tipoUrl)) setTipo(tipoUrl) })
    void carregarClientes().then((lista) => {
      if (!ativo || !clienteUrl) return
      const encontrado = lista.find((i) => i.id === clienteUrl || chave(i.nome) === chave(clienteUrl))
      if (encontrado) { setCliente(encontrado); setBusca(encontrado.nome) }
    }).catch((e) => { if (ativo) setErro(e instanceof Error ? e.message : "Não foi possível carregar os clientes.") }).finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = busca.trim()
    if (cliente || termo.length < 2) return []
    const t = chave(termo), cnpj = digitos(termo)
    return clientes.filter((i) => chave(i.nome).includes(t) || (cnpj && digitos(i.cnpj).includes(cnpj))).slice(0, 10)
  }, [busca, cliente, clientes])

  async function consultarCnpj() {
    const cnpj = digitos(novoCnpj)
    if (cnpj.length !== 14) return setErro("Informe um CNPJ com 14 dígitos.")
    setConsultandoCnpj(true); setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-app/clientes/cnpj/${encodeURIComponent(cnpj)}`, { cache: "no-store" })
      const retorno = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(retorno.detail) || `Consulta CNPJ: HTTP ${resposta.status}`)
      if (retorno.status === "CLIENTE_EXISTENTE") {
        const c = (retorno.cliente || {}) as Registro
        const encontrado = clientes.find((i) => i.id === texto(c.id)) || { id: texto(c.id), nome: texto(c.nome), cidade: texto(c.cidade), estado: texto(c.estado), cnpj: texto(c.cnpj) }
        if (encontrado.id && encontrado.nome) { setCliente(encontrado); setBusca(encontrado.nome); setCadastroAberto(false) }
        return
      }
      const d = (retorno.dados || {}) as Registro
      setNovoNome(texto(d.nome || d.razao_social)); setNovaCidade(texto(d.cidade || d.municipio)); setNovoEstado(texto(d.estado || d.uf).toUpperCase()); setNovoCnpj(texto(d.cnpj) || cnpj)
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível consultar o CNPJ.") } finally { setConsultandoCnpj(false) }
  }

  async function cadastrarCliente() {
    if (!novoNome.trim() || digitos(novoCnpj).length !== 14 || !novaCidade.trim() || novoEstado.trim().length !== 2) return setErro("Confirme CNPJ, nome, cidade e UF do novo cliente.")
    setSalvando(true); setErro("")
    try {
      const resposta = await fetchCrmSeguroProxy("crm-seguro/clientes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome: novoNome.trim(), cnpj: digitos(novoCnpj), cidade: novaCidade.trim(), estado: novoEstado.trim().toUpperCase(), categoria: "TRANSPORTADORA" }) })
      const retorno = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(retorno.detail) || `Cadastro: HTTP ${resposta.status}`)
      const c = (retorno.cliente || {}) as Registro
      const novo: Cliente = { id: texto(c.id), nome: texto(c.nome) || novoNome.trim(), cidade: texto(c.cidade) || novaCidade.trim(), estado: texto(c.estado).toUpperCase() || novoEstado.trim().toUpperCase(), cnpj: texto(c.cnpj) || digitos(novoCnpj) }
      if (!novo.id) throw new Error("O CTI não confirmou o identificador do novo cliente.")
      setClientes((atuais) => [...atuais.filter((i) => i.id !== novo.id), novo]); setCliente(novo); setBusca(novo.nome); setCadastroAberto(false)
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível cadastrar o cliente.") } finally { setSalvando(false) }
  }

  async function salvar(evento: FormEvent) {
    evento.preventDefault()
    if (envioRef.current || !usuario?.id) return
    if (contexto === "CLIENTE" && !cliente) return setErro("Selecione ou cadastre o cliente.")
    if (contexto === "PARCEIRO" && !parceiroNome.trim()) return setErro("Informe com quem foi a interação.")
    if (resultado === "OPORTUNIDADE" && contexto !== "CLIENTE") return setErro("Para abrir uma oportunidade é necessário identificar o cliente. O contato com parceiro/pessoa pode permanecer como lead em acompanhamento.")

    envioRef.current = true; setSalvando(true); setErro("")
    try {
      const rotulo = TIPOS.find(([codigo]) => codigo === tipo)?.[1] || "Interação"
      const pessoa = contexto === "CLIENTE" ? cliente!.nome : parceiroNome.trim()
      let oportunidadeId: string | null = null

      if (resultado === "OPORTUNIDADE" && cliente) {
        const oportunidadeResp = await fetchCrmSeguroProxy("crm-seguro/cliente-oportunidade", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
          cliente: { id: cliente.id, nome: cliente.nome, cidade: cliente.cidade || null, estado: cliente.estado || null },
          oportunidade: { responsavel_id: String(usuario.id), titulo: `Oportunidade · ${cliente.nome}`, descricao: descricao.trim() || `${rotulo} com evolução comercial.`, valor_estimado: 0, probabilidade: 20, municipio: cliente.cidade || null, estado: cliente.estado || null },
        }) })
        const op = await oportunidadeResp.json().catch(() => ({})) as Registro
        if (!oportunidadeResp.ok) throw new Error(texto(op.detail) || `Oportunidade: HTTP ${oportunidadeResp.status}`)
        const oportunidade = (op.oportunidade || {}) as Registro
        oportunidadeId = texto(oportunidade.id) || null
        if (!oportunidadeId) throw new Error("A oportunidade foi criada sem identificação.")
      }

      const agora = new Date()
      const atividadeResp = await fetchCrmSeguroProxy("crm-seguro/atividades", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        cliente_id: contexto === "CLIENTE" ? cliente!.id : null,
        parceiro_nome: contexto === "PARCEIRO" ? parceiroNome.trim() : null,
        parceiro_tipo: contexto === "PARCEIRO" ? parceiroTipo : null,
        parceiro_organizacao: contexto === "PARCEIRO" ? parceiroOrganizacao.trim() || null : null,
        oportunidade_id: oportunidadeId,
        usuario_id: String(usuario.id),
        tipo,
        titulo: `${rotulo} · ${pessoa}`,
        descricao: descricao.trim() || null,
        data: agora.toISOString().slice(0, 10),
        horario: agora.toTimeString().slice(0, 5),
        status: resultado === "LEAD" ? "PENDENTE" : "CONCLUIDA",
      }) })
      const atividade = await atividadeResp.json().catch(() => ({})) as Registro
      if (!atividadeResp.ok) throw new Error(texto(atividade.detail) || `Interação: HTTP ${atividadeResp.status}`)

      if (oportunidadeId) window.location.href = superficie === "app" ? `/crm-app/oportunidades/${encodeURIComponent(oportunidadeId)}` : `/oportunidades/${encodeURIComponent(oportunidadeId)}`
      else window.location.href = superficie === "app" ? "/crm-app/agenda" : "/atividades"
    } catch (e) { envioRef.current = false; setErro(e instanceof Error ? e.message : "Não foi possível registrar a interação.") } finally { setSalvando(false) }
  }

  return <form onSubmit={salvar} className="mx-auto w-full max-w-4xl space-y-4">
    {erro && <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}

    <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6">
      <p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">1 · Com quem?</p>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <button type="button" onClick={() => { setContexto("CLIENTE"); setResultado("LEAD") }} className={`min-h-14 rounded-2xl border px-3 font-semibold ${contexto === "CLIENTE" ? "border-cyan-400 bg-cyan-500 text-slate-950" : "border-[#24466f] bg-[#020817] text-slate-300"}`}><Building2 className="mr-2 inline" size={18}/>Cliente</button>
        <button type="button" onClick={() => { setContexto("PARCEIRO"); setCliente(null); setBusca(""); setResultado("LEAD") }} className={`min-h-14 rounded-2xl border px-3 font-semibold ${contexto === "PARCEIRO" ? "border-cyan-400 bg-cyan-500 text-slate-950" : "border-[#24466f] bg-[#020817] text-slate-300"}`}><UserRound className="mr-2 inline" size={18}/>Parceiro / pessoa</button>
      </div>

      {contexto === "CLIENTE" ? <div className="mt-4">
        {carregando ? <div className="flex min-h-14 items-center text-slate-400"><Loader2 className="mr-2 animate-spin" size={18}/>Carregando clientes...</div> : cliente ? <div className="flex items-center justify-between rounded-2xl border border-emerald-900 bg-emerald-950/20 p-4"><div><strong className="block">{cliente.nome}</strong><span className="text-sm text-slate-400">{[cliente.cidade, cliente.estado].filter(Boolean).join(" · ")}</span></div><button type="button" onClick={() => { setCliente(null); setBusca("") }} className="rounded-xl border border-[#24466f] px-3 py-2 text-sm">Trocar</button></div> : <div className="relative"><Search className="absolute left-4 top-4 text-slate-500" size={19}/><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Nome ou CNPJ do cliente" className="min-h-14 w-full rounded-2xl border border-[#24466f] bg-[#020817] pl-12 pr-4 text-base"/>{sugestoes.length > 0 && <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-[#24466f] bg-[#07162b] shadow-2xl">{sugestoes.map((i) => <button key={i.id} type="button" onClick={() => { setCliente(i); setBusca(i.nome) }} className="flex min-h-14 w-full items-center justify-between border-b border-[#16325c] px-4 text-left last:border-0"><span>{i.nome}</span><Check size={17} className="text-cyan-400"/></button>)}</div>}</div>}
        {!cliente && !cadastroAberto && <button type="button" onClick={() => setCadastroAberto(true)} className="mt-3 text-sm font-semibold text-cyan-300">Cliente não cadastrado? Cadastrar pelo CNPJ</button>}
        {cadastroAberto && <div className="mt-4 rounded-2xl border border-cyan-900 bg-[#020817] p-4"><p className="font-semibold">Cadastro rápido de cliente</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><input value={novoCnpj} onChange={(e) => setNovoCnpj(e.target.value)} placeholder="CNPJ" className="h-12 rounded-xl border border-[#24466f] bg-[#07162b] px-3"/><button type="button" onClick={consultarCnpj} disabled={consultandoCnpj} className="h-12 rounded-xl border border-cyan-700 text-cyan-200">{consultandoCnpj ? "Consultando..." : "Consultar e preencher"}</button><input value={novoNome} onChange={(e) => setNovoNome(e.target.value)} placeholder="Razão social / nome" className="h-12 rounded-xl border border-[#24466f] bg-[#07162b] px-3 sm:col-span-2"/><input value={novaCidade} onChange={(e) => setNovaCidade(e.target.value)} placeholder="Cidade" className="h-12 rounded-xl border border-[#24466f] bg-[#07162b] px-3"/><input value={novoEstado} onChange={(e) => setNovoEstado(e.target.value.toUpperCase().slice(0,2))} placeholder="UF" className="h-12 rounded-xl border border-[#24466f] bg-[#07162b] px-3"/></div><div className="mt-3 flex gap-2"><button type="button" onClick={cadastrarCliente} disabled={salvando} className="rounded-xl bg-cyan-500 px-4 py-2 font-bold text-slate-950">Cadastrar e selecionar</button><button type="button" onClick={() => setCadastroAberto(false)} className="rounded-xl border border-[#24466f] px-4 py-2">Cancelar</button></div></div>}
      </div> : <div className="mt-4 grid gap-3 sm:grid-cols-2"><input value={parceiroNome} onChange={(e) => setParceiroNome(e.target.value)} placeholder="Nome da pessoa / parceiro" className="h-12 rounded-xl border border-[#24466f] bg-[#020817] px-4 sm:col-span-2"/><select value={parceiroTipo} onChange={(e) => setParceiroTipo(e.target.value)} className="h-12 rounded-xl border border-[#24466f] bg-[#020817] px-4"><option value="PARCEIRO_COMERCIAL">Parceiro comercial</option><option value="PESSOA_FISICA">Pessoa física</option><option value="CONTATO_EXTERNO">Contato externo</option></select><input value={parceiroOrganizacao} onChange={(e) => setParceiroOrganizacao(e.target.value)} placeholder="Empresa / organização (opcional)" className="h-12 rounded-xl border border-[#24466f] bg-[#020817] px-4"/></div>}
    </section>

    <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6"><p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">2 · Como foi a interação?</p><div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">{TIPOS.map(([codigo, label]) => <button key={codigo} type="button" onClick={() => setTipo(codigo)} className={`min-h-14 rounded-2xl border px-3 text-sm font-semibold ${tipo === codigo ? "border-cyan-400 bg-cyan-500 text-slate-950" : "border-[#24466f] bg-[#020817] text-slate-300"}`}>{label}</button>)}</div></section>

    <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6"><p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">3 · O que aconteceu?</p><textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} rows={5} placeholder="Resumo objetivo e próximo passo." className="mt-4 w-full rounded-2xl border border-[#24466f] bg-[#020817] p-4 text-base leading-6"/></section>

    <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5 sm:p-6"><p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">4 · Qual foi o resultado?</p><div className="mt-4 grid gap-2 md:grid-cols-3"><button type="button" onClick={() => setResultado("LEAD")} className={`rounded-2xl border p-4 text-left ${resultado === "LEAD" ? "border-cyan-400 bg-cyan-950/40" : "border-[#24466f] bg-[#020817]"}`}><strong className="block">Acompanhar</strong><span className="mt-1 block text-sm text-slate-400">Ainda não há proposta. Mantém como lead e próxima ação.</span></button><button type="button" disabled={contexto !== "CLIENTE"} onClick={() => setResultado("OPORTUNIDADE")} className={`rounded-2xl border p-4 text-left disabled:opacity-40 ${resultado === "OPORTUNIDADE" ? "border-emerald-400 bg-emerald-950/30" : "border-[#24466f] bg-[#020817]"}`}><strong className="block">Virou oportunidade</strong><span className="mt-1 block text-sm text-slate-400">Existe potencial comercial. O CTI abre a oportunidade automaticamente.</span></button><button type="button" onClick={() => setResultado("SEM_CONTINUIDADE")} className={`rounded-2xl border p-4 text-left ${resultado === "SEM_CONTINUIDADE" ? "border-slate-400 bg-slate-900" : "border-[#24466f] bg-[#020817]"}`}><strong className="block">Sem continuidade</strong><span className="mt-1 block text-sm text-slate-400">Registra no histórico sem criar pendência comercial.</span></button></div></section>

    <button disabled={salvando} className="min-h-16 w-full rounded-2xl bg-cyan-500 px-5 text-lg font-bold text-slate-950 disabled:opacity-50">{salvando ? "Registrando..." : resultado === "OPORTUNIDADE" ? "Registrar e abrir oportunidade" : "Registrar interação"}</button>
  </form>
}
