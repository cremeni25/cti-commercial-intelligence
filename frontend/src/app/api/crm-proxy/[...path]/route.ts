import { NextRequest, NextResponse } from "next/server"

import { API_URL } from "@/lib/api"

async function encaminhar(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params
  const destino = new URL(`${API_URL}/${path.join("/")}`)
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

  const corpo = await resposta.text()
  return new NextResponse(corpo, {
    status: resposta.status,
    headers: { "content-type": resposta.headers.get("content-type") || "application/json" },
  })
}

export const GET = encaminhar
export const POST = encaminhar
export const PUT = encaminhar
export const PATCH = encaminhar
export const DELETE = encaminhar
