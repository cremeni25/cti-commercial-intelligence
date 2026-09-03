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

export async function getMapaEquipeVisao(responsavelId?: string | null): Promise<MapaEquipeVisao> {
  const qs = new URLSearchParams({ periodo: "ANO_ATUAL", contexto: "viena_sp" })
  if (responsavelId) qs.set("responsavel_id", responsavelId)
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/mapa-equipe/visao?${qs.toString()}`, { cache: "no-store" })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail?: unknown }).detail)
      : `Erro do backend CTI: ${resposta.status}`
    throw new Error(detalhe)
  }
  return payload as MapaEquipeVisao
}
