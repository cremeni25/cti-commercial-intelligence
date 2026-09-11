export type CrmFiltroCampoData = "INCLUSAO" | "PREVISAO"

export type CrmFiltrosComerciais = {
  responsavelId: string
  linha: string
  campoData: CrmFiltroCampoData
  inicio: string
  fim: string
}

export type CrmRegistroAnalitico = {
  id: string
  responsavelId: string
  responsavelNome: string
  linha: string
  dataInclusao: string
  dataPrevista: string
}

export type CrmMetricasPrazo = {
  diasPlanejados: number | null
  diasDecorridos: number | null
  diasAtraso: number
  atrasado: boolean
}

export const FILTROS_CRM_VAZIOS: CrmFiltrosComerciais = {
  responsavelId: "TODOS",
  linha: "TODAS",
  campoData: "INCLUSAO",
  inicio: "",
  fim: "",
}

function texto(valor: unknown): string {
  return String(valor ?? "").trim()
}

export function dataIso(valor: unknown): string {
  const bruto = texto(valor)
  if (!bruto) return ""
  const curta = bruto.slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(curta)) return curta
  const data = new Date(bruto)
  return Number.isNaN(data.getTime()) ? "" : data.toISOString().slice(0, 10)
}

export function normalizarLinha(valor: unknown): string {
  return texto(valor).replace(/\s+/g, " ").trim()
}

export function extrairDataInclusao(registro: Record<string, unknown>): string {
  return dataIso(
    registro.created_at ||
      registro.criado_em ||
      registro.data_criacao ||
      registro.incluido_em ||
      registro.data_inclusao ||
      registro.emissao_em ||
      registro.emitida_em,
  )
}

export function extrairDataPrevista(registro: Record<string, unknown>): string {
  return dataIso(
    registro.data_fechamento_prevista ||
      registro.fechamento_previsto ||
      registro.previsao_fechamento ||
      registro.data_prevista ||
      registro.previsao_conclusao ||
      registro.data_entrega_prevista ||
      registro.data,
  )
}

export function extrairLinha(registro: Record<string, unknown>): string {
  return normalizarLinha(
    registro.linha_equipamentos ||
      registro.linha_equipamento ||
      registro.familia_equipamento ||
      registro.familia ||
      registro.linha ||
      registro.equipamento,
  )
}

export function extrairResponsavelId(registro: Record<string, unknown>): string {
  return texto(registro.responsavel_id || registro.usuario_id || registro.vendedor_id || registro.owner_id)
}

export function extrairResponsavelNome(registro: Record<string, unknown>): string {
  return texto(
    registro.responsavel_nome ||
      registro.usuario_nome ||
      registro.vendedor_nome ||
      registro.representante_nome ||
      registro.consultor_nome,
  )
}

export function montarRegistroAnalitico(
  registro: Record<string, unknown>,
  nomesPorId: Record<string, string> = {},
): CrmRegistroAnalitico {
  const responsavelId = extrairResponsavelId(registro)
  return {
    id: texto(registro.id || registro.oportunidade_id || registro.proposta_id || registro.pedido_id),
    responsavelId,
    responsavelNome: extrairResponsavelNome(registro) || nomesPorId[responsavelId] || "Responsável não identificado",
    linha: extrairLinha(registro) || "Não informada",
    dataInclusao: extrairDataInclusao(registro),
    dataPrevista: extrairDataPrevista(registro),
  }
}

export function calcularMetricasPrazo(
  dataInclusao: string,
  dataPrevista: string,
  encerrado = false,
  hoje = new Date(),
): CrmMetricasPrazo {
  const inicio = dataInclusao ? new Date(`${dataInclusao}T00:00:00`) : null
  const prevista = dataPrevista ? new Date(`${dataPrevista}T00:00:00`) : null
  const agora = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate())
  const dia = 86_400_000
  const diasPlanejados = inicio && prevista ? Math.max(0, Math.round((prevista.getTime() - inicio.getTime()) / dia)) : null
  const diasDecorridos = inicio ? Math.max(0, Math.floor((agora.getTime() - inicio.getTime()) / dia)) : null
  const diasAtraso = !encerrado && prevista && agora.getTime() > prevista.getTime()
    ? Math.floor((agora.getTime() - prevista.getTime()) / dia)
    : 0
  return { diasPlanejados, diasDecorridos, diasAtraso, atrasado: diasAtraso > 0 }
}

export function aplicarFiltrosComerciais<T extends CrmRegistroAnalitico>(
  registros: T[],
  filtros: CrmFiltrosComerciais,
  master: boolean,
  usuarioId?: string,
): T[] {
  return registros.filter((registro) => {
    if (!master && usuarioId && registro.responsavelId && registro.responsavelId !== usuarioId) return false
    if (master && filtros.responsavelId !== "TODOS" && registro.responsavelId !== filtros.responsavelId) return false
    if (filtros.linha !== "TODAS" && registro.linha !== filtros.linha) return false
    const data = filtros.campoData === "PREVISAO" ? registro.dataPrevista : registro.dataInclusao
    if (filtros.inicio && (!data || data < filtros.inicio)) return false
    if (filtros.fim && (!data || data > filtros.fim)) return false
    return true
  })
}

export function opcoesUnicas(valores: string[], vazio?: string): string[] {
  return [...new Set(valores.map((item) => item.trim()).filter((item) => item && item !== vazio))].sort((a, b) =>
    a.localeCompare(b, "pt-BR"),
  )
}
