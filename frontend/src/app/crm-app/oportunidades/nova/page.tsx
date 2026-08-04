"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import { ArrowLeft, BriefcaseBusiness, CheckCircle2, Loader2, Search } from "lucide-react"
import { useAuth } from "@/core/auth"

type Registro = Record<string, unknown>
type Cliente = {
  id: string
  nome: string
  cidade: string
  estado: string
  ddd: string
  sub_regiao: string
  segmento: string
}

const produtosPorLinha: Record<string, string[]> = {
  TRAILER: ["X4-7500", "X4-7700", "Vector HE19", "Vector 8600MT"],
  "DIESEL TRUCK": ["Supra 1150", "Supra 850", "Supra 850MT", "Supra 750"],
  "DIRECT DRIVE": ["CM500", "CM400", "CM280", "Xarios 350", "Xarios 600", "D7", "D7 AE", "D6", "D6 AE"],
}

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

function normalizarCliente(item: Registro): Cliente | null {
  const nome = texto(item.razao_social || item.nome || item.nome_fantasia || item.empresa || item.cliente)
  if (!nome) return null
  return {
    id: texto(item.id || item.cliente_id || item.uuid),
    nome,
    cidade: texto(item.cidade || item.municipio),
    estado: texto(item.estado || item.uf).toUpperCase(),
    ddd: texto(item.ddd),
    sub_regiao: texto(item.sub_regiao || item.subRegiao),
    segmento: texto(item.segmento) || "TRANSPORTADOR",
  }
}

export default function NovaOportunidadePage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [buscaCliente, setBuscaCliente] = useState("")
  const [clienteSelecionado, setClienteSelecionado] = useState<Cliente | null>(null)
  const [linhas, setLinhas] = useState<string[]>([])
  const [equipamentos, setEquipamentos] = useState<string[]>([])
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState("")

  useEffect(() => {
    let ativo = true
    fetch("/api/crm-proxy/modulos/clientes?contexto=viena-sp&periodo=TODO_HISTORICO", { cache: "no-store" })
      .then(async (resposta) => (resposta.ok ? resposta.json() : []))
      .then((dados) => {
        if (!ativo) return
        const lista = (Array.isArray(dados) ? dados : [])
          .map((item) => normalizarCliente(item as Registro))
          .filter(Boolean) as Cliente[]
        setClientes(lista.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")))
      })
      .catch(() => {
        if (ativo) setClientes([])
      })
    return () => { ativo = false }
  }, [])

  const sugestoes = useMemo(() => {
    const termo = buscaCliente.trim().toLocaleLowerCase("pt-BR")
    if (termo.length < 2 || clienteSelecionado) return []
    return clientes.filter((cliente) => `${cliente.nome} ${cliente.cidade} ${cliente.estado}`.toLocaleLowerCase("pt-BR").includes(termo)).slice(0, 10)
  }, [buscaCliente, clienteSelecionado, clientes])

  const equipamentosDisponiveis = useMemo(
    () => [...new Set(linhas.flatMap((linha) => produtosPorLinha[linha] || []))],
    [linhas],
  )

  function alternarLinha(linha: string) {
    setLinhas((atuais) => {
      const novas = atuais.includes(linha) ? atuais.filter((item) => item !== linha) : [...atuais, linha]
      const permitidos = new Set(novas.flatMap((item) => produtosPorLinha[item] || []))
      setEquipamentos((itens) => itens.filter((item) => permitidos.has(item)))
      return novas
    })
  }

  function alternarEquipamento(equipamento: string) {
    setEquipamentos((atuais) => atuais.includes(equipamento) ? atuais.filter((item) => item !== equipamento) : [...atuais, equipamento])
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const formularioElemento = evento.currentTarget
    setErro("")
    setSucesso("")

    const userId = texto(usuario?.id)
    if (!userId) {
      setErro("Não foi possível confirmar o usuário autenticado.")
      return
    }

    const formulario = new FormData(formularioElemento)
    const clienteNome = (clienteSelecionado?.nome || buscaCliente).trim()
    const titulo = texto(formulario.get("titulo"))
    const municipio = texto(formulario.get("municipio"))
    const uf = texto(formulario.get("uf")).toUpperCase()
    const quantidade = Math.max(1, Number(formulario.get("quantidade") || 1))

    if (!clienteNome || !titulo || !municipio || uf.length !== 2 || equipamentos.length === 0) {
      setErro("Preencha cliente, título, município, UF e ao menos um equipamento.")
      return
    }

    const descricaoBase = texto(formulario.get("descricao"))
    const descricao = [
      descricaoBase,
      "[CONTEXTO CTI]",
      `linhas: ${linhas.join(", ")}`,
      `equipamentos: ${equipamentos.join(", ")}`,
      `quantidade: ${quantidade}`,
      `municipio: ${municipio}`,
      `uf: ${uf}`,
      `ddd: ${texto(formulario.get("ddd"))}`,
      `sub_regiao: ${texto(formulario.get("sub_regiao"))}`,
    ].filter(Boolean).join("\n")

    const payload = {
      cliente: {
        id: clienteSelecionado?.id || null,
        nome: clienteNome,
        cidade: municipio,
        estado: uf,
        segmento: clienteSelecionado?.segmento || "TRANSPORTADOR",
        ddd: texto(formulario.get("ddd")) || null,
        sub_regiao: texto(formulario.get("sub_regiao")) || null,
      },
      oportunidade: {
        responsavel_id: userId,
        titulo,
        descricao,
        valor_estimado: Number(formulario.get("valor_estimado") || 0),
        probabilidade: Number(formulario.get("probabilidade") || 0),
        data_fechamento_prevista: texto(formulario.get("data_fechamento_prevista")) || null,
        linha_equipamentos: linhas.join(", "),
        equipamento: equipamentos.join(", "),
        municipio,
        estado: uf,
        ddd: texto(formulario.get("ddd")) || null,
        sub_regiao: texto(formulario.get("sub_regiao")) || null,
      },
    }

    setSalvando(true)
    try {
      const resposta = await fetch("/api/crm-proxy/crm-app/cliente-oportunidade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const detalhe = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(texto(detalhe.detail) || `Falha ${resposta.status}`)
      formularioElemento.reset()
      setBuscaCliente("")
      setClienteSelecionado(null)
      setLinhas([])
      setEquipamentos([])
      setSucesso("Oportunidade criada e sincronizada com o CTI.")
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível criar a oportunidade.")
    } finally {
      setSalvando(false)
    }
  }

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-30 border-b border-[#16325c] bg-[#061126]/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center gap-3">
          <Link href="/crm-app/oportunidades" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20} /></Link>
          <div><p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-400">CTI CRM</p><h1 className="text-xl font-bold">Nova oportunidade</h1><p className="text-xs text-slate-400">Cadastro direto no núcleo comercial</p></div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-4 py-5">
        <section className="mb-4 rounded-3xl border border-[#16325c] bg-[#0a2242] p-5">
          <div className="flex items-center gap-3"><div className="grid size-12 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-300"><BriefcaseBusiness /></div><div><p className="text-xs text-slate-400">Operação comercial</p><h2 className="text-lg font-bold">Abrir nova negociação</h2></div></div>
        </section>

        {erro && <div className="mb-4 rounded-2xl border border-red-500/50 bg-red-950/30 px-4 py-3 text-sm text-red-200">{erro}</div>}
        {sucesso && <div className="mb-4 flex items-center gap-2 rounded-2xl border border-emerald-500/40 bg-emerald-950/25 px-4 py-3 text-sm text-emerald-200"><CheckCircle2 size={18} />{sucesso}</div>}

        <form onSubmit={salvar} className="space-y-4 rounded-3xl border border-[#16325c] bg-[#071a33] p-5">
          <div className="relative">
            <label className="mb-1 block text-xs text-slate-300">Cliente</label>
            <div className="relative"><Search className="absolute left-3 top-3 text-slate-500" size={17} /><input value={buscaCliente} onChange={(e) => { setBuscaCliente(e.target.value); setClienteSelecionado(null) }} placeholder="Digite ao menos 2 letras" className="w-full rounded-xl border border-[#28507c] bg-[#020d1f] py-3 pl-10 pr-3 text-sm outline-none focus:border-cyan-400" /></div>
            {sugestoes.length > 0 && <div className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-xl border border-[#28507c] bg-[#071a33] shadow-xl">{sugestoes.map((cliente) => <button type="button" key={`${cliente.id}-${cliente.nome}`} onClick={() => { setClienteSelecionado(cliente); setBuscaCliente(cliente.nome) }} className="block w-full border-b border-[#16325c] px-4 py-3 text-left text-sm hover:bg-cyan-500/10"><strong>{cliente.nome}</strong><span className="ml-2 text-xs text-slate-400">{cliente.cidade}/{cliente.estado}</span></button>)}</div>}
            {!clienteSelecionado && buscaCliente.trim().length >= 2 && sugestoes.length === 0 && <p className="mt-1 text-xs text-slate-400">Cliente não localizado: o nome digitado poderá ser cadastrado junto com a oportunidade.</p>}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-xs text-slate-300">Título da oportunidade<input name="titulo" required className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">Valor estimado total<input name="valor_estimado" type="number" min="0" step="0.01" defaultValue="0" className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">Chance estimada de fechamento (%)<input name="probabilidade" type="number" min="0" max="100" defaultValue="0" className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">Fechamento previsto<input name="data_fechamento_prevista" type="date" className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
          </div>

          <fieldset className="rounded-2xl border border-[#28507c] p-4"><legend className="px-2 text-xs text-slate-300">Linhas de produto Carrier</legend><div className="flex flex-wrap gap-2">{Object.keys(produtosPorLinha).map((linha) => <label key={linha} className={`cursor-pointer rounded-xl border px-3 py-2 text-sm ${linhas.includes(linha) ? "border-cyan-400 bg-cyan-500/10 text-cyan-200" : "border-[#16325c] bg-[#020d1f]"}`}><input type="checkbox" checked={linhas.includes(linha)} onChange={() => alternarLinha(linha)} className="mr-2" />{linha}</label>)}</div></fieldset>

          <fieldset className="rounded-2xl border border-[#28507c] p-4"><legend className="px-2 text-xs text-slate-300">Equipamentos Carrier</legend>{equipamentosDisponiveis.length === 0 ? <p className="text-sm text-slate-500">Selecione primeiro uma linha.</p> : <div className="flex flex-wrap gap-2">{equipamentosDisponiveis.map((equipamento) => <label key={equipamento} className={`cursor-pointer rounded-xl border px-3 py-2 text-sm ${equipamentos.includes(equipamento) ? "border-cyan-400 bg-cyan-500/10 text-cyan-200" : "border-[#16325c] bg-[#020d1f]"}`}><input type="checkbox" checked={equipamentos.includes(equipamento)} onChange={() => alternarEquipamento(equipamento)} className="mr-2" />{equipamento}</label>)}</div>}</fieldset>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-xs text-slate-300">Quantidade total de equipamentos<input name="quantidade" type="number" min="1" defaultValue="1" className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">Município<input name="municipio" required defaultValue={clienteSelecionado?.cidade || ""} key={`cidade-${clienteSelecionado?.id || "novo"}`} className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">UF<input name="uf" required maxLength={2} defaultValue={clienteSelecionado?.estado || ""} key={`uf-${clienteSelecionado?.id || "novo"}`} className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm uppercase outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300">DDD<input name="ddd" defaultValue={clienteSelecionado?.ddd || ""} key={`ddd-${clienteSelecionado?.id || "novo"}`} className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
            <label className="text-xs text-slate-300 sm:col-span-2">Sub-região<input name="sub_regiao" defaultValue={clienteSelecionado?.sub_regiao || ""} key={`sub-${clienteSelecionado?.id || "novo"}`} placeholder="Ex.: Região Leste ou Oeste" className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>
          </div>

          <label className="text-xs text-slate-300">Descrição / resultado esperado<textarea name="descricao" rows={6} className="mt-1 w-full rounded-xl border border-[#28507c] bg-[#020d1f] px-3 py-3 text-sm outline-none focus:border-cyan-400" /></label>

          <button disabled={salvando} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-4 font-bold text-[#00111f] disabled:opacity-60">{salvando ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}{salvando ? "Salvando..." : "Salvar no CTI"}</button>
        </form>
      </div>
    </main>
  )
}
