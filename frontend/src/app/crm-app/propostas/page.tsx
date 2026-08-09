import Link from "next/link"
import DocumentosComerciaisLista from "@/components/crm-app/DocumentosComerciaisLista"
import JornadaDocumentalNav from "@/components/crm-app/JornadaDocumentalNav"

export default function PropostasPage() {
  return <>
    <div className="bg-[#020817] px-4 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-6xl space-y-3">
        <Link href="/crm-app" className="inline-flex items-center rounded-xl border border-[#24466f] bg-[#07162b] px-4 py-2 text-sm font-semibold text-cyan-300">← Voltar ao CRM</Link>
        <JornadaDocumentalNav/>
      </div>
    </div>
    <DocumentosComerciaisLista tipo="propostas" />
  </>
}
