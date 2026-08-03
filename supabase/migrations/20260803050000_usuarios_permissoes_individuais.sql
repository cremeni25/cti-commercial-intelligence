begin;

alter table public.cti_users drop constraint if exists cti_users_tipo_usuario_check;

alter table public.cti_users
  add column if not exists funcao text,
  add column if not exists superior_id uuid references public.cti_users(id) on delete set null,
  add column if not exists senha_temporaria_criada_em timestamptz,
  add column if not exists primeiro_acesso_concluido_em timestamptz;

update public.cti_users
set funcao = coalesce(nullif(trim(cargo), ''), nullif(trim(tipo_usuario), ''), 'Colaborador')
where funcao is null or trim(funcao) = '';

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

insert into public.cti_user_permissions (
  user_id, acesso_portal, acesso_crm, dashboard_executivo,
  clientes_visualizar, clientes_editar,
  oportunidades_visualizar, oportunidades_editar,
  propostas_visualizar, propostas_emitir,
  pedidos_visualizar, pedidos_converter, pedidos_enviar,
  financeiro_visualizar, usuarios_administrar,
  configuracoes_administrar, acesso_total
)
select
  id, true, true, true,
  true, true,
  true, true,
  true, true,
  true, true, true,
  true, true,
  true, true
from public.cti_users
where upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER'
on conflict (user_id) do update set
  acesso_portal = true,
  acesso_crm = true,
  dashboard_executivo = true,
  clientes_visualizar = true,
  clientes_editar = true,
  oportunidades_visualizar = true,
  oportunidades_editar = true,
  propostas_visualizar = true,
  propostas_emitir = true,
  pedidos_visualizar = true,
  pedidos_converter = true,
  pedidos_enviar = true,
  financeiro_visualizar = true,
  usuarios_administrar = true,
  configuracoes_administrar = true,
  acesso_total = true,
  updated_at = now();

create index if not exists cti_users_superior_id_idx on public.cti_users(superior_id);

alter table public.cti_user_permissions enable row level security;
revoke all on table public.cti_user_permissions from anon;
revoke insert, update, delete on table public.cti_user_permissions from authenticated;
grant select on table public.cti_user_permissions to authenticated;

commit;
