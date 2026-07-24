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

export type AtividadeComercial = {
  id?: string
  titulo?: string
  descricao?: string
  data?: string
  horario?: string
  status?: string
  situacao?: string
}

export type OportunidadeComercial = {
  id?: string
  titulo?: string
  status?: string
  valor_estimado?: number
  equipamento?: string
  implementadora?: string
  data_fechamento_prevista?: string
}

export type ClienteDetalheComercial = {
  cliente: EmpresaResumoItem
  inteligencia: {
    prioridade: "ALTA" | "MEDIA" | "BAIXA"
    oportunidades_abertas: number
    atividades_atrasadas: number
    valor_pipeline: number
    proxima_acao?: AtividadeComercial | null
  }
  oportunidades: OportunidadeComercial[]
  atividades: AtividadeComercial[]
}

export type RankingItem = { nome: string; quantidade_registros: number }
export type EquipamentoResumo = { slug: string; nome: string; total_registros: number; valor_total: number; estados: RankingItem[]; implementadoras: RankingItem[]; linhas: RankingItem[]; empresas: RankingItem[]; metadata?: Record<string, string | null> }

function normalizarQuery(query: string) { return query.includes("=") ? query : `contexto=${encodeURIComponent(query)}` }
export function getEmpresas(query: string) { return apiGet(`/modulos/empresas?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getClientes(query: string) { return apiGet(`/modulos/clientes?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getClienteDetalhe(nome: string, query: string) { return apiGet(`/modulos/clientes/${encodeURIComponent(nome)}?${normalizarQuery(query)}`) as Promise<ClienteDetalheComercial> }
export function getTransportadoras(query: string) { return getEmpresas(query) }
export function getEquipamento(slug: string, query: string) { return apiGet(`/modulos/equipamentos/${slug}?${normalizarQuery(query)}`) as Promise<EquipamentoResumo> }
