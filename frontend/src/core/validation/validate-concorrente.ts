import {
  normalizeConcorrente,
} from "../normalization"

export function validateConcorrente(
  value?: string | null
) {
  const normalized =
    normalizeConcorrente(value)

  return {
    original: value ?? null,
    normalized,
    valid: !!normalized,
  }
}