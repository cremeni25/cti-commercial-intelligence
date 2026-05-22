export default function Sidebar() {
  return (
    <aside className="w-[280px] min-h-screen bg-[#071028] border-r border-[#13203f] flex flex-col">
      {/* HEADER */}
      <div className="p-6 border-b border-[#13203f]">
        <h1 className="text-3xl font-bold text-cyan-400">CTI</h1>

        <p className="text-sm text-gray-400 mt-2 leading-5">
          Centro de Tecnologia e Inteligência Comercial
        </p>
      </div>

      {/* MENU */}
      <div className="flex-1 p-4 space-y-2">
        <button className="w-full flex items-center gap-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl px-4 py-3 hover:bg-cyan-500/20 transition-all">
          <span>📊</span>
          <span>Dashboard Executivo</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>🧠</span>
          <span>IA Comercial</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>🚛</span>
          <span>Transportadoras</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>🏭</span>
          <span>Implementadoras</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>📈</span>
          <span>Oportunidades</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>🌎</span>
          <span>Mapa Estratégico</span>
        </button>

        <button className="w-full flex items-center gap-3 text-gray-300 rounded-xl px-4 py-3 hover:bg-[#101b36] transition-all">
          <span>⚙️</span>
          <span>Configurações</span>
        </button>
      </div>

      {/* FOOTER */}
      <div className="p-4 border-t border-[#13203f]">
        <div className="bg-[#101b36] rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-widest">
            Status Sistema
          </p>

          <div className="flex items-center gap-2 mt-3">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>

            <span className="text-green-400 text-sm font-medium">
              Online
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}