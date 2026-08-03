begin;

alter table public.cti_users
  add column if not exists status_acesso text,
  add column if not exists primeiro_acesso_pendente boolean not null default true,
  add column if not exists cadastro_completo boolean not null default false,
  add column if not exists telefone text,
  add column if not exists departamento text,
  add column if not exists senha_temporaria_criada_em timestamptz,
  add column if not exists primeiro_acesso_concluido_em timestamptz;

update public.cti_users
set
  status_acesso = coalesce(status_acesso, case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then 'ATIVO' else 'PRIMEIRO_ACESSO_PENDENTE' end),
  primeiro_acesso_pendente = case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then false else coalesce(primeiro_acesso_pendente, true) end,
  cadastro_completo = case when upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER' then true else coalesce(cadastro_completo, false) end;

alter table public.cti_users
  alter column status_acesso set default 'PRIMEIRO_ACESSO_PENDENTE',
  alter column primeiro_acesso_pendente set default true,
  alter column cadastro_completo set default false;

commit;
