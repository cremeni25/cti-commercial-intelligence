import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = "https://cti-backend-5ugf.onrender.com"
const METODOS_COM_CORPO = new Set(["POST", "PUT", "PATCH", "DELETE"])

type ContextoRota = { params: Promise<{ path: string[] }> }

async function encaminhar(request: NextRequest, contexto: ContextoRota) {
  const { path } = await contexto.params
  const destino = new URL(`${BACKEND_URL}/${path.join("/")}`)
  request.nextUrl.searchParams.forEach((valor, chave) => destino.searchParams.append(chave, valor))

  const headers = new Headers()
  for (const chave of ["authorization", "content-type", "accept", "x-requested-with"]) {
    const valor = request.headers.get(chave)
    if (valor) headers.set(chave, valor)
  }
  if (!headers.has("accept")) headers.set("accept", "application/json")

  const resposta = await fetch(destino, {
    method: request.method,
    headers,
    body: METODOS_COM_CORPO.has(request.method) ? await request.arrayBuffer() : undefined,
    cache: "no-store",
    redirect: "follow",
  })

  const corpo = await resposta.arrayBuffer()
  const retornoHeaders = new Headers({
    "cache-control": "no-store",
    "x-cti-backend": BACKEND_URL,
  })
  const contentType = resposta.headers.get("content-type")
  if (contentType) retornoHeaders.set("content-type", contentType)
  const contentDisposition = resposta.headers.get("content-disposition")
  if (contentDisposition) retornoHeaders.set("content-disposition", contentDisposition)

  return new NextResponse(corpo, {
    status: resposta.status,
    headers: retornoHeaders,
  })
}

export const GET = encaminhar
export const POST = encaminhar
export const PUT = encaminhar
export const PATCH = encaminhar
export const DELETE = encaminhar
