import Link from "next/link"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

const source = {
  file: "funil de vendas 2026(20260814-104652).xlsx",
  sha256: "54bb20087d96013e5a814a1d378f37315987c56b4a617631bd9603725ebb4583",
  records: 906,
  units: 3116,
  nominalValue: 193255897.4,
}

const sheets = [["BACKLOG", 277], ["OPORTUNIDADE", 518], ["INTERMEDIAÇÃO - OEM", 111]]
const years = [["2023", 33], ["2024", 381], ["2025", 307], ["2026", 185]]
const channels = [["DIRETA", 795], ["INDIRETA_OEM", 111]]
const reps = [["ANDERSON - VIENA SP", 403], ["VIENA SP", 287], ["ANDRE - VIENA SP", 128], ["NATHAN - VIENA SP", 66], ["MÔNICA - VIENA SP", 15], ["MICHELE - VIENA SP", 4], ["AUSENTE", 3]]
const statuses = [["INDETERMINADO", 625], ["PERDIDO", 196], ["GANHO", 53], ["EM_NEGOCIACAO", 32]]
const losses = [["OUTRO", 158], ["SEM_RETORNO", 31], ["CONCORRENCIA", 14], ["PRECO", 12], ["COMPROU_USADO", 6]]
const equipment = [["X4 7500", 184], ["SUPRA 850", 123], ["SUPRA 750", 101], ["VECTOR 8500", 32], ["SUPRA 1150", 27], ["CITIMAX 500AE", 21], ["VECTOR HE19", 20], ["SUPRA 1150MT", 19], ["CITIMAX 500AE 24V", 18], ["CITIMAX 700AE 24V", 17], ["CITIMAX 400 12V", 16], ["CITIMAX 700AE", 16]]
const implementers = [["IBIPORÃ", 42], ["FACCHINI", 14], ["LABONIA", 14], ["PAVAN", 14], ["RANDON", 9], ["NÃO_IDENTIFICADA", 9], ["NIJU", 7], ["MULTIEIXO", 6], ["FRATELI", 6], ["MERCOSUL", 1]]

export default function HistoricoComercialPage() {
  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar />
      <section className="min-w-0 flex-1 overflow-x-hidden">
        <Topbar />
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">Consulta histórica</p>
              <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200">SOMENTE CONSULTA · NÃO ALTERA O CRM</span>
            </div>
            <h1 className="mt-3 text-3xl font-bold">Histórico Comercial 2023–2026</h1>
            <p className="mt-2 max-w-5xl text-sm text-slate-400">Base histórica consolidada para consulta e auditoria. Clique em qualquer total ou linha para abrir os registros que formam o número.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 min-[1800px]:grid-cols-4">
            <Kpi title="Registros" value={source.records.toLocaleString("pt-BR")} note="277 + 518 + 111" href={drill("Histórico Comercial · todos os registros")} />
            <Kpi title="Unidades nominais" value={source.units.toLocaleString("pt-BR")} note="Medida de auditoria" href={drill("Histórico Comercial · registros por unidade nominal")} />
            <Kpi title="Valor nominal" value={money(source.nominalValue)} note="Não classificado como receita" href={drill("Histórico Comercial · composição do valor nominal")} />
            <Kpi title="Divergências aritméticas" value="0" note="Qtd × unitário × total" tone="good" />
          </section>

          <section className="rounded-2xl border border-[#17304d] bg-[#071226] p-5">
            <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
              <div className="min-w-0"><h2 className="text-lg font-semibold">Rastreabilidade da fonte</h2><p className="mt-2 break-words text-sm text-slate-400">{source.file}</p><p className="mt-1 break-all font-mono text-xs text-slate-500">SHA-256: {source.sha256}</p></div>
              <Link href={drill("Fonte histórica imutável · 906 registros")} className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200 transition hover:border-emerald-400">Fonte imutável confirmada · 906 registros</Link>
            </div>
          </section>

          <section className="grid gap-5 xl:grid-cols-3">
            <Panel title="Origem por aba"><Rows items={sheets} total={906} campo="aba" titulo="Histórico Comercial · Origem por aba" /></Panel>
            <Panel title="Distribuição por ano"><Rows items={years} total={906} campo="ano" titulo="Histórico Comercial · Distribuição por ano" /></Panel>
            <Panel title="Canal de venda"><Rows items={channels} total={906} campo="canal" titulo="Histórico Comercial · Canal de venda" /></Panel>
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <Panel title="Responsabilidade comercial normalizada">
              <Rows items={reps} total={906} campo="representante" titulo="Histórico Comercial · Responsabilidade comercial" />
              <div className="mt-4 rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 text-sm text-cyan-100">15 registros preservam CARLA como origem histórica e são atribuídos a MÔNICA como responsabilidade territorial atual.</div>
              <div className="mt-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">287 registros permanecem “VIENA SP” sem atribuição arbitrária a vendedor individual.</div>
            </Panel>
            <Panel title="Status reconstruído para auditoria"><Rows items={statuses} total={906} campo="status" titulo="Histórico Comercial · Status" /></Panel>
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <Panel title="Principais equipamentos históricos"><Rows items={equipment} total={906} campo="equipamento" titulo="Histórico Comercial · Equipamento" compact /></Panel>
            <Panel title="Implementadoras identificadas no canal OEM"><Rows items={implementers} total={111} campo="implementadora" titulo="Histórico Comercial · Implementadora" compact /></Panel>
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <Panel title="Motivos de perda / evidências"><Rows items={losses} total={221} campo="motivo_perda" titulo="Histórico Comercial · Motivo de perda" /></Panel>
            <Panel title="Regras de uso do histórico">
              <Checklist label="Arquivo original preservado" /><Checklist label="Origem arquivo → aba → linha preservada" /><Checklist label="DIRETA e INDIRETA_OEM permanecem separados" /><Checklist label="CARLA → MÔNICA sem apagar autoria histórica" /><Checklist label="Modelos históricos fora do catálogo são preservados" /><Checklist label="Este histórico não altera dados do CRM operacional" /><Checklist label="Este histórico não é incorporado automaticamente à IA Comercial" />
            </Panel>
          </section>

          <section className="rounded-2xl border border-cyan-500/30 bg-cyan-950/20 p-5"><h2 className="font-semibold text-cyan-100">Como usar este histórico</h2><p className="mt-2 text-sm text-cyan-100/80">Os totais agora são portas de investigação. Clique em uma linha para abrir exatamente os registros que formam aquele total e use “Voltar à tela anterior” para retornar ao mesmo contexto.</p></section>
        </div>
      </section>
    </main>
  )
}

function drill(titulo: string, campo?: string, valor?: string) {
  const query = new URLSearchParams({ camada: "historico", titulo, subtitulo: "Registros individualizados da fonte histórica homologada" })
  if (campo) query.set("campo", campo)
  if (valor) query.set("valor", valor)
  return `/detalhamento?${query.toString()}`
}

function Kpi({ title, value, note, tone, href }: { title: string; value: string; note: string; tone?: "good"; href?: string }) {
  const body = <><p className="text-xs uppercase tracking-wider text-slate-500">{title}</p><p className={`mt-2 break-words text-[clamp(1.5rem,2.35vw,1.875rem)] font-bold leading-tight ${tone === "good" ? "text-emerald-300" : "text-white"}`}>{value}</p><p className="mt-2 text-xs text-slate-500">{note}</p></>
  return href ? <Link href={href} className="min-w-0 rounded-2xl border border-[#17304d] bg-[#071226] p-5 transition hover:border-cyan-500/70 hover:bg-[#0a1a31]">{body}</Link> : <div className="min-w-0 rounded-2xl border border-[#17304d] bg-[#071226] p-5">{body}</div>
}
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="min-w-0 rounded-2xl border border-[#17304d] bg-[#071226] p-5"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section> }
function Rows({ items, total, compact = false, campo, titulo }: { items: (string | number)[][]; total: number; compact?: boolean; campo: string; titulo: string }) {
  return <div className={compact ? "grid gap-2 sm:grid-cols-2" : "space-y-2"}>{items.map(([label, raw]) => { const value = Number(raw); const pct = total ? value / total * 100 : 0; return <Link href={drill(`${titulo} · ${String(label)}`, campo, String(label))} key={String(label)} className="block min-w-0 rounded-xl border border-[#13203f] bg-[#08162d] p-3 transition hover:border-cyan-500/60 hover:bg-[#0b1d38]"><div className="flex items-center justify-between gap-3 text-sm"><span className="min-w-0 truncate text-slate-300">{label}</span><strong className="text-cyan-200">{value.toLocaleString("pt-BR")}</strong></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#13203f]"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.max(2, Math.min(100, pct))}%` }} /></div><p className="mt-1 text-right text-[11px] text-slate-500">{pct.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% · clique para detalhar</p></Link> })}</div>
}
function Checklist({ label }: { label: string }) { return <div className="mb-2 flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-sm text-emerald-100"><span className="text-emerald-400">✓</span><span>{label}</span></div> }
function money(value: number) { return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }) }
