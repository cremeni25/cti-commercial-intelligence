import { fetchCrmSeguroProxy } from "@/services/crm-secure"

/** Contrato do briefing do Agente de Inteligência Comercial (backend v1.0). */
export type CategoriaSinal = "acao" | "risco" | "oportunidade" | "qualidade"
export type SeveridadeSinal = "critica" | "alta" | "media" | "baixa"

export type PrioridadeComercial = {
  codigo: string
  categoria: CategoriaSinal
  severidade: SeveridadeSinal
  titulo: string
  explicacao: string
  acao_recomendada: string
  entidade_tipo: string
  entidade_id: string
  cliente_nome: string
  responsavel_id: string
  valor: number
  dias: number | null
  rota: string
  rota_app: string
  evidencias: string[]
  pontuacao: number
  sinais_relacionados: string[]
}

export type IndicadorBriefing = {
  codigo: string
  rotulo: string
  valor: number
  formato: "moeda" | "numero" | "percentual"
  detalhe: string
  tom: "neutro" | "atencao" | "positivo"
  rota: string
  rota_app: string
}

export type EtapaPipeline = { etapa: string; rotulo: string; quantidade: number; valor: number; valor_ponderado: number }

export type ProblemaQualidade = {
  codigo: string
  rotulo: string
  quantidade: number
  impacto: string
  exemplos: { oportunidade_id: string; cliente_nome: string; rota: string; rota_app: string }[]
}

export type BriefingComercial = {
  versao: string
  gerado_em: string
  data_referencia: string
  escopo: { tipo: "consolidado" | "individual" | string; responsavel_id?: string | null }
  manchete: string
  indicadores: IndicadorBriefing[]
  prioridades: PrioridadeComercial[]
  riscos: { codigo: string; rotulo: string; quantidade: number; valor: number }[]
  pipeline: { etapas: EtapaPipeline[]; quantidade_aberta: number; valor_aberto: number; valor_ponderado: number }
  qualidade: { indice: number; negocios_avaliados: number; problemas: ProblemaQualidade[] }
  sinais_por_codigo: Record<string, number>
  total_sinais: number
  provedores: { codigo: string; modulo: string; ok: boolean; sinais: number; erro?: string }[]
  fontes: string[]
  limitacoes: string[]
}

export type ModuloPlataforma = {
  codigo: string
  nome: string
  descricao: string
  categoria: string
  categoria_rotulo: string
  status: "ativo" | "beta" | "planejado"
  rota_web: string | null
  rota_app: string | null
  consultado_pela_ia: boolean
}

async function lerJson<T>(resposta: Response, contexto: string): Promise<T> {
  const tipo = resposta.headers.get("content-type") || ""
  const payload = tipo.includes("application/json") ? await resposta.json().catch(() => null) : null
  if (!resposta.ok || payload === null) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

/** Rejeita respostas fora do contrato (ex.: backend anterior ao agente ou fallback genérico). */
export function briefingValido(payload: unknown): payload is BriefingComercial {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return false
  const dados = payload as Partial<BriefingComercial>
  return typeof dados.manchete === "string"
    && Array.isArray(dados.prioridades)
    && Array.isArray(dados.indicadores)
    && Array.isArray(dados.riscos)
    && Boolean(dados.pipeline && Array.isArray(dados.pipeline.etapas))
    && Boolean(dados.qualidade && Array.isArray(dados.qualidade.problemas))
}

export async function buscarBriefingComercial(opcoes: { responsavelId?: string; limite?: number; signal?: AbortSignal } = {}) {
  const params = new URLSearchParams()
  if (opcoes.responsavelId) params.set("responsavel_id", opcoes.responsavelId)
  if (opcoes.limite) params.set("limite", String(opcoes.limite))
  const sufixo = params.toString() ? `?${params}` : ""
  const resposta = await fetchCrmSeguroProxy(`crm-seguro/inteligencia/briefing${sufixo}`, { cache: "no-store", signal: opcoes.signal }, { timeoutMs: 30000, tentativas: 2 })
  const payload = await lerJson<BriefingComercial>(resposta, "A leitura do agente")
  if (!briefingValido(payload)) throw new Error("A leitura do agente ainda não está disponível neste ambiente.")
  return payload
}

export async function buscarModulosPlataforma() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/plataforma/modulos", { cache: "no-store" }, { timeoutMs: 15000, tentativas: 2 })
  const payload = await lerJson<{ modulos: ModuloPlataforma[] }>(resposta, "O catálogo de módulos")
  return Array.isArray(payload.modulos) ? payload.modulos : []
}
