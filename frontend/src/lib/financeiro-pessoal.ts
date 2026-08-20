export type StatusFinanceiro = "NORMAL" | "ATENCAO" | "CRITICO" | "LIMITE"

export type ResumoFinanceiro = {
  totalGasto: number
  percentualConsumido: number
  saldoAteLimite: number
  receitaPreservada: number
  mediaDiaria: number
  gastoEsperadoAteHoje: number
  projecaoFechamento: number
  diasAteLimite: number | null
  ritmoAcimaDoPlanejado: boolean
  status: StatusFinanceiro
}

export function moeda(valor: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number.isFinite(valor) ? valor : 0)
}

export function hojeLocal() {
  const agora = new Date()
  const ano = agora.getFullYear()
  const mes = String(agora.getMonth() + 1).padStart(2, "0")
  const dia = String(agora.getDate()).padStart(2, "0")
  return `${ano}-${mes}-${dia}`
}

export function competenciaAtual() {
  return hojeLocal().slice(0, 7)
}

export function inicioCompetencia(competencia: string) {
  return `${competencia}-01`
}

export function proximaCompetencia(competencia: string) {
  const [ano, mes] = competencia.split("-").map(Number)
  const data = new Date(ano, mes, 1)
  const proximoAno = data.getFullYear()
  const proximoMes = String(data.getMonth() + 1).padStart(2, "0")
  return `${proximoAno}-${proximoMes}-01`
}

export function diasNoMes(competencia: string) {
  const [ano, mes] = competencia.split("-").map(Number)
  return new Date(ano, mes, 0).getDate()
}

export function diaDeReferencia(competencia: string, data = new Date()) {
  const atual = `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}`
  if (competencia === atual) return data.getDate()
  if (competencia < atual) return diasNoMes(competencia)
  return 1
}

export function calcularResumoFinanceiro({
  valores,
  receitaMensal,
  limiteGastos,
  alertaPercentual,
  competencia,
}: {
  valores: number[]
  receitaMensal: number
  limiteGastos: number
  alertaPercentual: number
  competencia: string
}): ResumoFinanceiro {
  const totalGasto = valores.reduce((soma, valor) => soma + (Number(valor) || 0), 0)
  const percentualConsumido = limiteGastos > 0 ? (totalGasto / limiteGastos) * 100 : 0
  const saldoAteLimite = Math.max(limiteGastos - totalGasto, 0)
  const receitaPreservada = receitaMensal - totalGasto
  const diasMes = diasNoMes(competencia)
  const diaReferencia = Math.max(1, diaDeReferencia(competencia))
  const mediaDiaria = totalGasto / diaReferencia
  const gastoEsperadoAteHoje = limiteGastos > 0 ? (limiteGastos * diaReferencia) / diasMes : 0
  const projecaoFechamento = mediaDiaria * diasMes
  const diasAteLimite = limiteGastos > totalGasto && mediaDiaria > 0
    ? Math.ceil((limiteGastos - totalGasto) / mediaDiaria)
    : null

  let status: StatusFinanceiro = "NORMAL"
  if (percentualConsumido >= 100) status = "LIMITE"
  else if (percentualConsumido >= 90) status = "CRITICO"
  else if (percentualConsumido >= alertaPercentual) status = "ATENCAO"

  return {
    totalGasto,
    percentualConsumido,
    saldoAteLimite,
    receitaPreservada,
    mediaDiaria,
    gastoEsperadoAteHoje,
    projecaoFechamento,
    diasAteLimite,
    ritmoAcimaDoPlanejado: limiteGastos > 0 && totalGasto > gastoEsperadoAteHoje,
    status,
  }
}
