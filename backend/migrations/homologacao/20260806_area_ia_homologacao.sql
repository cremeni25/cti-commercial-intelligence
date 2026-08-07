begin;

create extension if not exists pgcrypto;

create schema if not exists ia_homologacao;
revoke all on schema ia_homologacao from public, anon;
grant usage on schema ia_homologacao to authenticated, service_role;

create or replace function ia_homologacao.eh_admin_master()
returns boolean
language sql
stable
security definer
set search_path = public, auth, pg_temp
as $$
  select exists (
    select 1
    from public.cti_users u
    where u.auth_id = auth.uid()
      and u.ativo is true
      and upper(coalesce(u.tipo_usuario, '')) = 'ADMIN_MASTER'
  );
$$;

revoke all on function ia_homologacao.eh_admin_master() from public, anon;
grant execute on function ia_homologacao.eh_admin_master() to authenticated, service_role;

create table if not exists ia_homologacao.documentos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null,
  nome_arquivo text not null,
  tipo_mime text,
  tamanho_bytes bigint,
  storage_bucket text not null,
  storage_path text not null,
  sha256 text not null,
  status_processamento text not null default 'PENDENTE',
  metadados jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (sha256, storage_path)
);

create table if not exists ia_homologacao.documentos_segmentos (
  id uuid primary key default gen_random_uuid(),
  documento_id uuid not null references ia_homologacao.documentos(id) on delete cascade,
  ordem integer not null,
  pagina_inicial integer,
  pagina_final integer,
  conteudo text not null,
  metadados jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (documento_id, ordem)
);

create table if not exists ia_homologacao.conversas (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null,
  titulo text,
  status text not null default 'ATIVA',
  metadados jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ia_homologacao.mensagens (
  id uuid primary key default gen_random_uuid(),
  conversa_id uuid not null references ia_homologacao.conversas(id) on delete cascade,
  usuario_id uuid not null,
  papel text not null check (papel in ('system','user','assistant','tool')),
  conteudo text not null,
  ferramentas jsonb not null default '[]'::jsonb,
  fontes jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists ia_homologacao.fontes_web (
  id uuid primary key default gen_random_uuid(),
  conversa_id uuid references ia_homologacao.conversas(id) on delete cascade,
  mensagem_id uuid references ia_homologacao.mensagens(id) on delete cascade,
  url text not null,
  titulo text,
  dominio text,
  trecho text,
  consultado_em timestamptz not null default now(),
  metadados jsonb not null default '{}'::jsonb
);

create table if not exists ia_homologacao.execucoes (
  id uuid primary key default gen_random_uuid(),
  conversa_id uuid references ia_homologacao.conversas(id) on delete set null,
  usuario_id uuid not null,
  pergunta text not null,
  ferramentas_solicitadas jsonb not null default '[]'::jsonb,
  ferramentas_executadas jsonb not null default '[]'::jsonb,
  status text not null default 'INICIADA',
  erro text,
  iniciada_em timestamptz not null default now(),
  finalizada_em timestamptz,
  duracao_ms bigint,
  metadados jsonb not null default '{}'::jsonb
);

create table if not exists ia_homologacao.auditoria (
  id bigint generated always as identity primary key,
  usuario_id uuid,
  evento text not null,
  entidade text,
  entidade_id text,
  origem text not null default 'IA_HOMOLOGACAO',
  antes jsonb,
  depois jsonb,
  contexto jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ix_ia_documentos_usuario on ia_homologacao.documentos(usuario_id, created_at desc);
create index if not exists ix_ia_segmentos_documento on ia_homologacao.documentos_segmentos(documento_id, ordem);
create index if not exists ix_ia_conversas_usuario on ia_homologacao.conversas(usuario_id, updated_at desc);
create index if not exists ix_ia_mensagens_conversa on ia_homologacao.mensagens(conversa_id, created_at);
create index if not exists ix_ia_fontes_conversa on ia_homologacao.fontes_web(conversa_id, consultado_em desc);
create index if not exists ix_ia_execucoes_usuario on ia_homologacao.execucoes(usuario_id, iniciada_em desc);
create index if not exists ix_ia_auditoria_evento on ia_homologacao.auditoria(evento, created_at desc);

alter table ia_homologacao.documentos enable row level security;
alter table ia_homologacao.documentos_segmentos enable row level security;
alter table ia_homologacao.conversas enable row level security;
alter table ia_homologacao.mensagens enable row level security;
alter table ia_homologacao.fontes_web enable row level security;
alter table ia_homologacao.execucoes enable row level security;
alter table ia_homologacao.auditoria enable row level security;

do $$
declare
  t text;
begin
  foreach t in array array[
    'documentos','documentos_segmentos','conversas','mensagens',
    'fontes_web','execucoes','auditoria'
  ] loop
    execute format('drop policy if exists admin_master_total on ia_homologacao.%I', t);
    execute format(
      'create policy admin_master_total on ia_homologacao.%I for all to authenticated using (ia_homologacao.eh_admin_master()) with check (ia_homologacao.eh_admin_master())',
      t
    );
  end loop;
end $$;

grant select, insert, update, delete on all tables in schema ia_homologacao to authenticated, service_role;
grant usage, select on all sequences in schema ia_homologacao to authenticated, service_role;
alter default privileges in schema ia_homologacao grant select, insert, update, delete on tables to authenticated, service_role;
alter default privileges in schema ia_homologacao grant usage, select on sequences to authenticated, service_role;

commit;
