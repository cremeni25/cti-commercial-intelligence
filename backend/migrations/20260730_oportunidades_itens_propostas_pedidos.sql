begin;

create extension if not exists pgcrypto;

create table if not exists public.cti_oportunidade_itens (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid not null references public.cti_oportunidades(id) on delete cascade,
  linha_produto text not null,
  equipamento text not null,
  configuracao text,
  quantidade integer not null default 1 check (quantidade > 0),
  preco_unitario numeric(14,2) not null default 0 check (preco_unitario >= 0),
  desconto_percentual numeric(7,4) not null default 0 check (desconto_percentual between 0 and 100),
  valor_total numeric(14,2) generated always as (
    round((quantidade::numeric * preco_unitario) * (1 - desconto_percentual / 100), 2)
  ) stored,
  condicao_pagamento text,
  prazo_entrega text,
  validade_condicao date,
  frete text,
  local_entrega text,
  garantia text,
  opcionais jsonb not null default '[]'::jsonb,
  observacoes_comerciais text,
  observacoes_tecnicas text,
  status text not null default 'EM_NEGOCIACAO',
  ordem integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint cti_oportunidade_itens_status_check check (
    status in ('EM_NEGOCIACAO','PROPOSTA_EMITIDA','ACEITO','RECUSADO','CONVERTIDO_PEDIDO','CANCELADO')
  )
);

create index if not exists cti_oportunidade_itens_oportunidade_idx
  on public.cti_oportunidade_itens(oportunidade_id, ordem, created_at);

create table if not exists public.cti_modelos_proposta (
  id uuid primary key default gen_random_uuid(),
  linha_produto text not null,
  equipamento text not null,
  nome text not null,
  versao integer not null default 1,
  conteudo_template jsonb not null default '{}'::jsonb,
  arquivo_origem text,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (linha_produto, equipamento, versao)
);

alter table public.cti_propostas
  add column if not exists item_oportunidade_id uuid references public.cti_oportunidade_itens(id) on delete restrict,
  add column if not exists modelo_proposta_id uuid references public.cti_modelos_proposta(id) on delete restrict,
  add column if not exists versao integer not null default 1,
  add column if not exists status_documento text not null default 'RASCUNHO',
  add column if not exists snapshot_dados jsonb not null default '{}'::jsonb,
  add column if not exists arquivo_pdf text,
  add column if not exists hash_documento text,
  add column if not exists emitida_em timestamptz,
  add column if not exists enviada_em timestamptz,
  add column if not exists aceita_em timestamptz,
  add column if not exists recusada_em timestamptz,
  add column if not exists expira_em timestamptz;

alter table public.cti_propostas
  drop constraint if exists cti_propostas_status_documento_check;

alter table public.cti_propostas
  add constraint cti_propostas_status_documento_check check (
    status_documento in (
      'RASCUNHO','EM_REVISAO','APROVADA_INTERNA','EMITIDA','ENVIADA','VISUALIZADA',
      'EM_NEGOCIACAO','ACEITA','RECUSADA','EXPIRADA','CANCELADA','CONVERTIDA_PEDIDO'
    )
  );

create unique index if not exists cti_propostas_item_versao_unique
  on public.cti_propostas(item_oportunidade_id, versao)
  where item_oportunidade_id is not null;

create table if not exists public.cti_proposta_aceites (
  id uuid primary key default gen_random_uuid(),
  proposta_id uuid not null references public.cti_propostas(id) on delete cascade,
  metodo text not null,
  nome_signatario text not null,
  documento_signatario text,
  email_signatario text,
  telefone_signatario text,
  assinatura_desenhada text,
  codigo_validacao_hash text,
  aceite_termos boolean not null default false,
  ip_origem inet,
  user_agent text,
  latitude numeric(10,7),
  longitude numeric(10,7),
  evidencias jsonb not null default '{}'::jsonb,
  status text not null default 'PENDENTE',
  solicitado_em timestamptz not null default now(),
  visualizado_em timestamptz,
  aceito_em timestamptz,
  recusado_em timestamptz,
  constraint cti_proposta_aceites_metodo_check check (
    metodo in ('PRESENCIAL_TELA','REMOTO_LINK')
  ),
  constraint cti_proposta_aceites_status_check check (
    status in ('PENDENTE','VISUALIZADO','ACEITO','RECUSADO','EXPIRADO','CANCELADO')
  )
);

create index if not exists cti_proposta_aceites_proposta_idx
  on public.cti_proposta_aceites(proposta_id, solicitado_em desc);

alter table public.cti_pedidos
  add column if not exists proposta_aceita_id uuid references public.cti_propostas(id) on delete restrict,
  add column if not exists item_oportunidade_id uuid references public.cti_oportunidade_itens(id) on delete restrict,
  add column if not exists aceite_id uuid references public.cti_proposta_aceites(id) on delete restrict,
  add column if not exists dossie_documentos jsonb not null default '[]'::jsonb,
  add column if not exists enviado_carrier_em timestamptz,
  add column if not exists status_envio_carrier text not null default 'NAO_ENVIADO';

alter table public.cti_pedidos
  drop constraint if exists cti_pedidos_status_envio_carrier_check;

alter table public.cti_pedidos
  add constraint cti_pedidos_status_envio_carrier_check check (
    status_envio_carrier in ('NAO_ENVIADO','PREPARANDO','ENVIADO','FALHA','REENVIADO','CONFIRMADO')
  );

create table if not exists public.cti_destinatarios_carrier (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  email text not null,
  cargo text,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (lower(email))
);

create table if not exists public.cti_envios_carrier (
  id uuid primary key default gen_random_uuid(),
  pedido_id uuid references public.cti_pedidos(id) on delete cascade,
  proposta_id uuid references public.cti_propostas(id) on delete cascade,
  destinatarios jsonb not null default '[]'::jsonb,
  documentos jsonb not null default '[]'::jsonb,
  assunto text not null,
  corpo text,
  status text not null default 'PENDENTE',
  tentativas integer not null default 0,
  erro text,
  enviado_por uuid,
  created_at timestamptz not null default now(),
  enviado_em timestamptz,
  constraint cti_envios_carrier_status_check check (
    status in ('PENDENTE','ENVIANDO','ENVIADO','FALHA','CANCELADO')
  )
);

create index if not exists cti_envios_carrier_pedido_idx
  on public.cti_envios_carrier(pedido_id, created_at desc);

commit;
