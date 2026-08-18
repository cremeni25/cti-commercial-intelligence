-- IA-010 — memória semântica acumulativa de anexos do domínio frigorífico
-- Conhecimento documental rastreável e separado da verdade operacional do CRM.

create extension if not exists pgcrypto;

create table if not exists public.cti_ia_conhecimento_documentos (
    id uuid primary key default gen_random_uuid(),
    sha256 text not null unique,
    nome_arquivo text not null,
    tipo text not null,
    mime_type text not null,
    tamanho_bytes bigint not null default 0 check (tamanho_bytes >= 0),
    estrutura jsonb not null default '{}'::jsonb,
    origem text not null default 'ANEXO_CONVERSACIONAL',
    dominio text not null default 'CADEIA_FRIA',
    status text not null default 'ATIVO_SEMANTICO' check (status in ('ATIVO_SEMANTICO','INATIVO','REJEITADO')),
    escopo text not null default 'USUARIO' check (escopo in ('USUARIO','GLOBAL_CTI')),
    criado_por uuid,
    conversa_origem_id uuid,
    metadados jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_cti_ia_conhecimento_status on public.cti_ia_conhecimento_documentos(status, updated_at desc);
create index if not exists idx_cti_ia_conhecimento_escopo on public.cti_ia_conhecimento_documentos(escopo, criado_por);

create table if not exists public.cti_ia_conhecimento_fragmentos (
    id uuid primary key default gen_random_uuid(),
    documento_id uuid not null references public.cti_ia_conhecimento_documentos(id) on delete cascade,
    indice integer not null check (indice > 0),
    conteudo_texto text not null,
    metadados jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (documento_id, indice)
);

create index if not exists idx_cti_ia_conhecimento_fragmentos_doc on public.cti_ia_conhecimento_fragmentos(documento_id, indice);

alter table public.cti_ia_conhecimento_documentos enable row level security;
alter table public.cti_ia_conhecimento_fragmentos enable row level security;

revoke all on table public.cti_ia_conhecimento_documentos from anon, authenticated;
revoke all on table public.cti_ia_conhecimento_fragmentos from anon, authenticated;
grant all on table public.cti_ia_conhecimento_documentos to service_role;
grant all on table public.cti_ia_conhecimento_fragmentos to service_role;

comment on table public.cti_ia_conhecimento_documentos is
  'Memória semântica documental da IA Comercial CTI. Não representa verdade operacional de CRM nem autoriza escrita comercial.';
comment on column public.cti_ia_conhecimento_documentos.sha256 is
  'Hash da fonte documental que permite rastrear e deduplicar conhecimento acumulado.';
comment on column public.cti_ia_conhecimento_documentos.escopo is
  'GLOBAL_CTI para conhecimento promovido por ADMIN_MASTER; USUARIO para anexos de demais perfis.';
