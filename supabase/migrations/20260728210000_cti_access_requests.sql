create extension if not exists pgcrypto;

create table if not exists public.cti_access_requests (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  email text not null,
  telefone text,
  empresa text not null,
  cargo text not null,
  canal_solicitado text not null default 'AMBOS',
  observacoes text,
  status text not null default 'PENDENTE',
  tipo_usuario text,
  territorio text,
  ddds text[] not null default '{}',
  superior_id uuid references public.cti_users(id) on delete set null,
  aprovado_por uuid references public.cti_users(id) on delete set null,
  decidido_em timestamptz,
  motivo_decisao text,
  auth_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.cti_users add column if not exists acesso_portal boolean not null default true;
alter table public.cti_users add column if not exists acesso_crm boolean not null default true;
alter table public.cti_users add column if not exists status_acesso text not null default 'ATIVO';

alter table public.cti_access_requests drop constraint if exists cti_access_requests_status_check;
alter table public.cti_access_requests add constraint cti_access_requests_status_check check (
  status in ('PENDENTE','APROVADO','REJEITADO','CONVITE_ENVIADO','ATIVO','INATIVO')
);

alter table public.cti_access_requests drop constraint if exists cti_access_requests_canal_check;
alter table public.cti_access_requests add constraint cti_access_requests_canal_check check (
  canal_solicitado in ('PORTAL','CRM','AMBOS')
);

alter table public.cti_users drop constraint if exists cti_users_status_acesso_check;
alter table public.cti_users add constraint cti_users_status_acesso_check check (
  status_acesso in ('CONVITE_ENVIADO','ATIVO','INATIVO','BLOQUEADO')
);

create unique index if not exists cti_access_requests_email_pending_uidx
  on public.cti_access_requests(lower(email))
  where status in ('PENDENTE','APROVADO','CONVITE_ENVIADO');
create index if not exists cti_access_requests_status_idx on public.cti_access_requests(status, created_at desc);

alter table public.cti_access_requests enable row level security;
revoke all on table public.cti_access_requests from anon, authenticated;

grant select on table public.cti_users to authenticated;
