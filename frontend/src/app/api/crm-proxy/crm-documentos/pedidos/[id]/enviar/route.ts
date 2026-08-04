import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params
  const destino = `${BACKEND_CTI}/crm-documentos/pedidos/${encodeURIComponent(id)}/enviar-documento-oficial`
  const headers = new Headers({ "content-type": "application/json" })
  const authorization = request.headers.get("authorization")
  if (authorization) headers.set("authorization", authorization)

  try {
    const resposta = await fetch(destino, {
      method: "POST",
      headers,
      body: await request.text(),
      cache: "no-store",
    })
    const corpo = await resposta.text()
    return new NextResponse(corpo, {
      status: resposta.status,
      headers: {
        "content-type": resposta.headers.get("content-type") || "application/json",
      },
    })
  } catch (erro) {
    const detalhe = erro instanceof Error ? erro.message : "Falha de comunicação com o backend"
    return NextResponse.json(
      { detail: `Não foi possível enviar o PDF oficial: ${detalhe}` },
      { status: 502 },
    )
  }
}
