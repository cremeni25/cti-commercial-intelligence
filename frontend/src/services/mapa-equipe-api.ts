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

export type MapaInsights = {
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
  }>
  evolucao_linhas: Array<{
    ano: number
    trailer: number
    diesel_truck: number
    direct_drive: number
    nao_classificado: number
  }>
  perdas: {
    total_registros_com_motivo: number
    motivos: Array<{ nome: string; quantidade: number }>
    por_linha: Array<{ nome: string; quantidade: number }>
    por_ano: Array<{ nome: string; quantidade: number }>
  }
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

export async function getMapaEquipeVisao(responsavelId?: string | null): Promise<MapaEquipeVisao> {
  const qs = new URLSearchParams({ periodo: "ANO_ATUAL", contexto: "viena_sp" })
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/visao?${qs.toString()}`, { cache: "no-store" })
  return interpretarResposta<MapaEquipeVisao>(resposta)
}

export async function getMapaInsights(responsavelId?: string | null): Promise<MapaInsights> {
  const qs = new URLSearchParams()
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const sufixo = qs.toString() ? `?${qs.toString()}` : ""
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/insights${sufixo}`, { cache: "no-store" })
  return interpretarResposta<MapaInsights>(resposta)
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
