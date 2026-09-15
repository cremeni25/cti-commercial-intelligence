type Registro = Record<string, unknown>

type Props = {
  registro: Registro
  propostas?: number
  pedidos?: number
  vendas?: number
  compacto?: boolean
}

const FINAIS_GANHOS = new Set(["GANHO", "GANHA", "VENDIDO", "VENDA", "FATURADO", "FECHADO_GANHO", "CONVERTIDO"])
const FINAIS_PERDIDOS = new Set(["PERDIDO", "PERDIDA", "CANCELADO", "CANCELADA", "ENCERRADO", "FECHADO_PERDIDO"])

function texto(valor: unknown) {
  return String(valor ?? "").trim()
}

function chave(valor: unknown) {
  return texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase()
}

export default function CicloComercial({ registro, propostas = 0, pedidos = 0, vendas = 0, compacto = false }: Props) {
  const status = chave(registro.etapa || registro.status || registro.status_oportunidade)
  const temProposta = propostas > 0 || Boolean(texto(registro.proposta_id || registro.proposta_numero)) || status.includes("PROPOST")
  const temPedido = pedidos > 0 || Boolean(texto(registro.pedido_id || registro.pedido_numero)) || status.includes("PEDIDO")
  const vendaGanha = vendas > 0 || FINAIS_GANHOS.has(status) || status.includes("VENDA") || status.includes("FATUR")
  const perdido = FINAIS_PERDIDOS.has(status)

  const etapas = [
    { chave: "INTERACAO", rotulo: "Interação", existe: true },
    { chave: "OPORTUNIDADE", rotulo: "Oportunidade", existe: true },
    { chave: "PROPOSTA", rotulo: "Proposta", existe: temProposta },
    { chave: "PEDIDO", rotulo: "Pedido", existe: temPedido },
    { chave: "VENDA", rotulo: "Venda", existe: vendaGanha },
  ]

  const indiceAtual = vendaGanha ? 4 : temPedido ? 3 : temProposta ? 2 : 1

  return <section className={`rounded-3xl border border-[#16325c] bg-[#07162b] ${compacto ? "p-4" : "p-5 sm:p-6"}`}>
    <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-400">Ciclo comercial</p>
        <h2 className={`${compacto ? "mt-1 text-lg" : "mt-2 text-xl"} font-bold text-white`}>Onde este negócio está agora</h2>
      </div>
      <span className={`mt-2 w-fit rounded-full border px-3 py-1 text-xs font-semibold sm:mt-0 ${perdido ? "border-red-900 bg-red-950/30 text-red-200" : vendaGanha ? "border-emerald-800 bg-emerald-950/30 text-emerald-200" : "border-cyan-800 bg-cyan-950/30 text-cyan-200"}`}>
        {perdido ? "Encerrado · perdido" : vendaGanha ? "Venda concluída" : `Em andamento · ${etapas[indiceAtual].rotulo}`}
      </span>
    </div>

    <div className="mt-5 grid grid-cols-5 gap-2">
      {etapas.map((etapa, indice) => {
        const atual = !perdido && indice === indiceAtual
        const concluida = etapa.existe && indice < indiceAtual
        const feita = etapa.existe && (concluida || atual || vendaGanha && indice === 4)
        const pulada = vendaGanha && indice > 1 && indice < 4 && !etapa.existe
        return <div key={etapa.chave} className="min-w-0">
          <div className={`h-2 rounded-full ${atual ? "bg-cyan-400" : feita ? "bg-emerald-500" : pulada ? "bg-slate-700" : "bg-[#13203f]"}`} />
          <p className={`mt-2 truncate text-center text-[10px] font-semibold sm:text-xs ${atual ? "text-cyan-300" : feita ? "text-emerald-300" : "text-slate-500"}`}>{etapa.rotulo}</p>
          {pulada && <p className="mt-1 text-center text-[9px] text-slate-600">não exigida</p>}
        </div>
      })}
    </div>

    {!compacto && <p className="mt-5 text-sm leading-6 text-slate-400">O CTI registra o caminho real do negócio. Proposta e pedido são marcos comerciais, não etapas obrigatórias: uma oportunidade pode avançar diretamente para venda quando isso refletir a realidade da negociação.</p>}
  </section>
}
