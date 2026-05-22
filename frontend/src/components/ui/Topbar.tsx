export default function Topbar() {
  return (
    <header className="w-full h-[90px] border-b border-[#13203f] bg-[#071028] flex items-center justify-between px-8">
      {/* LEFT */}
      <div>
        <h2 className="text-2xl font-bold text-white">
          Dashboard Executivo
        </h2>

        <p className="text-sm text-gray-400 mt-1">
          Plataforma corporativa de inteligência comercial
        </p>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-5">
        {/* SEARCH */}
        <div className="bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3 w-[320px]">
          <input
            type="text"
            placeholder="Buscar implementadoras, regiões, oportunidades..."
            className="bg-transparent outline-none text-sm text-white w-full"
          />
        </div>

        {/* STATUS */}
        <div className="flex items-center gap-2 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3">
          <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>

          <span className="text-sm text-green-400 font-medium">
            Sistema Online
          </span>
        </div>

        {/* NOTIFICATION */}
        <button className="w-[52px] h-[52px] rounded-xl bg-[#0b1730] border border-[#13203f] text-xl hover:bg-[#13203f] transition-all">
          🔔
        </button>

        {/* NEW PROJECT */}
        <button className="bg-cyan-500 hover:bg-cyan-400 transition-all px-6 py-3 rounded-xl font-semibold text-black">
          Novo Projeto
        </button>

        {/* USER */}
        <div className="flex items-center gap-3 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-2">
          <div className="w-11 h-11 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-black">
            A
          </div>

          <div>
            <p className="text-sm font-semibold text-white">
              Anderson
            </p>

            <p className="text-xs text-gray-400">
              CEO • CTI
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}