"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CircleAlert, CircleCheck, Clock3, FileText, Loader2, PackageCheck, Search, WalletCards } from "lucide-react"

type Registro = Record<string, unknown>
type FiltroPedido = "TODOS" | "PENDENTES" | "ENVIADOS" | "FALHAS"

function texto(valor: unknown, padrao = "—") {
  const resultado = String(valor ?? "").trim()
  return resultado || padrao
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function dataBr(valor: unknown) {
  const bruto = texto(valor, "")
  if (!bruto) return "—"
  const data = new Date(bruto)
  return Number.isNaN(data.getTime()) ? bruto : data.toLocaleDateString("pt-BR")
}

function statusPedido(item: Registro) {
  return texto(item.status_envio_carrier || item.status_envio || item.status, "NAO_ENVIADO").toUpperCase()
}

function grupoPedido(item: Registro): Exclude<FiltroPedido, "TODOS"> {
  const status = statusPedido(item)
  if (["ENVIADO", "REENVIADO", "CONFIRMADO"].includes(status)) return "ENVIADOS"
  if (status === "FALHA") return "FALHAS"
  return "PENDENTES"
}

export default function DocumentosComerciaisLista({ tipo }: { tipo: "propostas" | "pedidos" }) {
  const [registros, setRegistros] = useState<Registro[]>([])
  const [busca, setBusca] = useState("")
  const [filtroPedido, setFiltroPedido] = useState<FiltroPedido>("TODOS")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const propostas = tipo === "propostas"
  const titulo = propostas ? "Propostas comerciais" : "Acompanhamento de pedidos"
  const subtitulo = propostas ? "Emissão, aceite e conversão em pedido" : "Situação operacional, envio e valor dos pedidos comerciais"
  const Icone = propostas ? FileText : PackageCheck

  useEffect(() => {
    fetch(`/api/crm-proxy/crm-documentos/${tipo}`, { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => [])
        if (!resposta.ok) throw new Error(String(payload.detail || `Falha ${resposta.status}`))
        setRegistros(Array.isArray(payload) ? payload : [])
      })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Não foi possível carregar os documentos."))
      .finally(() => setCarregando(false))
  }, [tipo])

  const resumoPedidos = useMemo(() => {
    const enviados = registros.filter((item) => grupoPedido(item) === "ENVIADOS").length
    const falhas = registros.filter((item) => grupoPedido(item) === "FALHAS").length
    const pendentes = registros.filter((item) => grupoPedido(item) === "PENDENTES").length
    const valor = registros.reduce((total, item) => total + Number(item.valor || 0), 0)
    return { total: registros.length, enviados, falhas, pendentes, valor }
  }, [registros])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    return registros.filter((item) => {
      if (!propostas && filtroPedido !== "TODOS" && grupoPedido(item) !== filtroPedido) return false
      if (!termo) return true
      const status = propostas ? texto(item.status_documento || item.status) : statusPedido(item)
      return `${texto(item.numero)} ${texto(item.cliente_nome)} ${texto(item.equipamento)} ${status}`
        .toLocaleLowerCase("pt-BR")
        .includes(termo)
    })
  }, [busca, filtroPedido, propostas, registros])

  const filtros: Array<{ id: FiltroPedido; label: string; valor: number }> = [
    { id: "TODOS", label: "Todos", valor: resumoPedidos.total },
    { id: "PENDENTES", label: "A acompanhar", valor: resumoPedidos.pendentes },
    { id: "ENVIADOS", label: "Enviados", valor: resumoPedidos.enviados },
    { id: "FALHAS", label: "Falhas", valor: resumoPedidos.falhas },
  ]

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-6xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">{titulo}</h1><p className="text-sm text-slate-400">{subtitulo}</p></div>
      </header>

      {!propostas && !carregando && !erro && <>
        <section className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Indicador icone={<PackageCheck size={18}/>} label="Pedidos" valor={String(resumoPedidos.total)} detalhe="volume total"/>
          <Indicador icone={<Clock3 size={18}/>} label="A acompanhar" valor={String(resumoPedidos.pendentes)} detalhe="aguardando avanço"/>
          <Indicador icone={<CircleCheck size={18}/>} label="Enviados" valor={String(resumoPedidos.enviados)} detalhe="envio registrado"/>
          <Indicador icone={<WalletCards size={18}/>} label="Valor em pedidos" valor={moeda(resumoPedidos.valor)} detalhe={resumoPedidos.falhas ? `${resumoPedidos.falhas} com falha de envio` : "sem falhas de envio"}/>
        </section>

        <section className="mb-4 flex flex-wrap gap-2">
          {filtros.map((filtro) => <button key={filtro.id} type="button" onClick={() => setFiltroPedido(filtro.id)} className={`rounded-full border px-4 py-2 text-sm ${filtroPedido === filtro.id ? "border-cyan-500 bg-cyan-950/50 text-cyan-200" : "border-[#24466f] bg-[#07162b] text-slate-400"}`}>{filtro.label} <strong className="ml-1">{filtro.valor}</strong></button>)}
        </section>
      </>}

      <div className="relative mb-4"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e)=>setBusca(e.target.value)} placeholder="Buscar número, cliente, equipamento ou status" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></div>
      {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : filtrados.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum registro encontrado.</div> : <div className="space-y-3">{filtrados.map((item) => {
        const id = texto(item.id, "")
        const status = propostas ? texto(item.status_documento || item.status).replaceAll("_", " ") : statusPedido(item).replaceAll("_", " ")
        const href = propostas ? `/crm-app/propostas/${id}` : `/crm-app/pedidos/${id}`
        const acao = propostas && String(item.status_documento || "").toUpperCase() === "ACEITA" ? "Revisar e converter em pedido" : propostas ? "Abrir proposta" : "Abrir acompanhamento"
        const enviadoEm = !propostas ? texto(item.enviado_carrier_em, "") : ""
        const falha = !propostas && grupoPedido(item) === "FALHAS"
        return <Link key={id} href={href} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5 transition hover:border-cyan-700">
          <span className={`rounded-2xl p-3 ${falha ? "bg-red-950/50 text-red-300" : "bg-cyan-950/50 text-cyan-300"}`}>{falha ? <CircleAlert size={22}/> : <Icone size={22}/>}</span>
          <span className="min-w-0 flex-1"><strong className="block truncate">{texto(item.numero, propostas ? "Proposta em elaboração" : "Pedido")}</strong><span className="mt-1 block text-sm text-slate-300">{texto(item.cliente_nome)} · {texto(item.equipamento)}{!propostas && item.quantidade ? ` · ${texto(item.quantidade)} un.` : ""}</span><span className="mt-1 block text-xs text-slate-500">{status} · {moeda(item.valor)}{enviadoEm ? ` · enviado ${dataBr(enviadoEm)}` : ""} · {acao}</span></span>
        </Link>
      })}</div>}
    </div>
  </main>
}

function Indicador({ icone, label, valor, detalhe }: { icone: React.ReactNode; label: string; valor: string; detalhe: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><div className="flex items-center gap-2 text-cyan-300">{icone}<span className="text-xs uppercase tracking-[.12em] text-slate-500">{label}</span></div><strong className="mt-3 block text-xl sm:text-2xl">{valor}</strong><span className="mt-1 block text-xs text-slate-500">{detalhe}</span></div>
}
