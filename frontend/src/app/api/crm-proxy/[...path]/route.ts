import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"

type Registro = Record<string, unknown>

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

async function fallbackNucleo(caminho: string): Promise<NextResponse | null> {
  if (
    !caminho.startsWith("crm/oportunidades") &&
    !caminho.startsWith("modulos/clientes")
  ) {
    return null
  }

  const resposta = await fetch(`${BACKEND_CTI}/crm/nucleo-comercial`, {
    cache: "no-store",
  })
  if (!resposta.ok) return null

  const payload = await resposta.json().catch(() => [])
  const linhas = Array.isArray(payload) ? (payload as Registro[]) : []

  if (caminho.startsWith("crm/oportunidades")) {
    const oportunidades = linhas.map((item) => ({
      id: texto(item.oportunidade_id || item.id),
      cliente_id: texto(item.cliente_id) || null,
      cliente_nome: texto(item.cliente_nome) || "Cliente não identificado",
      titulo: texto(item.titulo) || "Oportunidade comercial",
      descricao: texto(item.descricao) || null,
      origem: "CRM_APP",
      status: texto(item.etapa || item.status) || "OPORTUNIDADE",
      valor_estimado: Number(item.valor || item.valor_estimado || 0),
      probabilidade: Number(item.probabilidade || 0),
      data_fechamento_prevista:
        texto(item.data_fechamento_prevista) || null,
      equipamento: texto(item.equipamento) || null,
      linha_equipamentos: texto(item.linha_equipamentos) || null,
      created_at: texto(item.created_at) || null,
    }))
    return NextResponse.json(oportunidades)
  }

  const clientes = new Map<string, Registro>()
  for (const item of linhas) {
    const nome = texto(item.cliente_nome)
    if (!nome) continue
    const chave = nome.toLocaleUpperCase("pt-BR")
    if (!clientes.has(chave)) {
      clientes.set(chave, {
        id: texto(item.cliente_id) || nome,
        nome,
        razao_social: nome,
        cidade: texto(item.municipio) || null,
        estado: texto(item.estado || item.uf) || null,
        ddd: texto(item.ddd) || null,
        sub_regiao: texto(item.sub_regiao) || null,
        segmento: texto(item.segmento) || "TRANSPORTADOR",
      })
    }
  }
  return NextResponse.json([...clientes.values()])
}

async function encaminhar(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params
  const caminho = path.join("/")
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
    const resposta = await fetch(destino, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method)
        ? undefined
        : await request.text(),
      cache: "no-store",
    })

    if (!resposta.ok && request.method === "GET") {
      const alternativa = await fallbackNucleo(caminho)
      if (alternativa) return alternativa
    }

    const corpo = await resposta.text()
    return new NextResponse(corpo, {
      status: resposta.status,
      headers: {
        "content-type":
          resposta.headers.get("content-type") || "application/json",
      },
    })
  } catch (erro) {
    if (request.method === "GET") {
      const alternativa = await fallbackNucleo(caminho).catch(() => null)
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
