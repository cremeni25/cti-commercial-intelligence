import JornadaDocumentalNav from "@/components/crm-app/JornadaDocumentalNav"
import NegociosNativos from "../_components/NegociosNativos"

export default function CrmAppOportunidadesPage() {
  return <>
    <div className="bg-[#020817] px-4 pt-5 text-white sm:px-6">
      <div className="mx-auto max-w-5xl"><JornadaDocumentalNav/></div>
    </div>
    <NegociosNativos modo="oportunidades" />
  </>
}
