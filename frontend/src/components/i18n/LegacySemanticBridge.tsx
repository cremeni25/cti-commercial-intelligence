"use client"

import { useEffect } from "react"
import { useI18n } from "@/core/i18n/I18nContext"
import legacy from "@/core/i18n/legacy-semantic.json"

type LegacyEntry = { en: string; es: string }
type LegacyLocale = "en" | "es"
type Locale = "pt-BR" | "en" | "es"

const originalText = new WeakMap<Text, string>()
const originalAttributes = new WeakMap<Element, Map<string, string>>()
const attributeNames = ["placeholder", "title", "aria-label", "alt"] as const
const excludedTags = new Set(["SCRIPT", "STYLE", "CODE", "PRE"])
const catalog = legacy as Record<string, LegacyEntry>
const semanticCatalog = new Map(Object.entries(catalog).map(([key, value]) => [normalizeSemanticKey(key), value]))

function normalizeSemanticKey(value: string) {
  return value.normalize("NFC").replace(/\u00ad/g, "").replace(/\s+/g, " ").trim()
}

function intlLocale(locale: Locale) {
  return locale === "en" ? "en-US" : locale === "es" ? "es-419" : "pt-BR"
}

function brNumberToNumber(value: string) {
  const normalized = value.replace(/\./g, "").replace(",", ".")
  const number = Number(normalized)
  return Number.isFinite(number) ? number : null
}

function localizeBrazilianFormats(value: string, locale: Locale) {
  if (locale === "pt-BR") return value
  const target = intlLocale(locale)
  let result = value

  result = result.replace(/R\$\s*((?:\d{1,3}(?:\.\d{3})*|\d+)(?:,\d+)?)/g, (match, raw: string) => {
    const number = brNumberToNumber(raw)
    return number === null ? match : new Intl.NumberFormat(target, { style: "currency", currency: "BRL" }).format(number)
  })

  result = result.replace(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/g, (match, day: string, month: string, year: string) => {
    const date = new Date(Number(year), Number(month) - 1, Number(day))
    return Number.isNaN(date.getTime()) ? match : new Intl.DateTimeFormat(target).format(date)
  })

  result = result.replace(/(?<![\w/.-])((?:\d{1,3}(?:\.\d{3})+)(?:,\d+)?|\d+,\d+)(?![\w/.-])/g, (match, raw: string) => {
    const number = brNumberToNumber(raw)
    return number === null ? match : new Intl.NumberFormat(target).format(number)
  })

  return result
}

function translateCore(value: string, locale: Locale) {
  if (locale === "pt-BR") return value
  const exact = semanticCatalog.get(normalizeSemanticKey(value))
  return localizeBrazilianFormats(exact?.[locale as LegacyLocale] || value, locale)
}

function preserveWhitespace(value: string, locale: Locale) {
  const start = value.match(/^\s*/)?.[0] || ""
  const end = value.match(/\s*$/)?.[0] || ""
  const core = value.trim()
  if (!core) return value
  return `${start}${translateCore(core, locale)}${end}`
}

function shouldSkip(element: Element | null) {
  if (!element) return true
  if (excludedTags.has(element.tagName)) return true
  return Boolean(element.closest("[data-i18n-preserve='true']"))
}

export default function LegacySemanticBridge() {
  const { locale } = useI18n()

  useEffect(() => {
    const translateTextNode = (node: Text) => {
      const parent = node.parentElement
      if (shouldSkip(parent)) return
      if (!originalText.has(node)) originalText.set(node, node.nodeValue || "")
      const raw = originalText.get(node) || ""
      const translated = preserveWhitespace(raw, locale)
      if (node.nodeValue !== translated) node.nodeValue = translated
    }

    const translateElement = (element: Element) => {
      if (shouldSkip(element)) return
      let originals = originalAttributes.get(element)
      if (!originals) {
        originals = new Map<string, string>()
        originalAttributes.set(element, originals)
      }
      for (const attribute of attributeNames) {
        const current = element.getAttribute(attribute)
        if (current === null) continue
        if (!originals.has(attribute)) originals.set(attribute, current)
        const raw = originals.get(attribute) || ""
        const translated = translateCore(raw, locale)
        if (current !== translated) element.setAttribute(attribute, translated)
      }

      if (element instanceof HTMLTextAreaElement) {
        const rawValue = element.value
        const translated = translateCore(rawValue, locale)
        if (translated !== rawValue) {
          const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set
          setter?.call(element, translated)
          element.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }

    const translateTree = (root: Node) => {
      if (root.nodeType === Node.TEXT_NODE) {
        translateTextNode(root as Text)
        return
      }
      if (root.nodeType !== Node.ELEMENT_NODE && root !== document.body) return
      if (root instanceof Element) translateElement(root)
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT)
      let current: Node | null = walker.nextNode()
      while (current) {
        if (current.nodeType === Node.TEXT_NODE) translateTextNode(current as Text)
        else if (current instanceof Element) translateElement(current)
        current = walker.nextNode()
      }
    }

    translateTree(document.body)

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "characterData" && mutation.target.nodeType === Node.TEXT_NODE) {
          const text = mutation.target as Text
          const current = text.nodeValue || ""
          const knownOriginal = originalText.get(text)
          if (knownOriginal !== undefined && current !== preserveWhitespace(knownOriginal, locale)) {
            originalText.set(text, current)
          }
          translateTextNode(text)
          continue
        }
        mutation.addedNodes.forEach(translateTree)
        if (mutation.type === "attributes" && mutation.target instanceof Element) translateElement(mutation.target)
      }
    })
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: [...attributeNames] })

    const nativeAlert = window.alert.bind(window)
    const nativeConfirm = window.confirm.bind(window)
    const nativePrompt = window.prompt.bind(window)
    window.alert = (message?: unknown) => nativeAlert(typeof message === "string" ? translateCore(message, locale) : message)
    window.confirm = (message?: string) => nativeConfirm(translateCore(String(message || ""), locale))
    window.prompt = (message?: string, defaultValue?: string) => nativePrompt(translateCore(String(message || ""), locale), defaultValue)

    return () => {
      observer.disconnect()
      window.alert = nativeAlert
      window.confirm = nativeConfirm
      window.prompt = nativePrompt
    }
  }, [locale])

  return null
}
