import { Implementadora } from "../types/implementadora.types"

import {
  gerarInsightsImplementadora,
} from "../ai/implementadoraInsights"

/*
|--------------------------------------------------------------------------
| ORDENAÇÃO EXECUTIVA
|--------------------------------------------------------------------------
*/

export function ordenarImplementadoras(
  implementadoras: Implementadora[]
) {
  return [...implementadoras].sort(
    (a, b) => b.score - a.score
  )
}

/*
|--------------------------------------------------------------------------
| BADGE EXECUTIVA
|--------------------------------------------------------------------------
*/

export function getRankingBadge(
  index: number
) {
  if (index === 0)
    return "👑 Líder Operacional"

  if (index === 1)
    return "🔥 Alta Expansão"

  if (index === 2)
    return "⚡ Estratégica"

  return "📊 Monitoramento"
}

/*
|--------------------------------------------------------------------------
| SCORE VISUAL
|--------------------------------------------------------------------------
*/

export function getScoreColor(
  score: number
) {
  if (score >= 90)
    return "text-cyan-400"

  if (score >= 75)
    return "text-yellow-400"

  return "text-red-400"
}

/*
|--------------------------------------------------------------------------
| IA OPERACIONAL
|--------------------------------------------------------------------------
*/

export function gerarInsights(
  implementadora: Implementadora
) {
  return gerarInsightsImplementadora(
    implementadora
  )
}