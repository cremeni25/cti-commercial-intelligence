create schema if not exists historico_staging;

revoke all on schema historico_staging from public, anon, authenticated;
grant usage on schema historico_staging to service_role;

create table historico_staging.importacoes (
  id uuid primary key default gen_random_uuid(),
  arquivo_nome text not null,
  arquivo_hash_sha256 text not null,
  arquivo_tamanho_bytes bigint,
  versao_fonte text,
  data_arquivo date,
  quantidade_abas integer not null default 0 check (quantidade_abas >= 0),
  quantidade_registros integer not null default 0 check (quantidade_registros >= 0),
  status_importacao text not null default 'PREPARADA' check (status_importacao in ('PREPARADA','PROCESSANDO','PROCESSADA','FALHA','HOMOLOGADA','REJEITADA')),
  homologado boolean not null default false,
  homologado_por uuid,
  homologado_em timestamptz,
  metadados jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (arquivo_hash_sha256)
);

create table historico_staging.registros (
  id uuid primary key default gen_random_uuid(),
  importacao_id uuid not null references historico_staging.importacoes(id) on delete restrict,
  arquivo_origem text not null,
  aba_origem text not null check (aba_origem in ('BACKLOG','OPORTUNIDADE','INTERMEDIAÇÃO - OEM')),
  linha_origem integer not null check (linha_origem > 0),
  registro_original jsonb not null,
  registro_hash text not null,

  representante_original text,
  representante_normalizado text,
  representante_id uuid,
  status_reconciliacao_representante text not null default 'PENDENTE',

  cliente_original text,
  cliente_normalizado text,
  cliente_id uuid,
  cnpj_original text,
  status_reconciliacao_cliente text not null default 'PENDENTE',

  equipamento_original text,
  equipamento_normalizado text,
  equipamento_codigo text,
  status_reconciliacao_equipamento text not null default 'PENDENTE',

  quantidade_original text,
  quantidade_normalizada numeric(14,3),
  valor_unitario_original text,
  valor_unitario_normalizado numeric(18,2),
  valor_total_original text,
  valor_total_normalizado numeric(18,2),

  data_original text,
  data_normalizada date,
  previsao_original text,
  previsao_mes smallint check (previsao_mes between 1 and 12),
  previsao_ano smallint,
  previsao_data date,
  precisao_previsao text check (precisao_previsao is null or precisao_previsao in ('MES','DATA','DESCONHECIDA')),

  probabilidade_original text,
  probabilidade_normalizada numeric(7,4),
  confianca_probabilidade numeric(5,4) check (confianca_probabilidade is null or (confianca_probabilidade between 0 and 1)),

  status_original text,
  status_normalizado text,
  motivo_perda_normalizado text,
  observacao_original text,

  canal_venda text not null check (canal_venda in ('DIRETA','INDIRETA_OEM')),
  implementadora_original text,
  implementadora_normalizada text,
  implementadora_id uuid,
  status_reconciliacao_implementadora text not null default 'PENDENTE',

  status_reconciliacao text not null default 'PENDENTE',
  confianca_normalizacao numeric(5,4) check (confianca_normalizacao is null or (confianca_normalizacao between 0 and 1)),
  flags_validacao jsonb not null default '[]'::jsonb,

  homologado boolean not null default false,
  homologado_por uuid,
  homologado_em timestamptz,
  promovido boolean not null default false,
  promovido_em timestamptz,
  destino_promocao text,
  destino_id text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (importacao_id, aba_origem, linha_origem),
  unique (importacao_id, registro_hash),
  check ((canal_venda = 'DIRETA' and implementadora_id is null) or canal_venda = 'INDIRETA_OEM')
);

create table historico_staging.reconciliacoes (
  id uuid primary key default gen_random_uuid(),
  registro_id uuid not null references historico_staging.registros(id) on delete cascade,
  entidade_tipo text not null check (entidade_tipo in ('CLIENTE','REPRESENTANTE','EQUIPAMENTO','IMPLEMENTADORA')),
  valor_original text,
  valor_normalizado text,
  candidato_id text,
  candidato_nome text,
  metodo text,
  confianca numeric(5,4) check (confianca is null or (confianca between 0 and 1)),
  status text not null default 'PENDENTE' check (status in ('PENDENTE','RECONCILIADO','AMBIGUO','NAO_ENCONTRADO','REJEITADO')),
  decisao_por uuid,
  decisao_em timestamptz,
  observacao text,
  created_at timestamptz not null default now()
);

create table historico_staging.alias_clientes (
  id uuid primary key default gen_random_uuid(),
  valor_origem text not null,
  valor_normalizado text not null,
  cliente_id uuid,
  ativo boolean not null default true,
  origem_regra text,
  created_at timestamptz not null default now(),
  unique (valor_normalizado)
);

create table historico_staging.alias_representantes (
  id uuid primary key default gen_random_uuid(),
  valor_origem text not null,
  valor_normalizado text not null,
  representante_id uuid,
  representante_atual text,
  regra_temporal_territorial text,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  unique (valor_normalizado)
);

create table historico_staging.alias_equipamentos (
  id uuid primary key default gen_random_uuid(),
  valor_origem text not null,
  valor_normalizado text not null,
  equipamento_codigo text,
  ativo boolean not null default true,
  origem_regra text,
  created_at timestamptz not null default now(),
  unique (valor_normalizado)
);

create table historico_staging.alias_implementadoras (
  id uuid primary key default gen_random_uuid(),
  valor_origem text not null,
  valor_normalizado text not null,
  implementadora_id uuid,
  ativo boolean not null default true,
  origem_regra text,
  created_at timestamptz not null default now(),
  unique (valor_normalizado)
);

create table historico_staging.validacoes (
  id uuid primary key default gen_random_uuid(),
  importacao_id uuid not null references historico_staging.importacoes(id) on delete cascade,
  registro_id uuid references historico_staging.registros(id) on delete cascade,
  codigo text not null,
  severidade text not null check (severidade in ('INFO','AVISO','ERRO','BLOQUEIO')),
  campo text,
  mensagem text not null,
  detalhes jsonb not null default '{}'::jsonb,
  resolvido boolean not null default false,
  resolvido_por uuid,
  resolvido_em timestamptz,
  created_at timestamptz not null default now()
);

create index idx_hist_registros_importacao on historico_staging.registros(importacao_id);
create index idx_hist_registros_cliente_norm on historico_staging.registros(cliente_normalizado);
create index idx_hist_registros_equip_norm on historico_staging.registros(equipamento_normalizado);
create index idx_hist_registros_representante_norm on historico_staging.registros(representante_normalizado);
create index idx_hist_registros_canal on historico_staging.registros(canal_venda);
create index idx_hist_registros_impl_norm on historico_staging.registros(implementadora_normalizada);
create index idx_hist_reconciliacoes_registro on historico_staging.reconciliacoes(registro_id);
create index idx_hist_validacoes_importacao on historico_staging.validacoes(importacao_id);
create index idx_hist_validacoes_registro on historico_staging.validacoes(registro_id);

alter table historico_staging.importacoes enable row level security;
alter table historico_staging.registros enable row level security;
alter table historico_staging.reconciliacoes enable row level security;
alter table historico_staging.alias_clientes enable row level security;
alter table historico_staging.alias_representantes enable row level security;
alter table historico_staging.alias_equipamentos enable row level security;
alter table historico_staging.alias_implementadoras enable row level security;
alter table historico_staging.validacoes enable row level security;

revoke all on all tables in schema historico_staging from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema historico_staging to service_role;

comment on schema historico_staging is 'CTI HIST: staging historico isolado. Nao e fonte operacional nem fonte oficial da IA.';
comment on table historico_staging.registros is 'Registros historicos preservando origem e normalizacao; promocao permanece bloqueada por processo externo e autorizacao humana.';
