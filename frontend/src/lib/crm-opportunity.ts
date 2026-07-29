export type RegistroOportunidade = Record<string, unknown>

export type ContextoOportunidade = {
  linhas: string[]
  equipamentos: string[]
  quantidade: number
  municipio: string
  uf: string
  ddd: string
  subRegiao: string
  descricao: string
}

const MARCADOR = "[CONTEXTO CTI]"

export function textoSeguro(valor: unknown): string {
  if (valor == null) return ""
  if (typeof valor === "string" || typeof valor === "number") return String(valor)
  if (typeof valor === "object") {
    const item = valor as RegistroOportunidade
    return textoSeguro(item.nome || item.razao_social || item.nome_fantasia || item.empresa || item.codigo || item.id)
  }
  return ""
}

export function lerContextoOportunidade(item: RegistroOportunidade): ContextoOportunidade {
  const bruto = textoSeguro(item.descricao)
  const [descricaoBase, contextoBruto = ""] = bruto.split(MARCADOR)
  const contexto = new Map<string, string>()
  contextoBruto.split(/\r?\n/).forEach((linha) => {
    const indice = linha.indexOf(":")
    if (indice > 0) contexto.set(linha.slice(0, indice).trim().toLowerCase(), linha.slice(indice + 1).trim())
  })
  const lista = (valor: string) => valor.split(",").map((itemLista) => itemLista.trim()).filter(Boolean)
  return {
    linhas: lista(contexto.get("linhas") || textoSeguro(item.linha_equipamentos)),
    equipamentos: lista(contexto.get("equipamentos") || textoSeguro(item.equipamento)),
    quantidade: Math.max(1, Number(contexto.get("quantidade") || item.quantidade || 1) || 1),
    municipio: contexto.get("municipio") || textoSeguro(item.municipio),
    uf: contexto.get("uf") || textoSeguro(item.estado || item.uf),
    ddd: contexto.get("ddd") || textoSeguro(item.ddd),
    subRegiao: contexto.get("sub_regiao") || textoSeguro(item.sub_regiao),
    descricao: descricaoBase.trim(),
  }
}

export function montarDescricaoComContexto(descricao: string, contexto: Omit<ContextoOportunidade, "descricao">): string {
  const linhas = [descricao.trim(), MARCADOR]
  if (contexto.linhas.length) linhas.push(`linhas: ${contexto.linhas.join(", ")}`)
  if (contexto.equipamentos.length) linhas.push(`equipamentos: ${contexto.equipamentos.join(", ")}`)
  linhas.push(`quantidade: ${Math.max(1, contexto.quantidade)}`)
  if (contexto.municipio) linhas.push(`municipio: ${contexto.municipio}`)
  if (contexto.uf) linhas.push(`uf: ${contexto.uf}`)
  if (contexto.ddd) linhas.push(`ddd: ${contexto.ddd}`)
  if (contexto.subRegiao) linhas.push(`sub_regiao: ${contexto.subRegiao}`)
  return linhas.filter(Boolean).join("\n")
}
