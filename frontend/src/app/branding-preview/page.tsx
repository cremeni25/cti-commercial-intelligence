import Image from "next/image"
import logoCTI from "@/assets/logo/Logo CTI - fundo azul.png"
import logoViena from "@/assets/logo/Logo Viena.png"

export default function BrandingPreviewPage() {
  return (
    <main className="min-h-screen bg-[#020817] px-5 py-8 text-white sm:px-8 lg:px-12">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="rounded-3xl border border-[#17345f] bg-[linear-gradient(135deg,#07152e_0%,#061127_55%,#041020_100%)] p-6 shadow-2xl sm:p-8">
          <p className="text-xs uppercase tracking-[0.32em] text-cyan-400">Preview institucional</p>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Co-branding CTI + Refrigeração Viena</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 sm:text-base">
            CTI permanece como plataforma principal. Viena aparece como operação institucional atendida, sem alteração da arquitetura visual do CTI Web.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.05fr_1.95fr]">
          <div className="rounded-3xl border border-[#17345f] bg-[#071028] p-5 shadow-xl">
            <p className="mb-4 text-xs uppercase tracking-[0.25em] text-slate-400">Aplicação no layout atual</p>
            <div className="rounded-2xl border border-[#13203f] bg-[#071028] p-4">
              <div className="flex flex-col items-center gap-3 border-b border-[#13203f] pb-4">
                <Image src={logoCTI} alt="CTI" width={220} height={90} priority className="h-auto w-[220px] object-contain" />
                <div className="flex w-full items-center justify-center gap-3">
                  <div className="h-px w-10 bg-[#24466f]" />
                  <span className="text-[10px] uppercase tracking-[0.28em] text-slate-500">Operação atendida</span>
                  <div className="h-px w-10 bg-[#24466f]" />
                </div>
                <div className="rounded-xl bg-white px-4 py-2 shadow-inner">
                  <Image src={logoViena} alt="Refrigeração Viena" width={146} height={58} className="h-auto w-[128px] object-contain" />
                </div>
              </div>
              <nav className="space-y-2 pt-4 text-sm text-slate-300">
                {['Dashboard Executivo','Histórico Comercial','IA Comercial','Oportunidades','Pipeline','Propostas','Pedidos','Vendas','Relatórios','Atividades','Forecast'].map((item, index) => (
                  <div key={item} className={`rounded-xl px-4 py-3 ${index === 0 ? 'border border-cyan-500/20 bg-cyan-500/10 text-cyan-300' : 'bg-[#0a1630]'}`}>{item}</div>
                ))}
              </nav>
            </div>
            <p className="mt-4 text-xs leading-5 text-slate-400">
              O menu, a largura da sidebar e a disposição das funções permanecem iguais. A Viena entra somente como assinatura institucional abaixo da marca CTI.
            </p>
          </div>

          <div className="space-y-6">
            <section className="rounded-3xl border border-[#17345f] bg-[#091a33] p-6 shadow-xl sm:p-8">
              <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Login</p>
              <div className="mx-auto mt-6 max-w-xl rounded-3xl border border-[#16325c] bg-[#07162d] p-6 sm:p-8">
                <div className="flex flex-col items-center">
                  <Image src={logoCTI} alt="CTI" width={280} height={110} className="h-auto w-[250px] object-contain" />
                  <div className="mt-5 flex items-center gap-4">
                    <div className="h-10 w-px bg-[#24466f]" />
                    <div>
                      <p className="mb-1 text-[10px] uppercase tracking-[0.25em] text-slate-500">Operação atendida</p>
                      <div className="rounded-lg bg-white px-3 py-2">
                        <Image src={logoViena} alt="Refrigeração Viena" width={132} height={52} className="h-auto w-[118px] object-contain" />
                      </div>
                    </div>
                  </div>
                  <h2 className="mt-7 text-2xl font-bold">Acesso ao sistema</h2>
                  <p className="mt-2 text-sm text-slate-400">Entre com as credenciais autorizadas do CTI.</p>
                </div>
                <div className="mt-7 space-y-4">
                  <div className="rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-slate-500">E-mail</div>
                  <div className="rounded-xl border border-[#1d3b67] bg-[#061126] px-4 py-3 text-slate-500">Senha</div>
                  <div className="rounded-xl bg-cyan-500 px-4 py-3 text-center font-semibold text-slate-950">Entrar</div>
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-[#17345f] bg-[#08162d] p-6 shadow-xl sm:p-8">
              <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Relatórios e exportações</p>
              <div className="mt-5 overflow-hidden rounded-2xl border border-[#1c365e] bg-white text-slate-900">
                <div className="flex items-center justify-between gap-6 border-b border-slate-200 px-6 py-5">
                  <Image src={logoCTI} alt="CTI" width={180} height={72} className="h-auto w-[165px] object-contain" />
                  <div className="text-center">
                    <div className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Operação atendida</div>
                    <Image src={logoViena} alt="Refrigeração Viena" width={132} height={52} className="mt-2 h-auto w-[118px] object-contain" />
                  </div>
                </div>
                <div className="px-6 py-8">
                  <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Relatório comercial</div>
                  <div className="mt-2 text-2xl font-bold text-slate-900">Inteligência comercial · Operação Viena SP</div>
                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    {['Pipeline','Forecast','Atividades'].map((item) => <div key={item} className="rounded-xl bg-slate-100 p-4 font-semibold">{item}</div>)}
                  </div>
                </div>
              </div>
            </section>
          </div>
        </section>

        <section className="rounded-3xl border border-cyan-900/50 bg-cyan-950/10 p-6">
          <div className="grid gap-3 text-sm text-cyan-100 md:grid-cols-3">
            <div>CTI permanece como marca principal.</div>
            <div>Viena entra como assinatura institucional.</div>
            <div>As marcas não são fundidas em um único símbolo.</div>
          </div>
        </section>
      </div>
    </main>
  )
}
