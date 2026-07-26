begin;

create extension if not exists pgcrypto;

create table if not exists public.cti_product_lines (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code in ('TR','DT','DD')),
  name text not null,
  description text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.cti_product_models (
  id uuid primary key default gen_random_uuid(),
  line_id uuid not null references public.cti_product_lines(id) on delete restrict,
  canonical_name text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (line_id, canonical_name)
);

create table if not exists public.cti_product_aliases (
  id uuid primary key default gen_random_uuid(),
  model_id uuid references public.cti_product_models(id) on delete cascade,
  line_id uuid references public.cti_product_lines(id) on delete cascade,
  alias text not null,
  alias_normalized text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  check ((model_id is not null) <> (line_id is not null)),
  unique (alias_normalized)
);

create table if not exists public.cti_product_taxonomy_audit (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null check (entity_type in ('LINE','MODEL','ALIAS')),
  entity_id uuid,
  action text not null check (action in ('CREATE','UPDATE','ACTIVATE','DEACTIVATE')),
  before_data jsonb,
  after_data jsonb,
  actor text,
  created_at timestamptz not null default now()
);

create index if not exists idx_cti_product_models_line on public.cti_product_models(line_id);
create index if not exists idx_cti_product_aliases_model on public.cti_product_aliases(model_id);
create index if not exists idx_cti_product_aliases_line on public.cti_product_aliases(line_id);
create index if not exists idx_cti_product_aliases_normalized on public.cti_product_aliases(alias_normalized);

insert into public.cti_product_lines (code, name, description)
values
  ('TR', 'Trailer', 'Equipamentos para semirreboques refrigerados.'),
  ('DT', 'Diesel Truck', 'Unidades autônomas diesel para caminhões.'),
  ('DD', 'Direct Drive', 'Equipamentos acionados diretamente pelo motor do veículo.')
on conflict (code) do update set name = excluded.name, description = excluded.description, updated_at = now();

with linhas as (select id, code from public.cti_product_lines)
insert into public.cti_product_models (line_id, canonical_name)
select linhas.id, modelo from linhas join (values
  ('TR','X4-7500'),('TR','X4-7700'),('TR','VECTOR HE19'),
  ('DT','SUPRA 750'),('DT','SUPRA 850'),('DT','SUPRA 1150'),
  ('DD','CM280'),('DD','CM400'),('DD','CM500'),('DD','CM500AE'),
  ('DD','D6'),('DD','D6AE'),('DD','D7'),('DD','D7AE'),
  ('DD','XARIOS 350'),('DD','XARIOS 600')
) as dados(codigo, modelo) on dados.codigo = linhas.code
on conflict (line_id, canonical_name) do nothing;

with modelos as (
  select m.id, m.canonical_name from public.cti_product_models m
)
insert into public.cti_product_aliases (model_id, alias, alias_normalized)
select modelos.id, dados.alias, upper(regexp_replace(trim(dados.alias), '[^A-Za-z0-9]+', ' ', 'g'))
from modelos join (values
  ('X4-7500','X4 7500'),('X4-7500','X4-7500'),('X4-7500','X47500'),
  ('X4-7700','X4 7700'),('X4-7700','X4-7700'),('X4-7700','X47700'),
  ('VECTOR HE19','VECTOR HE19'),('VECTOR HE19','HE19'),('VECTOR HE19','HE 19'),
  ('SUPRA 750','SUPRA 750'),('SUPRA 750','SUPRA750'),
  ('SUPRA 850','SUPRA 850'),('SUPRA 850','SUPRA850'),
  ('SUPRA 1150','SUPRA 1150'),('SUPRA 1150','SUPRA1150'),
  ('CM280','CM280'),('CM280','CM 280'),('CM280','CM-280'),
  ('CM400','CM400'),('CM400','CM 400'),('CM400','CM-400'),
  ('CM500','CM500'),('CM500','CM 500'),('CM500','CM-500'),
  ('CM500AE','CM500AE'),('CM500AE','CM 500 AE'),('CM500AE','CM-500-AE'),('CM500AE','CM500 AE'),
  ('D6','D6'),('D6','D 6'),('D6AE','D6AE'),('D6AE','D6 AE'),('D6AE','D 6 AE'),
  ('D7','D7'),('D7','D 7'),('D7AE','D7AE'),('D7AE','D7 AE'),('D7AE','D 7 AE'),
  ('XARIOS 350','XARIOS 350'),('XARIOS 350','XARIOS350'),
  ('XARIOS 600','XARIOS 600'),('XARIOS 600','XARIOS600')
) as dados(modelo, alias) on dados.modelo = modelos.canonical_name
on conflict (alias_normalized) do nothing;

with linhas as (select id, code from public.cti_product_lines)
insert into public.cti_product_aliases (line_id, alias, alias_normalized)
select linhas.id, dados.alias, upper(regexp_replace(trim(dados.alias), '[^A-Za-z0-9]+', ' ', 'g'))
from linhas join (values
  ('TR','TR'),('TR','TRAILER'),('TR','LINHA TRAILER'),
  ('DT','DT'),('DT','DIESEL TRUCK'),('DT','DIESEL-TRUCK'),('DT','LINHA DIESEL TRUCK'),('DT','UNIDADE DIESEL'),
  ('DD','DD'),('DD','DIRECT DRIVE'),('DD','DIRECT-DRIVE'),('DD','ACIONAMENTO DIRETO'),('DD','ACOPLADO AO MOTOR')
) as dados(codigo, alias) on dados.codigo = linhas.code
on conflict (alias_normalized) do nothing;

alter table public.cti_product_lines enable row level security;
alter table public.cti_product_models enable row level security;
alter table public.cti_product_aliases enable row level security;
alter table public.cti_product_taxonomy_audit enable row level security;

commit;
