create table if not exists public.cti_fontes_reconciliacoes (
    id uuid primary key default gen_random_uuid(),
    fonte_id uuid not null unique references public.cti_fontes_universais(id) on delete cascade,
    classificacao text not null,
    dominio_alvo text not null,
    status text not null default 'PREPARADA' check (status in ('PREPARADA','EM_REVISAO','APROVADA','REJEITADA','PRONTO_PROMOCAO','PROMOVIDA','ERRO')),
    total_itens integer not null default 0,
    total_validos integer not null default 0,
    total_conflitos integer not null default 0,
    promocao_operacional_automatica boolean not null default false,
    detalhes jsonb not null default '{}'::jsonb,
    criado_por uuid,
    aprovado_por uuid,
    aprovado_em timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.cti_fontes_reconciliacao_itens (
    id uuid primary key default gen_random_uuid(),
    reconciliacao_id uuid not null references public.cti_fontes_reconciliacoes(id) on delete cascade,
    fonte_id uuid not null references public.cti_fontes_universais(id) on delete cascade,
    indice_semantico integer not null,
    entidade_sugerida text not null,
    acao_sugerida text not null,
    chave_canonica text not null,
    dados_origem jsonb not null default '{}'::jsonb,
    dados_normalizados jsonb not null default '{}'::jsonb,
    conflitos jsonb not null default '[]'::jsonb,
    status_item text not null default 'PENDENTE' check (status_item in ('PENDENTE','VALIDO','CONFLITO','REJEITADO','PRONTO_PROMOCAO','PROMOVIDO')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (reconciliacao_id, indice_semantico)
);

create index if not exists idx_cti_fontes_reconciliacoes_status on public.cti_fontes_reconciliacoes(status, updated_at desc);
create index if not exists idx_cti_fontes_reconciliacao_itens_rec on public.cti_fontes_reconciliacao_itens(reconciliacao_id, indice_semantico);

alter table public.cti_fontes_reconciliacoes enable row level security;
alter table public.cti_fontes_reconciliacao_itens enable row level security;
revoke all on table public.cti_fontes_reconciliacoes from anon, authenticated;
revoke all on table public.cti_fontes_reconciliacao_itens from anon, authenticated;
grant all on table public.cti_fontes_reconciliacoes to service_role;
grant all on table public.cti_fontes_reconciliacao_itens to service_role;

comment on table public.cti_fontes_reconciliacoes is 'Staging governado de reconciliação para fontes candidatas a dados operacionais. Não promove automaticamente registros ao CRM/CTI.';
comment on column public.cti_fontes_reconciliacoes.status is 'PRONTO_PROMOCAO significa aprovado pelo ADMIN_MASTER e sem conflitos; não implica escrita operacional já executada.';