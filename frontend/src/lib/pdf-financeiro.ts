export type PdfFinanceiroLancamento = {
  data: string
  categoria: string
  descricao?: string | null
  forma_pagamento?: string | null
  valor: number
}

export type PdfFinanceiroDados = {
  competencia: string
  receitaMensal: number
  limiteGastos: number
  alertaPercentual: number
  totalGasto: number
  saldoAteLimite: number
  metaPreservacao: number
  receitaAposGastos: number
  projecaoMes: number
  mediaDiaria: number
  gastoEsperadoAteHoje: number
  percentualLimite: number
  percentualReceita: number
  status: string
  lancamentos: PdfFinanceiroLancamento[]
}

const PAGE_W = 595
const PAGE_H = 842
const MARGIN = 44
const LINE = 15

function moeda(valor: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(valor || 0)
}

function competenciaPtBr(valor: string) {
  const [ano, mes] = valor.split("-").map(Number)
  return new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric" }).format(new Date(ano, mes - 1, 1))
}

function win1252(texto: string) {
  const mapa: Record<number, number> = {
    0x20ac: 0x80, 0x201a: 0x82, 0x0192: 0x83, 0x201e: 0x84, 0x2026: 0x85,
    0x2020: 0x86, 0x2021: 0x87, 0x02c6: 0x88, 0x2030: 0x89, 0x0160: 0x8a,
    0x2039: 0x8b, 0x0152: 0x8c, 0x017d: 0x8e, 0x2018: 0x91, 0x2019: 0x92,
    0x201c: 0x93, 0x201d: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
    0x02dc: 0x98, 0x2122: 0x99, 0x0161: 0x9a, 0x203a: 0x9b, 0x0153: 0x9c,
    0x017e: 0x9e, 0x0178: 0x9f,
  }
  const bytes: number[] = []
  for (const ch of texto) {
    const cp = ch.codePointAt(0) || 63
    if (cp <= 0xff) bytes.push(cp)
    else bytes.push(mapa[cp] ?? 63)
  }
  return bytes
}

function textoPdf(texto: string) {
  const bytes = win1252(texto)
  let out = ""
  for (const b of bytes) {
    if (b === 0x28 || b === 0x29 || b === 0x5c) out += `\\${String.fromCharCode(b)}`
    else if (b < 32 || b > 126) out += `\\${b.toString(8).padStart(3, "0")}`
    else out += String.fromCharCode(b)
  }
  return out
}

function cortar(texto: string, max = 88) {
  if (texto.length <= max) return texto
  return `${texto.slice(0, Math.max(0, max - 3))}...`
}

function gerarConteudoPagina(linhas: Array<{ texto: string; x?: number; y: number; size?: number; bold?: boolean }>) {
  return linhas.map((l) => {
    const fonte = l.bold ? "/F2" : "/F1"
    return `BT ${fonte} ${l.size || 10} Tf ${l.x ?? MARGIN} ${l.y} Td (${textoPdf(l.texto)}) Tj ET`
  }).join("\n")
}

export function exportarRelatorioFinanceiroPdf(dados: PdfFinanceiroDados) {
  if (typeof window === "undefined") return

  const paginas: string[] = []
  let linhas: Array<{ texto: string; x?: number; y: number; size?: number; bold?: boolean }> = []
  let y = PAGE_H - MARGIN

  const novaPagina = () => {
    if (linhas.length) paginas.push(gerarConteudoPagina(linhas))
    linhas = []
    y = PAGE_H - MARGIN
  }

  const add = (texto: string, opts?: { size?: number; bold?: boolean; gap?: number; x?: number }) => {
    if (y < 70) novaPagina()
    linhas.push({ texto, y, size: opts?.size, bold: opts?.bold, x: opts?.x })
    y -= opts?.gap ?? LINE
  }

  add("CTI / VIENA SAO PAULO", { size: 9, bold: true, gap: 18 })
  add("RELATORIO DE CONTROLE FINANCEIRO - ADMIN_MASTER", { size: 16, bold: true, gap: 22 })
  add(`Competencia: ${competenciaPtBr(dados.competencia)}`, { size: 10, gap: 22 })

  add("RESUMO EXECUTIVO", { size: 12, bold: true, gap: 18 })
  add(`Status: ${dados.status}`)
  add(`Receita mensal: ${moeda(dados.receitaMensal)}`)
  add(`Limite maximo de gastos: ${moeda(dados.limiteGastos)}`)
  add(`Meta a preservar: ${moeda(dados.metaPreservacao)}`)
  add(`Gasto acumulado: ${moeda(dados.totalGasto)}`)
  add(`Ainda pode gastar: ${moeda(dados.saldoAteLimite)}`)
  add(`Receita apos gastos: ${moeda(dados.receitaAposGastos)}`)
  add(`Projecao do mes: ${moeda(dados.projecaoMes)}`)
  add(`Limite utilizado: ${dados.percentualLimite.toFixed(1)}%`)
  add(`Receita comprometida: ${dados.percentualReceita.toFixed(1)}%`, { gap: 22 })

  add("RITMO E PLANEJAMENTO", { size: 12, bold: true, gap: 18 })
  add(`Media diaria observada: ${moeda(dados.mediaDiaria)}`)
  add(`Esperado ate agora pelo limite mensal: ${moeda(dados.gastoEsperadoAteHoje)}`)
  add(`Primeiro alerta configurado: ${dados.alertaPercentual.toFixed(0)}% do limite`, { gap: 22 })

  add("LANCAMENTOS DO MES", { size: 12, bold: true, gap: 20 })
  if (dados.lancamentos.length === 0) {
    add("Nenhum gasto registrado nesta competencia.")
  } else {
    dados.lancamentos.forEach((item, index) => {
      const data = item.data.split("-").reverse().join("/")
      add(`${index + 1}. ${data} | ${item.categoria} | ${moeda(item.valor)}`, { bold: true })
      const detalhe = [item.descricao, item.forma_pagamento].filter(Boolean).join(" | ")
      if (detalhe) add(`   ${cortar(detalhe, 92)}`, { gap: 18 })
      else y -= 3
    })
  }

  if (linhas.length) paginas.push(gerarConteudoPagina(linhas))

  const objetos: string[] = []
  const pageIds: number[] = []
  const contentIds: number[] = []
  const catalogId = 1
  const pagesId = 2
  const fontRegularId = 3
  const fontBoldId = 4
  let nextId = 5

  paginas.forEach(() => {
    pageIds.push(nextId++)
    contentIds.push(nextId++)
  })

  objetos[catalogId] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`
  objetos[pagesId] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`
  objetos[fontRegularId] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>`
  objetos[fontBoldId] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>`

  paginas.forEach((conteudo, i) => {
    objetos[pageIds[i]] = `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /Font << /F1 ${fontRegularId} 0 R /F2 ${fontBoldId} 0 R >> >> /Contents ${contentIds[i]} 0 R >>`
    objetos[contentIds[i]] = `<< /Length ${win1252(conteudo).length} >>\nstream\n${conteudo}\nendstream`
  })

  const bytes: number[] = []
  const pushAscii = (s: string) => { for (const c of s) bytes.push(c.charCodeAt(0) & 0xff) }
  pushAscii("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
  const offsets: number[] = [0]
  for (let id = 1; id < objetos.length; id++) {
    offsets[id] = bytes.length
    pushAscii(`${id} 0 obj\n`)
    for (const b of win1252(objetos[id])) bytes.push(b)
    pushAscii("\nendobj\n")
  }

  const xref = bytes.length
  pushAscii(`xref\n0 ${objetos.length}\n`)
  pushAscii("0000000000 65535 f \n")
  for (let id = 1; id < objetos.length; id++) pushAscii(`${String(offsets[id]).padStart(10, "0")} 00000 n \n`)
  pushAscii(`trailer\n<< /Size ${objetos.length} /Root ${catalogId} 0 R >>\nstartxref\n${xref}\n%%EOF`)

  const blob = new Blob([new Uint8Array(bytes)], { type: "application/pdf" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `controle-financeiro-${dados.competencia}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
