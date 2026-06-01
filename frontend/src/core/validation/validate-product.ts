import { normalizeProduct } from "../normalization"

export function validateProduct(
  value?: string | null
) {
  const normalized =
    normalizeProduct(value)

  return {
    original: value ?? null,
    normalized,
    valid: !!normalized,
  }
}