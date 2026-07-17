"use client";

import { usePathname } from "next/navigation";

const paginas = {
  "/dashboard": {
    titulo: "Dashboard Executivo",
    descricao: "Plataforma corporativa de inteligência comercial",
  },

  "/ia-comercial": {
    titulo: "IA Comercial",
    descricao: "Central de inteligência e recomendações estratégicas",
  },

  "/empresas": {
    titulo: "Empresas",
    descricao: "Gestão operacional de empresas e razões sociais",
  },

  "/transportadoras": {
    titulo: "Empresas",
    descricao: "Redirecionamento legado para Empresas",
  },

  "/implementadoras": {
    titulo: "Implementadoras",
    descricao: "Rede estratégica de implementadoras homologadas",
  },

  "/locadoras": {
    titulo: "Locadoras",
    descricao: "Gestão comercial e expansão de locadoras",
  },

  "/oportunidades": {
    titulo: "Oportunidades",
    descricao: "Pipeline estratégico e gestão de oportunidades",
  },

  "/pipeline": {
    titulo: "Pipeline",
    descricao: "Gestão visual do funil comercial",
  },

  "/propostas": {
    titulo: "Propostas",
    descricao: "Gestão e acompanhamento de propostas comerciais",
  },

  "/pedidos": {
    titulo: "Pedidos",
    descricao: "Controle operacional dos pedidos comerciais",
  },

  "/atividades": {
    titulo: "Atividades",
    descricao: "Agenda comercial e acompanhamento operacional",
  },

  "/forecast": {
    titulo: "Forecast",
    descricao: "Previsão comercial e projeção de resultados",
  },

  "/mapa-estrategico": {
    titulo: "Mapa Estratégico",
    descricao: "Análise territorial e expansão comercial",
  },

  "/equipamentos/trailer": {
    titulo: "TR • Trailer",
    descricao: "Linha Trailer Carrier Transicold",
  },

  "/equipamentos/diesel-truck": {
    titulo: "DT • Diesel Truck",
    descricao: "Linha Diesel Truck Carrier Transicold",
  },

  "/equipamentos/direct-drive": {
    titulo: "DD • Direct Drive",
    descricao: "Linha Direct Drive Carrier Transicold",
  },

  "/usuarios": {
    titulo: "Usuários",
    descricao: "Administração de usuários e permissões",
  },

  "/configuracoes": {
    titulo: "Configurações",
    descricao: "Configurações administrativas do CTI",
  },
};

export default function Topbar() {
  const pathname = usePathname();

  const paginaAtual =
    paginas[pathname as keyof typeof paginas] || {
      titulo: "CTI",
      descricao: "Centro de Tecnologia e Inteligência Comercial",
    };

  return (
    <header className="w-full h-[90px] border-b border-[#13203f] bg-[#071028] flex items-center justify-between px-8">
      {/* LEFT */}
      <div>
        <h2 className="text-2xl font-bold text-white">
          {paginaAtual.titulo}
        </h2>

        <p className="text-sm text-gray-400 mt-1">
          {paginaAtual.descricao}
        </p>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-5">
        {/* STATUS */}
        <div className="flex items-center gap-2 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3">
          <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>

          <span className="text-sm text-green-400 font-medium">
            CTI Online
          </span>
        </div>

        {/* NOTIFICATION */}
        <button className="w-[52px] h-[52px] rounded-xl bg-[#0b1730] border border-[#13203f] text-xl hover:bg-[#13203f] transition-all">
          🔔
        </button>

        {/* USER */}
        <div className="flex items-center gap-3 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-2">
          <div className="w-11 h-11 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-black">
            A
          </div>

          <div>
            <p className="text-sm font-semibold text-white">
              Anderson Navarro
            </p>

            <p className="text-xs text-gray-400">
              CEO • ADMIN_MASTER
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}