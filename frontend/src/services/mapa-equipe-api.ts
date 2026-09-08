import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type EquipeOpcao = {
  id: string
  nome: string
  tipo_usuario: string
  codigo_regional?: string | null
  ddds: string[]
}

export type MapaEquipeVisao = {
  regra: string
  pode_selecionar_responsavel: boolean
  equipe: EquipeOpcao[]
  selecao: {
    modo: "TODA_EQUIPE" | "RESPONSAVEL"
    id?: string | null
    nome: string
    codigo_regional?: string | null
    ddds: string[]
  }
  mercado: {
    mercado_real_viena_2026: number
    mercado_real_selecao_2026: number
    participacao_regiao_no_mercado_real_pct: number
    familias: { trailer: number; diesel_truck: number; direct_drive: number }
    clientes_unicos: number
    participacoes_equipe?: Array<{ id: string; nome: string; mercado: number; participacao_pct?: number }>
    mercado_real_sem_carteira?: number
  }
  evidencias: {
    historico_registros_2026: number
    historico_unidades_2026: number
    crm_registros: number
    crm_ativos: number
    crm_valor_ativo: number
    crm_status: Array<{ nome: string; quantidade: number }>
    motivos_perda_historico: Array<{ nome: string; quantidade: number }>
  }
  reconciliacao: {
    universo_clientes: number
    clientes_anfir: number
    clientes_historico: number
    clientes_crm: number
    anfir_historico: number
    anfir_crm: number
    historico_crm: number
    nas_tres_fontes: number
    somente_anfir: number
    somente_historico: number
    somente_crm: number
    historico_fora_mercado_real: number
    crm_fora_mercado_real: number
    regra: string
  }
  ciclo: {
    clientes_mercado_real: number
    clientes_historico_2026: number
    clientes_crm: number
    crm_com_evidencia_historico: number
    crm_com_evidencia_anfir: number
    clientes_com_evidencia_nas_tres_fontes: number
    nota: string
  }
}

export type LeituraComercial = {
  leitura_comercial: string
  acao_recomendada: string
}

export type ComposicaoMarcaLinha = {
  mercado: number
  carrier: number
  outras_marcas: number
  marca_nao_discriminada: number
  carrier_pct: number
  outras_marcas_pct: number
  marca_nao_discriminada_pct: number
  fechamento_total: number
  fechamento_ok: boolean
  marcas_concorrentes: Array<{ nome: string; quantidade: number; percentual_mercado: number }>
  regra: string
}

export type MapaInsights = {
  ano: 2026
  meses: string[]
  escopo: {
    consolidado: boolean
    modo: "TODA_EQUIPE" | "RESPONSAVEL"
    responsavel_id?: string | null
    responsavel_nome: string
    regra: string
  }
  regioes: Array<{
    id: string
    nome: string
    codigo_regional?: string | null
    ddds: string[]
    mercado_2026: number
    clientes_mercado: number
    crm_ativos: number
    pipeline_ativo: number
    mercado_mensal: number[]
    registros_sem_mes: number
  } & LeituraComercial>
  linhas_2026: {
    meses: string[]
    linhas: Array<{
      codigo: "trailer" | "diesel_truck" | "direct_drive"
      nome: string
      total_2026: number
      mensal: number[]
      composicao_marca: ComposicaoMarcaLinha
    } & LeituraComercial>
    nao_classificado_2026: number
    unidades_sem_mes: number
    fonte: "ANFIR_2026"
    regra_calculo?: string
  }
  perdas: {
    ano: 2026
    total_perdido: number
    total_com_motivo: number
    motivos: Array<{ nome: string; quantidade: number }>
    por_linha: Array<{ nome: string; quantidade: number }>
    mensal: number[]
    registros_sem_mes: number
  } & LeituraComercial
}

export type MapaDrilldown = {
  camada: "anfir" | "historico" | "crm"
  campo?: string | null
  valor?: string | null
  familia?: string | null
  total_registros: number
  pagina: number
  limite: number
  total_paginas: number
  metadata?: Record<string, unknown>
  registros: Record<string, unknown>[]
}

export type TurnoContextual = {
  role: "user" | "assistant"
  content: string
}

export type FonteContextual = {
  codigo: "TERRITORIO_RESPONSAVEL" | "ANFIR_2026" | "HISTORICO_FUNIL_2026" | "CRM_ATUAL"
  nome: string
  evidencia: string
}

export type MapaEquipeInteligencia = {
  analise: string
  selecao: MapaEquipeVisao["selecao"]
  origem: "IA_COMERCIAL_CTI"
  somente_leitura: boolean
  persistido?: boolean
  fontes?: Array<{ tipo?: string; descricao?: string; url?: string }>
  fontes_contextuais?: FonteContextual[]
}

const MAPA_TIMEOUT_MS = 25000

async function interpretarResposta<T>(resposta: Response): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail?: unknown }).detail)
      : `Erro do backend CTI: ${resposta.status}`
    throw new Error(detalhe)
  }
  return payload as T
}

async function fetchMapaComTimeout(path: string): Promise<Response> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), MAPA_TIMEOUT_MS)
  try {
    return await fetchCrmSeguroProxy(path, { cache: "no-store", signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("A leitura comercial demorou além do limite seguro. Atualize a tela para tentar novamente.")
    }
    throw error
  } finally {
    window.clearTimeout(timer)
  }
}

export async function getMapaEquipeVisao(responsavelId?: string | null): Promise<MapaEquipeVisao> {
  const qs = new URLSearchParams({ periodo: "ANO_ATUAL", contexto: "viena_sp" })
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const resposta = await fetchMapaComTimeout(`crm-seguro/mapa-equipe/visao?${qs.toString()}`)
  return interpretarResposta<MapaEquipeVisao>(resposta)
}

export async function getMapaInsights(responsavelId?: string | null): Promise<MapaInsights> {
  const qs = new URLSearchParams()
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const sufixo = qs.toString() ? `?${qs.toString()}` : ""
  const resposta = await fetchMapaComTimeout(`crm-seguro/mapa-equipe/insights${sufixo}`)
  return interpretarResposta<MapaInsights>(resposta)
}

export async function getMapaDrilldown(query: string): Promise<MapaDrilldown> {
  const resposta = await fetchMapaComTimeout(`crm-seguro/mapa-equipe/detalhamento?${query}`)
  return interpretarResposta<MapaDrilldown>(resposta)
}

export async function getMapaEquipeInteligencia(responsavelId?: string | null): Promise<MapaEquipeInteligencia> {
  const qs = new URLSearchParams()
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const sufixo = qs.toString() ? `?${qs.toString()}` : ""
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/inteligencia${sufixo}`, { cache: "no-store" })
  return interpretarResposta<MapaEquipeInteligencia>(resposta)
}

export async function perguntarMapaEquipeInteligencia(
  pergunta: string,
  historico: TurnoContextual[],
  responsavelId?: string | null,
): Promise<MapaEquipeInteligencia> {
  const qs = new URLSearchParams()
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const sufixo = qs.toString() ? `?${qs.toString()}` : ""
  const historicoSeguro = historico.slice(-8)
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/inteligencia/perguntar${sufixo}`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta, historico: historicoSeguro }),
  })
  return interpretarResposta<MapaEquipeInteligencia>(resposta)
}