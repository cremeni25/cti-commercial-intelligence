import { getSupabaseClient } from "@/core/database/supabase"
import { API_URL } from "@/lib/api"

export interface CatalogAlias {
  id?: string
  alias: string
  active?: boolean
}

export interface CatalogModel {
  id?: string
  canonical_name: string
  active: boolean
  aliases: Array<string | CatalogAlias>
}

export interface CatalogLine {
  id?: string
  code: string
  name: string
  active: boolean
  aliases: Array<string | CatalogAlias>
  models: CatalogModel[]
}

export interface ProductCatalog {
  source: "supabase" | "fallback"
  editable: boolean
  lines: CatalogLine[]
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH"
  body?: unknown
}

async function authenticatedRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()

  if (error || !data.session?.access_token) {
    throw new Error("Sessão autenticada não encontrada.")
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: options.method ?? "GET",
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${data.session.access_token}`,
      "Content-Type": "application/json",
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail || `Falha na API administrativa (${response.status}).`
    throw new Error(detail)
  }

  return response.json()
}

export function getProductCatalog() {
  return authenticatedRequest<ProductCatalog>("/admin/product-catalog")
}

export function createCatalogModel(lineId: string, canonicalName: string) {
  return authenticatedRequest<CatalogModel>("/admin/product-catalog/models", {
    method: "POST",
    body: { line_id: lineId, canonical_name: canonicalName },
  })
}

export function createCatalogAlias(alias: string, destination: { modelId?: string; lineId?: string }) {
  return authenticatedRequest<CatalogAlias>("/admin/product-catalog/aliases", {
    method: "POST",
    body: {
      alias,
      model_id: destination.modelId,
      line_id: destination.lineId,
    },
  })
}

export function setCatalogEntityActive(
  entity: "lines" | "models" | "aliases",
  id: string,
  active: boolean,
) {
  return authenticatedRequest(`/admin/product-catalog/${entity}/${id}/active`, {
    method: "PATCH",
    body: { active },
  })
}
