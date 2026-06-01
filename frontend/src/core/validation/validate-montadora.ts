import {
  normalizeMontadora,
} from "../normalization"

export function validateMontadora(
  value?: string | null
) {
  const normalized =
    normalizeMontadora(value)

  return {
    original: value ?? null,
    normalized,
    valid: !!normalized,
  }
}