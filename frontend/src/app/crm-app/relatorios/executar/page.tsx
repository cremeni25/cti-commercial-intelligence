"use client"

import { useEffect, useRef, useState } from "react"
import { Bot, Loader2 } from "lucide-react"
import { getSupabaseClient } from "@/core/database/supabase"

const API = "/api/crm-proxy/ia-comercial-cti"

async function tokenAtual(): Promise<string> {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.getSession()
  if (error || !data.session?.access_token) {
    throw new Error("Sessão autenticada não encontrada.")
  }
  return data.session.access_token
}

async function requisitar(caminho: string, init?: RequestInit) {
  const resposta = await fetch(`${API}${caminho}`, {
    ...init,
    cache: "no-store",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${await tokenAtual()}`,
      ...(init?.headers || {}),
    },
  })
  const payload = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new Error(payload?.detail || "Falha ao preparar o relatório.")
  return payload
}

export default function ExecutarRelatorioPage() {
  const iniciou = useRef(false)
  const [erro, setErro] = useState("")
  const [titulo, setTitulo] = useState("Relatório CRM")

  useEffect(() => {
    if (iniciou.current) return
    iniciou.current = true

    const parametros = new URLSearchParams(window.location.search)
    const prompt = parametros.get("prompt")?.trim() || ""
    const tituloAtual = parametros.get("titulo")?.trim() || "Relatório CRM"
    setTitulo(tituloAtual)

    if (!prompt) {
      setErro("O modelo de relatório não informou o contexto necessário.")
      return
    }

    const executar = async () => {
      const conversa = await requisitar("/conversas", {
        method: "POST",
        body: JSON.stringify({ titulo: tituloAtual }),
      })
      if (!conversa?.id) throw new Error("Não foi possível criar o contexto do relatório.")

      await requisitar(`/conversas/${conversa.id}/mensagens`, {
        method: "POST",
        body: JSON.stringify({ mensagem: prompt }),
      })

      window.location.replace("/ia-comercial")
    }

    void executar().catch((falha) => {
      setErro(falha instanceof Error ? falha.message : "Falha ao executar o relatório.")
    })
  }, [])

  return (
    <main className="grid min-h-[100dvh] place-items-center bg-[#020817] px-6 text-white">
      <section className="w-full max-w-lg rounded-3xl border border-[#16325c] bg-[#07162b] p-7 text-center">
        <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-cyan-950/60 text-cyan-300">
          {erro ? <Bot size={26} /> : <Loader2 className="animate-spin" size={26} />}
        </div>
        <h1 className="mt-5 text-xl font-bold">{erro ? "Não foi possível gerar" : titulo}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          {erro || "Criando um contexto novo, consultando exclusivamente as fontes deste tema e preparando texto, gráfico e PDF no mesmo snapshot."}
        </p>
        {erro ? (
          <button type="button" onClick={() => window.location.replace("/crm-app/relatorios")} className="mt-5 rounded-xl bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950">
            Voltar aos relatórios
          </button>
        ) : null}
      </section>
    </main>
  )
}
