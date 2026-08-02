import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"

async function encaminhar(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params
  const destino = new URL(`${BACKEND_CTI}/${path.join("/")}`)
  request.nextUrl.searchParams.forEach((valor, chave) =>
    destino.searchParams.set(chave, valor),
  )

  const headers = new Headers()
  const contentType = request.headers.get("content-type")
  if (contentType) headers.set("content-type", contentType)
  const authorization = request.headers.get("authorization")
  if (authorization) headers.set("authorization", authorization)

  try {
    const resposta = await fetch(destino, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method)
        ? undefined
        : await request.text(),
      cache: "no-store",
    })

    const corpo = await resposta.text()
    return new NextResponse(corpo, {
      status: resposta.status,
      headers: {
        "content-type":
          resposta.headers.get("content-type") || "application/json",
      },
    })
  } catch (erro) {
    const detalhe =
      erro instanceof Error ? erro.message : "Falha de comunicação com o backend"
    return NextResponse.json(
      { detail: `CRM App indisponível: ${detalhe}` },
      { status: 502 },
    )
  }
}

export const GET = encaminhar
export const POST = encaminhar
export const PUT = encaminhar
export const PATCH = encaminhar
export const DELETE = encaminhar
