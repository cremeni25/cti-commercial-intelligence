"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, BriefcaseBusiness, CheckCircle2, Loader2, Search, Tag, UserPlus } from "lucide-react"
import { useAuth } from "@/core/auth"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Cliente = { id: string; nome: string; razaoSocial: string; nomeFantasia: string; cnpj: string; cidade: string; estado: string; ddd: string; sub_regiao: string; segmento: string }
type PrecoVigente = { preco_cheio?: number; tabela_codigo?: string; vigencia_inicio?: string }
type EquipamentoCatalogo = { codigo: string; linha_produto: string; nome_comercial: string; configuracao?: string; preco_vigente?: PrecoVigente | null }
type ItemNegociado = { quantidade: number; desconto: number; precoNegociado: number }

const tiposOportunidade = [
  ["PROSPECCAO", "Prospecção comercial"],
  ["COTACAO", "Cotação / tomada de preços"],
  ["RENOVACAO_FROTA", "Renovação ou ampliação de frota"],
  ["SUBSTITUICAO", "Substituição de equipamento"],
  ["PROJETO", "Projeto em desenvolvimento"],
  ["CAMPANHA_COMERCIAL", "Campanha comercial"],
  ["TESTE_CAMPO", "Teste de campo / homologação"],
  ["OUTRO", "Outro"],
] as const

function texto(valor: unknown): string { return String(valor ?? "").trim() }
function chave(valor: unknown): string { return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleUpperCase("pt-BR") }
function somenteDigitos(valor: unknown): string { return texto(valor).replace(/\D/g, "") }
function formatarCnpj(valor: string): string { const d = somenteDigitos(valor); return d.length === 14 ? d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5") : valor }
function moeda(valor: number): string { return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }
function moedaInput(valor: number): string { return Number(valor || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function lerMoeda(valor: string): number { const digitos = valor.replace(/\D/g, ""); return digitos ? Number(digitos) / 100 : 0 }
function precoTabela(item?: EquipamentoCatalogo): number { return Number(item?.preco_vigente?.preco_cheio || 0) }
function campanhaTecnica(valor: string): string { return texto(valor).toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Z0-9_-]+/g, "_").replace(/^_+|_+$/g, "") }
function normalizarCliente(item: Registro): Cliente | null {
  const razaoSocial = texto(item.razao_social)
  const nomeFantasia = texto(item.nome_fantasia)
  const nome = texto(item.nome || razaoSocial || nomeFantasia || item.empresa || item.cliente)
  if (!nome) return null
  return { id: texto(item.id || item.cliente_id || item.uuid), nome, razaoSocial, nomeFantasia, cnpj: texto(item.cnpj || item.cnpj_cpf || item.documento), cidade: texto(item.cidade || item.municipio), estado: texto(item.estado || item.uf).toUpperCase(), ddd: texto(item.ddd), sub_regiao: texto(item.sub_regiao || item.subRegiao), segmento: texto(item.segmento || item.categoria) || "TRANSPORTADORA" }
}

export default function NovaOportunidadePage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [catalogo, setCatalogo] = useState<EquipamentoCatalogo[]>([])
  const [buscaCliente, setBuscaCliente] = useState("")
  const [clienteSelecionado, setClienteSelecionado] = useState<Cliente | null>(null)
  const [linhas, setLinhas] = useState<string[]>([])
  const [itens, setItens] = useState<Record<string, ItemNegociado>>({})
  const [tipo, setTipo] = useState("")
  const [campanha, setCampanha] = useState("HOMOLOGACAO_COMERCIAL_01")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  useEffect(() => {
    let ativo = true
    const params = new URLSearchParams(window.location.search)
    const clienteContexto = texto(params.get("cliente"))
    const nomeContexto = texto(params.get("nome"))
    void Promise.all([
      fetch("/api/crm-proxy/crm-app/clientes", { cache: "no-store" }).then(async (r) => r.ok ? r.json() : []),
      fetch("/api/crm-proxy/catalogo-comercial/equipamentos", { cache: "no-store" }).then(async (r) => { const p = await r.json().catch(() => []); if (!r.ok) throw new Error(texto((p as Registro).detail) || `Catálogo: HTTP ${r.status}`); return p }),
    ]).then(([dadosClientes, dadosCatalogo]) => {
      if (!ativo) return
      const listaClientes = (Array.isArray(dadosClientes) ? dadosClientes : []).map((item) => normalizarCliente(item as Registro)).filter(Boolean).sort((a, b) => (a as Cliente).nome.localeCompare((b as Cliente).nome, "pt-BR")) as Cliente[]
      const listaCatalogo = (Array.isArray(dadosCatalogo) ? dadosCatalogo : []).map((item: Registro) => ({ codigo: texto(item.codigo), linha_produto: texto(item.linha_produto), nome_comercial: texto(item.nome_comercial || item.equipamento), configuracao: texto(item.configuracao), preco_vigente: item.preco_vigente && typeof item.preco_vigente === "object" ? item.preco_vigente as PrecoVigente : null })).filter((item) => item.codigo && item.nome_comercial)
      setClientes(listaClientes)
      setCatalogo(listaCatalogo)
      const inicial = listaClientes.find((item) => clienteContexto && item.id === clienteContexto) || listaClientes.find((item) => nomeContexto && chave(item.nome) === chave(nomeContexto))
      if (inicial) { setClienteSelecionado(inicial); setBuscaCliente(inicial.nome) }
      else if (nomeContexto) setBuscaCliente(nomeContexto)
    }).catch((falha) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar clientes e catálogo.") }).finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = buscaCliente.trim()
    if (termo.length < 2 || clienteSelecionado) return []
    const termoTexto = chave(termo)
    const termoCnpj = somenteDigitos(termo)
    return clientes.filter((cliente) => {
      const nomes = [cliente.nome, cliente.razaoSocial, cliente.nomeFantasia].filter(Boolean).map(chave)
      return nomes.some((valor) => valor.includes(termoTexto)) || (termoCnpj.length > 0 && somenteDigitos(cliente.cnpj).includes(termoCnpj))
    }).slice(0, 10)
  }, [buscaCliente, clienteSelecionado, clientes])
  const linhasDisponiveis = useMemo(() => [...new Set(catalogo.map((item) => item.linha_produto).filter(Boolean))].sort(), [catalogo])
  const equipamentosDisponiveis = useMemo(() => catalogo.filter((item) => linhas.includes(item.linha_produto)), [catalogo, linhas])
  const itensSelecionados = useMemo(() => Object.keys(itens).map((codigo) => catalogo.find((item) => item.codigo === codigo)).filter(Boolean) as EquipamentoCatalogo[], [catalogo, itens])
  const totalTabela = useMemo(() => itensSelecionados.reduce((soma, equipamento) => soma + precoTabela(equipamento) * (itens[equipamento.codigo]?.quantidade || 0), 0), [itens, itensSelecionados])
  const totalNegociado = useMemo(() => itensSelecionados.reduce((soma, equipamento) => soma + (itens[equipamento.codigo]?.precoNegociado || 0) * (itens[equipamento.codigo]?.quantidade || 0), 0), [itens, itensSelecionados])
  const economia = Math.max(0, totalTabela - totalNegociado)

  function alternarLinha(linha: string) {
    setLinhas((atuais) => atuais.includes(linha) ? atuais.filter((item) => item !== linha) : [...atuais, linha])
  }

  function alternarEquipamento(equipamento: EquipamentoCatalogo) {
    const tabela = precoTabela(equipamento)
    if (tabela <= 0) return setErro(`${equipamento.nome_comercial} não possui preço vigente no catálogo.`)
    setErro("")
    setItens((atuais) => {
      const novos = { ...atuais }
      if (novos[equipamento.codigo]) delete novos[equipamento.codigo]
      else novos[equipamento.codigo] = { quantidade: 1, desconto: 0, precoNegociado: tabela }
      return novos
    })
  }

  function atualizarQuantidade(codigo: string, quantidade: number) {
    setItens((atuais) => ({ ...atuais, [codigo]: { ...atuais[codigo], quantidade: Math.max(1, Math.round(quantidade || 1)) } }))
  }

  function atualizarDesconto(equipamento: EquipamentoCatalogo, descontoBruto: number) {
    const desconto = Math.max(0, Math.min(100, Number.isFinite(descontoBruto) ? descontoBruto : 0))
    const negociado = precoTabela(equipamento) * (1 - desconto / 100)
    setItens((atuais) => ({ ...atuais, [equipamento.codigo]: { ...atuais[equipamento.codigo], desconto, precoNegociado: negociado } }))
  }

  function atualizarPrecoNegociado(equipamento: EquipamentoCatalogo, valorDigitado: string) {
    const tabela = precoTabela(equipamento)
    const negociado = Math.max(0, Math.min(tabela, lerMoeda(valorDigitado)))
    const desconto = tabela > 0 ? Math.max(0, Math.min(100, (1 - negociado / tabela) * 100)) : 0
    setItens((atuais) => ({ ...atuais, [equipamento.codigo]: { ...atuais[equipamento.codigo], precoNegociado: negociado, desconto } }))
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const elemento = evento.currentTarget
    setErro(""); setSucesso("")
    const userId = texto(usuario?.id)
    if (!userId) return setErro("Não foi possível confirmar o usuário autenticado.")
    const form = new FormData(elemento)
    const clienteNome = (clienteSelecionado?.nome || buscaCliente).trim()
    const titulo = texto(form.get("titulo"))
    const municipio = texto(form.get("municipio"))
    const uf = texto(form.get("uf")).toUpperCase()
    const outroTipo = texto(form.get("outro_tipo"))
    const campanhaNome = campanhaTecnica(campanha)
    if (!clienteNome || !tipo || !titulo || !municipio || uf.length !== 2 || itensSelecionados.length === 0) return setErro("Preencha cliente, tipo, título, município, UF e ao menos um equipamento com tabela vigente.")
    if (tipo === "OUTRO" && !outroTipo) return setErro("Informe o tipo da oportunidade.")
    if (tipo === "TESTE_CAMPO" && !campanhaNome) return setErro("Informe a campanha de teste de campo.")

    const rotuloTipo = tiposOportunidade.find(([codigo]) => codigo === tipo)?.[1] || outroTipo
    const quantidadeTotal = itensSelecionados.reduce((soma, equipamento) => soma + (itens[equipamento.codigo]?.quantidade || 0), 0)
    const descricao = [
      tipo === "TESTE_CAMPO" ? "TESTE DE CAMPO" : "",
      tipo === "TESTE_CAMPO" ? `[CAMPANHA: ${campanhaNome}]` : "",
      `Tipo da oportunidade: ${tipo === "OUTRO" ? outroTipo : rotuloTipo}`,
      tipo === "CAMPANHA_COMERCIAL" ? `Campanha comercial: ${texto(form.get("campanha_comercial"))}` : "",
      texto(form.get("descricao")),
      "[CONTEXTO CTI]",
      `linhas: ${[...new Set(itensSelecionados.map((item) => item.linha_produto))].join(", ")}`,
      `equipamentos: ${itensSelecionados.map((item) => item.nome_comercial).join(", ")}`,
      `quantidade: ${quantidadeTotal}`,
      `municipio: ${municipio}`,
      `uf: ${uf}`,
      `ddd: ${texto(form.get("ddd"))}`,
      `sub_regiao: ${texto(form.get("sub_regiao"))}`,
    ].filter(Boolean).join("\n")

    const payload = {
      cliente: { id: clienteSelecionado?.id || null, nome: clienteNome, cidade: municipio, estado: uf, segmento: clienteSelecionado?.segmento || "TRANSPORTADORA", ddd: texto(form.get("ddd")) || null, sub_regiao: texto(form.get("sub_regiao")) || null },
      oportunidade: { responsavel_id: userId, titulo, descricao, valor_estimado: totalNegociado, probabilidade: Number(form.get("probabilidade") || 0), data_fechamento_prevista: texto(form.get("data_fechamento_prevista")) || null, linha_equipamentos: [...new Set(itensSelecionados.map((item) => item.linha_produto))].join(", "), equipamento: itensSelecionados.map((item) => item.nome_comercial).join(", "), municipio, estado: uf, ddd: texto(form.get("ddd")) || null, sub_regiao: texto(form.get("sub_regiao")) || null },
    }

    setSalvando(true)
    try {
      const resposta = await fetchCrmSeguroProxy("crm-seguro/cliente-oportunidade", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      const detalhe = await resposta.json().catch(() => ({})) as Registro
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      const oportunidade = detalhe.oportunidade && typeof detalhe.oportunidade === "object" ? detalhe.oportunidade as Registro : {}
      const oportunidadeId = texto(oportunidade.id)
      if (!oportunidadeId) throw new Error("A oportunidade foi criada sem identificação para vincular os itens comerciais.")

      for (const equipamento of itensSelecionados) {
        const negociacao = itens[equipamento.codigo]
        const itemResposta = await fetch(`/api/crm-proxy/catalogo-comercial/oportunidades/${encodeURIComponent(oportunidadeId)}/itens`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ equipamento_codigo: equipamento.codigo, quantidade: negociacao.quantidade, desconto_percentual: Number(negociacao.desconto.toFixed(4)), ordem: itensSelecionados.indexOf(equipamento) }),
        })
        const itemRetorno = await itemResposta.json().catch(() => ({})) as Registro
        if (!itemResposta.ok) throw new Error(`Oportunidade criada, mas não foi possível vincular ${equipamento.nome_comercial}: ${texto(itemRetorno.detail) || `HTTP ${itemResposta.status}`}`)
      }

      elemento.reset(); setBuscaCliente(""); setClienteSelecionado(null); setLinhas([]); setItens({}); setTipo(""); setCampanha("HOMOLOGACAO_COMERCIAL_01")
      setSucesso(`${tipo === "TESTE_CAMPO" ? `Teste registrado na campanha ${campanhaNome}` : "Oportunidade criada"}. Valor negociado: ${moeda(totalNegociado)}. Tabela, desconto e itens foram gravados no núcleo comercial.`)
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Não foi possível criar a oportunidade.") }
    finally { setSalvando(false) }
  }

  const input = "mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400"
  if (carregando) return <main className="grid min-h-[100dvh] place-items-center bg-[#020817] text-cyan-300"><Loader2 className="animate-spin" /></main>

  return <main className="min-h-[100dvh] bg-[#020817] pb-28 text-white">
    <header className="sticky top-0 z-30 border-b border-[#16325c] bg-[#061126]/95 px-4 py-3"><div className="mx-auto flex w-full max-w-3xl items-center gap-3"><Link href="/crm-app/oportunidades" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20} /></Link><div><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-xl font-bold">Nova oportunidade</h1><p className="text-xs text-slate-400">Cliente, produto, preço e desconto em um único fluxo</p></div></div></header>
    <div className="mx-auto w-full max-w-3xl px-4 py-5">
      <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#0a2242] p-5"><div className="flex items-center gap-3"><div className="grid size-12 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-300"><BriefcaseBusiness /></div><div><p className="text-xs text-slate-400">Operação comercial</p><h2 className="text-lg font-bold">Abrir nova negociação</h2><p className="mt-1 text-xs text-slate-400">O preço vem da tabela oficial e o desconto fica explícito no item comercial.</p></div></div></section>
      {erro && <div className="mb-4 rounded-2xl border border-red-500/50 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</div>}
      {sucesso && <div className="mb-4 flex items-center gap-2 rounded-2xl border border-emerald-500/40 bg-emerald-950/25 px-4 py-3 text-sm text-emerald-200"><CheckCircle2 size={18} />{sucesso}</div>}
      <form onSubmit={salvar} className="space-y-5 rounded-3xl border border-[#16325c] bg-[#071a33] p-5">
        <section><div className="mb-2 flex items-center justify-between"><label className="text-xs font-semibold text-slate-300">Cliente</label><Link href="/crm-app/clientes/nova" className="flex items-center gap-1 text-xs font-semibold text-cyan-300"><UserPlus size={14}/>Cadastrar cliente completo</Link></div><div className="relative"><div className="relative"><Search className="absolute left-3 top-3 text-slate-500" size={17} /><input value={buscaCliente} onChange={(e) => { setBuscaCliente(e.target.value); setClienteSelecionado(null) }} placeholder="Nome, razão social, fantasia ou CNPJ" className="w-full rounded-xl border border-[#28507c] bg-[#020d1f] py-3 pl-10 pr-3 text-sm" /></div>{sugestoes.length > 0 && <div className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-xl border border-[#28507c] bg-[#071a33]">{sugestoes.map((cliente) => <button type="button" key={`${cliente.id}-${cliente.nome}`} onClick={() => { setClienteSelecionado(cliente); setBuscaCliente(cliente.nome) }} className="block w-full border-b border-[#16325c] px-4 py-3 text-left text-sm"><strong>{cliente.nome}</strong>{cliente.cnpj&&<span className="ml-2 text-xs text-cyan-300">CNPJ {formatarCnpj(cliente.cnpj)}</span>}<span className="ml-2 text-xs text-slate-400">{cliente.cidade}{cliente.estado?`/${cliente.estado}`:""}</span></button>)}</div>}</div>{clienteSelecionado && <p className="mt-2 text-xs text-emerald-300">Cliente selecionado: {clienteSelecionado.nome}{clienteSelecionado.cnpj?` · CNPJ ${formatarCnpj(clienteSelecionado.cnpj)}`:""}</p>}</section>

        <section className="grid gap-4 sm:grid-cols-2">
          <label className="text-xs text-slate-300">Tipo da oportunidade<select required value={tipo} onChange={(e) => setTipo(e.target.value)} className={input}><option value="">Selecione</option>{tiposOportunidade.map(([codigo, nome]) => <option key={codigo} value={codigo}>{nome}</option>)}</select></label>
          {tipo === "TESTE_CAMPO" && <label className="text-xs text-amber-200">Campanha de teste<input value={campanha} onChange={(e) => setCampanha(e.target.value)} className={`${input} border-amber-700`} /></label>}
          {tipo === "CAMPANHA_COMERCIAL" && <label className="text-xs text-slate-300">Nome da campanha comercial<input name="campanha_comercial" required className={input} /></label>}
          {tipo === "OUTRO" && <label className="text-xs text-slate-300">Informe o tipo<input name="outro_tipo" required className={input} /></label>}
          <label className="text-xs text-slate-300">Título da oportunidade<input name="titulo" required className={input} /></label>
          <label className="text-xs text-slate-300">Chance estimada de fechamento (%)<input name="probabilidade" type="number" min="0" max="100" defaultValue="0" className={input} /></label>
          <label className="text-xs text-slate-300">Fechamento previsto<input name="data_fechamento_prevista" type="date" className={input} /></label>
        </section>

        <fieldset className="rounded-2xl border border-[#28507c] p-4"><legend className="px-2 text-xs text-slate-300">1. Linha de produto</legend><div className="flex flex-wrap gap-2">{linhasDisponiveis.map((linha) => <button type="button" key={linha} onClick={() => alternarLinha(linha)} className={`rounded-xl border px-3 py-2 text-sm ${linhas.includes(linha) ? "border-cyan-400 bg-cyan-500/10 text-cyan-200" : "border-[#16325c] bg-[#020d1f] text-slate-300"}`}>{linha}</button>)}</div></fieldset>
        <fieldset className="rounded-2xl border border-[#28507c] p-4"><legend className="px-2 text-xs text-slate-300">2. Equipamento</legend>{equipamentosDisponiveis.length === 0 ? <p className="text-sm text-slate-500">Selecione uma linha para ver os equipamentos e preços vigentes.</p> : <div className="grid gap-2 sm:grid-cols-2">{equipamentosDisponiveis.map((equipamento) => { const tabela = precoTabela(equipamento), selecionado = Boolean(itens[equipamento.codigo]); return <button type="button" key={equipamento.codigo} disabled={tabela <= 0} onClick={() => alternarEquipamento(equipamento)} className={`rounded-2xl border p-3 text-left ${selecionado ? "border-cyan-400 bg-cyan-500/10" : "border-[#16325c] bg-[#020d1f] disabled:opacity-40"}`}><strong className="block text-sm">{equipamento.nome_comercial}</strong><span className="mt-1 block text-xs text-slate-400">{equipamento.codigo}</span><span className="mt-2 block text-sm font-semibold text-cyan-300">{tabela > 0 ? moeda(tabela) : "Sem preço vigente"}</span></button>})}</div>}</fieldset>

        {itensSelecionados.length > 0 && <section className="space-y-3"><div className="flex items-center gap-2"><Tag size={17} className="text-cyan-300"/><h3 className="font-semibold">3. Negociação de preço</h3></div>{itensSelecionados.map((equipamento) => { const negociacao = itens[equipamento.codigo], tabela = precoTabela(equipamento), total = negociacao.precoNegociado * negociacao.quantidade; return <article key={equipamento.codigo} className="rounded-2xl border border-[#28507c] bg-[#020d1f] p-4"><div className="mb-3"><strong>{equipamento.nome_comercial}</strong><p className="text-xs text-slate-400">Tabela: {moeda(tabela)}{equipamento.preco_vigente?.tabela_codigo ? ` · ${equipamento.preco_vigente.tabela_codigo}` : ""}{equipamento.preco_vigente?.vigencia_inicio ? ` · vigente desde ${equipamento.preco_vigente.vigencia_inicio}` : ""}</p></div><div className="grid gap-3 sm:grid-cols-3"><label className="text-xs text-slate-300">Quantidade<input type="number" min="1" value={negociacao.quantidade} onChange={(e) => atualizarQuantidade(equipamento.codigo, Number(e.target.value))} className={input}/></label><label className="text-xs text-slate-300">Desconto (%)<input type="number" min="0" max="100" step="0.01" value={Number(negociacao.desconto.toFixed(2))} onChange={(e) => atualizarDesconto(equipamento, Number(e.target.value))} className={input}/></label><label className="text-xs text-slate-300">Preço negociado unitário<div className="relative"><span className="absolute left-3 top-[17px] text-sm text-slate-500">R$</span><input inputMode="numeric" value={moedaInput(negociacao.precoNegociado)} onChange={(e) => atualizarPrecoNegociado(equipamento, e.target.value)} className={`${input} pl-10`}/></div></label></div><div className="mt-3 flex items-center justify-between rounded-xl bg-[#071a33] px-3 py-2 text-sm"><span className="text-slate-400">Total negociado</span><strong className="text-emerald-300">{moeda(total)}</strong></div></article>})}</section>}

        {itensSelecionados.length > 0 && <section className="rounded-2xl border border-emerald-900 bg-emerald-950/20 p-4"><div className="grid grid-cols-3 gap-3 text-center"><div><span className="block text-[11px] text-slate-400">Tabela</span><strong className="text-sm">{moeda(totalTabela)}</strong></div><div><span className="block text-[11px] text-slate-400">Desconto</span><strong className="text-sm text-amber-300">{moeda(economia)}</strong></div><div><span className="block text-[11px] text-slate-400">Negociado</span><strong className="text-sm text-emerald-300">{moeda(totalNegociado)}</strong></div></div></section>}

        <section className="grid gap-4 sm:grid-cols-2"><label className="text-xs text-slate-300">Município<input name="municipio" required defaultValue={clienteSelecionado?.cidade || ""} key={`cidade-${clienteSelecionado?.id || "novo"}`} className={input} /></label><label className="text-xs text-slate-300">UF<input name="uf" required maxLength={2} defaultValue={clienteSelecionado?.estado || ""} key={`uf-${clienteSelecionado?.id || "novo"}`} className={input} /></label><label className="text-xs text-slate-300">DDD<input name="ddd" defaultValue={clienteSelecionado?.ddd || ""} key={`ddd-${clienteSelecionado?.id || "novo"}`} className={input} /></label><label className="text-xs text-slate-300">Sub-região<input name="sub_regiao" defaultValue={clienteSelecionado?.sub_regiao || ""} key={`sub-${clienteSelecionado?.id || "novo"}`} placeholder="Ex.: Região Leste ou Oeste" className={input} /></label></section>
        <label className="text-xs text-slate-300">Descrição / resultado esperado<textarea name="descricao" rows={5} placeholder="Objetivo comercial, aplicação ou observações relevantes." className={input} /></label>
        <button disabled={salvando || itensSelecionados.length === 0} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-4 font-bold text-[#00111f] disabled:opacity-60">{salvando ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}{salvando ? "Salvando..." : `Salvar oportunidade · ${moeda(totalNegociado)}`}</button>
      </form>
    </div>
  </main>
}