import Link from "next/link"
import JornadaDocumentalNav from "@/components/crm-app/JornadaDocumentalNav"
import NegociosNativos from "../_components/NegociosNativos"

export default function CrmAppOportunidadesPage() {
  return <>
    <div className="bg-[#020817] px-4 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-5xl space-y-3"><JornadaDocumentalNav/><div className="flex justify-end"><Link href="/crm-app/historico" className="rounded-xl border border-amber-700 px-4 py-3 text-sm font-semibold text-amber-200">Histórico de encerrados</Link></div></div>
    </div>
    <NegociosNativos modo="oportunidades" />
  </>
}
