import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type PerfilCliente = {
  cliente_id: string
  nome: string | null
  cnpj: string | null
  cidade: string | null
  estado: string | null
  segmento: string | null
  responsavel_id: string | null
  responsavel_nome: string | null
  responsavel_ativo: boolean
  grupo: string
  porte: string
  sinais: string[]
  frota_registrada: number
  frota_carrier: number
  frota_concorrencia: number
  implementadora_principal: string | null
  ultima_compra: string | null
  compras: number
  unidades_compradas: number
  negocios_abertos: number
  valor_negocios_abertos: number
}
export type Rotulos = { grupos: Record<string, string>; portes: Record<string, string>; sinais: Record<string, string> }
export type Setorizacao = {
  total_clientes: number
  por_grupo: Record<string, number>
  por_porte: Record<string, number>
  por_sinal: Record<string, number>
  rotulos: Rotulos
  filtrados: number
  clientes: PerfilCliente[]
}
export type FichaEmpresa = PerfilCliente & {
  cadastro: Record<string, string | null>
  responsaveis_anteriores: { de: string | null; para: string | null; quando: string | null; motivo: string | null }[]
  negocios: { id: string; titulo: string | null; status: string | null; valor: number | null; responsavel: string | null; encerrado: boolean }[]
  atividades_recentes: { data: string | null; tipo: string | null; titulo: string | null; status: string | null; autor: string | null; feita: boolean }[]
  compras_planilha: { mes: string | null; equipamento: string | null; quantidade: number | null; vendedor: string | null }[]
  frota_por_implementadora: Record<string, number>
  frota_por_fabricante: Record<string, number>
}
export type TermoGlossario = { termo: string; definicao: string; sinonimos: string[] }

async function json<T>(resposta: Response, contexto: string): Promise<T> {
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `${contexto} indisponível no momento (${resposta.status}).`)
  }
  return payload as T
}

export async function buscarSetorizacao(filtros: { grupo?: string; sinal?: string } = {}) {
  const params = new URLSearchParams()
  if (filtros.grupo) params.set("grupo", filtros.grupo)
  if (filtros.sinal) params.set("sinal", filtros.sinal)
  const sufixo = params.toString() ? `?${params}` : ""
  return json<Setorizacao>(await fetchCrmSeguroProxy(`crm-seguro/carteira/setorizacao${sufixo}`, { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 }), "A carteira")
}

export async function buscarFichaEmpresa(clienteId: string) {
  return json<FichaEmpresa>(await fetchCrmSeguroProxy(`crm-seguro/carteira/empresa/${encodeURIComponent(clienteId)}`, { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 }), "A ficha da empresa")
}

export async function buscarGlossario() {
  const dados = await json<{ termos: TermoGlossario[] }>(await fetchCrmSeguroProxy("crm-seguro/glossario", { cache: "no-store" }, { timeoutMs: 20000, tentativas: 2 }), "O dicionário")
  return dados.termos || []
}
