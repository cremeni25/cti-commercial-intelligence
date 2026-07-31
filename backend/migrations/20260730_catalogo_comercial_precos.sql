begin;

create table if not exists public.cti_catalogo_equipamentos (
  codigo text primary key,
  linha_produto text not null,
  modelo_base text not null,
  nome_comercial text not null,
  configuracao text not null default 'PADRAO',
  compressor text,
  possui_eletrico boolean not null default false,
  descricao_tecnica jsonb not null default '{}'::jsonb,
  template_disponivel boolean not null default false,
  ativo boolean not null default true,
  ordem integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint cti_catalogo_configuracao_check check (configuracao in ('PADRAO','ACOPLADO','ACOPLADO_E_ELETRICO'))
);

create table if not exists public.cti_tabela_precos (
  id uuid primary key default gen_random_uuid(),
  tabela_codigo text not null,
  equipamento_codigo text not null references public.cti_catalogo_equipamentos(codigo) on delete restrict,
  preco_cheio numeric(14,2) not null default 0 check (preco_cheio >= 0),
  moeda text not null default 'BRL',
  vigencia_inicio date not null,
  vigencia_fim date,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tabela_codigo, equipamento_codigo, vigencia_inicio)
);

alter table public.cti_oportunidade_itens
  add column if not exists equipamento_codigo text references public.cti_catalogo_equipamentos(codigo) on delete restrict,
  add column if not exists modelo_base text,
  add column if not exists nome_comercial text,
  add column if not exists preco_tabela numeric(14,2),
  add column if not exists tabela_preco_codigo text,
  add column if not exists tabela_preco_vigencia date,
  add column if not exists compressor text,
  add column if not exists possui_eletrico boolean not null default false;

insert into public.cti_catalogo_equipamentos
(codigo, linha_produto, modelo_base, nome_comercial, configuracao, compressor, possui_eletrico, template_disponivel, ordem)
values
('VECTOR-8600-MT','TRAILER','VECTOR 8600 MT','VECTOR 8600 MT','PADRAO',null,false,false,10),
('VECTOR-8500','TRAILER','VECTOR 8500','VECTOR 8500','PADRAO',null,false,false,20),
('VECTOR-HE19','TRAILER','VECTOR HE 19','VECTOR HE 19','PADRAO',null,false,false,30),
('X4-7700','TRAILER','X4 7700','X4 7700','PADRAO',null,false,false,40),
('X4-7500','TRAILER','X4 7500','X4 7500','PADRAO',null,false,false,50),
('SUPRA-1150','DIESEL TRUCK','SUPRA 1150','SUPRA 1150','PADRAO','05G 6CC',true,true,100),
('SUPRA-850-MT','DIESEL TRUCK','SUPRA 850 MT','SUPRA 850 MT','PADRAO',null,true,false,110),
('SUPRA-850','DIESEL TRUCK','SUPRA 850','SUPRA 850','PADRAO','05K 4CC',true,true,120),
('SUPRA-750','DIESEL TRUCK','SUPRA 750','SUPRA 750','PADRAO','05K 2CC',true,true,130),
('S8','DIESEL TRUCK','S8','S8','PADRAO','05K 2CC',true,true,140),
('S9','DIESEL TRUCK','S9','S9','PADRAO','05K 4CC',true,true,150),
('CITIMAX-D7-AE','DIRECT DRIVE','CITIMAX D7','CITIMAX D7AE','ACOPLADO_E_ELETRICO',null,true,true,200),
('CITIMAX-D7','DIRECT DRIVE','CITIMAX D7','CITIMAX D7','ACOPLADO',null,false,true,210),
('CITIMAX-D6-AE','DIRECT DRIVE','CITIMAX D6','CITIMAX D6AE','ACOPLADO_E_ELETRICO','TM16',true,true,220),
('CITIMAX-D6','DIRECT DRIVE','CITIMAX D6','CITIMAX D6','ACOPLADO','TM16',false,true,230),
('CITIMAX-500-AE','DIRECT DRIVE','CITIMAX 500','CITIMAX 500AE','ACOPLADO_E_ELETRICO','TM16',true,true,240),
('CITIMAX-500','DIRECT DRIVE','CITIMAX 500','CITIMAX 500','ACOPLADO','TM16',false,true,250),
('CITIMAX-400-AE','DIRECT DRIVE','CITIMAX 400','CITIMAX 400AE','ACOPLADO_E_ELETRICO',null,true,true,260),
('CITIMAX-400','DIRECT DRIVE','CITIMAX 400','CITIMAX 400','ACOPLADO',null,false,true,270),
('CITIMAX-280','DIRECT DRIVE','CITIMAX 280','CITIMAX 280','PADRAO',null,false,true,280),
('XARIOS-350','DIRECT DRIVE','XARIOS 350','XARIOS 350','PADRAO','QP15',true,true,290),
('XARIOS-6','DIRECT DRIVE','XARIOS 6','XARIOS 6','PADRAO','QP16',true,true,300)
on conflict (codigo) do update set
  linha_produto = excluded.linha_produto,
  modelo_base = excluded.modelo_base,
  nome_comercial = excluded.nome_comercial,
  configuracao = excluded.configuracao,
  compressor = excluded.compressor,
  possui_eletrico = excluded.possui_eletrico,
  template_disponivel = excluded.template_disponivel,
  ordem = excluded.ordem,
  updated_at = now();

insert into public.cti_tabela_precos
(tabela_codigo, equipamento_codigo, preco_cheio, moeda, vigencia_inicio, ativo)
values
('TABELA-INICIAL-2026','VECTOR-8600-MT',0,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','VECTOR-8500',178000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','VECTOR-HE19',169000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','X4-7700',172000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','X4-7500',158000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','SUPRA-1150',128000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','SUPRA-850-MT',0,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','SUPRA-850',113000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','SUPRA-750',105000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','S8',0,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','S9',0,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-D7-AE',45000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-D7',29000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-D6-AE',43000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-D6',28000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-500-AE',41000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-500',27000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-400-AE',0,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-400',18500,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-280',14500,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','XARIOS-350',43000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','XARIOS-6',53000,'BRL','2026-07-30',true)
on conflict (tabela_codigo, equipamento_codigo, vigencia_inicio) do update set
  preco_cheio = excluded.preco_cheio,
  moeda = excluded.moeda,
  ativo = excluded.ativo,
  updated_at = now();

commit;
