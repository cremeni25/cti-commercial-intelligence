"use client"

import { useI18n, type Locale } from "@/core/i18n"

const options: Array<{ locale: Locale; labelKey: "language.pt" | "language.en" | "language.es" }> = [
  { locale: "pt-BR", labelKey: "language.pt" },
  { locale: "en", labelKey: "language.en" },
  { locale: "es", labelKey: "language.es" },
]

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, t } = useI18n()

  return (
    <div className="inline-flex items-center gap-1 rounded-xl border border-[#1d3b67] bg-[#061126]/80 p-1" role="group" aria-label={t("language.label")}>
      {options.map((option) => {
        const active = locale === option.locale
        return (
          <button
            key={option.locale}
            type="button"
            onClick={() => setLocale(option.locale)}
            aria-pressed={active}
            className={`${compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-xs"} rounded-lg font-semibold transition ${active ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:bg-[#101b36] hover:text-white"}`}
          >
            {t(option.labelKey)}
          </button>
        )
      })}
    </div>
  )
}
