"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/core/auth/AuthContext";
import { useI18n, type MessageKey } from "@/core/i18n";
import { OPERATIONAL_CONTEXTS, useOperationalContext, type OperationalContextValue, type PeriodPreset } from "@/context/OperationalContext";

type Pagina = { tituloKey?: MessageKey; titulo?: string; descricao: { "pt-BR": string; en: string; es: string } };

const paginas: Record<string, Pagina> = {
  "/dashboard": { tituloKey: "nav.dashboard", descricao: { "pt-BR": "Leitura estratégica ANFIR 2026 · Viena SP", en: "ANFIR 2026 strategic reading · Viena SP", es: "Lectura estratégica ANFIR 2026 · Viena SP" } },
  "/inteligencia": { titulo: "Inteligência de Mercado", descricao: { "pt-BR": "Leitura executiva do mercado realizado ANFIR", en: "Executive reading of realized ANFIR market", es: "Lectura ejecutiva del mercado realizado ANFIR" } },
  "/ia-comercial": { tituloKey: "nav.salesAi", descricao: { "pt-BR": "Central de inteligência e recomendações estratégicas", en: "Intelligence center for strategic recommendations", es: "Centro de inteligencia y recomendaciones estratégicas" } },
  "/empresas": { tituloKey: "nav.companies", descricao: { "pt-BR": "Gestão operacional de empresas e razões sociais", en: "Operational management of accounts and legal entities", es: "Gestión operativa de empresas y razones sociales" } },
  "/transportadoras": { tituloKey: "nav.companies", descricao: { "pt-BR": "Redirecionamento legado para Empresas", en: "Legacy redirect to Companies", es: "Redirección heredada a Empresas" } },
  "/implementadoras": { tituloKey: "nav.bodyBuilders", descricao: { "pt-BR": "Rede estratégica de implementadoras homologadas", en: "Strategic network of approved body builders", es: "Red estratégica de carroceros homologados" } },
  "/locadoras": { titulo: "Locadoras", descricao: { "pt-BR": "Gestão comercial e expansão de locadoras", en: "Commercial management and rental-fleet expansion", es: "Gestión comercial y expansión de empresas de alquiler" } },
  "/oportunidades": { tituloKey: "nav.opportunities", descricao: { "pt-BR": "Pipeline estratégico e gestão de oportunidades", en: "Strategic pipeline and opportunity management", es: "Pipeline estratégico y gestión de oportunidades" } },
  "/pipeline": { tituloKey: "nav.pipeline", descricao: { "pt-BR": "Gestão visual do funil comercial", en: "Visual sales-pipeline management", es: "Gestión visual del pipeline comercial" } },
  "/propostas": { tituloKey: "nav.proposals", descricao: { "pt-BR": "Gestão e acompanhamento de propostas comerciais", en: "Sales proposal management and follow-up", es: "Gestión y seguimiento de propuestas comerciales" } },
  "/pedidos": { tituloKey: "nav.orders", descricao: { "pt-BR": "Controle operacional dos pedidos comerciais", en: "Operational control of commercial orders", es: "Control operativo de pedidos comerciales" } },
  "/atividades": { tituloKey: "nav.activities", descricao: { "pt-BR": "Agenda comercial e acompanhamento operacional", en: "Sales agenda and operational follow-up", es: "Agenda comercial y seguimiento operativo" } },
  "/forecast": { tituloKey: "nav.forecast", descricao: { "pt-BR": "Previsão comercial e projeção de resultados", en: "Sales forecast and projected results", es: "Forecast comercial y proyección de resultados" } },
  "/mapa-estrategico": { tituloKey: "nav.strategicMap", descricao: { "pt-BR": "Análise territorial e expansão comercial", en: "Territory analysis and commercial expansion", es: "Análisis territorial y expansión comercial" } },
  "/equipamentos/trailer": { tituloKey: "nav.trailer", descricao: { "pt-BR": "Linha Trailer Carrier Transicold", en: "Carrier Transicold Trailer line", es: "Línea Trailer Carrier Transicold" } },
  "/equipamentos/diesel-truck": { tituloKey: "nav.dieselTruck", descricao: { "pt-BR": "Linha Diesel Truck Carrier Transicold", en: "Carrier Transicold Diesel Truck line", es: "Línea Diesel Truck Carrier Transicold" } },
  "/equipamentos/direct-drive": { tituloKey: "nav.directDrive", descricao: { "pt-BR": "Linha Direct Drive Carrier Transicold", en: "Carrier Transicold Direct Drive line", es: "Línea Direct Drive Carrier Transicold" } },
  "/usuarios": { tituloKey: "nav.users", descricao: { "pt-BR": "Administração de usuários e permissões", en: "User and permission administration", es: "Administración de usuarios y permisos" } },
  "/configuracoes": { tituloKey: "nav.settings", descricao: { "pt-BR": "Configurações administrativas do CTI", en: "CTI administrative settings", es: "Configuración administrativa de CTI" } },
};

const periodos: Record<"pt-BR" | "en" | "es", Array<{ value: PeriodPreset; label: string }>> = {
  "pt-BR": [
    { value: "TODO_HISTORICO", label: "Todo o histórico" }, { value: "ULTIMOS_30_DIAS", label: "Últimos 30 dias" }, { value: "ULTIMOS_90_DIAS", label: "Últimos 90 dias" }, { value: "ANO_ATUAL", label: "Ano atual" }, { value: "PERSONALIZADO", label: "Personalizado" },
  ],
  en: [
    { value: "TODO_HISTORICO", label: "All history" }, { value: "ULTIMOS_30_DIAS", label: "Last 30 days" }, { value: "ULTIMOS_90_DIAS", label: "Last 90 days" }, { value: "ANO_ATUAL", label: "Current year" }, { value: "PERSONALIZADO", label: "Custom" },
  ],
  es: [
    { value: "TODO_HISTORICO", label: "Todo el historial" }, { value: "ULTIMOS_30_DIAS", label: "Últimos 30 días" }, { value: "ULTIMOS_90_DIAS", label: "Últimos 90 días" }, { value: "ANO_ATUAL", label: "Año actual" }, { value: "PERSONALIZADO", label: "Personalizado" },
  ],
};

const ui = {
  "pt-BR": { territory: "Território", period: "Período", start: "Início", end: "Fim", user: "Usuário CTI", authenticated: "Acesso autenticado", pending: "PERFIL PENDENTE", logout: "Sair", fallback: "Centro de Tecnologia e Inteligência Comercial" },
  en: { territory: "Territory", period: "Period", start: "Start", end: "End", user: "CTI User", authenticated: "Authenticated access", pending: "PROFILE PENDING", logout: "Sign out", fallback: "Commercial Technology and Intelligence Center" },
  es: { territory: "Territorio", period: "Período", start: "Inicio", end: "Fin", user: "Usuario CTI", authenticated: "Acceso autenticado", pending: "PERFIL PENDIENTE", logout: "Salir", fallback: "Centro de Tecnología e Inteligencia Comercial" },
};

export default function Topbar() {
  const pathname = usePathname();
  const { usuario, sair } = useAuth();
  const { locale, t } = useI18n();
  const { contexto, setContexto, contextoAtual, periodo, setPeriodo, dataInicio, setDataInicio, dataFim, setDataFim } = useOperationalContext();
  const tx = ui[locale];
  const paginaAtual = paginas[pathname] || { titulo: "CTI", descricao: { "pt-BR": tx.fallback, en: tx.fallback, es: tx.fallback } };
  const titulo = paginaAtual.tituloKey ? t(paginaAtual.tituloKey) : paginaAtual.titulo || "CTI";
  const nome = usuario?.nome || tx.user;
  const cargo = usuario?.cargo || tx.authenticated;
  const perfil = usuario?.tipo_usuario || tx.pending;
  const inicial = nome.trim().charAt(0).toUpperCase() || "U";
  const exibirFiltrosExecutivos = pathname === "/inteligencia";

  return (
    <header className="w-full min-h-[90px] border-b border-[#13203f] bg-[#071028] flex flex-wrap items-center justify-between gap-3 px-8 py-3">
      <div><h2 className="text-2xl font-bold text-white">{titulo}</h2><p className="text-sm text-gray-400 mt-1">{paginaAtual.descricao[locale]}</p></div>
      <div className="flex flex-wrap items-center justify-end gap-3">
        {exibirFiltrosExecutivos && <>
          <label className="flex flex-col gap-1 bg-[#0b1730] border border-[#13203f] rounded-xl px-3 py-2 text-xs text-gray-400">
            {tx.territory}
            <select value={contexto} onChange={(e) => setContexto(e.target.value as OperationalContextValue)} className="bg-transparent text-sm text-white outline-none max-w-[180px]" aria-label={`${tx.territory} — ${titulo}`}>
              {OPERATIONAL_CONTEXTS.map((item) => <option key={item.value} value={item.value} className="bg-[#071028] text-white">{item.label}</option>)}
            </select>
            <span className="sr-only">{contextoAtual.description}</span>
          </label>
          <label className="flex flex-col gap-1 bg-[#0b1730] border border-[#13203f] rounded-xl px-3 py-2 text-xs text-gray-400">
            {tx.period}
            <select value={periodo} onChange={(e) => setPeriodo(e.target.value as PeriodPreset)} className="bg-[#071028] text-sm text-white outline-none" aria-label={`${tx.period} — ${titulo}`}>
              {periodos[locale].map((item) => <option key={item.value} value={item.value} className="bg-[#071028] text-white">{item.label}</option>)}
            </select>
          </label>
          {periodo === "PERSONALIZADO" && <><label className="flex flex-col gap-1 text-xs text-gray-400">{tx.start}<input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} className="rounded-lg border border-[#13203f] bg-[#0b1730] px-2 py-2 text-white" /></label><label className="flex flex-col gap-1 text-xs text-gray-400">{tx.end}<input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} className="rounded-lg border border-[#13203f] bg-[#0b1730] px-2 py-2 text-white" /></label></>}
        </>}
        <div className="flex items-center gap-2 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-3"><div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div><span className="text-sm text-green-400 font-medium">CTI Online</span></div>
        <div className="flex items-center gap-3 bg-[#0b1730] border border-[#13203f] rounded-xl px-4 py-2"><div className="w-11 h-11 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-black">{inicial}</div><div><p className="text-sm font-semibold text-white">{nome}</p><p className="text-xs text-gray-400">{cargo} • {perfil}</p></div><button type="button" onClick={() => void sair()} className="ml-2 rounded-lg border border-[#29456f] px-3 py-2 text-xs font-semibold text-slate-300 hover:border-cyan-400 hover:text-white">{tx.logout}</button></div>
      </div>
    </header>
  );
}
