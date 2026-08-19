create table if not exists public.cti_fontes_promocoes (
    id uuid primary key default gen_random_uuid(),
    fonte_id uuid not null references public.cti_fontes_universais(id) on delete cascade,
    reconciliacao_id uuid not null references public.cti_fontes_reconciliacoes(id) on delete cascade,
    dominio_alvo text not null,
    status text not null default 'EM_EXECUCAO' check (status in ('EM_EXECUCAO','CONCLUIDA','ERRO')),
    total_itens integer not null default 0,
    total_promovidos integer not null default 0,
    resultado jsonb not null default '{}'::jsonb,
    executado_por uuid,
    created_at timestamptz not null default now(),
    concluido_em timestamptz
);

create index if not exists idx_cti_fontes_promocoes_rec on public.cti_fontes_promocoes(reconciliacao_id, created_at desc);
create index if not exists idx_cti_fontes_promocoes_status on public.cti_fontes_promocoes(status, created_at desc);

alter table public.cti_fontes_promocoes enable row level security;
revoke all on table public.cti_fontes_promocoes from anon, authenticated;
grant all on table public.cti_fontes_promocoes to service_role;

comment on table public.cti_fontes_promocoes is 'Auditoria de promoções controladas originadas do Back Office. Apenas lotes PRONTO_PROMOCAO e adaptadores canônicos podem escrever no núcleo operacional.';