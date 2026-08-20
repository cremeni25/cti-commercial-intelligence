"use client"

import Link from "next/link"
import { Archive, ArchiveRestore, Building2, CalendarDays, Layers3, Plus, Target } from "lucide-react"
import { usePathname, useRouter } from "next/navigation"
import { useState } from "react"
import { useAuth } from "@/core/auth"

const itens = [
  { href: "/crm-app", label: "Início", icon: Building2 },
  { href: "/crm-app/agenda", label: "Agenda", icon: CalendarDays },
  { href: "/crm-app/oportunidades", label: "Negócios", icon: Target },
  { href: "/crm-app/atividades/nova", label: "Registrar", icon: Plus, destaque: true },
]

function ativo(pathname: string, href: string) {
  if (href === "/crm-app") return pathname === href
  if (href === "/crm-app/oportunidades") {
    return pathname.startsWith("/crm-app/oportunidades") || pathname.startsWith("/crm-app/pipeline") || pathname.startsWith("/crm-app/forecast") || pathname.startsWith("/crm-app/historico")
  }
  return pathname.startsWith(href)
}

export function CrmAppShellNav() {
  const pathname = usePathname() || "/crm-app"
  const router = useRouter()
  const { usuario } = useAuth()
  const [arquivando, setArquivando] = useState(false)
  const [erro, setErro] = useState("")
  if (pathname.startsWith("/crm-app/login")) return null

  const matchEditar = pathname.match(/^\/crm-app\/oportunidades\/([^/]+)\/editar$/)
  const oportunidadeId = matchEditar ? decodeURIComponent(matchEditar[1]) : ""
  const adminMaster = String(usuario?.tipo_usuario || "").toUpperCase() === "ADMIN_MASTER"

  async function arquivarTeste() {
    if (!oportunidadeId || arquivando) return
    if (!window.confirm("Arquivar esta oportunidade como registro de teste? Ela deixará de participar de Pipeline, Forecast, Relatórios e IA, mas continuará preservada para auditoria.")) return
    setArquivando(true)
    setErro("")
    try {
      const resposta = await fetch(`/api/crm-proxy/crm-app/oportunidades/${encodeURIComponent(oportunidadeId)}/arquivar-teste`, { method: "POST" })
      const payload = await resposta.json().catch(() => ({}))
      if (!resposta.ok) throw new Error(String(payload?.detail || `Falha ${resposta.status}`))
      router.push("/crm-app/oportunidades")
      router.refresh()
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível arquivar o registro de teste.")
    } finally {
      setArquivando(false)
    }
  }

  return (
    <>
      {adminMaster && pathname === "/crm-app" && (
        <div className="fixed right-3 bottom-[82px] z-40">
          <Link href="/crm-app/testes-arquivados" className="flex min-h-11 items-center gap-2 rounded-xl border border-amber-700 bg-[#07162b]/98 px-4 text-xs font-semibold text-amber-200 shadow-xl backdrop-blur">
            <ArchiveRestore size={16} />
            Testes arquivados
          </Link>
        </div>
      )}

      {oportunidadeId && (
        <div className="fixed inset-x-3 bottom-[82px] z-40 mx-auto max-w-3xl rounded-2xl border border-[#24466f] bg-[#07162b]/98 p-3 shadow-2xl backdrop-blur">
          {erro && <p className="mb-2 rounded-xl border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-200">{erro}</p>}
          <div className={`grid gap-2 ${adminMaster ? "grid-cols-2" : "grid-cols-1"}`}>
            <Link href={`/crm-app/historico/${encodeURIComponent(oportunidadeId)}?origem=oportunidades`} className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-3 text-sm font-bold text-slate-950">
              <Layers3 size={17} />
              Gerenciar itens
            </Link>
            {adminMaster && (
              <button type="button" disabled={arquivando} onClick={() => void arquivarTeste()} className="flex min-h-12 items-center justify-center gap-2 rounded-xl border border-amber-700 bg-amber-950/40 px-3 text-sm font-semibold text-amber-200 disabled:opacity-50">
                <Archive size={17} />
                {arquivando ? "Arquivando..." : "Arquivar teste"}
              </button>
            )}
          </div>
        </div>
      )}

      <nav aria-label="Navegação principal do CRM" className="fixed inset-x-0 bottom-0 z-50 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 text-white backdrop-blur">
        <div className="mx-auto grid max-w-4xl grid-cols-4 gap-2">
          {itens.map(({ href, label, icon: Icon, destaque }) => {
            const selecionado = ativo(pathname, href)
            return (
              <Link key={href} href={href} aria-current={selecionado ? "page" : undefined} className={`flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-xs transition ${destaque ? selecionado ? "bg-cyan-300 font-bold text-slate-950" : "bg-cyan-500 font-semibold text-slate-950" : selecionado ? "bg-cyan-950/60 font-semibold text-cyan-200" : "text-slate-400 hover:bg-[#0a1d38] hover:text-slate-200"}`}>
                <Icon size={20} />
                <span>{label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </>
  )
}
