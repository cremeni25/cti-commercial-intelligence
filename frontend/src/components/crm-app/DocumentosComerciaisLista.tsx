"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, FileText, Loader2, PackageCheck, Search } from "lucide-react"

type Registro = Record<string, unknown>

function texto(valor: unknown, padrao = "—") {
  const resultado = String(valor ?? "").trim()
  return resultado || padrao
}

function moeda(valor: unknown) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export default function DocumentosComerciaisLista({ tipo }: { tipo: "propostas" | "pedidos" }) {
  const [registros, setRegistros] = useState<Registro[]>([])
  const [busca, setBusca] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const propostas = tipo === "propostas"
  const titulo = propostas ? "Propostas comerciais" : "Pedidos comerciais"
  const subtitulo = propostas ? "Emissão, aceite e conversão em pedido" : "Acompanhamento e situação de envio"
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

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR")
    if (!termo) return registros
    return registros.filter((item) => `${texto(item.numero)} ${texto(item.cliente_nome)} ${texto(item.equipamento)} ${texto(item.status_documento || item.status)}`.toLocaleLowerCase("pt-BR").includes(termo))
  }, [busca, registros])

  return <main className="min-h-[100dvh] bg-[#020817] px-4 py-5 pb-24 text-white sm:px-6">
    <div className="mx-auto max-w-5xl">
      <header className="mb-5 flex items-center gap-3">
        <Link href="/crm-app" className="grid size-11 place-items-center rounded-2xl border border-[#16325c] bg-[#091a33] text-cyan-300"><ArrowLeft size={20}/></Link>
        <div><p className="text-xs uppercase tracking-[.24em] text-cyan-400">CTI CRM</p><h1 className="text-2xl font-bold">{titulo}</h1><p className="text-sm text-slate-400">{subtitulo}</p></div>
      </header>
      <div className="relative mb-4"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={busca} onChange={(e)=>setBusca(e.target.value)} placeholder="Buscar número, cliente, equipamento ou status" className="h-12 w-full rounded-2xl border border-[#16325c] bg-[#07162b] pl-11 pr-4"/></div>
      {erro && <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-red-200">{erro}</div>}
      {carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : filtrados.length === 0 ? <div className="rounded-3xl border border-dashed border-[#24466f] p-8 text-center text-slate-400">Nenhum registro encontrado.</div> : <div className="space-y-3">{filtrados.map((item) => {
        const id = texto(item.id, "")
        const status = texto(item.status_documento || item.status).replaceAll("_", " ")
        const href = propostas ? `/crm-app/propostas/${id}` : `/crm-app/pedidos/${id}`
        const acao = propostas && String(item.status_documento || "").toUpperCase() === "ACEITA" ? "Revisar e converter em pedido" : propostas ? "Abrir proposta" : "Acompanhar pedido"
        return <Link key={id} href={href} className="flex items-center gap-4 rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <span className="rounded-2xl bg-cyan-950/50 p-3 text-cyan-300"><Icone size={22}/></span>
          <span className="min-w-0 flex-1"><strong className="block truncate">{texto(item.numero, propostas ? "Proposta em elaboração" : "Pedido")}</strong><span className="mt-1 block text-sm text-slate-300">{texto(item.cliente_nome)} · {texto(item.equipamento)}</span><span className="mt-1 block text-xs text-slate-500">{status} · {moeda(item.valor)} · {acao}</span></span>
        </Link>
      })}</div>}
    </div>
  </main>
}
