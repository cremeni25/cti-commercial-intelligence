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
  cliente_id: string
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
  sinais_suprimidos?: number
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

async function enviar(caminho: string, metodo: "POST" | "PUT", corpo: unknown | undefined, contexto: string) {
  const resposta = await fetchCrmSeguroProxy(caminho, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  })
  if (!resposta.ok) {
    const payload = await resposta.json().catch(() => null)
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} não foi concluído (${resposta.status}).`)
  }
  return resposta.json().catch(() => ({}))
}

export const TIPOS_PROXIMO_PASSO = [
  { valor: "LIGACAO", rotulo: "Ligação" },
  { valor: "WHATSAPP", rotulo: "WhatsApp" },
  { valor: "VISITA", rotulo: "Visita" },
  { valor: "REUNIAO", rotulo: "Reunião" },
  { valor: "EMAIL", rotulo: "E-mail" },
] as const

export const MOTIVOS_AJUSTE = [
  { valor: "JA_TRATADO", rotulo: "Já tratei fora do sistema" },
  { valor: "CLIENTE_PEDIU_AGUARDAR", rotulo: "Cliente pediu para aguardar" },
  { valor: "SERA_ENCERRADO", rotulo: "Negócio será encerrado" },
  { valor: "DADO_INCORRETO", rotulo: "Dado do sistema está incorreto" },
  { valor: "ALERTA_CEDO_DEMAIS", rotulo: "Alerta cedo demais para este tipo de venda" },
  { valor: "OUTRO", rotulo: "Outro motivo" },
] as const

/** Agenda o próximo passo do negócio pelo mesmo fluxo seguro de atividades do CRM. */
export function agendarProximoPasso(item: PrioridadeComercial, dados: { tipo: string; data: string; titulo: string; usuarioId: string }) {
  if (!item.cliente_id) return Promise.reject(new Error("Este negócio não tem cliente vinculado; abra o negócio para agendar."))
  return enviar("crm-seguro/atividades", "POST", {
    cliente_id: item.cliente_id,
    oportunidade_id: item.entidade_tipo === "oportunidade" ? item.entidade_id : null,
    usuario_id: item.responsavel_id || dados.usuarioId,
    tipo: dados.tipo,
    titulo: dados.titulo,
    data: dados.data,
    status: "PENDENTE",
  }, "O agendamento")
}

export function concluirAtividadePrioridade(item: PrioridadeComercial) {
  return enviar(`crm-seguro/atividades/${encodeURIComponent(item.entidade_id)}/concluir`, "PUT", undefined, "A conclusão")
}

export function reagendarAtividadePrioridade(item: PrioridadeComercial, data: string) {
  return enviar(`crm-seguro/atividades/${encodeURIComponent(item.entidade_id)}`, "PUT", { data }, "O reagendamento")
}

export function ajustarSinal(item: PrioridadeComercial, ajuste: { decisao: "NAO_SE_APLICA" | "ADIAR"; motivo: string; observacao?: string; adiarAte?: string }) {
  return enviar("crm-seguro/inteligencia/feedback", "POST", {
    codigo: item.codigo,
    entidade_tipo: item.entidade_tipo,
    entidade_id: item.entidade_id,
    decisao: ajuste.decisao,
    motivo: ajuste.motivo,
    observacao: ajuste.observacao || null,
    adiar_ate: ajuste.adiarAte || null,
  }, "O ajuste do alerta")
}

export type AprendizadoAgente = {
  total_ajustes: number
  sinais: { codigo: string; total: number; motivos: { motivo: string; rotulo: string; quantidade: number }[] }[]
}

export async function buscarAprendizadoAgente() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/inteligencia/aprendizado", { cache: "no-store" }, { timeoutMs: 15000, tentativas: 2 })
  return lerJson<AprendizadoAgente>(resposta, "A leitura de calibração")
}

/* ---------- Catálogo ---------- */

export type MaterialCatalogo = { titulo: string; url: string; tipo: string }
export type EquipamentoCatalogo = {
  codigo: string
  nome_comercial: string
  modelo_base: string | null
  configuracao: string
  compressor: string | null
  possui_eletrico: boolean
  descricao_tecnica: Record<string, unknown>
  preco_vigente: { valor: number; moeda: string; tabela: string | null; vigencia_inicio: string } | null
  materiais: MaterialCatalogo[]
}
export type LinhaCatalogo = { codigo: string; nome: string; sigla: string; descricao: string; equipamentos: EquipamentoCatalogo[]; materiais: MaterialCatalogo[] }
export type TabelaAplicacao = {
  titulo: string
  condicao: string
  tamanhos: { codigo: string; comprimento_m: number; volume_m3: number }[]
  equipamentos: { modelo: string; linha: string; refrigerante: string | null; acoplamento: string | null; isolamento_mm: number | null; temperaturas: (number | null)[] }[]
  premissas: string[]
  observacao: string
}

export type VitrineCatalogo = {
  tabela_aplicacao?: TabelaAplicacao | null
  materiais_internos?: (MaterialCatalogo & { enviado_em?: string })[]
  fonte: string
  precos_visiveis: boolean
  linktree_url: string | null
  materiais_gerais: MaterialCatalogo[]
  linhas: LinhaCatalogo[]
  total_equipamentos: number
}

export async function buscarVitrineCatalogo() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/catalogo/vitrine", { cache: "no-store" }, { timeoutMs: 20000, tentativas: 2 })
  const payload = await lerJson<VitrineCatalogo>(resposta, "O catálogo")
  if (!payload || !Array.isArray(payload.linhas)) throw new Error("O catálogo ainda não está disponível neste ambiente.")
  return payload
}

export async function anexarMaterialCatalogo(titulo: string, arquivo: File) {
  const corpo = new FormData()
  corpo.set("titulo", titulo)
  corpo.set("arquivo", arquivo)
  const resposta = await fetchCrmSeguroProxy("crm-seguro/catalogo/materiais", { method: "POST", body: corpo }, { timeoutMs: 60000, tentativas: 1 })
  if (!resposta.ok) {
    const payload = await resposta.json().catch(() => null)
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `Não foi possível anexar o material (${resposta.status}).`)
  }
  return resposta.json()
}

/* ---------- Planilhas comerciais (funil e NEGOCIAÇÕES) ---------- */

export type ResumoPlanilhasComerciais = {
  disponivel: boolean
  erro?: string | null
  gerado_em?: string
  arquivos?: { nome: string; tipo: "FUNIL_VENDAS" | "NEGOCIACOES" | string; enviado_em?: string | null }[]
  totais?: { funil_vendas_atual: number; negociacoes_andamento: number; vendas_realizadas: number }
}

export async function buscarResumoPlanilhas() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/planilhas-comerciais/resumo", { cache: "no-store" }, { timeoutMs: 30000, tentativas: 2 })
  return lerJson<ResumoPlanilhasComerciais>(resposta, "O resumo das planilhas")
}

export async function enviarPlanilhasComerciais(arquivos: { funil?: File | null; negociacoes?: File | null }) {
  const corpo = new FormData()
  if (arquivos.funil) corpo.set("funil", arquivos.funil)
  if (arquivos.negociacoes) corpo.set("negociacoes", arquivos.negociacoes)
  const resposta = await fetchCrmSeguroProxy("crm-seguro/planilhas-comerciais/carga", { method: "POST", body: corpo }, { timeoutMs: 120000, tentativas: 1 })
  return lerJson<ResumoPlanilhasComerciais>(resposta, "O envio das planilhas")
}
