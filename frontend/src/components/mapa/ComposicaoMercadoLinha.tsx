type MarcaConcorrente = { nome: string; quantidade: number; percentual_mercado: number }

export type ComposicaoMarcaLinha = {
  mercado: number
  carrier: number
  outras_marcas: number
  marca_nao_discriminada: number
  carrier_pct: number
  outras_marcas_pct: number
  marca_nao_discriminada_pct: number
  fechamento_total: number
  fechamento_ok: boolean
  marcas_concorrentes: MarcaConcorrente[]
}

function Linha({ nome, valor, percentual }: { nome: string; valor: number; percentual: number }) {
  return <div>
    <div className="flex items-center justify-between gap-3 text-xs"><span className="text-slate-300">{nome}</span><strong className="text-cyan-300">{valor} · {percentual.toFixed(1)}%</strong></div>
    <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-900"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(100, Math.max(0, percentual))}%` }} /></div>
  </div>
}

export default function ComposicaoMercadoLinha({ dados }: { dados: ComposicaoMarcaLinha }) {
  return <div className="rounded-2xl border border-slate-700/50 bg-[#071226] p-3">
    <div className="mb-3 flex items-center justify-between gap-3"><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">Composição do mercado da linha</p><strong className={dados.fechamento_ok ? "text-xs text-emerald-300" : "text-xs text-red-300"}>{dados.fechamento_total}/{dados.mercado} · {dados.fechamento_ok ? "100% auditado" : "divergência"}</strong></div>
    <div className="space-y-2">
      <Linha nome="Carrier" valor={dados.carrier} percentual={dados.carrier_pct} />
      <Linha nome="Outras marcas" valor={dados.outras_marcas} percentual={dados.outras_marcas_pct} />
      <Linha nome="Marca não discriminada" valor={dados.marca_nao_discriminada} percentual={dados.marca_nao_discriminada_pct} />
    </div>
    {dados.marcas_concorrentes.length > 0 && <details className="mt-3 border-t border-slate-800 pt-3"><summary className="cursor-pointer text-xs font-semibold text-slate-400">Abrir marcas informadas no arquivo</summary><div className="mt-2 space-y-1">{dados.marcas_concorrentes.map((marca) => <div key={marca.nome} className="flex justify-between gap-3 text-xs text-slate-400"><span>{marca.nome}</span><span>{marca.quantidade} · {marca.percentual_mercado.toFixed(1)}%</span></div>)}</div></details>}
  </div>
}
