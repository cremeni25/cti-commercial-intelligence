"use client"

import { useEffect, useId, useRef, useState } from "react"
import { Check, ChevronDown } from "lucide-react"

type Opcao = readonly [string, string]

type ControlledSelectProps = {
  value: string
  onChange: (value: string) => void
  options: readonly Opcao[]
  name?: string
  disabled?: boolean
  buttonClassName?: string
}

export function ControlledSelect({
  value,
  onChange,
  options,
  name,
  disabled = false,
  buttonClassName = "rounded-2xl",
}: ControlledSelectProps) {
  const [aberto, setAberto] = useState(false)
  const raizRef = useRef<HTMLDivElement>(null)
  const listaId = useId()
  const selecionada = options.find(([valor]) => valor === value)

  useEffect(() => {
    function fecharAoTocarFora(evento: PointerEvent) {
      if (!raizRef.current?.contains(evento.target as Node)) setAberto(false)
    }
    function fecharComEsc(evento: KeyboardEvent) {
      if (evento.key === "Escape") setAberto(false)
    }
    document.addEventListener("pointerdown", fecharAoTocarFora)
    document.addEventListener("keydown", fecharComEsc)
    return () => {
      document.removeEventListener("pointerdown", fecharAoTocarFora)
      document.removeEventListener("keydown", fecharComEsc)
    }
  }, [])

  useEffect(() => {
    if (disabled) setAberto(false)
  }, [disabled])

  return (
    <div ref={raizRef} className="relative w-full">
      {name ? <input type="hidden" name={name} value={value} /> : null}
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={aberto}
        aria-controls={listaId}
        onClick={() => setAberto((atual) => !atual)}
        className={`flex h-12 w-full items-center justify-between gap-3 border border-[#24466f] bg-[#020817] px-4 text-left text-white outline-none transition focus:border-cyan-600 disabled:cursor-not-allowed disabled:opacity-60 ${buttonClassName}`}
      >
        <span className="min-w-0 truncate">{selecionada?.[1] || "Selecione"}</span>
        <ChevronDown size={18} className={`shrink-0 text-slate-400 transition-transform ${aberto ? "rotate-180" : ""}`} />
      </button>

      {aberto && !disabled ? (
        <div
          id={listaId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-[80] mt-2 max-h-60 overflow-y-auto overscroll-contain rounded-2xl border border-[#24466f] bg-[#07162b] p-1 shadow-2xl shadow-black/60"
        >
          {options.map(([valor, rotulo]) => {
            const ativo = valor === value
            return (
              <button
                key={`${valor}:${rotulo}`}
                type="button"
                role="option"
                aria-selected={ativo}
                onClick={() => {
                  onChange(valor)
                  setAberto(false)
                }}
                className="flex min-h-11 w-full items-center justify-between gap-3 rounded-xl px-3 py-2 text-left text-sm text-slate-100 hover:bg-[#0b2749] focus:bg-[#0b2749] focus:outline-none"
              >
                <span className="min-w-0 break-words">{rotulo}</span>
                {ativo ? <Check size={16} className="shrink-0 text-cyan-300" /> : null}
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
