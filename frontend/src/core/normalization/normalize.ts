export function normalizeText(
  value?: string | null
) {
  if (!value) {
    return ""
  }

  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9 ]/g, "")
    .trim()
    .toUpperCase()
}