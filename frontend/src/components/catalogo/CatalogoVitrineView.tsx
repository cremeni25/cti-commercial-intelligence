"use client"

import { useEffect, useMemo, useState } from "react"
import { Check, Copy, ExternalLink, FileText, Loader2, PlayCircle, Search, Zap } from "lucide-react"
import { useAuth } from "@/core/auth/AuthContext"
import { useOperationalI18n } from "@/core/i18n/operational"
import TabelaAplicacaoView from "@/components/catalogo/TabelaAplicacaoView"
import { anexarMaterialCatalogo, buscarVitrineCatalogo, type EquipamentoCatalogo, type LinhaCatalogo, type MaterialCatalogo, type VitrineCatalogo } from "@/services/inteligencia-comercial"

const ROTULO_CONFIGURACAO: Record<string, string> = {
  PADRAO: "Padrão",
  ACOPLADO: "Acoplado ao motor",
  ACOPLADO_E_ELETRICO: "Acoplado + elétrico (stand-by)",
}

function rotuloCampo(chave: string) {
  const texto = chave.replaceAll("_", " ").trim()
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function normalizar(valor: string) {
  return valor.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
}

/** Texto curto e pronto para colar no WhatsApp/e-mail do cliente. */
export function resumoParaCompartilhar(linha: LinhaCatalogo, equipamento: EquipamentoCatalogo) {
  const partes = [`*${equipamento.nome_comercial}* — Carrier Transicold, linha ${linha.nome} (${linha.sigla})`]
  const configuracao = ROTULO_CONFIGURACAO[equipamento.configuracao]
  if (configuracao && equipamento.configuracao !== "PADRAO") partes.push(`Configuração: ${configuracao}`)
  if (equipamento.compressor) partes.push(`Compressor: ${equipamento.compressor}`)
  if (equipamento.possui_eletrico) partes.push("Com operação elétrica (stand-by)")
  Object.entries(equipamento.descricao_tecnica).slice(0, 4).forEach(([chave, valor]) => partes.push(`${rotuloCampo(chave)}: ${String(valor)}`))
  const materiais = equipamento.materiais.length > 0 ? equipamento.materiais : linha.materiais
  materiais.slice(0, 2).forEach((material) => partes.push(`${material.titulo}: ${material.url}`))
  return partes.join("\n")
}

async function copiar(texto: string) {
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    const area = document.createElement("textarea")
    area.value = texto
    area.setAttribute("readonly", "")
    area.style.position = "fixed"
    area.style.opacity = "0"
    document.body.appendChild(area)
    area.select()
    const ok = document.execCommand("copy")
    area.remove()
    return ok
  }
}

function IconeMaterial({ tipo }: { tipo: string }) {
  return tipo === "video" ? <PlayCircle size={14}/> : <FileText size={14}/>
}

function LinksMateriais({ materiais }: { materiais: MaterialCatalogo[] }) {
  if (materiais.length === 0) return null
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {materiais.map((material) => (
        <a key={material.url} href={material.url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-9 items-center gap-1.5 rounded-xl border border-[#24466f] px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:border-cyan-600">
          <IconeMaterial tipo={material.tipo}/>{material.titulo}<ExternalLink size={12} className="opacity-60"/>
        </a>
      ))}
    </div>
  )
}

function AnexarMaterial({ onAnexado }: { onAnexado: () => void }) {
  const [titulo, setTitulo] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [mensagem, setMensagem] = useState("")
  async function enviar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const arquivo = (evento.currentTarget.elements.namedItem("arquivo") as HTMLInputElement | null)?.files?.[0]
    if (!arquivo || !titulo.trim()) return
    setEnviando(true)
    setMensagem("")
    try {
      await anexarMaterialCatalogo(titulo.trim(), arquivo)
      setMensagem("Material anexado. Já aparece para a equipe no web e no app.")
      setTitulo("")
      onAnexado()
    } catch (falha) {
      setMensagem(falha instanceof Error ? falha.message : "Não foi possível anexar.")
    } finally {
      setEnviando(false)
    }
  }
  return (
    <details className="mt-3 rounded-2xl border border-[#163356] bg-[#050f22] p-3">
      <summary className="cursor-pointer text-xs font-semibold text-slate-300">Anexar PDF interno (Master)</summary>
      <form onSubmit={enviar} className="mt-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
        <input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título do material" aria-label="Título do material" maxLength={120} className="min-h-10 rounded-xl border border-[#24466f] bg-[#020817] px-3 text-sm text-white"/>
        <input name="arquivo" type="file" accept="application/pdf" aria-label="Arquivo PDF" className="text-xs text-slate-300"/>
        <button type="submit" disabled={enviando} className="min-h-10 rounded-xl bg-cyan-500 px-4 text-sm font-bold text-slate-950 disabled:opacity-60">{enviando ? "Enviando..." : "Anexar"}</button>
      </form>
      {mensagem && <p role="status" className="mt-2 text-xs text-cyan-100">{mensagem}</p>}
    </details>
  )
}

export default function CatalogoVitrineView({ compacto = false }: { compacto?: boolean }) {
  const { formatCurrency } = useOperationalI18n()
  const { usuario } = useAuth()
  const master = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"
  const [versao, setVersao] = useState(0)
  const [vitrine, setVitrine] = useState<VitrineCatalogo | null>(null)
  const [erro, setErro] = useState("")
  const [linhaAtiva, setLinhaAtiva] = useState("TODAS")
  const [busca, setBusca] = useState("")
  const [copiado, setCopiado] = useState("")

  useEffect(() => {
    let ativo = true
    buscarVitrineCatalogo()
      .then((dados) => { if (ativo) setVitrine(dados) })
      .catch((falha: unknown) => { if (ativo) setErro(falha instanceof Error ? falha.message : "Não foi possível carregar o catálogo.") })
    return () => { ativo = false }
  }, [versao])

  useEffect(() => {
    if (!copiado) return
    const temporizador = window.setTimeout(() => setCopiado(""), 2500)
    return () => window.clearTimeout(temporizador)
  }, [copiado])

  const linhas = useMemo(() => {
    if (!vitrine) return []
    const termo = normalizar(busca.trim())
    return vitrine.linhas
      .filter((linha) => linhaAtiva === "TODAS" || linha.codigo === linhaAtiva)
      .map((linha) => ({
        ...linha,
        equipamentos: termo
          ? linha.equipamentos.filter((item) => normalizar(`${item.nome_comercial} ${item.modelo_base || ""} ${item.codigo} ${item.compressor || ""} ${linha.nome} ${linha.sigla}`).includes(termo))
          : linha.equipamentos,
      }))
      .filter((linha) => linha.equipamentos.length > 0 || (!termo && linha.materiais.length > 0))
  }, [vitrine, linhaAtiva, busca])

  if (erro) return <div className="rounded-2xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-200">{erro}</div>
  if (!vitrine) return <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div>

  const encontrados = linhas.reduce((total, linha) => total + linha.equipamentos.length, 0)

  return (
    <div className="space-y-5">
      {vitrine.tabela_aplicacao && <TabelaAplicacaoView tabela={vitrine.tabela_aplicacao} onCopiado={setCopiado}/>}

      {(vitrine.linktree_url || vitrine.materiais_gerais.length > 0 || (vitrine.materiais_internos || []).length > 0 || master) && (
        <section className="rounded-3xl border border-cyan-900/70 bg-[#06182f] p-5">
          <p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Materiais de divulgação</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {vitrine.linktree_url && <a href={vitrine.linktree_url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-bold text-slate-950">Catálogo completo<ExternalLink size={14}/></a>}
          </div>
          <LinksMateriais materiais={[...(vitrine.materiais_internos || []), ...vitrine.materiais_gerais]}/>
          {master && !compacto && <AnexarMaterial onAnexado={() => setVersao((v) => v + 1)}/>}
        </section>
      )}

      <section className="sticky top-0 z-10 -mx-1 space-y-3 bg-[#020817]/95 px-1 py-2 backdrop-blur">
        <label className="flex items-center gap-2 rounded-2xl border border-[#24466f] bg-[#061126] px-4">
          <Search size={18} className="text-slate-500"/>
          <span className="sr-only">Buscar equipamento</span>
          <input value={busca} onChange={(evento) => setBusca(evento.target.value)} placeholder="Buscar modelo, linha ou compressor" className="min-h-12 w-full bg-transparent text-sm text-white outline-none"/>
        </label>
        <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Linhas de produto">
          {[{ codigo: "TODAS", nome: "Todas" }, ...vitrine.linhas].map((linha) => (
            <button key={linha.codigo} type="button" role="tab" aria-selected={linhaAtiva === linha.codigo} onClick={() => setLinhaAtiva(linha.codigo)} className={`shrink-0 rounded-full border px-4 py-2 text-xs font-semibold ${linhaAtiva === linha.codigo ? "border-cyan-500 bg-cyan-950/60 text-cyan-100" : "border-[#24466f] text-slate-400"}`}>
              {linha.nome}
            </button>
          ))}
        </div>
      </section>

      {copiado && <p role="status" className="rounded-xl border border-emerald-800 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-200">{copiado}</p>}
      {encontrados === 0 && <p className="rounded-2xl border border-dashed border-[#24466f] p-6 text-center text-sm text-slate-400">Nenhum equipamento encontrado para esta busca.</p>}

      {linhas.map((linha) => (
        <section key={linha.codigo} aria-label={`Linha ${linha.nome}`}>
          <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 className="text-lg font-bold text-white">{linha.nome} <span className="text-sm font-semibold text-cyan-400">· {linha.sigla}</span></h2>
              <p className="text-sm text-slate-400">{linha.descricao}</p>
            </div>
            <span className="text-xs text-slate-500">{linha.equipamentos.length} modelo{linha.equipamentos.length === 1 ? "" : "s"}</span>
          </div>
          <LinksMateriais materiais={linha.materiais}/>
          <div className={`mt-3 grid gap-3 ${compacto ? "" : "sm:grid-cols-2 xl:grid-cols-3"}`}>
            {linha.equipamentos.map((equipamento) => {
              const tecnica = Object.entries(equipamento.descricao_tecnica)
              return (
                <article key={equipamento.codigo} className="flex flex-col rounded-2xl border border-[#163356] bg-[#081a32] p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold leading-6 text-white">{equipamento.nome_comercial}</h3>
                    {equipamento.possui_eletrico && <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-amber-700/70 px-2 py-0.5 text-[11px] text-amber-200"><Zap size={11}/>Elétrico</span>}
                  </div>
                  <dl className="mt-2 space-y-1 text-xs text-slate-400">
                    {equipamento.configuracao !== "PADRAO" && <div className="flex gap-1"><dt>Configuração:</dt><dd className="text-slate-200">{ROTULO_CONFIGURACAO[equipamento.configuracao] || equipamento.configuracao}</dd></div>}
                    {equipamento.compressor && <div className="flex gap-1"><dt>Compressor:</dt><dd className="text-slate-200">{equipamento.compressor}</dd></div>}
                    {tecnica.slice(0, 4).map(([chave, valor]) => <div key={chave} className="flex gap-1"><dt>{rotuloCampo(chave)}:</dt><dd className="text-slate-200">{String(valor)}</dd></div>)}
                  </dl>
                  {equipamento.preco_vigente && equipamento.preco_vigente.valor > 0 && (
                    <p className="mt-3 text-sm"><span className="text-xs text-slate-500">Preço de tabela </span><strong className="text-emerald-300">{formatCurrency(equipamento.preco_vigente.valor)}</strong></p>
                  )}
                  <LinksMateriais materiais={equipamento.materiais}/>
<div className="mt-auto pt-4"><button type="button" onClick={() => void copiar(resumoParaCompartilhar(linha, equipamento)).then((ok) => setCopiado(ok ? `Resumo do ${equipamento.nome_comercial} copiado. Cole no WhatsApp ou e-mail.` : "Não foi possível copiar neste dispositivo."))} className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-[#22466d] bg-[#0b2342] text-sm font-semibold text-cyan-200">
                    {copiado.includes(equipamento.nome_comercial) ? <Check size={16}/> : <Copy size={16}/>} Copiar para WhatsApp
                  </button></div>
                </article>
              )
            })}
          </div>
        </section>
      ))}

      <p className="text-xs text-slate-600">{vitrine.precos_visiveis ? "Preços de tabela vigentes, sem descontos ou condições negociadas." : "Preços disponíveis para quem emite propostas."} {vitrine.fonte === "catalogo_oficial_sem_precos" ? "Exibindo o catálogo oficial de modelos." : ""}</p>
    </div>
  )
}
