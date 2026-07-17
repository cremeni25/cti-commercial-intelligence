import { apiGet } from "@/lib/api"
import type { OperationalContextValue } from "@/context/OperationalContext"

export type EmpresaResumoItem = {
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
  empresas: RankingItem[]
}

function contextoQuery(contexto: OperationalContextValue) {
  return `?contexto=${encodeURIComponent(contexto)}`
}

export function getEmpresas(contexto: OperationalContextValue) {
  return apiGet(`/modulos/empresas${contextoQuery(contexto)}`) as Promise<EmpresaResumoItem[]>
}

export function getTransportadoras(contexto: OperationalContextValue) {
  return getEmpresas(contexto)
}

export function getEquipamento(slug: string, contexto: OperationalContextValue) {
  return apiGet(`/modulos/equipamentos/${slug}${contextoQuery(contexto)}`) as Promise<EquipamentoResumo>
}
