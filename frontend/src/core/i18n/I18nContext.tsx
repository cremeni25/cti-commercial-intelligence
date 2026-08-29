"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { useAuth } from "@/core/auth/AuthContext"
import { messages, normalizeLocale, type Locale, type MessageKey } from "./catalog"

type Params = Record<string, string | number>

type I18nContextValue = {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: MessageKey, params?: Params) => string
  formatDate: (value: string | Date, options?: Intl.DateTimeFormatOptions) => string
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
  formatCurrency: (value: number, currency?: string) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function storageKey(userId?: string | null) {
  return `cti.locale.${userId || "guest"}`
}

function interpolate(template: string, params?: Params) {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(params[key] ?? `{${key}}`))
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const { usuario } = useAuth()
  const [locale, setLocaleState] = useState<Locale>("pt-BR")

  useEffect(() => {
    const saved = window.localStorage.getItem(storageKey(usuario?.id))
    const browser = typeof navigator !== "undefined" ? navigator.language : "pt-BR"
    setLocaleState(normalizeLocale(saved || browser))
  }, [usuario?.id])

  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    window.localStorage.setItem(storageKey(usuario?.id), next)
    // Mantém também uma preferência de fallback para login e troca entre CTI Web e CRM App.
    window.localStorage.setItem(storageKey(null), next)
  }, [usuario?.id])

  const t = useCallback((key: MessageKey, params?: Params) => {
    const dictionary = messages[locale] as Record<string, string>
    const fallback = messages["pt-BR"] as Record<string, string>
    return interpolate(dictionary[key] || fallback[key] || key, params)
  }, [locale])

  const intlLocale = locale === "pt-BR" ? "pt-BR" : locale === "en" ? "en-US" : "es-419"

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    setLocale,
    t,
    formatDate: (input, options) => {
      const date = input instanceof Date ? input : new Date(input)
      return Number.isNaN(date.getTime()) ? String(input) : new Intl.DateTimeFormat(intlLocale, options).format(date)
    },
    formatNumber: (number, options) => new Intl.NumberFormat(intlLocale, options).format(number),
    formatCurrency: (number, currency = "BRL") => new Intl.NumberFormat(intlLocale, { style: "currency", currency }).format(number),
  }), [intlLocale, locale, setLocale, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) throw new Error("useI18n must be used inside I18nProvider")
  return context
}
