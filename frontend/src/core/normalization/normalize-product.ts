import {
  PRODUTOS_ALIAS,
} from "../taxonomy/taxonomy.constants"

import { normalizeText } from "./normalize"

export function normalizeProduct(
  value?: string | null
) {
  const normalized =
    normalizeText(value)

  return (
    PRODUTOS_ALIAS[
      normalized as keyof typeof PRODUTOS_ALIAS
    ] ?? null
  )
}