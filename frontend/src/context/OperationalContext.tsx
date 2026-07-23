"use client"

import { createContext, useContext, useEffect, useMemo, useState } from "react"

export type OperationalContextValue = "brasil" | "viena-sp" | `uf-${string}` | `ddd-${string}`
export type PeriodPreset = "TODO_HISTORICO" | "ULTIMOS_30_DIAS" | "ULTIMOS_90_DIAS" | "ANO_ATUAL" | "PERSONALIZADO"

export type ContextConfig = {
  value: OperationalContextValue
  label: string
  description: string
}

const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
const VIENA_DDDS = ["011", "012", "013", "014", "015", "018"]

export const OPERATIONAL_CONTEXTS: ContextConfig[] = [
  { value: "brasil", label: "Brasil", description: "Visão consolidada nacional" },
  { value: "viena-sp", label: "Viena SP", description: "Registros do autorizado Viena" },
  ...UFS.map((uf) => ({ value: `uf-${uf.toLowerCase()}` as OperationalContextValue, label: `UF • ${uf}`, description: `Registros da unidade federativa ${uf}` })),
  ...VIENA_DDDS.map((ddd) => ({ value: `ddd-${ddd}` as OperationalContextValue, label: `Viena • DDD ${ddd}`, description: `Território autorizado Viena no DDD ${ddd}` })),
]

const STORAGE_KEY = "cti-contexto-operacional"
const PERIOD_KEY = "cti-periodo-global"
const START_KEY = "cti-data-inicial"
const END_KEY = "cti-data-final"

type OperationalContextState = {
  contexto: OperationalContextValue
  setContexto: (contexto: OperationalContextValue) => void
  contextoAtual: ContextConfig
  periodo: PeriodPreset
  setPeriodo: (periodo: PeriodPreset) => void
  dataInicio: string
  setDataInicio: (valor: string) => void
  dataFim: string
  setDataFim: (valor: string) => void
  queryString: string
}

const OperationalContext = createContext<OperationalContextState | null>(null)

function normalizarContexto(valor: string | null): OperationalContextValue {
  return OPERATIONAL_CONTEXTS.some((item) => item.value === valor) ? valor as OperationalContextValue : "brasil"
}

function normalizarPeriodo(valor: string | null): PeriodPreset {
  return ["TODO_HISTORICO", "ULTIMOS_30_DIAS", "ULTIMOS_90_DIAS", "ANO_ATUAL", "PERSONALIZADO"].includes(valor || "") ? valor as PeriodPreset : "TODO_HISTORICO"
}

export function OperationalContextProvider({ children }: { children: React.ReactNode }) {
  const [contexto, setContextoState] = useState<OperationalContextValue>("brasil")
  const [periodo, setPeriodoState] = useState<PeriodPreset>("TODO_HISTORICO")
  const [dataInicio, setDataInicioState] = useState("")
  const [dataFim, setDataFimState] = useState("")

  useEffect(() => {
    queueMicrotask(() => {
      setContextoState(normalizarContexto(window.localStorage.getItem(STORAGE_KEY)))
      setPeriodoState(normalizarPeriodo(window.localStorage.getItem(PERIOD_KEY)))
      setDataInicioState(window.localStorage.getItem(START_KEY) || "")
      setDataFimState(window.localStorage.getItem(END_KEY) || "")
    })
  }, [])

  function persistir(chave: string, valor: string) {
    window.localStorage.setItem(chave, valor)
    window.dispatchEvent(new CustomEvent("cti-filtros-globais"))
  }

  function setContexto(valor: OperationalContextValue) { setContextoState(valor); persistir(STORAGE_KEY, valor) }
  function setPeriodo(valor: PeriodPreset) { setPeriodoState(valor); persistir(PERIOD_KEY, valor) }
  function setDataInicio(valor: string) { setDataInicioState(valor); persistir(START_KEY, valor) }
  function setDataFim(valor: string) { setDataFimState(valor); persistir(END_KEY, valor) }

  const contextoAtual = useMemo(() => OPERATIONAL_CONTEXTS.find((item) => item.value === contexto) ?? OPERATIONAL_CONTEXTS[0], [contexto])
  const queryString = useMemo(() => {
    const params = new URLSearchParams({ contexto, periodo })
    if (periodo === "PERSONALIZADO" && dataInicio) params.set("inicio", dataInicio)
    if (periodo === "PERSONALIZADO" && dataFim) params.set("fim", dataFim)
    return params.toString()
  }, [contexto, periodo, dataInicio, dataFim])

  return <OperationalContext.Provider value={{ contexto, setContexto, contextoAtual, periodo, setPeriodo, dataInicio, setDataInicio, dataFim, setDataFim, queryString }}>{children}</OperationalContext.Provider>
}

export function useOperationalContext() {
  const value = useContext(OperationalContext)
  if (!value) throw new Error("useOperationalContext deve ser usado dentro de OperationalContextProvider")
  return value
}
