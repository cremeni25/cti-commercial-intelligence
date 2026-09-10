"use client"

import { useEffect, useMemo, useState } from "react"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

type Registro = Record<string, unknown>
type Sugestao = { email: string; usos: number; ultima: string }

type Cache = { carregadoEm: number; sugestoes: Sugestao[] }
let cache: Cache | null = null
let carregamento: Promise<Sugestao[]> | null = null

function listaEmails(valor: unknown): string[] {
  if (!Array.isArray(valor)) return []
  return valor.map((item) => String(item || "").trim().toLowerCase()).filter((item) => item.includes("@"))
}

function extrair(lista: unknown): Sugestao[] {
  if (!Array.isArray(lista)) return []
  const mapa = new Map<string, Sugestao>()
  for (const bruto of lista as Registro[]) {
    const snapshot = bruto?.snapshot_dados && typeof bruto.snapshot_dados === "object" ? bruto.snapshot_dados as Registro : null
    const envio = snapshot?.envio_email && typeof snapshot.envio_email === "object" ? snapshot.envio_email as Registro : null
    if (!envio) continue
    const ultima = String(envio.enviado_em || bruto.enviada_em || bruto.updated_at || bruto.created_at || "")
    for (const email of [...listaEmails(envio.para || envio.destinatarios), ...listaEmails(envio.cc), ...listaEmails(envio.cco)]) {
      const atual = mapa.get(email)
      if (!atual) mapa.set(email, { email, usos: 1, ultima })
      else {
        atual.usos += 1
        if (ultima > atual.ultima) atual.ultima = ultima
      }
    }
  }
  return [...mapa.values()].sort((a, b) => b.usos - a.usos || b.ultima.localeCompare(a.ultima))
}

async function buscarSugestoes(): Promise<Sugestao[]> {
  const agora = Date.now()
  if (cache && agora - cache.carregadoEm < 300_000) return cache.sugestoes
  if (carregamento) return carregamento
  carregamento = (async () => {
    try {
      const resposta = await fetchCrmSeguroProxy("crm-seguro/propostas", { cache: "no-store" })
      const payload = await resposta.json().catch(() => [])
      if (!resposta.ok) return []
      const sugestoes = extrair(payload)
      cache = { carregadoEm: Date.now(), sugestoes }
      return sugestoes
    } finally {
      carregamento = null
    }
  })()
  return carregamento
}

function termoAtual(valor: string): string {
  const partes = valor.split(/[;,\n]+/)
  return (partes.at(-1) || "").trim().toLowerCase()
}

function selecionar(valor: string, email: string): string {
  const partes = valor.split(/([;,\n]+)/)
  let ultimoConteudo = -1
  for (let i = partes.length - 1; i >= 0; i -= 1) {
    if (!/^[;,\n]+$/.test(partes[i])) {
      ultimoConteudo = i
      break
    }
  }
  if (ultimoConteudo < 0) return email
  partes[ultimoConteudo] = email
  return partes.join("").replace(/\s*([;,])\s*/g, "$1 ").trim()
}

export default function EmailsFrequentes({ valor, alterar }: { valor: string; alterar: (valor: string) => void }) {
  const [sugestoes, setSugestoes] = useState<Sugestao[]>([])

  useEffect(() => {
    let ativo = true
    void buscarSugestoes().then((itens) => { if (ativo) setSugestoes(itens) })
    return () => { ativo = false }
  }, [])

  const termo = termoAtual(valor)
  const correspondencias = useMemo(() => {
    if (termo.length < 2) return []
    const existentes = new Set(valor.split(/[;,\n]+/).map((item) => item.trim().toLowerCase()).filter(Boolean))
    return sugestoes
      .filter((item) => !existentes.has(item.email) || item.email.includes(termo))
      .filter((item) => item.email.includes(termo))
      .slice(0, 5)
  }, [sugestoes, termo, valor])

  if (!correspondencias.length) return null

  return <div className="mt-1 overflow-hidden rounded-xl border border-[#24466f] bg-[#061326] shadow-xl">
    {correspondencias.map((item) => <button
      key={item.email}
      type="button"
      onMouseDown={(evento) => evento.preventDefault()}
      onClick={() => alterar(selecionar(valor, item.email))}
      className="flex w-full items-center justify-between gap-3 border-b border-[#173354] px-3 py-2 text-left text-sm text-cyan-100 last:border-b-0 hover:bg-[#0b2038]"
    >
      <span className="truncate">{item.email}</span>
      {item.usos > 1 ? <span className="shrink-0 text-[11px] text-slate-500">{item.usos}x</span> : null}
    </button>)}
  </div>
}
