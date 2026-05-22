export interface Implementadora {
  id: number

  nome: string

  cidade: string
  estado: string
  regiao: string

  status: "Ativo" | "Inativo"

  /*
   * MODELAGEM ORIGINAL
   */

  score: number
  oportunidades: number

  potencial: "Alto" | "Médio" | "Baixo"

  responsavel: string
  telefone: string

  ultimaInteracao: string

  montadorasRelacionadas: string[]

  equipamentos: string[]

  observacoes: string

  /*
   * EVOLUÇÃO ENTERPRISE
   * TODOS OPCIONAIS
   * PARA NÃO QUEBRAR COMPATIBILIDADE
   */

  ddds?: string[]

  scoreOperacional?: number
  scoreComercial?: number

  potencialMercado?: "Alto" | "Médio" | "Baixo"

  oportunidadesAbertas?: number

  email?: string

  proximoFollowUp?: string

  equipamentosRelacionados?: string[]

  transportadorasRelacionadas?: string[]

  concorrentesRelacionados?: string[]

  concorrentePrincipal?: string

  presencaCarrier?: string

  crescimento?: number

  marketShare?: number

  dominanciaRegional?: string

  ativo?: boolean

  createdAt?: string
  updatedAt?: string

eventos?: {
  data: string
  titulo: string
  descricao: string
  tipo:
    | "positivo"
    | "alerta"
    | "negativo"
    | "estrategico"
}[]

}