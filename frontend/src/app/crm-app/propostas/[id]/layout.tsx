"use client"

import type { ReactNode } from "react"
import { useParams } from "next/navigation"
import PrimeiraPaginaProposta from "@/components/propostas/PrimeiraPaginaProposta"
import { useClosureI18n } from "@/core/i18n/closure"

const copy = {
  "pt-BR": { title: "Elaboração da proposta:", text: "preencha e salve os dados do documento oficial abaixo antes de emitir ou enviar ao cliente." },
  en: { title: "Proposal preparation:", text: "complete and save the official document details below before issuing or sending it to the account." },
  es: { title: "Preparación de la propuesta:", text: "complete y guarde los datos del documento oficial antes de emitirlo o enviarlo al cliente." },
}

export default function PropostaCrmLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>()
  const id = String(params?.id || "")
  const { locale } = useClosureI18n()
  const t = copy[locale as keyof typeof copy] || copy["pt-BR"]

  return <>
    {id && <div className="bg-[#020817] px-4 pt-5 text-white sm:px-6"><div className="mx-auto max-w-4xl"><div className="mb-3 rounded-2xl border border-cyan-900 bg-cyan-950/20 p-4 text-sm text-cyan-100"><strong>{t.title}</strong> {t.text}</div><PrimeiraPaginaProposta propostaId={id} compacto /></div></div>}
    {/* O detalhe é remontado na troca de idioma para sincronizar defaults localizados (ex.: mensagem-padrão de e-mail), sem traduzir texto livre já salvo no backend. */}
    <div key={locale}>{children}</div>
  </>
}
