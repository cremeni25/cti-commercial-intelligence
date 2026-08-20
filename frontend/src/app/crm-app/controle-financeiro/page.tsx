"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertTriangle, ArrowLeft, Gauge, PiggyBank, Plus, Save, Trash2, TrendingUp, WalletCards } from "lucide-react"
import { useAuth } from "@/core/auth"
import { getSupabaseClient } from "@/core/database/supabase"
import {
  calcularResumoFinanceiro,
  competenciaAtual,
  hojeLocal,
  inicioCompetencia,
  moeda,
  proximaCompetencia,
  type StatusFinanceiro,
} from "@/lib/financeiro-pessoal"

type ConfigFinanceira = {
  id: string
  auth_id: string
  competencia: string
  receita_mensal: number
  limite_gastos: number
  alerta_percentual: number
}

type Lancamento = {
  id: string
  auth_id: string
  data: string
  categoria: string
  descricao: string | null
  valor: number
  forma_pagamento: string | null
  created_at: string
}

const CATEGORIAS = ["Alimentação", "Combustível", "Mercado", "Casa", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Outros"]
const FORMAS_PAGAMENTO = ["", "Pix", "Débito", "Crédito", "Dinheiro", "Transferência", "Boleto"]

function numero(valor: string | number | null | undefined) {
  const convertido = Number(valor ?? 0)
  return Number.isFinite(convertido) ? convertido : 0
}

function rotuloStatus(status: StatusFinanceiro) {
  if (status === "LIMITE") return "Limite atingido"
  if (status === "CRITICO") return "Faixa crítica"
  if (status === "ATENCAO") return "Atenção"
  return "Dentro do planejado"
}

function classeStatus(status: StatusFinanceiro) {
  if (status === "LIMITE") return "border-red-800 bg-red-950/35 text-red-100"
  if (status === "CRITICO") return "border-orange-800 bg-orange-950/30 text-orange-100"
  if (status === "ATENCAO") return "border-amber-800 bg-amber-950/30 text-amber-100"
  return "border-emerald-900 bg-emerald-950/25 text-emerald-100"
}

export default function ControleFinanceiroPage() {
  const { usuario, loading: authLoading } = useAuth()
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [competencia, setCompetencia] = useState(competenciaAtual())
  const [authId, setAuthId] = useState("")
  const [config, setConfig] = useState<ConfigFinanceira | null>(null)
  const [lancamentos, setLancamentos] = useState<Lancamento[]>([])
  const [receitaMensal, setReceitaMensal] = useState("")
  const [limiteGastos, setLimiteGastos] = useState("")
  const [alertaPercentual, setAlertaPercentual] = useState("80")
  const [valor, setValor] = useState("")
  const [categoria, setCategoria] = useState(CATEGORIAS[0])
  const [descricao, setDescricao] = useState("")
  const [data, setData] = useState(hojeLocal())
  const [formaPagamento, setFormaPagamento] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [aviso, setAviso] = useState("")
  const [erro, setErro] = useState("")

  const carregar = useCallback(async () => {
    if (!adminMaster) return
    setCarregando(true)
    setErro("")
    try {
      const supabase = getSupabaseClient()
      const { data: sessao, error: erroSessao } = await supabase.auth.getSession()
      if (erroSessao || !sessao.session?.user.id) throw new Error("Sessão autenticada não encontrada.")
      const usuarioAuthId = sessao.session.user.id
      setAuthId(usuarioAuthId)

      const inicio = inicioCompetencia(competencia)
      const fim = proximaCompetencia(competencia)
      const [{ data: configuracao, error: erroConfig }, { data: gastos, error: erroGastos }] = await Promise.all([
        supabase.from("cti_financeiro_pessoal_config").select("id,auth_id,competencia,receita_mensal,limite_gastos,alerta_percentual").eq("auth_id", usuarioAuthId).eq("competencia", inicio).maybeSingle(),
        supabase.from("cti_financeiro_pessoal_lancamentos").select("id,auth_id,data,categoria,descricao,valor,forma_pagamento,created_at").eq("auth_id", usuarioAuthId).gte("data", inicio).lt("data", fim).order("data", { ascending: false }).order("created_at", { ascending: false }),
      ])

      if (erroConfig) throw erroConfig
      if (erroGastos) throw erroGastos

      const cfg = configuracao
        ? ({
            ...configuracao,
            receita_mensal: numero(configuracao.receita_mensal),
            limite_gastos: numero(configuracao.limite_gastos),
            alerta_percentual: numero(configuracao.alerta_percentual),
          } as ConfigFinanceira)
        : null

      setConfig(cfg)
      setReceitaMensal(cfg ? String(cfg.receita_mensal) : "")
      setLimiteGastos(cfg ? String(cfg.limite_gastos) : "")
      setAlertaPercentual(cfg ? String(cfg.alerta_percentual) : "80")
      setLancamentos((gastos || []).map((item) => ({ ...item, valor: numero(item.valor) })) as Lancamento[])
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Falha ao carregar o controle financeiro.")
    } finally {
      setCarregando(false)
    }
  }, [adminMaster, competencia])

  useEffect(() => {
    if (!authLoading && adminMaster) void carregar()
    if (!authLoading && !adminMaster) setCarregando(false)
  }, [adminMaster, authLoading, carregar])

  const resumo = useMemo(
    () => calcularResumoFinanceiro({
      valores: lancamentos.map((item) => item.valor),
      receitaMensal: numero(receitaMensal),
      limiteGastos: numero(limiteGastos),
      alertaPercentual: numero(alertaPercentual) || 80,
      competencia,
    }),
    [alertaPercentual, competencia, lancamentos, limiteGastos, receitaMensal],
  )

  const receitaPlanejada = numero(receitaMensal)
  const limitePlanejado = numero(limiteGastos)
  const metaPreservacao = receitaPlanejada - limitePlanejado
  const percentualReceitaComprometida = receitaPlanejada > 0 ? (resumo.totalGasto / receitaPlanejada) * 100 : 0
  const parametrosCoerentes = receitaPlanejada > 0 && limitePlanejado > 0 && limitePlanejado <= receitaPlanejada

  async function salvarConfiguracao() {
    if (!authId) return
    const receita = numero(receitaMensal)
    const limite = numero(limiteGastos)
    const alerta = numero(alertaPercentual)
    if (receita <= 0 || limite <= 0 || alerta <= 0 || alerta > 100) {
      setErro("Informe receita maior que zero, limite maior que zero e alerta entre 1% e 100%.")
      return
    }
    if (limite > receita) {
      setErro("O limite máximo de gastos não pode ser maior que a receita mensal. Ajuste o limite para preservar parte da receita.")
      return
    }

    setSalvando(true)
    setErro("")
    setAviso("")
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.from("cti_financeiro_pessoal_config").upsert(
        {
          auth_id: authId,
          competencia: inicioCompetencia(competencia),
          receita_mensal: receita,
          limite_gastos: limite,
          alerta_percentual: alerta,
          updated_at: new Date().toISOString(),
        },
        { onConflict: "auth_id,competencia" },
      )
      if (error) throw error
      setAviso("Parâmetros atualizados. Meta de preservação e limites recalculados.")
      await carregar()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Falha ao salvar a configuração.")
    } finally {
      setSalvando(false)
    }
  }

  async function adicionarLancamento(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!authId) return
    const gasto = numero(valor)
    if (gasto <= 0 || !categoria || !data) {
      setErro("Informe data, categoria e um valor maior que zero.")
      return
    }
    setSalvando(true)
    setErro("")
    setAviso("")
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.from("cti_financeiro_pessoal_lancamentos").insert({
        auth_id: authId,
        data,
        categoria,
        descricao: descricao.trim() || null,
        valor: gasto,
        forma_pagamento: formaPagamento || null,
      })
      if (error) throw error
      setValor("")
      setDescricao("")
      setFormaPagamento("")
      setAviso("Gasto registrado e indicadores recalculados.")
      await carregar()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Falha ao registrar o gasto.")
    } finally {
      setSalvando(false)
    }
  }

  async function excluirLancamento(id: string) {
    if (!authId) return
    setSalvando(true)
    setErro("")
    try {
      const supabase = getSupabaseClient()
      const { error } = await supabase.from("cti_financeiro_pessoal_lancamentos").delete().eq("id", id).eq("auth_id", authId)
      if (error) throw error
      setAviso("Lançamento removido e indicadores recalculados.")
      await carregar()
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Falha ao excluir o lançamento.")
    } finally {
      setSalvando(false)
    }
  }

  if (authLoading || carregando) {
    return <main className="min-h-[100dvh] bg-[#020817] p-6 text-slate-300">Carregando Controle Financeiro...</main>
  }

  if (!adminMaster) {
    return (
      <main className="min-h-[100dvh] bg-[#020817] p-6 text-white">
        <div className="mx-auto max-w-xl rounded-3xl border border-red-900/70 bg-red-950/20 p-6">
          <h1 className="text-xl font-bold">Acesso restrito</h1>
          <p className="mt-2 text-sm text-red-100/80">Este módulo é exclusivo do perfil ADMIN_MASTER.</p>
          <Link href="/crm-app" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-cyan-300"><ArrowLeft size={16}/>Voltar ao CRM</Link>
        </div>
      </main>
    )
  }

  const progresso = Math.min(Math.max(resumo.percentualConsumido, 0), 100)

  return (
    <main className="min-h-[100dvh] bg-[#020817] pb-24 text-white">
      <header className="sticky top-0 z-20 border-b border-cyan-950/80 bg-[#061126]/95 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex w-full max-w-[94vw] items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/crm-app" aria-label="Voltar ao CRM" className="rounded-xl border border-[#16325c] p-2 text-cyan-300"><ArrowLeft size={20}/></Link>
            <div><p className="text-[10px] font-semibold uppercase tracking-[.28em] text-cyan-400">Privado · ADMIN_MASTER</p><h1 className="mt-1 text-lg font-bold sm:text-2xl">Controle Financeiro</h1></div>
          </div>
          <input aria-label="Competência" type="month" value={competencia} onChange={(event) => setCompetencia(event.target.value)} className="rounded-xl border border-[#16325c] bg-[#07162b] px-3 py-2 text-sm"/>
        </div>
      </header>

      <div className="mx-auto w-full max-w-[94vw] space-y-5 px-4 py-5 sm:px-6">
        {erro && <div className="rounded-2xl border border-red-900/70 bg-red-950/25 p-4 text-sm text-red-100">{erro}</div>}
        {aviso && <div className="rounded-2xl border border-emerald-900/70 bg-emerald-950/25 p-4 text-sm text-emerald-100">{aviso}</div>}

        <section className={`rounded-3xl border p-5 shadow-xl sm:p-7 ${classeStatus(resumo.status)}`}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm opacity-80">Status do mês</p>
              <h2 className="mt-1 text-2xl font-bold">{rotuloStatus(resumo.status)}</h2>
              {parametrosCoerentes && <p className="mt-2 text-sm opacity-80">Planejamento: gastar até {moeda(limitePlanejado)} de {moeda(receitaPlanejada)} e preservar pelo menos {moeda(metaPreservacao)}.</p>}
            </div>
            <div className="rounded-2xl border border-current/20 bg-black/10 px-4 py-2 text-right"><strong className="text-2xl">{resumo.percentualConsumido.toFixed(1)}%</strong><span className="block text-xs opacity-75">do limite utilizado</span></div>
          </div>
          <div className="mt-5 h-3 overflow-hidden rounded-full bg-black/25"><div className="h-full rounded-full bg-current transition-all" style={{ width: `${progresso}%` }}/></div>
          {resumo.status === "LIMITE" && <p className="mt-4 flex items-start gap-2 text-sm font-semibold"><AlertTriangle size={18} className="mt-0.5 shrink-0"/>Seu limite mensal foi atingido. Novos gastos já comprometem a faixa de receita que você decidiu preservar.</p>}
          {resumo.ritmoAcimaDoPlanejado && resumo.status !== "LIMITE" && <p className="mt-4 flex items-start gap-2 text-sm"><TrendingUp size={18} className="mt-0.5 shrink-0"/>O ritmo de gastos está acima do proporcional esperado para este ponto do mês.</p>}
        </section>

        <section className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          <Indicador icon={WalletCards} label="Gasto acumulado" valor={moeda(resumo.totalGasto)}/>
          <Indicador icon={PiggyBank} label="Ainda pode gastar" valor={moeda(resumo.saldoAteLimite)}/>
          <Indicador icon={Gauge} label="Meta a preservar" valor={moeda(Math.max(metaPreservacao, 0))}/>
          <Indicador icon={Gauge} label="Receita após gastos" valor={moeda(resumo.receitaPreservada)}/>
          <Indicador icon={TrendingUp} label="Projeção do mês" valor={moeda(resumo.projecaoFechamento)}/>
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,.8fr)_minmax(0,1.2fr)]">
          <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
            <div className="flex items-center gap-3"><Save className="text-cyan-300" size={22}/><div><h2 className="text-lg font-semibold">Parâmetros do mês</h2><p className="text-xs text-slate-400">Defina a entrada prevista e quanto dela você aceita gastar.</p></div></div>
            <div className="mt-5 space-y-4">
              <CampoNumerico label="Receita mensal" detalhe="Entrada líquida que você espera ter disponível no mês." value={receitaMensal} onChange={setReceitaMensal}/>
              <CampoNumerico label="Limite máximo de gastos" detalhe="Máximo da receita mensal que você aceita consumir com despesas." value={limiteGastos} onChange={setLimiteGastos}/>
              <label className="block text-sm text-slate-300">Primeiro alerta (%)<input type="number" min="1" max="100" step="1" value={alertaPercentual} onChange={(event) => setAlertaPercentual(event.target.value)} className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white"/><span className="mt-1 block text-xs text-slate-500">O sistema entra em atenção quando esse percentual do limite for utilizado.</span></label>

              {receitaPlanejada > 0 && limitePlanejado > 0 && (
                <div className={`rounded-2xl border p-4 text-sm ${limitePlanejado <= receitaPlanejada ? "border-emerald-900/70 bg-emerald-950/20 text-emerald-100" : "border-red-900/70 bg-red-950/20 text-red-100"}`}>
                  {limitePlanejado <= receitaPlanejada
                    ? <>Com estes parâmetros, você aceita gastar até <strong>{moeda(limitePlanejado)}</strong> e pretende preservar pelo menos <strong>{moeda(metaPreservacao)}</strong> da receita.</>
                    : <>O limite informado supera a receita mensal. Reduza o limite para manter uma faixa de preservação.</>}
                </div>
              )}

              <button type="button" onClick={() => void salvarConfiguracao()} disabled={salvando} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-[#02111d] disabled:opacity-50"><Save size={18}/>{config ? "Atualizar parâmetros" : "Salvar parâmetros"}</button>
            </div>
          </section>

          <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
            <div className="flex items-center gap-3"><Plus className="text-cyan-300" size={22}/><div><h2 className="text-lg font-semibold">Registrar gasto</h2><p className="text-xs text-slate-400">O impacto aparece imediatamente no painel</p></div></div>
            <form onSubmit={adicionarLancamento} className="mt-5 grid gap-4 sm:grid-cols-2">
              <CampoNumerico label="Valor" value={valor} onChange={setValor}/>
              <label className="block text-sm text-slate-300">Data<input type="date" value={data} onChange={(event) => setData(event.target.value)} className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white"/></label>
              <label className="block text-sm text-slate-300">Categoria<select value={categoria} onChange={(event) => setCategoria(event.target.value)} className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white">{CATEGORIAS.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label className="block text-sm text-slate-300">Forma de pagamento<select value={formaPagamento} onChange={(event) => setFormaPagamento(event.target.value)} className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white">{FORMAS_PAGAMENTO.map((item) => <option key={item || "sem"} value={item}>{item || "Não informar"}</option>)}</select></label>
              <label className="block text-sm text-slate-300 sm:col-span-2">Descrição<input type="text" maxLength={160} value={descricao} onChange={(event) => setDescricao(event.target.value)} placeholder="Ex.: almoço, abastecimento, mercado" className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white placeholder:text-slate-600"/></label>
              <button type="submit" disabled={salvando} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-[#02111d] disabled:opacity-50 sm:col-span-2"><Plus size={18}/>Adicionar gasto</button>
            </form>
          </section>
        </div>

        <section className="grid gap-3 md:grid-cols-4">
          <Leitura label="Média diária" valor={moeda(resumo.mediaDiaria)} detalhe="ritmo médio observado"/>
          <Leitura label="Esperado até agora" valor={moeda(resumo.gastoEsperadoAteHoje)} detalhe="proporcional ao limite mensal"/>
          <Leitura label="Receita comprometida" valor={`${percentualReceitaComprometida.toFixed(1)}%`} detalhe="percentual da receita já gasto"/>
          <Leitura label="Estimativa até o limite" valor={resumo.diasAteLimite === null ? "—" : `${resumo.diasAteLimite} dia${resumo.diasAteLimite === 1 ? "" : "s"}`} detalhe="mantido o ritmo atual"/>
        </section>

        <section className="rounded-3xl border border-[#16325c] bg-[#07162b] p-5">
          <div className="flex items-center justify-between gap-4"><div><h2 className="text-lg font-semibold">Lançamentos do mês</h2><p className="text-xs text-slate-400">{lancamentos.length} registro{lancamentos.length === 1 ? "" : "s"}</p></div><strong className="text-cyan-300">{moeda(resumo.totalGasto)}</strong></div>
          <div className="mt-4 divide-y divide-[#16325c]">
            {lancamentos.length === 0 && <p className="py-8 text-center text-sm text-slate-500">Nenhum gasto registrado nesta competência.</p>}
            {lancamentos.map((item) => <div key={item.id} className="flex items-center gap-3 py-4"><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-x-2"><strong>{item.categoria}</strong><span className="text-xs text-slate-500">{item.data.split("-").reverse().join("/")}</span></div><p className="mt-1 truncate text-sm text-slate-400">{item.descricao || item.forma_pagamento || "Sem descrição"}{item.descricao && item.forma_pagamento ? ` · ${item.forma_pagamento}` : ""}</p></div><strong className="whitespace-nowrap text-cyan-300">{moeda(item.valor)}</strong><button type="button" disabled={salvando} onClick={() => void excluirLancamento(item.id)} aria-label="Excluir lançamento" className="rounded-xl border border-red-950 bg-red-950/20 p-2 text-red-300 disabled:opacity-50"><Trash2 size={17}/></button></div>)}
          </div>
        </section>
      </div>
    </main>
  )
}

function Indicador({ icon: Icon, label, valor }: { icon: typeof WalletCards; label: string; valor: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#07162b] p-4"><Icon size={20} className="text-cyan-300"/><span className="mt-3 block text-xs text-slate-400">{label}</span><strong className="mt-1 block text-lg text-white sm:text-xl">{valor}</strong></div>
}

function Leitura({ label, valor, detalhe }: { label: string; valor: string; detalhe: string }) {
  return <div className="rounded-2xl border border-[#16325c] bg-[#061126] p-4"><span className="text-xs text-slate-500">{label}</span><strong className="mt-1 block text-lg">{valor}</strong><span className="mt-1 block text-xs text-slate-500">{detalhe}</span></div>
}

function CampoNumerico({ label, detalhe, value, onChange }: { label: string; detalhe?: string; value: string; onChange: (valor: string) => void }) {
  return <label className="block text-sm text-slate-300">{label}<input type="number" min="0" step="0.01" inputMode="decimal" value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-[#16325c] bg-[#061126] px-3 py-3 text-white"/>{detalhe && <span className="mt-1 block text-xs text-slate-500">{detalhe}</span>}</label>
}
