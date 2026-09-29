create table if not exists public.cti_grupo_estabelecimentos (
  id uuid primary key default gen_random_uuid(),
  grupo_cliente_id uuid not null references public.clientes(id) on delete cascade,
  estabelecimento_cliente_id uuid not null references public.clientes(id) on delete cascade,
  criado_em timestamptz not null default now(),
  criado_por uuid null,
  unique (grupo_cliente_id, estabelecimento_cliente_id)
);

create index if not exists idx_cti_grupo_estabelecimentos_grupo
  on public.cti_grupo_estabelecimentos(grupo_cliente_id);
create index if not exists idx_cti_grupo_estabelecimentos_estabelecimento
  on public.cti_grupo_estabelecimentos(estabelecimento_cliente_id);

alter table public.cti_grupo_estabelecimentos enable row level security;
