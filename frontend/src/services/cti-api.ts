import { getSupabaseClient } from "@/core/database/supabase"
import { fetchCrmSeguroProxy } from "@/services/crm-secure"

const API_URL = "/api/cti"
const BACKOFFICE_URL = "/api/crm-proxy/backoffice-fontes"

export type OperationalContextValue = "brasil" | "viena-sp" | `uf-${string}` | `ddd-${string}`

export type ImplementadoraContextual = {
  nome: string
  aliases?: string[]
  quantidade_registros?: number
  valor_total?: number
  estados?: string[]
  municipios?: string[]
  clientes?: number
  linhas_produto?: string[]
}

export type ResultadoImportacao = {
  destino: "ANFIR" | "GOVERNANCA"
  resultado: Record<string, unknown>
}

async function authHeaders(extra?: HeadersInit) {
  const headers = new Headers(extra)
  const supabase = getSupabaseClient()
  const { data } = await supabase.auth.getSession()
  if (data.session?.access_token) headers.set("Authorization", `Bearer ${data.session.access_token}`)
  if (!headers.has("Accept")) headers.set("Accept", "application/json")
  return headers
}

async function request(endpoint: string) {
  const response = await fetch(`${API_URL}${endpoint}`, { cache: "no-store", headers: await authHeaders() })
  const contentType = response.headers.get("content-type") || ""
  if (!contentType.includes("application/json")) {
    const trecho = (await response.text()).slice(0, 160).replace(/\s+/g, " ")
    throw new Error(`Backend CTI retornou conteúdo inválido (${response.status}): ${trecho || "sem conteúdo"}`)
  }
  const payload = await response.json()
  if (!response.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String(payload.detail)
      : `Erro ao carregar ${endpoint}`
    throw new Error(detalhe)
  }
  return payload
}

async function requestSeguro(endpoint: string) {
  const response = await fetchCrmSeguroProxy(endpoint, { cache: "no-store" })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail?: unknown }).detail)
      : `Erro ao carregar ${endpoint}`
    throw new Error(detalhe)
  }
  return payload
}

async function backofficeRequest(caminho: string, init?: RequestInit): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKOFFICE_URL}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: await authHeaders(init?.headers),
  })
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload
      ? (payload as { detail?: unknown }).detail
      : `Falha ${response.status}`
    throw new Error(typeof detalhe === "string" ? detalhe : JSON.stringify(detalhe))
  }
  return payload && typeof payload === "object" ? payload as Record<string, unknown> : {}
}

function objeto(valor: unknown): Record<string, unknown> {
  return valor && typeof valor === "object" && !Array.isArray(valor) ? valor as Record<string, unknown> : {}
}

async function registrarFonteGovernada(file: File): Promise<Record<string, unknown>> {
  const formData = new FormData()
  formData.append("arquivo", file)
  return backofficeRequest("/upload", { method: "POST", body: formData })
}

/**
 * Fluxo operacional para fontes não-ANFIR.
 *
 * O arquivo continua preservado na Governança Universal. Quando a semântica comprova
 * que a fonte é exclusivamente CRM_CADASTRAL, o próprio ADMIN_MASTER que fez o upload
 * dispara a reconciliação controlada. Lotes sem conflito são aprovados e promovidos
 * pelo adaptador canônico de CLIENTE; qualquer divergência interrompe a promoção e
 * permanece visível no Back Office, sem sobrescrever dados existentes.
 */
async function processarFonteGovernada(file: File): Promise<Record<string, unknown>> {
  const registrada = await registrarFonteGovernada(file)
  const fonte = objeto(registrada.fonte)
  const fonteId = String(fonte.id || "")

  if (!fonteId || registrada.duplicado === true) {
    return {
      ...registrada,
      fluxo_operacional: registrada.duplicado === true ? "DUPLICADO_PRESERVADO" : "RECEBIDO",
    }
  }

  try {
    await backofficeRequest(`/${fonteId}/interpretar`, { method: "POST" })
    const semantica = await backofficeRequest(`/${fonteId}/semantica`, { method: "POST" })
    const fonteSemantica = objeto(semantica.fonte)
    const decisao = objeto(semantica.decisao_destino_canonico)
    const classificacao = String(fonteSemantica.classificacao_sugerida || decisao.classificacao || "").toUpperCase()
    const destino = String(decisao.destino || "").toUpperCase()

    if (destino !== "CANDIDATO_OPERACIONAL_VALIDACAO" || classificacao !== "COMERCIAL") {
      return {
        ...registrada,
        fonte: fonteSemantica,
        semantica,
        fluxo_operacional: "GOVERNANCA_REQUER_REVISAO",
      }
    }

    const preparada = await backofficeRequest(`/${fonteId}/reconciliacao/preparar`, { method: "POST" })
    const resumo = objeto(preparada.resumo)
    const naturezas = objeto(resumo.naturezas)
    const totalConflitos = Number(resumo.total_conflitos || 0)
    const chavesNatureza = Object.keys(naturezas).filter((chave) => Number(naturezas[chave] || 0) > 0)
    const exclusivamenteClientes = chavesNatureza.length === 1 && chavesNatureza[0] === "CRM_CADASTRAL"

    if (!exclusivamenteClientes || totalConflitos > 0) {
      return {
        ...registrada,
        fonte: fonteSemantica,
        semantica,
        reconciliacao: preparada,
        fluxo_operacional: "RECONCILIACAO_REQUER_MASTER",
      }
    }

    await backofficeRequest(`/${fonteId}/reconciliacao/aprovar`, { method: "POST" })
    try {
      const promovida = await backofficeRequest(`/${fonteId}/reconciliacao/promover?natureza=CRM_CADASTRAL`, { method: "POST" })
      return {
        ...registrada,
        fonte: fonteSemantica,
        semantica,
        reconciliacao: preparada,
        promocao: promovida,
        fluxo_operacional: "CLIENTES_PROMOVIDOS_COM_SEGURANCA",
      }
    } catch (erroPromocao) {
      return {
        ...registrada,
        fonte: fonteSemantica,
        semantica,
        reconciliacao: preparada,
        fluxo_operacional: "PROMOCAO_BLOQUEADA_DIVERGENCIA",
        mensagem_fluxo: erroPromocao instanceof Error ? erroPromocao.message : "Divergência detectada durante a promoção.",
      }
    }
  } catch (erro) {
    return {
      ...registrada,
      fluxo_operacional: "GOVERNANCA_REQUER_REVISAO",
      mensagem_fluxo: erro instanceof Error ? erro.message : "A fonte foi preservada, mas o processamento automático não foi concluído.",
    }
  }
}

export async function getDashboardExecutivo() { return request("/analytics/dashboard") }
export async function getDashboardExecutivoContextual(query: string | OperationalContextValue) {
  const qs = query.includes("=") ? query : `contexto=${encodeURIComponent(query)}`
  return request(`/analytics/dashboard?${qs}`)
}
export async function getImplementadorasContextuais(query: string | OperationalContextValue): Promise<ImplementadoraContextual[]> {
  const qs = query.includes("=") ? query : `contexto=${encodeURIComponent(query)}`
  const payload = await requestSeguro(`crm-seguro/implementadoras?${qs}`)
  return payload && typeof payload === "object" && "itens" in payload
    ? (payload as { itens?: ImplementadoraContextual[] }).itens || []
    : []
}
export async function getBrasilDashboard() { return request("/brasil/dashboard") }
export async function getBrasilImplementadoras() { return request("/brasil/implementadoras") }
export async function getVienaDashboard() { return request("/autorizados/viena-sp/dashboard") }
export async function getVienaImplementadoras() { return request("/autorizados/viena-sp/implementadoras") }
export async function getVienaHistorico() { return request("/autorizados/viena-sp/historico") }
export async function getInsights() { return request("/dashboard/insights") }
export async function getPipelineStatus() { return request("/pipeline/status") }

export async function uploadArquivo(file: File, contexto: OperationalContextValue = "brasil") {
  const formData = new FormData(); formData.append("file", file); formData.append("contexto_operacional", contexto)
  const response = await fetch(`${API_URL}/upload/anfir/seguro`, { method: "POST", body: formData, headers: await authHeaders() })
  if (!response.ok) throw new Error("Erro ao realizar upload ANFIR")
  return response.json()
}

export async function importarDados(file: File, contexto: OperationalContextValue = "brasil"): Promise<ResultadoImportacao> {
  const extensao = file.name.split(".").pop()?.toLowerCase() || ""
  const planilhaExcel = extensao === "xlsx" || extensao === "xls"

  if (planilhaExcel) {
    const anf: unknown = await uploadArquivo(file, contexto)
    const resultadoAnfir = anf && typeof anf === "object" ? anf as Record<string, unknown> : {}
    if (resultadoAnfir.status !== "SEM_REGISTROS_PROCESSADOS") {
      return { destino: "ANFIR", resultado: resultadoAnfir }
    }
  }

  const governada = await processarFonteGovernada(file)
  return { destino: "GOVERNANCA", resultado: governada }
}

export async function processarPipeline() { return request("/pipeline/status") }

// Mantém o contrato interno da tela de upload sem expor dados operacionais por rota pública.
export async function getDebugAmostra(): Promise<Record<string, unknown>[]> { return [] }
