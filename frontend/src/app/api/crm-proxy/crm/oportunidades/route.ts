import { NextRequest, NextResponse } from "next/server"

import { API_URL } from "@/lib/api"

type Oportunidade = Record<string, unknown>

function pertenceAoApp(item: Oportunidade): boolean {
  const origem = String(item.origem || "").toUpperCase()
  const descricao = String(item.descricao || "").toUpperCase()
  return origem === "CRM_APP" || descricao.includes("[CONTEXTO CTI]")
}

async function encaminhar(request: NextRequest) {
  const destino = new URL(`${API_URL}/crm/oportunidades`)
  request.nextUrl.searchParams.forEach((valor, chave) => destino.searchParams.set(chave, valor))

  const headers = new Headers()
  const contentType = request.headers.get("content-type")
  if (contentType) headers.set("content-type", contentType)

  const resposta = await fetch(destino, {
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

  const normalizados = Array.isArray(dados)
    ? dados.map((item) => {
        const oportunidade = item as Oportunidade
        return pertenceAoApp(oportunidade)
          ? { ...oportunidade, origem: "CRM_APP" }
          : oportunidade
      })
    : dados

  return NextResponse.json(normalizados, { status: resposta.status })
}

export const GET = encaminhar
export const POST = encaminhar
export const PUT = encaminhar
export const PATCH = encaminhar
export const DELETE = encaminhar
