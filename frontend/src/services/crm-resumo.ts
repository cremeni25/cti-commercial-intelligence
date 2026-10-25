export type RegistroResumoCrm = Record<string, unknown>

// Uma resposta inválida não equivale a uma carteira vazia.
export function registrosResumoCrm(payload: unknown): RegistroResumoCrm[] {
  if (Array.isArray(payload)) return payload as RegistroResumoCrm[]
  if (payload && typeof payload === "object") {
    const registro = payload as RegistroResumoCrm
    for (const chave of ["dados", "itens", "oportunidades", "resultado", "atividades", "clientes", "propostas", "pedidos", "vendas"]) {
      if (Array.isArray(registro[chave])) return registro[chave] as RegistroResumoCrm[]
    }
  }
  throw new Error("O CTI recebeu um resumo incompleto. Tente sincronizar novamente.")
}

export function diaLocalCrm(data = new Date()): string {
  return `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}-${String(data.getDate()).padStart(2, "0")}`
}

export function ocorreuNoDiaCrm(valor: unknown, hoje = new Date()): boolean {
  const texto = String(valor ?? "").trim()
  // Datas sem horário representam o dia comercial, sem conversão de fuso.
  if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) return texto === diaLocalCrm(hoje)
  if (!texto) return false
  const data = new Date(texto)
  return !Number.isNaN(data.getTime()) && diaLocalCrm(data) === diaLocalCrm(hoje)
}
