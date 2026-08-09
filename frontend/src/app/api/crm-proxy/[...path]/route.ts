import { NextRequest, NextResponse } from "next/server"

const BACKEND_CTI =
  process.env.VERCEL_ENV === "preview"
    ? "https://cti-backend-pr-206.onrender.com"
    : "https://cti-backend-5ugf.onrender.com"

type Registro = Record<string, unknown>

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

async function buscarJson(caminho: string): Promise<unknown | null> {
  const resposta = await fetch(`${BACKEND_CTI}/${caminho}`, {
    cache: "no-store",
  }).catch(() => null)
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

function clientesDas(linhas: Registro[]) {
  const clientes = new Map<string, Registro>()
  for (const item of linhas) {
    const nome = texto(
      item.cliente_nome || item.razao_social || item.nome || item.nome_fantasia,
    )
    if (!nome) continue
    const chave = nome.toLocaleUpperCase("pt-BR")
    if (!clientes.has(chave)) {
      clientes.set(chave, {
        id: texto(item.cliente_id || item.id) || nome,
        nome,
        razao_social: nome,
        cidade: texto(item.municipio || item.cidade) || null,
        estado: texto(item.estado || item.uf) || null,
        ddd: texto(item.ddd) || null,
        sub_regiao: texto(item.sub_regiao) || null,
        segmento: texto(item.segmento) || "TRANSPORTADOR",
      })
    }
  }
  return [...clientes.values()]
}

async function fallbackSeguro(caminho: string): Promise<NextResponse | null> {
  if (caminho.startsWith("crm/agenda")) {
    return NextResponse.json({
      resumo: { hoje: 0, atrasadas: 0 },
      itens: [],
    })
  }

  if (caminho.startsWith("crm/atividades")) {
    return NextResponse.json([])
  }

  // O cadastro de oportunidade não depende da listagem legada. Uma falha
  // dessa leitura não pode bloquear a abertura nem o envio do formulário.
  if (caminho === "crm/oportunidades") {
    return NextResponse.json([])
  }

  if (
    !caminho.startsWith("crm/oportunidades") &&
    !caminho.startsWith("modulos/clientes")
  ) {
    return null
  }

  const nucleo = linhasDo(await buscarJson("crm/nucleo-comercial"))
  const base = nucleo.length > 0 ? nucleo : []

  if (caminho.startsWith("crm/oportunidades")) {
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

  return NextResponse.json(clientesDas(base))
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
      const alternativa = await fallbackSeguro(caminho)
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
      const alternativa = await fallbackSeguro(caminho).catch(() => null)
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
