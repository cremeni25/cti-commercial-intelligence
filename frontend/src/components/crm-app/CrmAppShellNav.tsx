"use client"

import Link from "next/link"
import { Building2, CalendarDays, Plus, Target } from "lucide-react"
import { usePathname } from "next/navigation"

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
  if (pathname.startsWith("/crm-app/login")) return null

  return (
    <nav aria-label="Navegação principal do CRM" className="fixed inset-x-0 bottom-0 z-50 border-t border-[#16325c] bg-[#061126]/98 px-3 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 text-white backdrop-blur">
      <div className="mx-auto grid max-w-4xl grid-cols-4 gap-2">
        {itens.map(({ href, label, icon: Icon, destaque }) => {
          const selecionado = ativo(pathname, href)
          return (
            <Link
              key={href}
              href={href}
              aria-current={selecionado ? "page" : undefined}
              className={`flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-xs transition ${
                destaque
                  ? selecionado
                    ? "bg-cyan-300 font-bold text-slate-950"
                    : "bg-cyan-500 font-semibold text-slate-950"
                  : selecionado
                    ? "bg-cyan-950/60 font-semibold text-cyan-200"
                    : "text-slate-400 hover:bg-[#0a1d38] hover:text-slate-200"
              }`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
