create table if not exists public.cti_anfir_concorrente_classificacao (
  id uuid primary key default gen_random_uuid(),
  anf
ir_id uuid not null unique references public.cti_anfir(id) on delete cascade,
  fabricante_cti text not null,
  observacao text,
  alterado_por text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_cti_anfir_concorrente_classificacao_fabricante
  on public.cti_anfir_concorrente_classificacao (fabricante_cti);

alter table public.cti_anfir_concorrente_classificacao enable row level security;

comment on table public.cti_anfir_concorrente_classificacao is
  'Classificação comercial CTI complementar ao dado bruto Carrier/JOV. Nunca altera cti_anfir.';
comment on column public.cti_anfir_concorrente_classificacao.fabricante_cti is
  'Fabricante concorrente confirmado/classificado no CTI para o registro ANFIR; origem Carrier/JOV permanece imutável.';
