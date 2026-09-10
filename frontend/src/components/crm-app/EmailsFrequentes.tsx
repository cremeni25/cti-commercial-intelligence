"use client"

import { useEffect, useState } from "react"
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
  return [...mapa.values()].sort((a, b) => b.usos - a.usos || b.ultima.localeCompare(a.ultima)).slice(0, 8)
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

function acrescentar(valor: string, email: string): string {
  const atuais = valor.split(/[;,\n]+/).map((item) => item.trim()).filter(Boolean)
  if (atuais.some((item) => item.toLowerCase() === email.toLowerCase())) return valor
  return [...atuais, email].join("; ")
}

export default function EmailsFrequentes({ valor, alterar }: { valor: string; alterar: (valor: string) => void }) {
  const [sugestoes, setSugestoes] = useState<Sugestao[]>([])

  useEffect(() => {
    let ativo = true
    void buscarSugestoes().then((itens) => { if (ativo) setSugestoes(itens) })
    return () => { ativo = false }
  }, [])

  if (!sugestoes.length) return null
  return <div className="mt-2 flex flex-wrap gap-2">
    {sugestoes.map((item) => <button key={item.email} type="button" onClick={() => alterar(acrescentar(valor, item.email))} className="rounded-full border border-[#24466f] bg-[#061326] px-3 py-1.5 text-xs text-cyan-200 hover:border-cyan-600">
      {item.email}{item.usos > 1 ? ` · ${item.usos}x` : ""}
    </button>)}
  </div>
}
