"use client"

import { useCallback, useRef } from "react"
import { useStrategicI18n } from "./strategic"

export function useStableStrategicI18n() {
  const base = useStrategicI18n()
  const translateRef = useRef(base.t)
  translateRef.current = base.t
  const t = useCallback((key: string, params?: Record<string, string | number>) => translateRef.current(key, params), [])
  return { ...base, t }
}
