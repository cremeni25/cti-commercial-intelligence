begin;

create table if not exists public.cti_ia_conversas (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null,
  titulo text not null default 'Nova conversa',
  status text not null default 'ATIVA',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists cti_ia_conversas_usuario_idx
  on public.cti_ia_conversas (usuario_id, updated_at desc);

create table if not exists public.cti_ia_mensagens (
  id uuid primary key default gen_random_uuid(),
  conversa_id uuid not null references public.cti_ia_conversas(id) on delete cascade,
  usuario_id uuid not null,
  papel text not null check (papel in ('user', 'assistant', 'system')),
  conteudo text not null,
  fontes jsonb not null default '[]'::jsonb,
  metadados jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists cti_ia_mensagens_conversa_idx
  on public.cti_ia_mensagens (conversa_id, created_at);

create table if not exists public.cti_ia_auditoria (
  id uuid primary key default gen_random_uuid(),
  conversa_id uuid,
  usuario_id uuid not null,
  acao text not null,
  detalhes jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists cti_ia_auditoria_usuario_idx
  on public.cti_ia_auditoria (usuario_id, created_at desc);

commit;
