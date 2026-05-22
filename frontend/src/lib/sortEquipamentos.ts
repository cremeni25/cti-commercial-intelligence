export function sortEquipamentos(
  equipamentos: string[]
) {
  return [...equipamentos].sort((a, b) => {
    const aCarrier =
      a.toUpperCase() === "CARRIER"

    const bCarrier =
      b.toUpperCase() === "CARRIER"

    if (aCarrier) return -1
    if (bCarrier) return 1

    return a.localeCompare(b)
  })
}