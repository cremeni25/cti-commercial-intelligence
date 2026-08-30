"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { messages, type Locale, type MessageKey } from "./catalog"

type Params = Record<string, string | number>
type CurrencyOptions = Intl.NumberFormatOptions | string

type I18nContextValue = {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: MessageKey, params?: Params) => string
  formatDate: (value: string | Date, options?: Intl.DateTimeFormatOptions) => string
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
  formatCurrency: (value: number, options?: CurrencyOptions) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)
const FIXED_LOCALE: Locale = "pt-BR"

function interpolate(template: string, params?: Params) {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(params[key] ?? `{${key}}`))
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(FIXED_LOCALE)

  useEffect(() => {
    setLocaleState(FIXED_LOCALE)
    document.documentElement.lang = FIXED_LOCALE
    document.documentElement.dataset.locale = FIXED_LOCALE
  }, [])

  const setLocale = useCallback((_next: Locale) => {
    setLocaleState(FIXED_LOCALE)
    document.documentElement.lang = FIXED_LOCALE
    document.documentElement.dataset.locale = FIXED_LOCALE
  }, [])

  const t = useCallback((key: MessageKey, params?: Params) => {
    const dictionary = messages[FIXED_LOCALE] as Record<string, string>
    return interpolate(dictionary[key] || key, params)
  }, [])

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    setLocale,
    t,
    formatDate: (input, options) => {
      const date = input instanceof Date ? input : new Date(input)
      return Number.isNaN(date.getTime()) ? String(input) : new Intl.DateTimeFormat(FIXED_LOCALE, options).format(date)
    },
    formatNumber: (number, options) => new Intl.NumberFormat(FIXED_LOCALE, options).format(number),
    formatCurrency: (number, options = "BRL") => {
      const config = typeof options === "string"
        ? { style: "currency" as const, currency: options }
        : { ...options, style: "currency" as const, currency: options.currency || "BRL" }
      return new Intl.NumberFormat(FIXED_LOCALE, config).format(number)
    },
  }), [locale, setLocale, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) throw new Error("useI18n must be used inside I18nProvider")
  return context
}
