-- BACKOFFICE UNIVERSAL DE FONTES — BOF-001
-- Núcleo de governança para qualquer fonte documental recebida pelo CTI.

create extension if not exists pgcrypto;

create table if not exists public.cti_fontes_universais (
    id uuid primary key default gen_random_uuid(),
    nome_arquivo text not null,
    nome_exibicao text,
    mime_type text,
    extensao text,
    tamanho_bytes bigint not null default 0 check (tamanho_bytes >= 0),
    sha256 text not null,
    storage_bucket text not null default 'cti-fontes-universais',
    storage_path text not null,
    tipo_detectado text not null default 'DESCONHECIDO',
    classificacao_negocio text not null default 'NAO_CLASSIFICADA',
    status_governanca text not null default 'RECEBIDO' check (
        status_governanca in ('RECEBIDO','INTERPRETADO','VALIDADO','HOMOLOGADO','PUBLICADO_IA','REJEITADO','ERRO')
    ),
    interpretacao_resumo jsonb not null default '{}'::jsonb,
    entidades_detectadas jsonb not null default '[]'::jsonb,
    alertas jsonb not null default '[]'::jsonb,
    metadados jsonb not null default '{}'::jsonb,
    publicado_ia boolean not null default false,
    homologado_por uuid,
    homologado_em timestamptz,
    publicado_ia_em timestamptz,
    criado_por uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (sha256)
);

create index if not exists idx_cti_fontes_status on public.cti_fontes_universais(status_governanca);
create index if not exists idx_cti_fontes_tipo on public.cti_fontes_universais(tipo_detectado);
create index if not exists idx_cti_fontes_classificacao on public.cti_fontes_universais(classificacao_negocio);
create index if not exists idx_cti_fontes_created_at on public.cti_fontes_universais(created_at desc);

create table if not exists public.cti_fontes_eventos (
    id uuid primary key default gen_random_uuid(),
    fonte_id uuid not null references public.cti_fontes_universais(id) on delete cascade,
    evento text not null,
    status_anterior text,
    status_novo text,
    detalhes jsonb not null default '{}'::jsonb,
    usuario_id uuid,
    created_at timestamptz not null default now()
);

create index if not exists idx_cti_fontes_eventos_fonte on public.cti_fontes_eventos(fonte_id, created_at desc);

alter table public.cti_fontes_universais enable row level security;
alter table public.cti_fontes_eventos enable row level security;

revoke all on table public.cti_fontes_universais from anon, authenticated;
revoke all on table public.cti_fontes_eventos from anon, authenticated;
grant all on table public.cti_fontes_universais to service_role;
grant all on table public.cti_fontes_eventos to service_role;

insert into storage.buckets (id, name, public, file_size_limit)
values ('cti-fontes-universais', 'cti-fontes-universais', false, 52428800)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit;

comment on table public.cti_fontes_universais is 'Back Office Universal de Fontes: registro, governança e publicação controlada de documentos para a camada semântica CTI.';
comment on column public.cti_fontes_universais.publicado_ia is 'Somente true após homologação explícita e publicação controlada; upload por si só nunca publica para IA.';
