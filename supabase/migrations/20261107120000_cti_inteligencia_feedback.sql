-- Ajustes da equipe sobre os sinais do Agente de Inteligência Comercial.
-- Somente o backend (service role) lê e grava; nenhum dado comercial é alterado.
create table if not exists public.cti_inteligencia_feedback (
  id uuid primary key default gen_random_uuid(),
  usuario_id text not null,
  codigo text not null,
  entidade_tipo text not null,
  entidade_id text not null,
  decisao text not null check (decisao in ('NAO_SE_APLICA', 'ADIAR')),
  motivo text not null,
  observacao text,
  suprimir_ate date not null,
  created_at timestamptz not null default now()
);

create index if not exists cti_inteligencia_feedback_entidade_idx
  on public.cti_inteligencia_feedback (entidade_tipo, entidade_id, codigo);
create index if not exists cti_inteligencia_feedback_vigencia_idx
  on public.cti_inteligencia_feedback (suprimir_ate);

alter table public.cti_inteligencia_feedback enable row level security;
revoke all on public.cti_inteligencia_feedback from anon, authenticated;
