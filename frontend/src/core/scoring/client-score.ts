interface ClientScoreInput {
  faturamento?: number | null
  quantidadeCompras?: number | null
  diasSemComprar?: number | null
}

export function calculateClientScore(
  input: ClientScoreInput
) {
  let score = 0

  // FATURAMENTO
  if ((input.faturamento ?? 0) > 500000) {
    score += 40
  } else if ((input.faturamento ?? 0) > 150000) {
    score += 25
  } else if ((input.faturamento ?? 0) > 14000) {
    score += 10
  }

  // FREQUÊNCIA
  if ((input.quantidadeCompras ?? 0) > 20) {
    score += 30
  } else if (
    (input.quantidadeCompras ?? 0) > 10
  ) {
    score += 20
  } else if (
    (input.quantidadeCompras ?? 0) > 3
  ) {
    score += 10
  }

  // RECÊNCIA
  if ((input.diasSemComprar ?? 999) < 30) {
    score += 30
  } else if (
    (input.diasSemComprar ?? 999) < 90
  ) {
    score += 15
  }

  return {
    score,

    classification:
      score >= 80
        ? "ESTRATÉGICO"
        : score >= 50
        ? "ALTO POTENCIAL"
        : score >= 25
        ? "OPERACIONAL"
        : "BAIXA PRIORIDADE",
  }
}