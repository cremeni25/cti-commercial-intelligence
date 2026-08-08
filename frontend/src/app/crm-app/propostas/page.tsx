import DocumentosComerciaisLista from "@/components/crm-app/DocumentosComerciaisLista"
import JornadaDocumentalNav from "@/components/crm-app/JornadaDocumentalNav"

export default function PropostasPage() {
  return <><div className="bg-[#020817] px-4 pt-5 text-white sm:px-6"><div className="mx-auto max-w-6xl"><JornadaDocumentalNav/></div></div><DocumentosComerciaisLista tipo="propostas" /></>
}
