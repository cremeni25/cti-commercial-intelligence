-- Aparelhos inscritos no resumo diário (Web Push) do Agente de Inteligência.
-- Somente o backend (service role) lê e grava.
create table if not exists public.cti_push_assinaturas (
  id uuid primary key default gen_random_uuid(),
  usuario_id text not null,
  endpoint text not null unique,
  p256dh text not null,
  auth text not null,
  user_agent text,
  ativo boolean not null default true,
  falhas integer not null default 0,
  ultimo_envio_em timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists cti_push_assinaturas_usuario_idx
  on public.cti_push_assinaturas (usuario_id) where ativo;

alter table public.cti_push_assinaturas enable row level security;
revoke all on public.cti_push_assinaturas from anon, authenticated;
