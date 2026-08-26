create table if not exists public.cti_atividades_auditoria (
  id uuid primary key default gen_random_uuid(),
  atividade_id uuid not null,
  acao text not null,
  usuario_id uuid,
  antes jsonb not null default '{}'::jsonb,
  depois jsonb not null default '{}'::jsonb,
  motivo text,
  created_at timestamptz not null default now()
);

create index if not exists idx_cti_atividades_auditoria_atividade
  on public.cti_atividades_auditoria (atividade_id, created_at desc);

comment on table public.cti_atividades_auditoria is
  'Trilha administrativa imutável para edição e arquivamento de atividades do CRM pelo ADMIN_MASTER.';
