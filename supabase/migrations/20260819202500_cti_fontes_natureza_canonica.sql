alter table public.cti_fontes_reconciliacao_itens
    add column if not exists natureza_canonica text,
    add column if not exists camada_dashboard text;

comment on column public.cti_fontes_reconciliacao_itens.natureza_canonica is
    'Natureza de negócio preservada na reconciliação: mercado realizado, cadastro CRM, Funil, execução comercial ou realizado comercial. Não autoriza fusão entre domínios.';

comment on column public.cti_fontes_reconciliacao_itens.camada_dashboard is
    'Camada analítica permitida. Dashboard Executivo pode correlacionar camadas sem fundi-las; Inteligência de Mercado usa fatos realizados de mercado, principalmente ANFIR.';
