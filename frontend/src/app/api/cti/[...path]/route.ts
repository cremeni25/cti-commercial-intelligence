import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = "https://cti-backend-5ugf.onrender.com"
const METODOS_COM_CORPO = new Set(["POST", "PUT", "PATCH", "DELETE"])
const STATUS_TRANSITORIOS = new Set([502, 503, 504])
const ATRASOS_RETRY_GET_MS = [500, 1500, 3000]

type ContextoRota = { params: Promise<{ path: string[] }> }

function aguardar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function buscarBackend(destino: URL, request: NextRequest, headers: Headers, corpo?: ArrayBuffer) {
  const podeRepetir = request.method === "GET"
  const totalTentativas = podeRepetir ? ATRASOS_RETRY_GET_MS.length + 1 : 1
  let ultimaFalha: unknown = null

  for (let tentativa = 0; tentativa < totalTentativas; tentativa += 1) {
    try {
      const resposta = await fetch(destino, {
        method: request.method,
        headers,
        body: METODOS_COM_CORPO.has(request.method) ? corpo : undefined,
        cache: "no-store",
        redirect: "follow",
      })

      if (!podeRepetir || !STATUS_TRANSITORIOS.has(resposta.status) || tentativa === totalTentativas - 1) {
        return resposta
      }
    } catch (erro) {
      ultimaFalha = erro
      if (!podeRepetir || tentativa === totalTentativas - 1) throw erro
    }

    await aguardar(ATRASOS_RETRY_GET_MS[tentativa])
  }

  throw ultimaFalha instanceof Error ? ultimaFalha : new Error("Backend CTI indisponível")
}

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

  const corpoRequest = METODOS_COM_CORPO.has(request.method) ? await request.arrayBuffer() : undefined

  let resposta: Response
  try {
    resposta = await buscarBackend(destino, request, headers, corpoRequest)
  } catch {
    return NextResponse.json(
      { detail: "Serviço CTI temporariamente indisponível. Aguarde alguns segundos e tente novamente." },
      { status: 503, headers: { "cache-control": "no-store", "x-cti-backend": BACKEND_URL } },
    )
  }

  const contentType = resposta.headers.get("content-type") || ""
  if (!resposta.ok && !contentType.includes("application/json")) {
    return NextResponse.json(
      { detail: "Serviço CTI temporariamente indisponível. Aguarde alguns segundos e tente novamente." },
      { status: resposta.status, headers: { "cache-control": "no-store", "x-cti-backend": BACKEND_URL } },
    )
  }

  const corpo = await resposta.arrayBuffer()
  const retornoHeaders = new Headers({
    "cache-control": "no-store",
    "x-cti-backend": BACKEND_URL,
  })
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
