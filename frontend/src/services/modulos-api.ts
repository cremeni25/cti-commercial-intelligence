import { apiGet } from "@/lib/api"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

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
export type EquipamentoResumo = { slug: string; nome: string; total_registros: number; valor_total: number; estados: RankingItem[]; implementadoras: RankingItem[]; linhas: RankingItem[]; empresas: RankingItem[]; metadata?: Record<string, unknown> }

export type CamadaRealizado = {
  origem: string
  semantica: "REALIZADO"
  total_registros: number
  valor_total: number
  estados: RankingItem[]
  municipios: RankingItem[]
  ddds: RankingItem[]
  implementadoras: RankingItem[]
  empresas: RankingItem[]
  equipamentos: RankingItem[]
  familias?: RankingItem[]
}

export type CamadaHistorico = {
  origem: string
  semantica: "CONSULTA_HISTORICA"
  total_registros: number
  total_unidades: number
  valor_nominal: number
  equipamentos: RankingItem[]
  implementadoras: RankingItem[]
  empresas: RankingItem[]
  status: RankingItem[]
  familias?: RankingItem[]
  nota_territorial?: string
}

export type CamadaEmCurso = {
  origem: string
  semantica: "EM_CURSO"
  total_registros: number
  valor_pipeline: number
  estados: RankingItem[]
  municipios: RankingItem[]
  ddds: RankingItem[]
  equipamentos: RankingItem[]
  status: RankingItem[]
  familias?: RankingItem[]
}

export type EquipamentoEstrategico = {
  slug: string
  nome: string
  regra: "CAMADAS_SEPARADAS_SEM_FUSAO"
  metadata?: Record<string, unknown>
  realizado: CamadaRealizado
  historico_comercial: CamadaHistorico
  em_curso: CamadaEmCurso
}

export type MapaEstrategicoResumo = {
  regra: "CORRELACAO_SEM_FUSAO"
  metadata?: Record<string, unknown>
  realizado: CamadaRealizado
  historico_comercial: CamadaHistorico
  em_curso: CamadaEmCurso
}

export type DrilldownResultado = {
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

export type HistoricoResumo = {
  total_registros: number
  total_unidades: number
  valor_nominal: number
  abas: RankingItem[]
  anos: RankingItem[]
  canais: RankingItem[]
  representantes: RankingItem[]
  status: RankingItem[]
  equipamentos: RankingItem[]
  implementadoras: RankingItem[]
  motivos_perda: RankingItem[]
}

export type ClienteCanonicoSeguro = {
  id: string
  nome: string
  razao_social?: string
  nome_fantasia?: string
  cnpj?: string
  cidade?: string
  estado?: string
  segmento?: string
  categoria?: string
  status?: string
}

export type CrmResumoEmpresaSeguro = {
  oportunidades: Record<string, unknown>[]
  propostas: Record<string, unknown>[]
  pedidos: Record<string, unknown>[]
  atividades: Record<string, unknown>[]
}

function normalizarQuery(query: string) { return query.includes("=") ? query : `contexto=${encodeURIComponent(query)}` }

async function apiSeguro<T>(caminho: string): Promise<T> {
  const resposta = await fetchCrmSeguroProxy(caminho, { cache: "no-store" })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail?: unknown }).detail)
      : `Erro do backend CTI: ${resposta.status}`
    throw new Error(detalhe)
  }
  return payload as T
}

async function apiEstrategiaSegura<T>(caminho: string): Promise<T> {
  return apiSeguro<T>(`crm-seguro/estrategia/${caminho}`)
}

export async function getEmpresas(query: string) {
  const payload = await apiSeguro<{ itens?: EmpresaResumoItem[] }>(`crm-seguro/empresas?${normalizarQuery(query)}`)
  return Array.isArray(payload?.itens) ? payload.itens : []
}
export function getClientes(query: string) { return getEmpresas(query) }
export function getClienteDetalhe(nome: string, query: string) { return apiGet(`/modulos/clientes/${encodeURIComponent(nome)}?${normalizarQuery(query)}`) as Promise<ClienteDetalheComercial> }
export function getClientesCanonicosSeguros() { return apiSeguro<ClienteCanonicoSeguro[]>("crm-seguro/clientes") }
export function getCrmResumoEmpresasSeguro() { return apiSeguro<CrmResumoEmpresaSeguro>("crm-seguro/empresas/crm-resumo") }
export function getTransportadoras(query: string) { return getEmpresas(query) }
export function getEquipamento(slug: string, query: string) { return apiEstrategiaSegura<EquipamentoEstrategico>(`equipamentos/${slug}?${normalizarQuery(query)}`) }
export function getMapaEstrategico(query: string) { return apiEstrategiaSegura<MapaEstrategicoResumo>(`mapa?${normalizarQuery(query)}`) }
export function getDrilldown(query: string) { return apiEstrategiaSegura<DrilldownResultado>(`detalhamento?${query}`) }
export function getHistoricoResumo() { return apiEstrategiaSegura<HistoricoResumo>("detalhamento/resumo-historico") }
