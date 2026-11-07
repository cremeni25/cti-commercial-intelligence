"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Boxes, GraduationCap, Loader2, RefreshCw } from "lucide-react"
import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"
import BriefingComercialView from "@/components/inteligencia/BriefingComercialView"
import { useBriefingComercial } from "@/components/inteligencia/useBriefingComercial"
import { useAuth } from "@/core/auth/AuthContext"
import { possuiVisaoConsolidada } from "@/core/rbac/commercial-scope"
import { listarUsuarios } from "@/modules/usuarios/services/usuarios.service"
import type { UsuarioCTI as UsuarioGovernanca } from "@/modules/usuarios/types/usuario.types"
import { buscarModulosPlataforma, type ModuloPlataforma } from "@/services/inteligencia-comercial"

const ROTULO_STATUS: Record<ModuloPlataforma["status"], string> = { ativo: "Ativo", beta: "Em evolução", planejado: "Em breve" }
const ESTILO_STATUS: Record<ModuloPlataforma["status"], string> = {
  ativo: "border-emerald-800 text-emerald-300",
  beta: "border-amber-800 text-amber-300",
  planejado: "border-slate-700 text-slate-400",
}

export default function CentralInteligenciaPage() {
  const { usuario } = useAuth()
  const gestao = Boolean(usuario && possuiVisaoConsolidada(usuario))
  const [responsavel, setResponsavel] = useState("")
  const [usuarios, setUsuarios] = useState<UsuarioGovernanca[]>([])
  const [modulos, setModulos] = useState<ModuloPlataforma[]>([])
  const { briefing, carregando, erro, atualizar } = useBriefingComercial({ responsavelId: responsavel || undefined, limite: 12 })

  useEffect(() => { if (gestao) void listarUsuarios().then(setUsuarios).catch(() => setUsuarios([])) }, [gestao])
  useEffect(() => { void buscarModulosPlataforma().then(setModulos).catch(() => setModulos([])) }, [])

  const equipe = useMemo(() => usuarios.filter((item) => item.id && item.nome).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")), [usuarios])
  const outrosModulos = modulos.filter((modulo) => modulo.codigo !== "central")

  return (
    <main className="flex min-h-screen bg-[#020817] text-white">
      <Sidebar/>
      <section className="min-w-0 flex-1">
        <Topbar/>
        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-400">Agente de Inteligência Comercial</p>
              <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Central de Inteligência</h1>
              <p className="mt-2 max-w-2xl text-gray-400">O que importa agora na carteira: prioridades, riscos e a saúde do funil, com o próximo passo de cada negócio.</p>
            </div>
            <div className="flex flex-wrap items-end gap-3">
              {gestao && (
                <label className="flex min-w-56 flex-col gap-1 text-sm text-gray-300">Responsável
                  <select value={responsavel} onChange={(evento) => setResponsavel(evento.target.value)} className="rounded-lg border border-[#24466f] bg-[#020817] px-3 py-2 text-white">
                    <option value="">Equipe consolidada</option>
                    {equipe.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}
                  </select>
                </label>
              )}
              <button type="button" onClick={() => void atualizar()} disabled={carregando} className="flex items-center gap-2 rounded-xl border border-cyan-700 px-4 py-2 text-sm font-semibold text-cyan-200 disabled:opacity-60"><RefreshCw size={16} className={carregando ? "animate-spin" : ""}/> Atualizar leitura</button>
            </div>
          </header>

          {erro && <div className="rounded-xl border border-red-500/60 bg-red-950/30 p-4 text-sm text-red-200">{erro}</div>}
          {briefing ? <BriefingComercialView briefing={briefing} canal="web"/> : carregando ? <div className="grid min-h-64 place-items-center"><Loader2 className="animate-spin text-cyan-300"/></div> : null}

          {outrosModulos.length > 0 && (
            <section className="rounded-3xl border border-[#13203f] bg-[#061126] p-5">
              <h2 className="flex items-center gap-2 text-lg font-semibold"><Boxes size={20} className="text-cyan-400"/> Módulos da plataforma</h2>
              <p className="mt-1 text-sm text-slate-500">Tudo o que o CTI faz, em um só lugar. Módulos novos aparecem aqui assim que entram em operação.</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {outrosModulos.map((modulo) => {
                  const conteudo = (
                    <>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] uppercase tracking-wider text-slate-500">{modulo.categoria_rotulo}</span>
                        <span className={`rounded-full border px-2 py-0.5 text-[11px] ${ESTILO_STATUS[modulo.status]}`}>{ROTULO_STATUS[modulo.status]}</span>
                      </div>
                      <p className="mt-2 flex items-center gap-2 font-semibold text-white">{modulo.codigo === "treinamentos" && <GraduationCap size={16} className="text-cyan-300"/>}{modulo.nome}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{modulo.descricao}</p>
                      {modulo.consultado_pela_ia && <p className="mt-2 text-[11px] text-cyan-300/80">Lido pela IA Comercial</p>}
                    </>
                  )
                  return modulo.rota_web
                    ? <Link key={modulo.codigo} href={modulo.rota_web} className="rounded-2xl border border-[#163356] bg-[#081a32] p-4 transition hover:border-cyan-700">{conteudo}</Link>
                    : <div key={modulo.codigo} className="rounded-2xl border border-dashed border-[#24466f] bg-[#050f22] p-4">{conteudo}</div>
                })}
              </div>
            </section>
          )}
        </div>
      </section>
    </main>
  )
}
