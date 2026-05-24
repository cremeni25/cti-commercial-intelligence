import { Implementadora } from "@/modules/implementadoras/types/implementadora.types"

interface InsightResponse {
  alertaIA: string

  recomendacoesIA: string[]

  oportunidadeIA: string

  riscoConcorrencial: string

  prioridadeEstrategica: string

  criticidade: string

  temperaturaOperacional: string

  badgeExecutiva: string
}

export function gerarInsightsImplementadora(
  implementadora: Implementadora
): InsightResponse {
  const scoreComercial =
    implementadora.scoreComercial ??
    implementadora.score

  const crescimento =
    implementadora.crescimento ?? 0

  const marketShare =
    implementadora.marketShare ?? 0

  const dominancia =
    implementadora.dominanciaRegional ??
    "Moderada"

  const concorrente =
    implementadora.concorrentePrincipal ??
    "Concorrente regional"

  const presencaCarrier =
    implementadora.presencaCarrier ??
    "Moderada"

  /*
   * INTELIGÊNCIA OPERACIONAL DINÂMICA
   */

  const forcaOperacional =
    (
      implementadora.score +
      scoreComercial +
      marketShare +
      crescimento
    ) / 4

  const pressaoConcorrencial =
      implementadora.concorrentesRelacionados
        ?.length ?? 0

  const nivelExpansao =
      crescimento >= 15
        ? "EXPANSÃO ACELERADA"

        : crescimento >= 8
        ? "EXPANSÃO MODERADA"

        : "ESTABILIDADE"

  const prioridadeRegional =
      marketShare >= 35
        ? "DOMINÂNCIA REGIONAL"

        : marketShare >= 20
        ? "PRESENÇA ESTRATÉGICA"

        : "OPORTUNIDADE DE EXPANSÃO"

  /*
   * CLASSIFICAÇÃO EXECUTIVA
   */

  const criticidade =
    implementadora.score >= 90
      ? "PRIORIDADE MÁXIMA"

      : implementadora.score >= 75
      ? "MONITORAMENTO"

      : "RISCO OPERACIONAL"

  /*
   * TEMPERATURA OPERACIONAL
   */

  const temperaturaOperacional =
    implementadora.score >= 90
      ? "🔥 Operação Aquecida"

      : implementadora.score >= 75
      ? "⚡ Operação Estável"

      : "❄ Operação Fria"

  /*
   * BADGE EXECUTIVA
   */

  const badgeExecutiva =
    implementadora.status === "Inativo"
      ? "🔴 Recuperação"

      : implementadora.score >= 90
      ? "👑 Estratégica"

      : implementadora.score >= 75
      ? "🟡 Monitoramento"

      : "⚠ Atenção"

  /*
   * IMPLEMENTADORA INATIVA
   */

  if (
    implementadora.status === "Inativo"
  ) {
    return {
      criticidade,

      temperaturaOperacional,

      badgeExecutiva,

      alertaIA:
        "Implementadora apresenta retração operacional e perda de relevância estratégica regional.",

      recomendacoesIA: [
        "Retomar relacionamento comercial",
        "Agendar visita estratégica",
        "Reavaliar presença regional",
        "Analisar avanço concorrencial",
      ],

      oportunidadeIA:
        "Existe oportunidade de reativação regional através de operações refrigeradas locais.",

      riscoConcorrencial: "Alto",

      prioridadeEstrategica: "Média",
    }
  }

  /*
   * LIDERANÇA OPERACIONAL
   */

  if (
    scoreComercial >= 85 &&
    marketShare >= 30
  ) {
    return {
      criticidade,

      temperaturaOperacional,

      badgeExecutiva,

      alertaIA:
        `Implementadora apresenta liderança regional com ${marketShare}% de market share e forte estabilidade operacional.`,

      recomendacoesIA: [
        "Expandir presença Carrier",
        "Fortalecer relacionamento premium",
        "Priorizar expansão territorial",
        "Aumentar frequência comercial",
      ],

      oportunidadeIA:
        `A região demonstra elevado potencial de crescimento com dominância ${dominancia} e forte presença da Carrier (${presencaCarrier}).`,

      riscoConcorrencial: "Baixo",

      prioridadeEstrategica: "Máxima",
    }
  }

  /*
   * CRESCIMENTO POSITIVO
   */

  if (
    crescimento > 10
  ) {
    return {
      criticidade,

      temperaturaOperacional,

      badgeExecutiva,

      alertaIA:
        `Implementadora apresenta crescimento operacional acelerado (${crescimento}%) e avanço competitivo regional.`,

      recomendacoesIA: [
        "Aumentar presença comercial",
        "Expandir operações Carrier",
        "Monitorar evolução concorrencial",
        "Fortalecer relacionamento regional",
      ],

      oportunidadeIA:
        `Existe potencial relevante de expansão antes do avanço do concorrente ${concorrente}.`,

      riscoConcorrencial: "Médio",

      prioridadeEstrategica: "Alta",
    }
  }

  /*
   * RISCO CONCORRENCIAL
   */

  if (
    marketShare < 15
  ) {
    return {
      criticidade,

      temperaturaOperacional,

      badgeExecutiva,

      alertaIA:
        `Baixa participação regional (${marketShare}%) e avanço competitivo identificado.`,

      recomendacoesIA: [
        "Reforçar presença regional",
        "Aumentar relacionamento comercial",
        "Expandir ações estratégicas",
        "Analisar domínio concorrencial",
      ],

      oportunidadeIA:
        `Ainda existe espaço operacional relevante para crescimento regional da Carrier.`,

      riscoConcorrencial: "Alto",

      prioridadeEstrategica: "Alta",
    }
  }

  /*
   * ESTABILIDADE MODERADA
   */

  return {
    criticidade,

    temperaturaOperacional,

    badgeExecutiva,

    alertaIA:
      "Implementadora possui estabilidade moderada com necessidade de fortalecimento competitivo.",

    recomendacoesIA: [
      "Intensificar follow-up",
      "Monitorar concorrência",
      "Expandir relacionamento regional",
      "Aumentar presença comercial",
    ],

    oportunidadeIA:
      `A presença Carrier (${presencaCarrier}) ainda permite crescimento operacional sustentável.`,

    riscoConcorrencial: "Médio",

    prioridadeEstrategica: "Alta",
  }
}