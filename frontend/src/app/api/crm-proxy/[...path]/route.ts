import { NextRequest, NextResponse } from "next/server"

import { caminhoCanonicoLeitura } from "@/lib/crm-canonical"

const BACKEND_CTI = (process.env.CTI_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "https://cti-backend-5ugf.onrender.com").replace(/\/$/, "")
const STATUS_TRANSITORIOS = new Set([500, 502, 503, 504])
const ATRASOS_RETRY_MS = [0, 180, 450]

type Registro = Record<string, unknown>

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

function aguardar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchBackend(destino: URL | string, init: RequestInit, permitirRetry: boolean) {
  let ultimoErro: unknown = null
  let ultimaResposta: Response | null = null
  const tentativas = permitirRetry ? ATRASOS_RETRY_MS : [0]

  for (const atraso of tentativas) {
    if (atraso) await aguardar(atraso)
    try {
      const resposta = await fetch(destino, { ...init, cache: "no-store" })
      ultimaResposta = resposta
      if (!permitirRetry || !STATUS_TRANSITORIOS.has(resposta.status)) return resposta
    } catch (erro) {
      ultimoErro = erro
      if (!permitirRetry) throw erro
    }
  }

  if (ultimaResposta) return ultimaResposta
  throw ultimoErro instanceof Error ? ultimoErro : new Error("Falha transitória de comunicação com o backend")
}

async function buscarJson(caminho: string): Promise<unknown | null> {
  const resposta = await fetchBackend(`${BACKEND_CTI}/${caminho}`, {}, true).catch(() => null)
  if (!resposta?.ok) return null
  return resposta.json().catch(() => null)
}

function linhasDo(payload: unknown): Registro[] {
  if (Array.isArray(payload)) return payload as Registro[]
  if (payload && typeof payload === "object") {
    const objeto = payload as Registro
    for (const chave of ["oportunidades", "dados", "itens", "resultado"]) {
      if (Array.isArray(objeto[chave])) return objeto[chave] as Registro[]
    }
  }
  return []
}

function mapearOportunidades(linhas: Registro[]) {
  return linhas.map((item) => ({
    id: texto(item.oportunidade_id || item.id),
    cliente_id: texto(item.cliente_id) || null,
    cliente_nome: texto(item.cliente_nome) || "Cliente não identificado",
    titulo: texto(item.titulo) || "Oportunidade comercial",
    descricao: texto(item.descricao) || null,
    origem: texto(item.origem) || "CRM_APP",
    status:
      texto(item.etapa || item.status || item.status_oportunidade) ||
      "OPORTUNIDADE",
    valor_estimado: Number(item.valor || item.valor_estimado || 0),
    probabilidade: Number(item.probabilidade || 0),
    data_fechamento_prevista:
      texto(item.data_fechamento_prevista) || null,
    equipamento: texto(item.equipamento) || null,
    linha_equipamentos: texto(item.linha_equipamentos) || null,
    proposta_id: texto(item.proposta_id) || null,
    proposta_numero: texto(item.proposta_numero) || null,
    status_proposta: texto(item.status_proposta) || null,
    pedido_id: texto(item.pedido_id) || null,
    pedido_numero: texto(item.pedido_numero) || null,
    status_pedido: texto(item.status_pedido) || null,
    created_at: texto(item.created_at) || null,
  }))
}

async function fallbackSeguro(caminho: string): Promise<NextResponse | null> {
  if (caminho.startsWith("crm/agenda")) {
    return NextResponse.json({ disponibilidade: "INDISPONIVEL", resumo: { hoje: 0, atrasadas: 0, futuras: 0, sem_data: 0 }, itens: [] }, { status: 503 })
  }

  if (caminho.startsWith("crm/atividades")) {
    return NextResponse.json({ disponibilidade: "INDISPONIVEL", dados: [] }, { status: 503 })
  }

  if (caminho.startsWith("modulos/clientes")) {
    return null
  }

  if (caminho === "crm/oportunidades") {
    return NextResponse.json({ disponibilidade: "INDISPONIVEL", oportunidades: [] }, { status: 503 })
  }

  if (!caminho.startsWith("crm/oportunidades")) {
    return null
  }

  const nucleo = linhasDo(await buscarJson("crm/nucleo-comercial"))
  const base = nucleo.length > 0 ? nucleo : []
  const oportunidadeId = caminho.split("/")[2]
  const oportunidades = mapearOportunidades(base)
  if (oportunidadeId) {
    const encontrada = oportunidades.find((item) => item.id === oportunidadeId)
    return encontrada
      ? NextResponse.json(encontrada)
      : NextResponse.json({ detail: "Oportunidade não encontrada" }, { status: 404 })
  }
  return NextResponse.json(oportunidades)
}

async function encaminhar(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params
  const caminhoSolicitado = path.join("/")
  const caminho = caminhoCanonicoLeitura(caminhoSolicitado, request.method)
  const destino = new URL(`${BACKEND_CTI}/${caminho}`)
  request.nextUrl.searchParams.forEach((valor, chave) =>
    destino.searchParams.set(chave, valor),
  )

  const headers = new Headers()
  const contentType = request.headers.get("content-type")
  if (contentType) headers.set("content-type", contentType)
  const authorization = request.headers.get("authorization")
  if (authorization) headers.set("authorization", authorization)

  try {
    const leitura = ["GET", "HEAD"].includes(request.method)
    const resposta = await fetchBackend(destino, {
      method: request.method,
      headers,
      body: leitura ? undefined : await request.arrayBuffer(),
    }, leitura)

    if (!resposta.ok && request.method === "GET") {
      const alternativa = await fallbackSeguro(caminhoSolicitado)
      if (alternativa) return alternativa
    }

    const tipoResposta = resposta.headers.get("content-type") || "application/json"
    const disposicao = resposta.headers.get("content-disposition")
    const headersResposta = new Headers({ "content-type": tipoResposta })
    if (disposicao) headersResposta.set("content-disposition", disposicao)

    if (
      tipoResposta.includes("application/pdf") ||
      tipoResposta.includes("image/") ||
      tipoResposta.includes("application/octet-stream")
    ) {
      return new NextResponse(await resposta.arrayBuffer(), {
        status: resposta.status,
        headers: headersResposta,
      })
    }

    return new NextResponse(await resposta.text(), {
      status: resposta.status,
      headers: headersResposta,
    })
  } catch (erro) {
    if (request.method === "GET") {
      const alternativa = await fallbackSeguro(caminhoSolicitado).catch(() => null)
      if (alternativa) return alternativa
    }

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
