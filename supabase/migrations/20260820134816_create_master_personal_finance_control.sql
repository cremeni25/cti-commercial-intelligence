create schema if not exists private;
revoke all on schema private from public;
grant usage on schema private to authenticated;

create or replace function private.is_cti_admin_master()
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public
as $$
  select (select auth.uid()) is not null
    and exists (
      select 1
      from public.cti_users u
      where u.auth_id = (select auth.uid())
        and upper(coalesce(u.tipo_usuario, '')) = 'ADMIN_MASTER'
        and coalesce(u.ativo, true) = true
    );
$$;

revoke all on function private.is_cti_admin_master() from public;
grant execute on function private.is_cti_admin_master() to authenticated;

create table if not exists public.cti_financeiro_pessoal_config (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid not null references auth.users(id) on delete cascade,
  competencia date not null,
  receita_mensal numeric(14,2) not null default 0 check (receita_mensal >= 0),
  limite_gastos numeric(14,2) not null default 0 check (limite_gastos >= 0),
  alerta_percentual numeric(5,2) not null default 80 check (alerta_percentual > 0 and alerta_percentual <= 100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint cti_financeiro_pessoal_config_competencia_mes
    check (competencia = date_trunc('month', competencia)::date),
  constraint cti_financeiro_pessoal_config_auth_competencia_key
    unique (auth_id, competencia)
);

create table if not exists public.cti_financeiro_pessoal_lancamentos (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid not null references auth.users(id) on delete cascade,
  data date not null default current_date,
  categoria text not null check (length(trim(categoria)) > 0),
  descricao text,
  valor numeric(14,2) not null check (valor > 0),
  forma_pagamento text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists cti_financeiro_pessoal_config_auth_competencia_idx
  on public.cti_financeiro_pessoal_config (auth_id, competencia desc);
create index if not exists cti_financeiro_pessoal_lancamentos_auth_data_idx
  on public.cti_financeiro_pessoal_lancamentos (auth_id, data desc);

revoke all on table public.cti_financeiro_pessoal_config from anon;
revoke all on table public.cti_financeiro_pessoal_lancamentos from anon;
grant select, insert, update, delete on table public.cti_financeiro_pessoal_config to authenticated;
grant select, insert, update, delete on table public.cti_financeiro_pessoal_lancamentos to authenticated;

alter table public.cti_financeiro_pessoal_config enable row level security;
alter table public.cti_financeiro_pessoal_lancamentos enable row level security;

create policy "admin_master_select_finance_config"
on public.cti_financeiro_pessoal_config
for select
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_insert_finance_config"
on public.cti_financeiro_pessoal_config
for insert
to authenticated
with check ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_update_finance_config"
on public.cti_financeiro_pessoal_config
for update
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()))
with check ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_delete_finance_config"
on public.cti_financeiro_pessoal_config
for delete
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_select_finance_entries"
on public.cti_financeiro_pessoal_lancamentos
for select
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_insert_finance_entries"
on public.cti_financeiro_pessoal_lancamentos
for insert
to authenticated
with check ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_update_finance_entries"
on public.cti_financeiro_pessoal_lancamentos
for update
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()))
with check ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));

create policy "admin_master_delete_finance_entries"
on public.cti_financeiro_pessoal_lancamentos
for delete
to authenticated
using ((select auth.uid()) = auth_id and (select private.is_cti_admin_master()));
