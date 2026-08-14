alter table public.cti_fontes_universais
    add column if not exists classificacao_sugerida text,
    add column if not exists confianca_classificacao numeric(5,4),
    add column if not exists descricao_semantica text,
    add column if not exists campos_semanticos jsonb not null default '[]'::jsonb,
    add column if not exists escopo_ia text not null default 'ADMIN_MASTER',
    add column if not exists versao_semantica integer not null default 1,
    add column if not exists interpretado_semanticamente_em timestamptz;

create table if not exists public.cti_fontes_semanticas (
    id uuid primary key default gen_random_uuid(),
    fonte_id uuid not null references public.cti_fontes_universais(id) on delete cascade,
    indice integer not null,
    tipo_registro text not null,
    conteudo_texto text,
    dados jsonb not null default '{}'::jsonb,
    metadados jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (fonte_id, indice)
);

create index if not exists idx_cti_fontes_semanticas_fonte on public.cti_fontes_semanticas(fonte_id, indice);
create index if not exists idx_cti_fontes_semanticas_tipo on public.cti_fontes_semanticas(tipo_registro);

alter table public.cti_fontes_semanticas enable row level security;
revoke all on table public.cti_fontes_semanticas from anon, authenticated;
grant all on table public.cti_fontes_semanticas to service_role;

comment on table public.cti_fontes_semanticas is 'Registros semanticos homologaveis derivados de fontes universais; somente fontes PUBLICADO_IA entram no catalogo dinamico da IA.';
comment on column public.cti_fontes_universais.escopo_ia is 'Escopo inicial de consumo da fonte pela IA; BOF-002 publica por padrao apenas para ADMIN_MASTER.';
