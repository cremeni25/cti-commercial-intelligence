"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { useAuth } from "@/core/auth/AuthContext"
import { messages, normalizeLocale, type Locale, type MessageKey } from "./catalog"

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
const CURRENT_LOCALE_KEY = "cti.locale.current"
const LOCALE_EVENT = "cti:locale-change"

function storageKey(userId?: string | null) {
  return `cti.locale.${userId || "guest"}`
}

function interpolate(template: string, params?: Params) {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(params[key] ?? `{${key}}`))
}

function readStoredLocale(userId?: string | null): Locale {
  const currentPreference = window.localStorage.getItem(CURRENT_LOCALE_KEY)
  const userPreference = userId ? window.localStorage.getItem(storageKey(userId)) : null
  const sharedPreference = window.localStorage.getItem(storageKey(null))
  const browser = typeof navigator !== "undefined" ? navigator.language : "pt-BR"
  return normalizeLocale(currentPreference || userPreference || sharedPreference || browser)
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const { usuario } = useAuth()
  const userId = usuario?.id || null
  const [locale, setLocaleState] = useState<Locale>("pt-BR")

  useEffect(() => {
    const resolved = readStoredLocale(userId)
    queueMicrotask(() => setLocaleState(resolved))
  }, [userId])

  useEffect(() => {
    document.documentElement.lang = locale
    document.documentElement.dataset.locale = locale
  }, [locale])

  useEffect(() => {
    const syncFromStorage = (event: StorageEvent) => {
      const relevantKeys = new Set([CURRENT_LOCALE_KEY, storageKey(null), userId ? storageKey(userId) : ""])
      if (!event.key || !relevantKeys.has(event.key)) return
      setLocaleState(readStoredLocale(userId))
    }
    const syncFromWindow = (event: Event) => {
      const requested = (event as CustomEvent<string>).detail
      if (requested) setLocaleState(normalizeLocale(requested))
    }
    window.addEventListener("storage", syncFromStorage)
    window.addEventListener(LOCALE_EVENT, syncFromWindow)
    return () => {
      window.removeEventListener("storage", syncFromStorage)
      window.removeEventListener(LOCALE_EVENT, syncFromWindow)
    }
  }, [userId])

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    window.localStorage.setItem(CURRENT_LOCALE_KEY, next)
    if (userId) window.localStorage.setItem(storageKey(userId), next)
    window.localStorage.setItem(storageKey(null), next)
    window.dispatchEvent(new CustomEvent<string>(LOCALE_EVENT, { detail: next }))
  }, [userId])

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
    formatCurrency: (number, options = "BRL") => {
      const config = typeof options === "string"
        ? { style: "currency" as const, currency: options }
        : { ...options, style: "currency" as const, currency: options.currency || "BRL" }
      return new Intl.NumberFormat(intlLocale, config).format(number)
    },
  }), [intlLocale, locale, setLocale, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) throw new Error("useI18n must be used inside I18nProvider")
  return context
}
