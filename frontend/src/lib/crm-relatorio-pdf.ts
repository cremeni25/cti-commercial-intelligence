export type ColunaRelatorioCrm = { chave: string; titulo: string }

function escapar(valor: unknown): string {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

export function exportarRelatorioCrmPdf({
  titulo,
  subtitulo,
  colunas,
  registros,
}: {
  titulo: string
  subtitulo?: string
  colunas: ColunaRelatorioCrm[]
  registros: Array<Record<string, unknown>>
}) {
  if (typeof window === "undefined") return
  const janela = window.open("", "_blank", "noopener,noreferrer,width=1200,height=800")
  if (!janela) return
  const linhas = registros
    .map((registro) => `<tr>${colunas.map((coluna) => `<td>${escapar(registro[coluna.chave])}</td>`).join("")}</tr>`)
    .join("")
  const cabecalho = colunas.map((coluna) => `<th>${escapar(coluna.titulo)}</th>`).join("")
  const geradoEm = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date())
  janela.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${escapar(titulo)}</title><style>
    @page{size:landscape;margin:12mm}body{font-family:Arial,sans-serif;color:#111827;margin:0}h1{font-size:22px;margin:0 0 4px}p{margin:0 0 14px;color:#4b5563;font-size:12px}.meta{margin-bottom:14px;font-size:11px;color:#6b7280}table{width:100%;border-collapse:collapse;font-size:10px}th,td{border:1px solid #d1d5db;padding:6px;text-align:left;vertical-align:top}th{background:#e5e7eb;font-weight:700}tr:nth-child(even){background:#f9fafb}.rodape{margin-top:10px;font-size:10px;color:#6b7280}
  </style></head><body><h1>${escapar(titulo)}</h1>${subtitulo ? `<p>${escapar(subtitulo)}</p>` : ""}<div class="meta">Gerado em ${escapar(geradoEm)} · ${registros.length} registro(s)</div><table><thead><tr>${cabecalho}</tr></thead><tbody>${linhas}</tbody></table><div class="rodape">CTI Inteligência Comercial · relatório baseado na seleção exibida no CRM.</div><script>window.onload=()=>{window.print()}</script></body></html>`)
  janela.document.close()
}
