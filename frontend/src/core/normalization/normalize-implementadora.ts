import {
  IMPLEMENTADORAS_ALIAS,
} from "../taxonomy/taxonomy.constants"

import { normalizeText } from "./normalize"

export function normalizeImplementadora(
  value?: string | null
) {
  const normalized =
    normalizeText(value)

  return (
    IMPLEMENTADORAS_ALIAS[
      normalized as keyof typeof IMPLEMENTADORAS_ALIAS
    ] ?? null
  )
}