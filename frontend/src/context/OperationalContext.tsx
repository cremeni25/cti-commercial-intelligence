"use client"

import { createContext, useContext, useEffect, useMemo, useState } from "react"

export type OperationalContextValue = "brasil" | "viena-sp"

type ContextConfig = {
  value: OperationalContextValue
  label: string
  description: string
}

export const OPERATIONAL_CONTEXTS: ContextConfig[] = [
  {
    value: "brasil",
    label: "Brasil",
    description: "Visão consolidada nacional",
  },
  {
    value: "viena-sp",
    label: "Viena SP",
    description: "Registros do autorizado Viena",
  },
]

const STORAGE_KEY = "cti-contexto-operacional"

type OperationalContextState = {
  contexto: OperationalContextValue
  setContexto: (contexto: OperationalContextValue) => void
  contextoAtual: ContextConfig
}

const OperationalContext = createContext<OperationalContextState | null>(null)

function normalizarContexto(valor: string | null): OperationalContextValue {
  return valor === "viena-sp" ? "viena-sp" : "brasil"
}

export function OperationalContextProvider({ children }: { children: React.ReactNode }) {
  const [contexto, setContextoState] = useState<OperationalContextValue>("brasil")

  useEffect(() => {
    queueMicrotask(() => {
      setContextoState(normalizarContexto(window.localStorage.getItem(STORAGE_KEY)))
    })
  }, [])

  function setContexto(novoContexto: OperationalContextValue) {
    setContextoState(novoContexto)
    window.localStorage.setItem(STORAGE_KEY, novoContexto)
    window.dispatchEvent(new CustomEvent("cti-contexto-operacional", { detail: novoContexto }))
  }

  const contextoAtual = useMemo(
    () => OPERATIONAL_CONTEXTS.find((item) => item.value === contexto) ?? OPERATIONAL_CONTEXTS[0],
    [contexto]
  )

  return (
    <OperationalContext.Provider value={{ contexto, setContexto, contextoAtual }}>
      {children}
    </OperationalContext.Provider>
  )
}

export function useOperationalContext() {
  const value = useContext(OperationalContext)
  if (!value) {
    throw new Error("useOperationalContext deve ser usado dentro de OperationalContextProvider")
  }
  return value
}
