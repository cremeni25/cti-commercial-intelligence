begin;

alter table public.cti_users add column if not exists status_acesso text;
alter table public.cti_users add column if not exists acesso_portal boolean;
alter table public.cti_users add column if not exists acesso_crm boolean;
alter table public.cti_users add column if not exists primeiro_acesso_pendente boolean;
alter table public.cti_users add column if not exists cadastro_completo boolean;
alter table public.cti_users add column if not exists telefone text;
alter table public.cti_users add column if not exists departamento text;
alter table public.cti_users add column if not exists updated_at timestamptz default now();

-- Remove exclusivamente registros históricos sem autenticação real.
delete from public.cti_users where auth_id is null;

update public.cti_users
set
  ativo = true,
  status_acesso = 'ATIVO',
  acesso_portal = true,
  acesso_crm = true,
  primeiro_acesso_pendente = false,
  cadastro_completo = true,
  updated_at = now()
where tipo_usuario = 'ADMIN_MASTER' and auth_id is not null;

alter table public.cti_users alter column status_acesso set default 'PRIMEIRO_ACESSO';
alter table public.cti_users alter column acesso_portal set default true;
alter table public.cti_users alter column acesso_crm set default true;
alter table public.cti_users alter column primeiro_acesso_pendente set default true;
alter table public.cti_users alter column cadastro_completo set default false;

create unique index if not exists ux_cti_users_auth_id
  on public.cti_users(auth_id)
  where auth_id is not null;

create unique index if not exists ux_cti_users_email_normalizado
  on public.cti_users(lower(trim(email)))
  where email is not null and trim(email) <> '';

create table if not exists public.cti_funcoes (
  codigo text primary key,
  nome_exibicao text not null,
  descricao text not null,
  acesso_portal boolean not null default true,
  acesso_crm boolean not null default true,
  administra_sistema boolean not null default false,
  escopo text not null,
  ativo boolean not null default true,
  ordem integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.cti_funcoes
  (codigo, nome_exibicao, descricao, acesso_portal, acesso_crm, administra_sistema, escopo, ativo, ordem)
values
  ('ADMIN_MASTER', 'Admin Master', 'Administração técnica e operacional integral do CTI.', true, true, true, 'GLOBAL', true, 1),
  ('DIRETOR_VIENA_SP', 'Diretor VIENA SP', 'Acesso integral à operação, sem administração do sistema.', true, true, false, 'VIENA_SP_TOTAL', true, 2),
  ('ADMIN_COMERCIAL_VIENA_SP', 'Admin Comercial VIENA SP', 'Administração integral da operação comercial da VIENA SP.', true, true, false, 'VIENA_SP_COMERCIAL', true, 3),
  ('ADMIN_FINANCEIRO_VIENA_SP', 'Admin Financeiro VIENA SP', 'Acesso financeiro e documental da operação VIENA SP.', true, true, false, 'VIENA_SP_FINANCEIRO', true, 4),
  ('INDICADOR_VIENA_SP', 'Indicador VIENA SP', 'Acesso às indicações e aos registros vinculados.', true, true, false, 'VIENA_SP_INDICACOES', true, 5),
  ('REPRES_REGIAO_01', 'Representante Região 01', 'Operação comercial da Região 01 e carteira atribuída.', true, true, false, 'REGIAO_01', true, 6),
  ('REPRES_REGIAO_02', 'Representante Região 02', 'Operação comercial da Região 02 e carteira atribuída.', true, true, false, 'REGIAO_02', true, 7)
on conflict (codigo) do update set
  nome_exibicao = excluded.nome_exibicao,
  descricao = excluded.descricao,
  acesso_portal = excluded.acesso_portal,
  acesso_crm = excluded.acesso_crm,
  administra_sistema = excluded.administra_sistema,
  escopo = excluded.escopo,
  ativo = excluded.ativo,
  ordem = excluded.ordem,
  updated_at = now();

commit;
