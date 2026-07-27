create extension if not exists pgcrypto;

create table if not exists public.cti_users (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid unique,
  email text not null unique,
  nome text not null,
  empresa text,
  cargo text,
  tipo_usuario text not null,
  territorio text,
  ddds text[] not null default '{}',
  superior_id uuid references public.cti_users(id) on delete set null,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.cti_users add column if not exists auth_id uuid;
alter table public.cti_users add column if not exists email text;
alter table public.cti_users add column if not exists nome text;
alter table public.cti_users add column if not exists empresa text;
alter table public.cti_users add column if not exists cargo text;
alter table public.cti_users add column if not exists tipo_usuario text;
alter table public.cti_users add column if not exists territorio text;
alter table public.cti_users add column if not exists ddds text[] not null default '{}';
alter table public.cti_users add column if not exists superior_id uuid references public.cti_users(id) on delete set null;
alter table public.cti_users add column if not exists ativo boolean not null default true;
alter table public.cti_users add column if not exists created_at timestamptz not null default now();
alter table public.cti_users add column if not exists updated_at timestamptz not null default now();

create unique index if not exists cti_users_auth_id_uidx on public.cti_users(auth_id) where auth_id is not null;
create unique index if not exists cti_users_email_lower_uidx on public.cti_users(lower(email));
create index if not exists cti_users_tipo_idx on public.cti_users(tipo_usuario);
create index if not exists cti_users_superior_idx on public.cti_users(superior_id);

alter table public.cti_users drop constraint if exists cti_users_tipo_usuario_check;
alter table public.cti_users add constraint cti_users_tipo_usuario_check check (
  tipo_usuario in ('ADMIN_MASTER','DIRETOR','GESTOR_REGIONAL','VENDEDOR_REGIONAL','GERENTE','VENDEDOR')
);

alter table public.cti_users enable row level security;

revoke all on table public.cti_users from anon;
revoke insert, update, delete on table public.cti_users from authenticated;
grant select on table public.cti_users to authenticated;
