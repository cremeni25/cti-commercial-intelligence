/* eslint-disable react-hooks/set-state-in-effect */
"use client"

import { FormEvent, useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { API_URL } from "@/lib/api"

type Pacote = {
  aceite: Record<string, unknown>
  proposta: Record<string, unknown>
  item: Record<string, unknown> | null
}

const texto = (valor: unknown, padrao = "—") => String(valor ?? "").trim() || padrao
const moeda = (valor: unknown) => Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })

export default function AceitePage() {
  const params = useParams<{ token: string }>()
  const token = String(params?.token || "")
  const [dados, setDados] = useState<Pacote | null>(null)
  const [nome, setNome] = useState("")
  const [confirmado, setConfirmado] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState(false)
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    if (!token) return
    fetch(`${API_URL}/crm-documentos/aceites/${token}/publico`, { cache: "no-store" })
      .then(async (resposta) => {
        const payload = await resposta.json().catch(() => null)
        if (!resposta.ok) throw new Error(payload?.detail || "Link de aceite indisponível.")
        return payload as Pacote
      })
      .then((payload) => { setDados(payload); setNome(texto(payload.aceite.nome_signatario, "")) })
      .catch((falha) => setErro(falha instanceof Error ? falha.message : "Link de aceite inválido."))
      .finally(() => setCarregando(false))
  }, [token])

  async function concluir(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setErro("")
    if (!confirmado) return setErro("Confirme a leitura e o aceite das condições comerciais.")
    if (!nome.trim()) return setErro("Informe o nome completo do signatário.")
    setSalvando(true)
    try {
      const resposta = await fetch(`${API_URL}/crm-documentos/aceites/${token}/confirmar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          aceite_termos: true,
          assinatura_desenhada: nome.trim(),
          user_agent: navigator.userAgent,
          evidencias: { origem: "ACEITE_CTI", tipo: "NOME_CONFIRMADO" },
        }),
      })
      const payload = await resposta.json().catch(() => null)
      if (!resposta.ok) throw new Error(payload?.detail || "Não foi possível registrar o aceite.")
      setSucesso(true)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Falha ao registrar o aceite.")
    } finally {
      setSalvando(false)
    }
  }

  if (carregando) return <main className="min-h-screen bg-[#020817] p-6 text-white">Carregando proposta...</main>
  if (erro && !dados) return <main className="min-h-screen bg-[#020817] p-6 text-red-200">{erro}</main>
  if (sucesso) return <main className="min-h-screen bg-[#020817] p-6 text-white"><section className="mx-auto max-w-3xl rounded-3xl border border-emerald-900 bg-emerald-950/30 p-8"><h1 className="text-3xl font-bold">Aceite registrado</h1><p className="mt-4 text-emerald-100">A confirmação foi incorporada ao histórico comercial da proposta.</p></section></main>

  return <main className="min-h-screen bg-[#020817] p-4 text-white sm:p-6">
    <section className="mx-auto max-w-3xl space-y-6">
      <header className="rounded-3xl border border-[#16325c] bg-[#091a33] p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">CTI • Aceite comercial</p>
        <h1 className="mt-3 text-3xl font-bold">{texto(dados?.proposta.numero, "Proposta comercial")}</h1>
        <p className="mt-3 text-slate-400">Confira os dados e registre a confirmação da negociação.</p>
      </header>

      <article className="rounded-3xl border border-[#13203f] bg-[#071427] p-6">
        <dl className="space-y-3 text-sm">
          <Linha label="Equipamento" valor={texto(dados?.item?.equipamento)} />
          <Linha label="Linha" valor={texto(dados?.item?.linha_produto)} />
          <Linha label="Quantidade" valor={texto(dados?.item?.quantidade, "1")} />
          <Linha label="Valor" valor={moeda(dados?.proposta.valor)} />
          <Linha label="Pagamento" valor={texto(dados?.item?.condicao_pagamento)} />
          <Linha label="Prazo" valor={texto(dados?.item?.prazo_entrega)} />
          <Linha label="Garantia" valor={texto(dados?.item?.garantia)} />
          <Linha label="Entrega" valor={texto(dados?.item?.local_entrega)} />
        </dl>
      </article>

      <form onSubmit={concluir} className="rounded-3xl border border-[#16325c] bg-[#091a33] p-6">
        <label className="block text-sm text-slate-300">Nome completo do signatário<input value={nome} onChange={(evento) => setNome(evento.target.value)} className="mt-2 w-full rounded-xl border border-[#24466f] bg-[#020817] px-4 py-3" required /></label>
        <label className="mt-5 flex items-start gap-3 rounded-xl border border-cyan-900 bg-cyan-950/20 p-4 text-sm text-cyan-100"><input type="checkbox" checked={confirmado} onChange={(evento) => setConfirmado(evento.target.checked)} className="mt-1" /><span>Declaro que li e aceito as condições comerciais desta proposta.</span></label>
        {erro && <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-4 text-red-200">{erro}</div>}
        <button disabled={salvando} className="mt-6 w-full rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{salvando ? "Registrando..." : "Confirmar aceite"}</button>
      </form>
    </section>
  </main>
}

function Linha({ label, valor }: { label: string; valor: string }) { return <div className="flex items-start justify-between gap-4 border-b border-[#13203f] pb-3"><dt className="text-slate-500">{label}</dt><dd className="max-w-[65%] text-right text-slate-200">{valor}</dd></div> }
