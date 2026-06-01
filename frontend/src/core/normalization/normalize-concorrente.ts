import {
  CONCORRENTES_ALIAS,
} from "../taxonomy/taxonomy.constants"

import { normalizeText } from "./normalize"

export function normalizeConcorrente(
  value?: string | null
) {
  const normalized =
    normalizeText(value)

  return (
    CONCORRENTES_ALIAS[
      normalized as keyof typeof CONCORRENTES_ALIAS
    ] ?? null
  )
}