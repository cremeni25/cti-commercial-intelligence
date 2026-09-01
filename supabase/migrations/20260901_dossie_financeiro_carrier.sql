create table if not exists public.cti_cliente_documentos_financeiros (
  id uuid primary key default gen_random_uuid(),
  cliente_id uuid not null,
  categoria text not null,
  nome_arquivo text not null,
  storage_bucket text not null default 'documentos-financeiros-clientes',
  storage_path text not null,
  mime_type text,
  tamanho_bytes bigint,
  sha256 text,
  observacao text,
  criado_por uuid,
  created_at timestamptz not null default now(),
  arquivado_em timestamptz,
  arquivado_por uuid
);

create index if not exists idx_cti_cliente_doc_fin_cliente on public.cti_cliente_documentos_financeiros(cliente_id, created_at desc);

create table if not exists public.cti_cliente_cadastro_financeiro_carrier (
  id uuid primary key default gen_random_uuid(),
  cliente_id uuid not null,
  status text not null default 'EM_PREPARACAO',
  validado_carrier_em date,
  valido_ate date,
  observacao text,
  criado_por uuid,
  atualizado_por uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint cti_cliente_cadastro_fin_status_chk check (status in ('EM_PREPARACAO','EM_ANALISE','VALIDADO_CARRIER','PROXIMO_VENCIMENTO','VENCIDO','RENOVACAO_EM_ANALISE'))
);

create unique index if not exists uq_cti_cliente_cadastro_fin_ativo
  on public.cti_cliente_cadastro_financeiro_carrier(cliente_id)
  where status in ('EM_PREPARACAO','EM_ANALISE','VALIDADO_CARRIER','PROXIMO_VENCIMENTO','VENCIDO','RENOVACAO_EM_ANALISE');

create table if not exists public.cti_proposta_documentos_financeiros (
  id uuid primary key default gen_random_uuid(),
  proposta_id uuid not null,
  documento_id uuid not null,
  vinculado_por uuid,
  vinculado_em timestamptz not null default now(),
  unique(proposta_id, documento_id)
);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documentos-financeiros-clientes',
  'documentos-financeiros-clientes',
  false,
  20971520,
  array[
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png'
  ]::text[]
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
