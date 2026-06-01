import {
  MONTADORAS_ALIAS,
} from "../taxonomy/taxonomy.constants"

import { normalizeText } from "./normalize"

export function normalizeMontadora(
  value?: string | null
) {
  const normalized =
    normalizeText(value)

  return (
    MONTADORAS_ALIAS[
      normalized as keyof typeof MONTADORAS_ALIAS
    ] ?? null
  )
}