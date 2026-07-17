import { apiGet } from "@/lib/api"

export type ModuloResumoItem = {
  nome: string
  quantidade_registros: number
  valor_total?: number
  estados?: string[]
  municipios?: string[]
  linhas?: string[]
  status?: Record<string, number>
}

export type RankingItem = {
  nome: string
  quantidade_registros: number
}

export type EquipamentoResumo = {
  slug: string
  nome: string
  total_registros: number
  valor_total: number
  estados: RankingItem[]
  implementadoras: RankingItem[]
  linhas: RankingItem[]
  clientes: RankingItem[]
}

export function getTransportadoras() {
  return apiGet("/modulos/transportadoras") as Promise<ModuloResumoItem[]>
}

export function getEquipamento(slug: string) {
  return apiGet(`/modulos/equipamentos/${slug}`) as Promise<EquipamentoResumo>
}
