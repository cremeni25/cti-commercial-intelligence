import { apiGet } from "@/lib/api"

export type EmpresaResumoItem = {
  nome: string
  quantidade_registros: number
  valor_total?: number
  estados?: string[]
  municipios?: string[]
  linhas?: string[]
  status?: Record<string, number>
  quantidade_chassis?: number
  quantidade_placas?: number
  chassis?: string[]
  placas?: string[]
  implementadoras?: string[]
  equipamentos?: string[]
}
export type RankingItem = { nome: string; quantidade_registros: number }
export type EquipamentoResumo = { slug: string; nome: string; total_registros: number; valor_total: number; estados: RankingItem[]; implementadoras: RankingItem[]; linhas: RankingItem[]; empresas: RankingItem[]; metadata?: Record<string, string | null> }

function normalizarQuery(query: string) { return query.includes("=") ? query : `contexto=${encodeURIComponent(query)}` }
export function getEmpresas(query: string) { return apiGet(`/modulos/empresas?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getClientes(query: string) { return apiGet(`/modulos/clientes?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getTransportadoras(query: string) { return getEmpresas(query) }
export function getEquipamento(slug: string, query: string) { return apiGet(`/modulos/equipamentos/${slug}?${normalizarQuery(query)}`) as Promise<EquipamentoResumo> }
