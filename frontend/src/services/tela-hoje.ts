import { fetchCrmSeguroProxy } from "@/services/crm-secure"

export type CartaoHoje = {
  tipo: "negocio" | "agenda" | "carteira" | "comissao"
  titulo: string
  detalhe: string
  acao: string
  cliente: string | null
  valor: number
  href: string
  href_app: string
  tom: "risco" | "oportunidade" | "acao"
}
export type Hoje = { manchete: string; cartoes: CartaoHoje[]; limitacoes: string[] }

export async function buscarHoje() {
  const resposta = await fetchCrmSeguroProxy("crm-seguro/hoje", { cache: "no-store" }, { timeoutMs: 90000, tentativas: 2 })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail || "") : ""
    throw new Error(detalhe || `A tela Hoje está indisponível no momento (${resposta.status}).`)
  }
  return payload as Hoje
}
