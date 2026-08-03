begin;

alter table public.cti_users
  add column if not exists senha_temporaria_criada_em timestamptz,
  add column if not exists primeiro_acesso_concluido_em timestamptz;

alter table public.cti_users
  drop constraint if exists cti_users_tipo_usuario_check;

alter table public.cti_users
  add constraint cti_users_tipo_usuario_check check (
    tipo_usuario in (
      'ADMIN_MASTER',
      'DIRETOR_VIENA_SP',
      'ADMIN_COMERCIAL_VIENA_SP',
      'ADMIN_FINANCEIRO_VIENA_SP',
      'INDICADOR_VIENA_SP',
      'REPRES_REGIAO_01',
      'REPRES_REGIAO_02'
    )
  );

alter table public.cti_users
  alter column status_acesso set default 'PRIMEIRO_ACESSO_PENDENTE',
  alter column acesso_portal set default true,
  alter column acesso_crm set default true,
  alter column primeiro_acesso_pendente set default true,
  alter column cadastro_completo set default false;

commit;
