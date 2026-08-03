begin;

create extension if not exists pgcrypto;

create table if not exists public.cti_users (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid,
  email text,
  nome text,
  empresa text,
  cargo text,
  funcao text,
  tipo_usuario text,
  territorio text,
  ddds text[] not null default '{}',
  gestor_responsavel text,
  superior_id uuid,
  ativo boolean not null default true,
  status_acesso text default 'PRIMEIRO_ACESSO_PENDENTE',
  primeiro_acesso_pendente boolean not null default true,
  cadastro_completo boolean not null default false,
  telefone text,
  departamento text,
  senha_temporaria_criada_em timestamptz,
  primeiro_acesso_concluido_em timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.cti_users
  add column if not exists auth_id uuid,
  add column if not exists email text,
  add column if not exists nome text,
  add column if not exists empresa text,
  add column if not exists cargo text,
  add column if not exists funcao text,
  add column if not exists tipo_usuario text,
  add column if not exists territorio text,
  add column if not exists ddds text[] not null default '{}',
  add column if not exists gestor_responsavel text,
  add column if not exists superior_id uuid,
  add column if not exists ativo boolean not null default true,
  add column if not exists status_acesso text default 'PRIMEIRO_ACESSO_PENDENTE',
  add column if not exists primeiro_acesso_pendente boolean not null default true,
  add column if not exists cadastro_completo boolean not null default false,
  add column if not exists telefone text,
  add column if not exists departamento text,
  add column if not exists senha_temporaria_criada_em timestamptz,
  add column if not exists primeiro_acesso_concluido_em timestamptz,
  add column if not exists created_at timestamptz not null default now(),
  add column if not exists updated_at timestamptz not null default now();

alter table public.cti_users
  drop constraint if exists cti_users_tipo_usuario_check;

update public.cti_users
set
  funcao = coalesce(nullif(trim(funcao), ''), nullif(trim(cargo), ''), nullif(trim(tipo_usuario), ''), 'Colaborador'),
  ddds = coalesce(ddds, '{}'),
  ativo = coalesce(ativo, true),
  status_acesso = coalesce(status_acesso, case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then 'ATIVO' else 'PRIMEIRO_ACESSO_PENDENTE' end),
  primeiro_acesso_pendente = case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then false else coalesce(primeiro_acesso_pendente, true) end,
  cadastro_completo = case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then true else coalesce(cadastro_completo, false) end,
  updated_at = coalesce(updated_at, now());

alter table public.cti_users
  alter column ddds set default '{}',
  alter column ativo set default true,
  alter column status_acesso set default 'PRIMEIRO_ACESSO_PENDENTE',
  alter column primeiro_acesso_pendente set default true,
  alter column cadastro_completo set default false,
  alter column created_at set default now(),
  alter column updated_at set default now();

create unique index if not exists ux_cti_users_auth_id
  on public.cti_users(auth_id)
  where auth_id is not null;

create unique index if not exists ux_cti_users_email_normalizado
  on public.cti_users(lower(trim(email)))
  where email is not null and trim(email) <> '';

create index if not exists ix_cti_users_tipo_usuario
  on public.cti_users(tipo_usuario);

create index if not exists ix_cti_users_territorio
  on public.cti_users(territorio);

create table if not exists public.cti_user_permissions (
  user_id uuid primary key references public.cti_users(id) on delete cascade,
  acesso_portal boolean not null default false,
  acesso_crm boolean not null default false,
  dashboard_executivo boolean not null default false,
  clientes_visualizar boolean not null default false,
  clientes_editar boolean not null default false,
  oportunidades_visualizar boolean not null default false,
  oportunidades_editar boolean not null default false,
  propostas_visualizar boolean not null default false,
  propostas_emitir boolean not null default false,
  pedidos_visualizar boolean not null default false,
  pedidos_converter boolean not null default false,
  pedidos_enviar boolean not null default false,
  financeiro_visualizar boolean not null default false,
  usuarios_administrar boolean not null default false,
  configuracoes_administrar boolean not null default false,
  acesso_total boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

do $$
declare
  ausentes text[];
begin
  select array_agg(coluna order by coluna)
  into ausentes
  from (
    select unnest(array[
      'id','auth_id','email','nome','empresa','cargo','funcao','tipo_usuario',
      'territorio','ddds','gestor_responsavel','superior_id','ativo',
      'status_acesso','primeiro_acesso_pendente','cadastro_completo','telefone',
      'departamento','senha_temporaria_criada_em','primeiro_acesso_concluido_em',
      'created_at','updated_at'
    ]) as coluna
  ) esperado
  where not exists (
    select 1
    from information_schema.columns c
    where c.table_schema = 'public'
      and c.table_name = 'cti_users'
      and c.column_name = esperado.coluna
  );

  if ausentes is not null then
    raise exception 'Contrato incompleto de cti_users. Colunas ausentes: %', array_to_string(ausentes, ', ');
  end if;
end $$;

notify pgrst, 'reload schema';

commit;
