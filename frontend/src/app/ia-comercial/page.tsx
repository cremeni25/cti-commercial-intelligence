import Sidebar from "@/components/ui/Sidebar"
import Topbar from "@/components/ui/Topbar"

interface Props {
  title: string
  description: string
}

function ModulePlaceholder({
  title,
  description,
}: Props) {
  return (
    <main className="flex min-h-screen bg-[#020817]">
      <Sidebar />

      <section className="flex-1">
        <Topbar />

        <div className="p-8">
          <div className="bg-[#091a33] border border-[#13203f] rounded-3xl p-10">
            <p className="text-cyan-400 text-sm uppercase tracking-[0.2em]">
              CTI OPERACIONAL
            </p>

            <h1 className="text-5xl font-bold text-white mt-4">
              {title}
            </h1>

            <p className="text-gray-400 text-lg mt-6 max-w-3xl leading-8">
              {description}
            </p>
          </div>
        </div>
      </section>
    </main>
  )
}

export default function Page() {
  return (
    <ModulePlaceholder
      title="IA COMERCIAL"
      description="
      Central analítica de inteligência comercial, recomendações estratégicas,
      monitoramento operacional e suporte executivo orientado por dados.
      "
    />
  )
}