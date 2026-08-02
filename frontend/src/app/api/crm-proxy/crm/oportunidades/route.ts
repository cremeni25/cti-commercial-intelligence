import { NextRequest, NextResponse } from "next/server"

import { API_URL } from "@/lib/api"

type Oportunidade = Record<string, unknown>

function pertenceAoApp(item: Oportunidade): boolean {
  const origem = String(item.origem || "").toUpperCase()
  const descricao = String(item.descricao || "").toUpperCase()
  return origem === "CRM_APP" || descricao.includes("[CONTEXTO CTI]")
}

function extrairLista(payload: unknown): Oportunidade[] {
  if (Array.isArray(payload)) return payload as Oportunidade[]
  if (payload && typeof payload === "object") {
    const registro = payload as Record<string, unknown>
    for (const chave of ["dados", "itens", "resultado", "oportunidades"]) {
      if (Array.isArray(registro[chave])) return registro[chave] as Oportunidade[]
    }
  }
  return []
}

async function lerComFallback(destino: URL): Promise<Response> {
  const principal = await fetch(destino, { method: "GET", cache: "no-store" })
  if (principal.ok) return principal

  const fallback = new URL(`${API_URL}/crm/nucleo-comercial`)
  destino.searchParams.forEach((valor, chave) => fallback.searchParams.set(chave, valor))
  return fetch(fallback, { method: "GET", cache: "no-store" })
}

async function encaminhar(request: NextRequest) {
  const destino = new URL(`${API_URL}/crm/oportunidades`)
  request.nextUrl.searchParams.forEach((valor, chave) => destino.searchParams.set(chave, valor))

  const headers = new Headers()
  const contentType = request.headers.get("content-type")
  if (contentType) headers.set("content-type", contentType)

  const resposta = request.method === "GET"
    ? await lerComFallback(destino)
    : await fetch(destino, {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.text(),
        cache: "no-store",
      })

  const texto = await resposta.text()
  if (!resposta.ok || request.method !== "GET") {
    return new NextResponse(texto, {
      status: resposta.status,
      headers: { "content-type": resposta.headers.get("content-type") || "application/json" },
    })
  }

  let dados: unknown
  try {
    dados = JSON.parse(texto)
  } catch {
    return new NextResponse(texto, {
      status: resposta.status,
      headers: { "content-type": resposta.headers.get("content-type") || "application/json" },
    })
  }

  const normalizados = extrairLista(dados).map((item) =>
    pertenceAoApp(item) ? { ...item, origem: "CRM_APP" } : item,
  )

  return NextResponse.json(normalizados, { status: 200 })
}

export const GET = encaminhar
export const POST = encaminhar
export const PUT = encaminhar
export const PATCH = encaminhar
export const DELETE = encaminhar
