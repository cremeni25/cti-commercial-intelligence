import {
  normalizeImplementadora,
} from "../normalization"

export function validateImplementadora(
  value?: string | null
) {
  const normalized =
    normalizeImplementadora(value)

  return {
    original: value ?? null,
    normalized,
    valid: !!normalized,
  }
}