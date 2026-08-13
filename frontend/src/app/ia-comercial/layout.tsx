import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>
    <Link href="/crm-app" aria-label="Voltar ao CRM" className="fixed left-3 top-3 z-[100] grid size-10 place-items-center rounded-xl border border-[#24466f] bg-[#07162b] text-cyan-300 xl:hidden">
      <ArrowLeft size={18} />
    </Link>
    {children}
  </>
}
