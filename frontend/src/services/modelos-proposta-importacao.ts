import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

export type ImportacaoPacoteResultado = {
  ok: boolean
  total_esperado: number
  importados: number
  ignorados_ja_armazenados: number
  resultados: Array<{
    modelo_id: string
    equipamento: string
    arquivo: string
    caminho?: string
    status: string
  }>
}

type BackendResultado = {
  ok?: boolean
  arquivos_unicos_recebidos?: number
  modelos_processados?: number
  armazenados_ou_existentes?: number
  falhas?: Array<{
    modelo_id?: string
    arquivo?: string
    erro?: string
  }>
  resultados?: Array<{
    modelo_id?: string
    equipamento?: string
    arquivo?: string
    caminho?: string
    situacao?: string
    status?: string
  }>
}

function formatApiDetail(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) return detail

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item
        if (item && typeof item === "object") {
          const record = item as Record<string, unknown>
          const location = Array.isArray(record.loc) ? record.loc.join(" → ") : ""
          const message = typeof record.msg === "string" ? record.msg : JSON.stringify(record)
          return location ? `${location}: ${message}` : message
        }
        return String(item)
      })
      .filter(Boolean)
    if (messages.length) return messages.join(" | ")
  }

  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>
    const mensagem = typeof record.mensagem === "string" ? record.mensagem : ""
    const faltantes = Array.isArray(record.faltantes) ? record.faltantes.map(String) : []
    const extras = Array.isArray(record.extras) ? record.extras.map(String) : []
    const partes = [mensagem]
    if (faltantes.length) partes.push(`Faltantes: ${faltantes.join(", ")}`)
    if (extras.length) partes.push(`Extras: ${extras.join(", ")}`)
    const texto = partes.filter(Boolean).join(" | ")
    if (texto) return texto
    return JSON.stringify(record)
  }

  return `Falha ao importar o pacote (${status}).`
}

export async function importarPacoteModelos(file: File): Promise<ImportacaoPacoteResultado> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()

  if (error || !data.session?.access_token) {
    throw new Error("Sessão autenticada não encontrada.")
  }

  const formData = new FormData()
  formData.append("pacote", file)

  const response = await fetch(`${API_URL}/modelos-proposta-importacao/pacote`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${data.session.access_token}`,
    },
    body: formData,
  })

  const payload = (await response.json().catch(() => null)) as BackendResultado | { detail?: unknown } | null
  if (!response.ok) {
    const detail = payload && "detail" in payload ? payload.detail : null
    throw new Error(formatApiDetail(detail, response.status))
  }

  const backend = (payload || {}) as BackendResultado
  const resultadosBackend = backend.resultados || []
  const resultados = resultadosBackend.map((item) => ({
    modelo_id: String(item.modelo_id || ""),
    equipamento: String(item.equipamento || item.arquivo || "Modelo de proposta"),
    arquivo: String(item.arquivo || ""),
    caminho: item.caminho,
    status: String(item.status || item.situacao || "PROCESSADO"),
  }))

  const importados = resultados.filter((item) => item.status === "ARMAZENADO").length
  const ignorados = resultados.filter((item) => item.status === "JA_ARMAZENADO").length

  if (Array.isArray(backend.falhas) && backend.falhas.length) {
    const detalhes = backend.falhas
      .map((item) => `${item.arquivo || item.modelo_id || "Arquivo"}: ${item.erro || "falha não identificada"}`)
      .join(" | ")
    throw new Error(`A importação não foi concluída integralmente. ${detalhes}`)
  }

  return {
    ok: backend.ok !== false,
    total_esperado: Number(backend.modelos_processados || backend.arquivos_unicos_recebidos || resultados.length),
    importados,
    ignorados_ja_armazenados: ignorados,
    resultados,
  }
}
