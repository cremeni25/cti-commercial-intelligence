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
  metadata?: Record<string, string | null>
  realizado: CamadaRealizado
  historico_comercial: CamadaHistorico
  em_curso: CamadaEmCurso
}

export type MapaEstrategicoResumo = {
  regra: "CORRELACAO_SEM_FUSAO"
  metadata?: Record<string, string | null>
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
  metadata?: Record<string, string | null>
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

function normalizarQuery(query: string) { return query.includes("=") ? query : `contexto=${encodeURIComponent(query)}` }
export function getEmpresas(query: string) { return apiGet(`/modulos/empresas?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getClientes(query: string) { return apiGet(`/modulos/clientes?${normalizarQuery(query)}`) as Promise<EmpresaResumoItem[]> }
export function getClienteDetalhe(nome: string, query: string) { return apiGet(`/modulos/clientes/${encodeURIComponent(nome)}?${normalizarQuery(query)}`) as Promise<ClienteDetalheComercial> }
export function getTransportadoras(query: string) { return getEmpresas(query) }
export function getEquipamento(slug: string, query: string) { return apiGet(`/estrategia/equipamentos/${slug}?${normalizarQuery(query)}`) as Promise<EquipamentoEstrategico> }
export function getMapaEstrategico(query: string) { return apiGet(`/estrategia/mapa?${normalizarQuery(query)}`) as Promise<MapaEstrategicoResumo> }
export function getDrilldown(query: string) { return apiGet(`/estrategia/detalhamento?${query}`) as Promise<DrilldownResultado> }
export function getHistoricoResumo() { return apiGet(`/estrategia/detalhamento/resumo-historico`) as Promise<HistoricoResumo> }
