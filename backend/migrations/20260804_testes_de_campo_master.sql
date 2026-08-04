begin;

create table if not exists public.cti_testes_campo (
  id uuid primary key default gen_random_uuid(),
  campanha text not null,
  oportunidade_id uuid not null,
  cliente_id uuid,
  criado_por uuid,
  observacao text not null default 'TESTE DE CAMPO',
  status text not null default 'ATIVO',
  created_at timestamptz not null default now(),
  encerrado_em timestamptz,
  encerrado_por uuid,
  unique (campanha, oportunidade_id)
);

create index if not exists cti_testes_campo_campanha_idx
  on public.cti_testes_campo (campanha, status);

create table if not exists public.cti_testes_campo_auditoria (
  id uuid primary key default gen_random_uuid(),
  campanha text not null,
  executado_por uuid not null,
  executado_em timestamptz not null default now(),
  contagens jsonb not null default '{}'::jsonb,
  ids_processados jsonb not null default '{}'::jsonb,
  hash_relatorio text not null,
  observacao text not null default 'Encerramento controlado de TESTE DE CAMPO'
);

commit;
